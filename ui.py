import logging
import time

import discord
from discord import ui
from sqlalchemy import select

from config import CARGO_GESTOR_ID, CANAL_LOJA_ID
from database import Produto, Session
from pagamentos import gerar_pagamento, verificar_pagamento
from utils import marcar_loja_para_atualizar

logger = logging.getLogger(__name__)

class GerenciarProdutos(ui.LayoutView):
    def __init__(self):
        super().__init__()

        container = ui.Container()
        container.add_item(ui.TextDisplay("## Gerenciar Produtos"))

        self.add_item(container)

        with Session() as session:
            produtos = session.query(Produto).all()
            if not produtos:
                container.add_item(ui.TextDisplay("Nenhum produto cadastrado!"))
            else:
                self.produtos = produtos
                for produto in produtos:
                    produto_info = []
                    produto_info.append(f"## {produto.nome}\n")
                    produto_info.append(f"**Preço:** `{produto.preco}`\n")
                    produto_info.append(f"**Estoque:** `{produto.estoque}`\n")
                    produto_info.append(f"✅ **Ativo**" if produto.ativo else "❌ **Inativo**")
                    if produto.descricao:
                        produto_info.append(f"\n```{produto.descricao}```")
                    
                    container.add_item(ui.TextDisplay("".join(produto_info)))

                    botoes_produto = ui.ActionRow()
                    botoes_produto.add_item(EditarProdutoBotao(produto.id))
                    botoes_produto.add_item(RemoverProdutoBotao(produto.id))

                    container.add_item(botoes_produto)
                    container.add_item(ui.Separator())

                botoes = ui.ActionRow() 
                botoes.add_item(AdicionarProdutoBotao())
                container.add_item(botoes)

class VerProdutos(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = ui.Container()
        container.add_item(ui.TextDisplay("# Explore nossos produtos!"))

        self.add_item(container)

        with Session() as session:
            produtos = session.query(Produto).filter_by(ativo=True).all()
            if not produtos:
                container.add_item(ui.TextDisplay("Nenhum produto disponível."))
            else:
                self.produtos = produtos
                for produto in produtos:
                    produto_info = []
                    produto_info.append(f"## {produto.nome}\n")
                    produto_info.append(f"**Preço:** `{produto.preco}`\n")
                    produto_info.append(f"**Estoque:** `{produto.estoque}`\n")
                    if produto.descricao:
                        produto_info.append(f"\n```{produto.descricao}```")
                    
                    container.add_item(ui.TextDisplay("".join(produto_info)))

                    botoes_produto = ui.ActionRow()
                    botoes_produto.add_item(ComprarProdutoBotao(produto.id))

                    container.add_item(botoes_produto)
                    container.add_item(ui.Separator())

class ComprarProdutoBotao(ui.Button):
    cooldown_segundos = 10
    _cooldowns = {}

    def __init__(self, produto_id):
        super().__init__(label="Comprar", style=discord.ButtonStyle.green, custom_id=f"Comprar_{produto_id}")
        self.produto_id = produto_id

    @classmethod
    def _tempo_restante(cls, user_id:int):
        expira = cls._cooldowns.get(user_id, 0)
        restante = expira - time.monotonic()
        return restante if restante > 0 else 0

    @classmethod
    def _em_cooldown(cls, user_id:int):
        return cls._tempo_restante(user_id) > 0

    @classmethod
    def _definir_cooldown(cls, user_id:int):
        cls._cooldowns[user_id] = time.monotonic() + cls.cooldown_segundos

    def _consumir_estoque(self):
        with Session() as session:
            transacao = session.begin()
            try:
                resultado = session.execute(
                    select(Produto).where(Produto.id == self.produto_id).with_for_update()
                ).scalar_one_or_none()
                if not resultado or resultado.estoque <= 0:
                    transacao.rollback()
                    logger.warning("Tentativa de compra sem estoque para produto %s", self.produto_id)
                    return False

                resultado.estoque -= 1
                transacao.commit()
            except Exception:
                transacao.rollback()
                raise

        marcar_loja_para_atualizar()
        return True

    async def _notificar_gestores(self, interact:discord.Interaction, produto_nome:str):
        canal = interact.client.get_channel(CANAL_LOJA_ID)
        if not canal:
            try:
                canal = await interact.client.fetch_channel(CANAL_LOJA_ID)
            except Exception:
                logger.exception("Não foi possível notificar o canal de gestão %s", CANAL_LOJA_ID)
                return

        await canal.send(f"Nova compra realizada por {interact.user.mention}: **{produto_nome}**.")
    
    async def callback(self, interact:discord.Interaction):
        if self._em_cooldown(interact.user.id):
            restante = int(self._tempo_restante(interact.user.id)) + 1
            return await interact.response.send_message(f"Aguarde {restante}s antes de tentar novamente.", ephemeral=True)

        self._definir_cooldown(interact.user.id)
        await interact.response.defer(ephemeral=True)

        with Session() as session:
            produto:Produto = session.query(Produto).get(self.produto_id)
            if not produto or not produto.ativo:
                return await interact.followup.send("Produto indisponível no momento.", ephemeral=True)

            if produto.estoque <= 0:
                return await interact.followup.send("Produto sem estoque!", ephemeral=True)

            preco = produto.preco
            produto_nome = produto.nome
            descricao = produto.descricao

        pagamento_id, qrcode = gerar_pagamento(preco, interact.user.id, self.produto_id)
        if not pagamento_id or not qrcode:
            return await interact.followup.send("Não foi possível gerar o pagamento. Tente novamente mais tarde.", ephemeral=True)

        qrcode = discord.File(qrcode, filename="qrcode.png")
        embed = discord.Embed(
            title="Realize o pagamento no QR Code abaixo para prosseguir.",
            description=f"Produto: **{produto_nome}**\nValor: R$ {preco:.2f}",
            color=discord.Colour.green()
        )
        if descricao:
            embed.add_field(name="Descrição", value=descricao[:1024], inline=False)
        embed.set_image(url="attachment://qrcode.png")

        pagamento_msg = await interact.followup.send(embed=embed, ephemeral=True, file=qrcode)

        pagamento_status = await verificar_pagamento(
            pagamento_id,
            preco,
            interact.user.id,
            self.produto_id,
            cooldown=5
        )
        if not pagamento_status:
            await interact.followup.send("O pagamento não foi encontrado. Caso o tenha feito, entre com contato com o suporte.", ephemeral=True)
            await pagamento_msg.delete()
            return

        if not self._consumir_estoque():
            await interact.followup.send("O estoque do produto acabou antes de concluirmos sua compra.", ephemeral=True)
            await pagamento_msg.delete()
            return

        logger.info("Compra confirmada do produto %s pelo usuário %s", self.produto_id, interact.user.id)
            
        canal_loja = interact.channel
        ticket = await canal_loja.create_thread(name=interact.user.name, type=discord.ChannelType.private_thread)
        await ticket.add_user(interact.user)
        await ticket.send(f"Olá, {interact.user.name}! Obrigado por comprar conosco. Aguarde um momento que jajá alguém virá te atender!\nProduto: {produto_nome}\n<@&{CARGO_GESTOR_ID}>")

        await self._notificar_gestores(interact, produto_nome)
        await interact.followup.send(embed=discord.Embed(title=f"O pagamento foi concluído com sucesso!\nProssiga para o ticket: {ticket.mention}"), ephemeral=True)
        await pagamento_msg.delete()

class AdicionarProdutoBotao(ui.Button):
    def __init__(self):
        super().__init__(label="Adicionar Produto", style=discord.ButtonStyle.green)
    
    async def callback(self, interact:discord.Interaction):
        await interact.response.send_modal(ProdutoModal())


class RemoverProdutoBotao(ui.Button):
    def __init__(self, produto_id):
        super().__init__(label="Remover", style=discord.ButtonStyle.red)
        self.produto_id = produto_id
    
    async def callback(self, interact:discord.Interaction):
        produto_id = self.produto_id
        with Session() as session:
            produto = session.query(Produto).get(produto_id)
            if not produto:
                return await interact.response.send_message("Produto não encontrado.", ephemeral=True)
            session.delete(produto)
            session.commit()
            marcar_loja_para_atualizar()
            logger.info("Produto %s removido por %s", produto.nome, interact.user.id)
        
        await interact.response.send_message(f"Produto deletado com sucesso!", ephemeral=True)
        await interact.message.edit(view=GerenciarProdutos())

class EditarProdutoBotao(ui.Button):
    def __init__(self, produto_id):
        super().__init__(label="Editar", style=discord.ButtonStyle.blurple)
        self.produto_id = produto_id
    
    async def callback(self, interact:discord.Interaction):
        await interact.response.send_modal(ProdutoModal(self.produto_id))

class ProdutoModal(ui.Modal):
    def __init__(self, produto_id=None):
        super().__init__(title="Formulário")
        self.produto_id = produto_id

        self.nome = ui.TextInput(label="Nome do produto")
        self.preco = ui.TextInput(label="Preço do produto")
        self.descricao = ui.TextInput(label="Descrição do produto", style=discord.TextStyle.long, required=False)
        self.estoque = ui.TextInput(label="Estoque do produto", required=False)
        self.ativo = ui.TextInput(label="Visível para usuários", placeholder="Digite apenas 'sim' ou 'não'")

        if produto_id:
            with Session() as session:
                produto:Produto = session.query(Produto).get(produto_id)
                self.nome.default = produto.nome
                self.preco.default = str(produto.preco)
                self.descricao.default = produto.descricao
                self.estoque.default = str(produto.estoque)
                self.ativo.default = "sim" if produto.ativo else "não"

        self.add_item(self.nome)
        self.add_item(self.preco)
        self.add_item(self.descricao)
        self.add_item(self.estoque)
        self.add_item(self.ativo)

    async def on_submit(self, interact:discord.Interaction):
        nome = self.nome.value
        preco = self.preco.value
        descricao = self.descricao.value
        estoque = self.estoque.value
        ativo = self.ativo.value


        try:
            preco = float(preco)
        except:
            return await interact.response.send_message(f"Digite um preço válido.", ephemeral=True)
        
        if estoque != "":
            try:
                estoque = int(estoque)
            except:
                return await interact.response.send_message(f"Digite um estoque válido", ephemeral=True)
        else:
            estoque = 0
        
        if ativo != "" and ativo.lower() not in ["sim", "não", "s", "n", "nao"]:
            return await interact.response.send_message(f"Erro no ativo. Digite apenas 'Sim' ou 'Não'.")
        else:
            if ativo.lower().startswith("s"):
                ativo = True
            else:
                ativo = False

        await interact.response.defer()

        with Session() as session:
            if self.produto_id:
                produto:Produto = session.query(Produto).get(self.produto_id)
                produto.nome = nome
                produto.preco = preco
                produto.descricao = descricao
                produto.estoque = estoque
                produto.ativo = ativo
                session.commit()
                marcar_loja_para_atualizar()
                logger.info("Produto %s atualizado por %s", produto.id, interact.user.id)

                msg = "Produto editado com sucesso!"
            else:
                produto = Produto(nome=nome, descricao=descricao, preco=preco, estoque=estoque, ativo=ativo)
                session.add(produto)
                session.commit()
                marcar_loja_para_atualizar()
                logger.info("Produto %s criado por %s", produto.id, interact.user.id)

                msg = "Produto adicionado com sucesso!"
            
        await interact.followup.send(msg, ephemeral=True)
        await interact.message.edit(view=GerenciarProdutos())

    
                


