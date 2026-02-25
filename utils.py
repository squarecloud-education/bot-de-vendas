import discord

from config import CARGO_GESTOR_ID

_loja_precisa_atualizar = True

def verificar_gestor(membro:discord.Member):
    for cargo in membro.roles:
        if cargo.id == CARGO_GESTOR_ID:
            return True
    
    return False


def marcar_loja_para_atualizar():
    global _loja_precisa_atualizar
    _loja_precisa_atualizar = True


def consumir_sinalizacao_loja():
    global _loja_precisa_atualizar
    if not _loja_precisa_atualizar:
        return False

    _loja_precisa_atualizar = False
    return True
