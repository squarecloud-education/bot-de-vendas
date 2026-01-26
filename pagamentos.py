import mercadopago, base64, io, asyncio
from config import MP_TOKEN

mp_sdk = mercadopago.SDK(MP_TOKEN)

def gerar_pagamento(valor):
    dados_pagamento = {
        "transaction_amount":valor,
        "payment_method_id":"pix",
        "payer":{
            "email":"payer_email@gmail.com"
        }
    }
    pagamento = mp_sdk.payment().create(dados_pagamento)

    id = pagamento['response']['id']
    qrcode = pagamento['response']['point_of_interaction']['transaction_data']['qr_code_base64']
    qrcode = base64.b64decode(qrcode)
    qrcode = io.BytesIO(qrcode)

    return id, qrcode

async def verificar_pagamento(pagamento_id, tentativas = 20, cooldown=10):
    for t in range(tentativas-1):
        await asyncio.sleep(cooldown)

        pagamento = mp_sdk.payment().get(pagamento_id)
        situacao = pagamento['response']['status']

        if situacao == "approved":
            return situacao
    
    return False