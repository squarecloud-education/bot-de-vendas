import discord
from discord.ext import commands, tasks
from discord import Intents
from config import BOT_TOKEN, CANAL_LOJA_ID
from utils import verificar_gestor
from ui import GerenciarProdutos, VerProdutos

bot = commands.Bot("!", intents=Intents.all())

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerProdutos())
    atualizar_loja.start()

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

@tasks.loop(minutes=1)
async def atualizar_loja():
    canal = await bot.fetch_channel(CANAL_LOJA_ID)
    async for msg in canal.history(limit=1):
        await msg.edit(view=VerProdutos())

bot.run(BOT_TOKEN)