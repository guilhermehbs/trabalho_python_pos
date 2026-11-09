"""Roda o pipeline inteiro.

Uso:
    python src/main.py                 # ingestão, qualidade, ETL, EDA e gráficos
    python src/main.py --somente-eda   # usa o que já está em data/processed/ (pula o ETL)
"""
import argparse

import pandas as pd

import analise
import etl
import ingestao
import qualidade
import visualizacao
from config import DIR_REPORTS


def formatar_resultados(res: dict) -> str:
    """Junta os resultados de cada pergunta num texto só (usado no resultados_eda.txt)."""
    linhas = []
    for titulo, bloco in res.items():
        linhas.append(f"=== {titulo} ===")
        if isinstance(bloco, pd.DataFrame):
            linhas.append(bloco.round(2).to_string())
        elif isinstance(bloco, dict):
            for k, v in bloco.items():
                linhas.append(f"{k}: {round(v, 3) if isinstance(v, float) else v}")
        linhas.append("")
    return "\n".join(linhas)


def rodar_eda(pedidos: pd.DataFrame, itens: pd.DataFrame) -> None:
    """Responde as 4 perguntas, gera os gráficos e salva os números em reports/."""
    mensal, r1 = analise.serie_mensal(pedidos)
    cat, r2 = analise.receita_por_categoria(itens)
    atraso, r3 = analise.atraso_vs_nota(pedidos)
    estados, r4 = analise.entrega_frete_por_estado(pedidos)
    outliers = analise.resumo_outliers(itens)

    visualizacao.grafico_distribuicoes(itens)
    visualizacao.grafico_serie_mensal(mensal)
    visualizacao.grafico_categorias(cat)
    visualizacao.grafico_atraso_nota(atraso)
    visualizacao.grafico_estados(estados, r4["pearson_dias_frete"])

    resultados = {
        "P1 - resumo": r1, "P1 - serie mensal": mensal,
        "P2 - resumo": r2, "P2 - top 15 categorias": cat.head(15),
        "P3 - resumo": r3, "P3 - faixas de atraso": atraso,
        "P4 - resumo": r4, "P4 - estados": estados,
        "Outliers - preco": outliers["preco"], "Outliers - frete": outliers["frete"],
    }
    texto = formatar_resultados(resultados)
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    (DIR_REPORTS / "resultados_eda.txt").write_text(texto, encoding="utf-8")
    print("\n" + texto)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de EDA - Olist")
    parser.add_argument("--somente-eda", action="store_true", help="pula a ingestão e o ETL, usa data/processed/")
    args = parser.parse_args()

    if args.somente_eda:
        dados = etl.carregar_processados()
    else:
        tabelas = ingestao.carregar_todas()
        qualidade.diagnosticar(tabelas)
        qualidade.inconsistencias_brutas(tabelas)
        dados = etl.executar_etl(tabelas)

    rodar_eda(dados["pedidos"], dados["itens"])


if __name__ == "__main__":
    main()
