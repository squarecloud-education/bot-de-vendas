from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URI

engine = create_engine(DATABASE_URI)
Base = declarative_base()

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    descricao = Column(String, nullable=True)
    preco = Column(Float)
    estoque = Column(Integer, default=0)
    ativo = Column(Boolean, default=False)

Base.metadata.create_all(engine)
Session = sessionmaker(engine)