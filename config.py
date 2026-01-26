from dotenv import load_dotenv
from os import getenv

load_dotenv(".env", override=True)

BOT_TOKEN = getenv("BOT_TOKEN")
MP_TOKEN = getenv("MP_TOKEN")
DATABASE_URI = getenv("DATABASE_URI")
CARGO_GESTOR_ID = int(getenv("CARGO_GESTOR_ID"))
CANAL_LOJA_ID = int(getenv("CANAL_LOJA_ID"))