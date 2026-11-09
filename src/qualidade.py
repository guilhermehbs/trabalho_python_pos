"""Diagnóstico de qualidade dos dados.

As funções daqui só olham os dados, não mudam nada. A correção fica no etl.py,
para manter separado o que é diagnosticar e o que é corrigir.
"""
import numpy as np
import pandas as pd

from config import COLUNAS_DATA, DIR_REPORTS, FATOR_IQR


def nulos_por_coluna(df: pd.DataFrame) -> pd.DataFrame:
    """Quantidade e percentual de nulos por coluna (só mostra as que têm algum)."""
    qtd = df.isna().sum()
    resultado = pd.DataFrame({"nulos": qtd, "pct_nulos": (qtd / len(df) * 100).round(2)})
    return resultado[resultado["nulos"] > 0].sort_values("nulos", ascending=False)


def contar_duplicatas(df: pd.DataFrame, chave: list[str] | None = None) -> dict:
    """Conta linhas totalmente repetidas e, se passar a chave, repetidas pela chave."""
    info = {"duplicatas_linha_inteira": int(df.duplicated().sum())}
    if chave:
        info[f"duplicatas_chave_{'+'.join(chave)}"] = int(df.duplicated(subset=chave).sum())
    return info


def tipos_inferidos_vs_esperados(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    """Compara o tipo que o pandas inferiu com o esperado (só as datas têm tipo diferente)."""
    esperados_data = set(COLUNAS_DATA.get(nome, []))
    linhas = []
    for col in df.columns:
        esperado = "datetime64" if col in esperados_data else str(df[col].dtype)
        inferido = str(df[col].dtype)
        linhas.append(
            {
                "coluna": col,
                "tipo_inferido": inferido,
                "tipo_esperado": esperado,
                "inadequado": esperado.startswith("datetime") and not inferido.startswith("datetime"),
            }
        )
    return pd.DataFrame(linhas)


def detectar_outliers_iqr(serie: pd.Series, fator: float = FATOR_IQR) -> dict:
    """Marca outliers pelo intervalo interquartil (IQR).

    Devolve os limites e quantos valores ficaram fora. Não remove nada.
    """
    s = serie.dropna()
    q1, q3 = np.percentile(s, [25, 75])
    iqr = q3 - q1
    inf, sup = q1 - fator * iqr, q3 + fator * iqr
    mask = (s < inf) | (s > sup)
    return {
        "q1": float(q1),
        "q3": float(q3),
        "limite_inferior": float(inf),
        "limite_superior": float(sup),
        "n_outliers": int(mask.sum()),
        "pct_outliers": round(float(mask.mean() * 100), 2),
        "maximo": float(s.max()),
    }


def diagnosticar(tabelas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Faz o diagnóstico inicial (resumo por tabela) e salva os detalhes em reports/."""
    # chave que deveria identificar cada linha de cada tabela
    chaves = {
        "clientes": ["customer_id"],
        "pedidos": ["order_id"],
        "itens": ["order_id", "order_item_id"],
        "pagamentos": ["order_id", "payment_sequential"],
        "avaliacoes": ["review_id"],
        "produtos": ["product_id"],
        "traducao_categorias": ["product_category_name"],
    }
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)

    resumo, detalhes_nulos, detalhes_tipos = [], [], []
    for nome, df in tabelas.items():
        dup = contar_duplicatas(df, chaves.get(nome))
        nulos = nulos_por_coluna(df)
        tipos = tipos_inferidos_vs_esperados(df, nome)
        resumo.append(
            {
                "tabela": nome,
                "linhas": len(df),
                "colunas": df.shape[1],
                "colunas_com_nulos": len(nulos),
                "total_nulos": int(df.isna().sum().sum()),
                "duplicatas_linha": dup["duplicatas_linha_inteira"],
                "duplicatas_chave": [v for k, v in dup.items() if k.startswith("duplicatas_chave")][0]
                if chaves.get(nome)
                else 0,
                "colunas_tipo_inadequado": int(tipos["inadequado"].sum()),
            }
        )
        detalhes_nulos.append(nulos.assign(tabela=nome).reset_index(names="coluna"))
        detalhes_tipos.append(tipos[tipos["inadequado"]].assign(tabela=nome))

    resumo_df = pd.DataFrame(resumo)
    pd.concat(detalhes_nulos).to_csv(DIR_REPORTS / "diagnostico_nulos.csv", index=False)
    pd.concat(detalhes_tipos).to_csv(DIR_REPORTS / "diagnostico_tipos.csv", index=False)
    resumo_df.to_csv(DIR_REPORTS / "diagnostico_resumo.csv", index=False)

    print("\n[qualidade] DIAGNÓSTICO INICIAL (dados brutos)")
    print(resumo_df.to_string(index=False))
    print("\n[qualidade] Nulos por coluna (tabelas brutas):")
    print(pd.concat(detalhes_nulos).to_string(index=False))
    return resumo_df


def inconsistencias_brutas(tabelas: dict[str, pd.DataFrame]) -> dict:
    """Procura dados que não fazem sentido (ex.: entrega antes da compra) nos dados brutos.

    As datas são convertidas numa cópia só para poder comparar; os dados originais
    não mudam.
    """
    pedidos = tabelas["pedidos"].copy()
    for col in COLUNAS_DATA["pedidos"]:
        pedidos[col] = pd.to_datetime(pedidos[col], errors="coerce")
    itens, pagamentos = tabelas["itens"], tabelas["pagamentos"]
    avaliacoes = tabelas["avaliacoes"]

    entregue = pedidos["order_status"] == "delivered"
    resultado = {
        "pedidos_entregues_sem_data_de_entrega": int(
            (entregue & pedidos["order_delivered_customer_date"].isna()).sum()
        ),
        "entrega_antes_da_compra": int(
            (pedidos["order_delivered_customer_date"] < pedidos["order_purchase_timestamp"]).sum()
        ),
        "itens_com_preco_nao_positivo": int((itens["price"] <= 0).sum()),
        "pagamentos_com_valor_zero": int((pagamentos["payment_value"] <= 0).sum()),
        "pagamentos_tipo_not_defined": int((pagamentos["payment_type"] == "not_defined").sum()),
        "pedidos_com_mais_de_uma_avaliacao": int((avaliacoes.groupby("order_id").size() > 1).sum()),
    }
    out_preco = detectar_outliers_iqr(itens["price"])
    out_frete = detectar_outliers_iqr(itens["freight_value"])
    resultado["outliers_preco_iqr"] = out_preco["n_outliers"]
    resultado["outliers_frete_iqr"] = out_frete["n_outliers"]

    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    pd.Series(resultado, name="ocorrencias").to_csv(DIR_REPORTS / "diagnostico_inconsistencias.csv")
    print("\n[qualidade] INCONSISTÊNCIAS (regras de negócio):")
    for k, v in resultado.items():
        print(f"  {k:<42} {v:>8,}")
    return resultado
