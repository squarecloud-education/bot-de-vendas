import discord
from config import CARGO_GESTOR_ID

def verificar_gestor(membro:discord.Member):
    for cargo in membro.roles:
        if cargo.id == CARGO_GESTOR_ID:
            return True
    
    return False