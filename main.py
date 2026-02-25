import logging

import discord
from discord import Intents
from discord.ext import commands, tasks

from config import BOT_TOKEN, CANAL_LOJA_ID
from utils import consumir_sinalizacao_loja, verificar_gestor
from ui import GerenciarProdutos, VerProdutos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = commands.Bot("!", intents=Intents.all())

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerProdutos())
    if consumir_sinalizacao_loja():
        await atualizar_loja_view()
    atualizar_loja.start()
    logger.info("Bot iniciado como %s", bot.user)

@bot.tree.command()
async def gerenciar(interact:discord.Interaction):
    if not verificar_gestor(interact.user):
        return await interact.response.send_message("Você não tem permissão pra usar esse comando!", ephemeral=True)
    
    await interact.response.send_message(view=GerenciarProdutos())

@bot.command()
async def mostrar_produtos(ctx:commands.Context):
    if not verificar_gestor(ctx.author):
        return
    
    await ctx.send(view=VerProdutos())
    await ctx.message.delete()

async def atualizar_loja_view():
    canal = await bot.fetch_channel(CANAL_LOJA_ID)
    async for msg in canal.history(limit=1):
        await msg.edit(view=VerProdutos())
    logger.info("Loja atualizada no canal %s", CANAL_LOJA_ID)

@tasks.loop(minutes=1)
async def atualizar_loja():
    if not consumir_sinalizacao_loja():
        return
    await atualizar_loja_view()

bot.run(BOT_TOKEN)
