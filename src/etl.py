"""Limpeza, criação de variáveis e gravação dos dados (o "T" e o "L" do ETL).

Cada função cuida de uma tabela e os comentários explicam o que foi feito e por quê.
As mesmas decisões aparecem no relatório.
"""
import numpy as np
import pandas as pd

from config import COLUNAS_DATA, DIR_PROCESSED, DIR_REPORTS


def tratar_clientes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="customer_id").copy()
    # padronizo o texto (UF maiúscula, cidade minúscula, sem espaços sobrando) para que
    # "SP" e "sp " não virem grupos diferentes na hora de agrupar
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    df["customer_city"] = df["customer_city"].str.strip().str.lower()
    return df[["customer_id", "customer_unique_id", "customer_city", "customer_state"]]


def tratar_pedidos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="order_id").copy()
    # as datas vêm como texto, então converto para datetime; sem isso não dá para
    # calcular prazo de entrega nem agrupar por mês
    for col in COLUNAS_DATA["pedidos"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    # não preencho as datas que faltam: nos pedidos cancelados ou ainda não entregues
    # a data de entrega é nula mesmo, e isso já é uma informação
    # entrega antes da compra é impossível, então essa data vira nula
    invalido = df["order_delivered_customer_date"] < df["order_purchase_timestamp"]
    df.loc[invalido, "order_delivered_customer_date"] = pd.NaT
    return df


def tratar_itens(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["order_id", "order_item_id"]).copy()
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    # item com preço zero ou negativo não tem valor para a análise de receita
    df = df[df["price"] > 0]
    # os outliers de preço e frete ficam: produto caro existe de verdade em e-commerce.
    # Na análise uso mediana e escala logarítmica para eles não distorcerem o resultado.
    return df


def tratar_pagamentos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["order_id", "payment_sequential"]).copy()
    # pagamentos com valor zero ou tipo "not_defined" são registros inválidos, então saem
    df = df[(df["payment_value"] > 0) & (df["payment_type"] != "not_defined")]
    return df


def tratar_avaliacoes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()  # não altera a tabela bruta recebida
    for col in COLUNAS_DATA["avaliacoes"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    # título e mensagem da avaliação são texto livre, quase sempre vazio, e nenhuma das
    # perguntas usa, então descarto as duas colunas
    df = df.drop(columns=["review_comment_title", "review_comment_message"])
    # alguns pedidos têm mais de uma avaliação; fico com a mais recente para sobrar
    # uma linha por pedido e o join não duplicar pedidos
    df = df.sort_values("review_answer_timestamp").drop_duplicates(subset="order_id", keep="last")
    return df[["order_id", "review_score"]]


def tratar_produtos(df: pd.DataFrame, traducao: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="product_id").copy()
    # o dataset original escreve "lenght" errado; corrijo para "length"
    df = df.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )
    # traduzo as categorias com a tabela de tradução do próprio dataset; as que não
    # têm tradução ficam com o nome original em português
    df = df.merge(traducao, on="product_category_name", how="left")
    df["categoria"] = df["product_category_name_english"].fillna(df["product_category_name"])
    # produto sem categoria vira "unknown" em vez de ser descartado, porque ele
    # também gerou receita
    df["categoria"] = df["categoria"].fillna("unknown")
    return df[["product_id", "categoria"]]


def construir_itens_analiticos(itens: pd.DataFrame, produtos: pd.DataFrame, pedidos: pd.DataFrame) -> pd.DataFrame:
    """Tabela com uma linha por item vendido, já com a categoria e o status do pedido."""
    df = itens.merge(produtos, on="product_id", how="left")
    df["categoria"] = df["categoria"].fillna("unknown")
    df = df.merge(pedidos[["order_id", "order_status", "order_purchase_timestamp"]], on="order_id", how="left")
    return df[
        ["order_id", "order_item_id", "product_id", "categoria", "price", "freight_value",
         "order_status", "order_purchase_timestamp"]
    ]


def construir_pedidos_analiticos(
    pedidos: pd.DataFrame,
    clientes: pd.DataFrame,
    itens_an: pd.DataFrame,
    pagamentos: pd.DataFrame,
    avaliacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Tabela com uma linha por pedido, juntando as outras e criando as variáveis novas."""
    agg_itens = itens_an.groupby("order_id").agg(
        n_itens=("order_item_id", "count"),
        valor_produtos=("price", "sum"),
        valor_frete=("freight_value", "sum"),
    )
    # categoria principal do pedido = a do item mais caro
    idx_max = itens_an.groupby("order_id")["price"].idxmax()
    cat_principal = itens_an.loc[idx_max, ["order_id", "categoria"]].set_index("order_id")
    cat_principal.columns = ["categoria_principal"]

    agg_pag = pagamentos.groupby("order_id").agg(
        valor_pago=("payment_value", "sum"),
        parcelas_max=("payment_installments", "max"),
    )
    tipo_principal = (
        pagamentos.sort_values("payment_value", ascending=False)
        .drop_duplicates("order_id")
        .set_index("order_id")[["payment_type"]]
        .rename(columns={"payment_type": "tipo_pagamento"})
    )

    df = (
        pedidos.merge(clientes[["customer_id", "customer_state"]], on="customer_id", how="left")
        .merge(agg_itens, on="order_id", how="left")
        .merge(cat_principal, on="order_id", how="left")
        .merge(agg_pag, on="order_id", how="left")
        .merge(tipo_principal, on="order_id", how="left")
        .merge(avaliacoes, on="order_id", how="left")
    )

    compra = df["order_purchase_timestamp"]
    entrega = df["order_delivered_customer_date"]
    prevista = df["order_estimated_delivery_date"]
    um_dia = np.timedelta64(1, "D")
    df["dias_entrega"] = (entrega - compra) / um_dia          # da compra até a entrega
    df["dias_atraso"] = (entrega - prevista) / um_dia         # positivo = atrasou, negativo = chegou antes
    df["entregue_com_atraso"] = df["dias_atraso"] > 0
    df["ano_mes"] = compra.dt.to_period("M").astype(str)
    df["valor_total"] = df["valor_produtos"] + df["valor_frete"]
    df["pct_frete"] = df["valor_frete"] / df["valor_total"] * 100
    # arredondo só os valores em reais e o % de frete (2 casas) para o CSV não ficar com
    # números como 399.68000000000006. Os prazos em dias não arredondo: isso mudaria alguns
    # pedidos de faixa de atraso (0,004 dia virando 0) e alteraria a análise.
    colunas_num = ["valor_produtos", "valor_frete", "valor_total", "pct_frete"]
    df[colunas_num] = df[colunas_num].round(2)
    return df


def executar_etl(tabelas: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    clientes = tratar_clientes(tabelas["clientes"])
    pedidos = tratar_pedidos(tabelas["pedidos"])
    itens = tratar_itens(tabelas["itens"])
    pagamentos = tratar_pagamentos(tabelas["pagamentos"])
    avaliacoes = tratar_avaliacoes(tabelas["avaliacoes"])
    produtos = tratar_produtos(tabelas["produtos"], tabelas["traducao_categorias"])

    itens_an = construir_itens_analiticos(itens, produtos, pedidos)
    pedidos_an = construir_pedidos_analiticos(pedidos, clientes, itens_an, pagamentos, avaliacoes)

    # log com as linhas antes e depois de cada tabela, para ver o que cada tratamento removeu
    log = pd.DataFrame(
        [
            ("clientes", len(tabelas["clientes"]), len(clientes)),
            ("pedidos", len(tabelas["pedidos"]), len(pedidos)),
            ("itens", len(tabelas["itens"]), len(itens)),
            ("pagamentos", len(tabelas["pagamentos"]), len(pagamentos)),
            ("avaliacoes", len(tabelas["avaliacoes"]), len(avaliacoes)),
            ("produtos", len(tabelas["produtos"]), len(produtos)),
        ],
        columns=["tabela", "linhas_antes", "linhas_depois"],
    )
    log["linhas_removidas"] = log["linhas_antes"] - log["linhas_depois"]
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    log.to_csv(DIR_REPORTS / "etl_log.csv", index=False)
    print("\n[etl] Linhas antes/depois do tratamento:")
    print(log.to_string(index=False))

    # salva os dados limpos em pasta separada, sem mexer nos brutos
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    pedidos_an.to_csv(DIR_PROCESSED / "pedidos_limpo.csv", index=False)
    itens_an.to_csv(DIR_PROCESSED / "itens_limpo.csv", index=False)

    print(f"\n[etl] pedidos_limpo.csv: {pedidos_an.shape[0]:,} linhas x {pedidos_an.shape[1]} colunas")
    print(f"[etl] itens_limpo.csv:   {itens_an.shape[0]:,} linhas x {itens_an.shape[1]} colunas")
    return {"pedidos": pedidos_an, "itens": itens_an, "pagamentos": pagamentos, "pedidos_tratados": pedidos}


def carregar_processados() -> dict[str, pd.DataFrame]:
    pedidos = pd.read_csv(
        DIR_PROCESSED / "pedidos_limpo.csv",
        parse_dates=[
            "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
            "order_delivered_customer_date", "order_estimated_delivery_date",
        ],
    )
    itens = pd.read_csv(DIR_PROCESSED / "itens_limpo.csv", parse_dates=["order_purchase_timestamp"])
    return {"pedidos": pedidos, "itens": itens}
