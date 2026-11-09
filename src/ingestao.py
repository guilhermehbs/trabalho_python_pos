"""Leitura dos dados brutos (o "E" do ETL).

Não converto nenhum tipo aqui de propósito: o diagnóstico de qualidade precisa
ver o que o pandas inferiu para comparar com o que era esperado.
"""
from pathlib import Path

import pandas as pd

from config import ARQUIVOS_OLIST, DIR_RAW


def carregar_tabela(nome: str, dir_raw: Path = DIR_RAW) -> pd.DataFrame:
    """Lê uma tabela do Olist pelo nome definido no config (ex.: 'pedidos')."""
    caminho = dir_raw / ARQUIVOS_OLIST[nome]
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}\n"
            "Baixe o dataset em https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce "
            "e extraia os CSVs em data/raw/."
        )
    return pd.read_csv(caminho)


def carregar_todas(dir_raw: Path = DIR_RAW) -> dict[str, pd.DataFrame]:
    tabelas = {nome: carregar_tabela(nome, dir_raw) for nome in ARQUIVOS_OLIST}
    for nome, df in tabelas.items():
        print(f"[ingestão] {nome:<20} {df.shape[0]:>8,} linhas x {df.shape[1]:>2} colunas")
    return tabelas
