import asyncio
import base64
import io
import logging
from decimal import Decimal
from uuid import uuid4

import mercadopago

from config import MP_TOKEN

mp_sdk = mercadopago.SDK(MP_TOKEN)
logger = logging.getLogger(__name__)
_PAGAMENTOS_PROCESSADOS = set()


def _normalizar_valor(valor):
    return round(Decimal(str(valor)), 2)


def gerar_pagamento(valor, usuario_id, produto_id):
    dados_pagamento = {
        "transaction_amount": float(valor),
        "payment_method_id": "pix",
        "payer": {
            "email": f"{usuario_id}@bot.com"
        },
        "metadata": {
            "user_id": usuario_id,
            "produto_id": produto_id,
            "valor": float(valor)
        },
        "external_reference": f"{usuario_id}-{produto_id}-{uuid4()}"
    }

    try:
        pagamento = mp_sdk.payment().create(dados_pagamento)
    except Exception:
        logger.exception("Falha ao gerar pagamento para o produto %s", produto_id)
        return None, None

    response = pagamento.get('response', {})
    pagamento_id = response.get('id')
    if not pagamento_id:
        logger.error("Resposta inválida ao criar pagamento: %s", response)
        return None, None

    qrcode_base64 = response.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64')
    if not qrcode_base64:
        logger.error("QR Code não encontrado na resposta do pagamento %s", pagamento_id)
        return None, None

    qrcode = base64.b64decode(qrcode_base64)
    qrcode = io.BytesIO(qrcode)

    return pagamento_id, qrcode


async def verificar_pagamento(pagamento_id, valor_esperado, usuario_id, produto_id, tentativas=20, cooldown=10):
    valor_normalizado = _normalizar_valor(valor_esperado)
    email_esperado = f"{usuario_id}@bot.com"

    for tentativa in range(tentativas):
        if tentativa:
            await asyncio.sleep(cooldown)

        try:
            pagamento = mp_sdk.payment().get(pagamento_id)
        except Exception:
            logger.exception("Erro ao consultar pagamento %s", pagamento_id)
            continue

        response = pagamento.get('response', {})
        situacao = response.get('status')

        if situacao != "approved":
            continue

        pagamento_unico = response.get('id')
        if pagamento_unico in _PAGAMENTOS_PROCESSADOS:
            logger.warning("Pagamento %s já utilizado", pagamento_unico)
            return False

        valor_recebido = _normalizar_valor(response.get('transaction_amount', 0))
        if valor_recebido != valor_normalizado:
            logger.warning("Valor divergente no pagamento %s", pagamento_unico)
            return False

        payer_email = response.get('payer', {}).get('email')
        if payer_email != email_esperado:
            logger.warning("Usuário divergente no pagamento %s", pagamento_unico)
            return False

        metadata = response.get('metadata') or {}
        if metadata.get('user_id') != usuario_id or metadata.get('produto_id') != produto_id:
            logger.warning("Metadados inválidos no pagamento %s", pagamento_unico)
            return False

        _PAGAMENTOS_PROCESSADOS.add(pagamento_unico)
        return True

    logger.info("Pagamento %s não aprovado nas tentativas configuradas", pagamento_id)
    return False
