"""Análise exploratória (pandas e numpy).

Cada função responde uma das perguntas e devolve tabelas e números.
Os gráficos de cada uma ficam no visualizacao.py.
"""
import numpy as np
import pandas as pd

from config import MIN_PEDIDOS_ESTADO, MIN_PEDIDOS_MES, PERIODO_FIM, PERIODO_INICIO
from qualidade import detectar_outliers_iqr


def _entregues(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Só os pedidos entregues (status 'delivered'), base para receita e prazos."""
    return pedidos[pedidos["order_status"] == "delivered"]


# P1 — Evolução de pedidos e receita
def serie_mensal(pedidos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pedidos, receita e ticket médio por mês, mais a tendência linear da receita."""
    base = _entregues(pedidos).dropna(subset=["valor_produtos"])
    mensal = base.groupby("ano_mes").agg(
        n_pedidos=("order_id", "count"),
        receita=("valor_produtos", "sum"),
        ticket_medio=("valor_produtos", "mean"),
    )
    # recorta o período e tira meses com poucos pedidos (ver config.py), por causa
    # dos poucos registros de 2016 e do fim de 2018
    mensal = mensal.loc[PERIODO_INICIO:PERIODO_FIM]
    mensal = mensal[mensal["n_pedidos"] >= MIN_PEDIDOS_MES].copy()
    mensal["var_receita_pct"] = mensal["receita"].pct_change() * 100

    # comparo 2017 com 2018 só nos mesmos meses (jan a ago), senão a conta fica injusta
    jan_ago_2017 = mensal.loc["2017-01":"2017-08", "receita"].sum()
    jan_ago_2018 = mensal.loc["2018-01":"2018-08", "receita"].sum()
    ped_2017 = mensal.loc["2017-01":"2017-08", "n_pedidos"].sum()
    ped_2018 = mensal.loc["2018-01":"2018-08", "n_pedidos"].sum()

    # tendência linear com numpy: receita = a * mês + b
    x = np.arange(len(mensal))
    coef_a, _ = np.polyfit(x, mensal["receita"].to_numpy(), 1)
    resumo = {
        "mes_inicial": mensal.index[0],
        "mes_final": mensal.index[-1],
        "n_meses": len(mensal),
        "crescimento_receita_pct": float((mensal["receita"].iloc[-1] / mensal["receita"].iloc[0] - 1) * 100),
        "tendencia_receita_por_mes": float(coef_a),
        "receita_jan_ago_2017": float(jan_ago_2017),
        "receita_jan_ago_2018": float(jan_ago_2018),
        "crescimento_yoy_receita_pct": float((jan_ago_2018 / jan_ago_2017 - 1) * 100),
        "crescimento_yoy_pedidos_pct": float((ped_2018 / ped_2017 - 1) * 100),
        "receita_nov_2017": float(mensal.loc["2017-11", "receita"]),
        "alta_nov_2017_vs_out_pct": float(mensal.loc["2017-11", "var_receita_pct"]),
        "mes_pico": mensal["receita"].idxmax(),
        "receita_pico": float(mensal["receita"].max()),
        "ticket_medio_geral": float(base["valor_produtos"].mean()),
        "ticket_mediano_geral": float(base["valor_produtos"].median()),
    }
    return mensal, resumo


# P2 — Receita por categoria
def receita_por_categoria(itens: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Receita, preço médio e mediano e concentração (Pareto) por categoria."""
    base = itens[itens["order_status"] == "delivered"]
    cat = base.groupby("categoria").agg(
        receita=("price", "sum"),
        n_itens=("order_item_id", "count"),
        preco_medio=("price", "mean"),
        preco_mediano=("price", "median"),
    )
    cat = cat.sort_values("receita", ascending=False)
    cat["pct_receita"] = cat["receita"] / cat["receita"].sum() * 100
    cat["pct_acumulado"] = cat["pct_receita"].cumsum()

    n_80 = int(np.searchsorted(cat["pct_acumulado"].to_numpy(), 80) + 1)
    resumo = {
        "n_categorias": len(cat),
        "n_categorias_80pct": n_80,
        "pct_categorias_80pct": n_80 / len(cat) * 100,
        "top1": cat.index[0],
        "top1_pct": float(cat["pct_receita"].iloc[0]),
        "top5_pct": float(cat["pct_receita"].head(5).sum()),
        "categoria_preco_medio_mais_alto": cat[cat["n_itens"] >= 100]["preco_medio"].idxmax(),
    }
    return cat, resumo


# P3 — Atraso na entrega x nota de avaliação
def atraso_vs_nota(pedidos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Nota média e % de notas baixas por faixa de atraso, mais a correlação de Spearman."""
    base = _entregues(pedidos).dropna(subset=["dias_atraso", "review_score"]).copy()
    faixas = ["No prazo ou antes", "1 a 3 dias", "4 a 7 dias", "Mais de 7 dias"]
    base["faixa_atraso"] = pd.cut(
        base["dias_atraso"], bins=[-np.inf, 0, 3, 7, np.inf], labels=faixas
    )
    tabela = base.groupby("faixa_atraso", observed=True).agg(
        n_pedidos=("order_id", "count"),
        nota_media=("review_score", "mean"),
        pct_notas_baixas=("review_score", lambda s: (s <= 2).mean() * 100),
    )
    # Spearman porque a nota é ordinal (1 a 5) e o atraso tem valores extremos.
    # Calculo como a correlação dos ranks: o corr(method="spearman") do pandas
    # precisa do scipy, que não está nas dependências do projeto.
    spearman = float(base["dias_atraso"].rank().corr(base["review_score"].rank()))
    resumo = {
        "n_pedidos": len(base),
        "pct_pedidos_atrasados": float(base["entregue_com_atraso"].mean() * 100),
        "nota_media_geral": float(base["review_score"].mean()),
        "spearman_atraso_nota": spearman,
    }
    return tabela, resumo


# P4 — Estados: prazo de entrega e frete
def entrega_frete_por_estado(pedidos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Prazo médio de entrega, frete mediano e % de atrasos por estado."""
    base = _entregues(pedidos).dropna(subset=["dias_entrega", "valor_frete"])
    est = base.groupby("customer_state").agg(
        n_pedidos=("order_id", "count"),
        dias_entrega_medio=("dias_entrega", "mean"),
        frete_mediano=("valor_frete", "median"),
        pct_atraso=("entregue_com_atraso", lambda s: s.mean() * 100),
    )
    est = est[est["n_pedidos"] >= MIN_PEDIDOS_ESTADO].sort_values("dias_entrega_medio")
    corr = float(est["dias_entrega_medio"].corr(est["frete_mediano"]))
    resumo = {
        "n_estados": len(est),
        "estado_mais_rapido": est.index[0],
        "dias_mais_rapido": float(est["dias_entrega_medio"].iloc[0]),
        "estado_mais_lento": est.index[-1],
        "dias_mais_lento": float(est["dias_entrega_medio"].iloc[-1]),
        "estado_frete_mais_caro": est["frete_mediano"].idxmax(),
        "frete_mais_caro": float(est["frete_mediano"].max()),
        "estado_frete_mais_barato": est["frete_mediano"].idxmin(),
        "frete_mais_barato": float(est["frete_mediano"].min()),
        "pearson_dias_frete": corr,
        "pct_pedidos_sp": float(
            base["customer_state"].eq("SP").mean() * 100
        ),
    }
    return est, resumo


# Extra — outliers de preço e frete
def resumo_outliers(itens: pd.DataFrame) -> dict:
    """Conta os outliers (IQR) de preço e de frete dos itens vendidos."""
    return {
        "preco": detectar_outliers_iqr(itens["price"]),
        "frete": detectar_outliers_iqr(itens["freight_value"]),
    }
