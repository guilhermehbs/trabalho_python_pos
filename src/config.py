"""Caminhos e parâmetros do projeto.

Deixei tudo aqui para não ficar com número solto espalhado pelos outros arquivos.
"""
from pathlib import Path

# a raiz do projeto é a pasta acima de src/
RAIZ = Path(__file__).resolve().parent.parent

DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_REPORTS = RAIZ / "reports"
DIR_FIGURAS = DIR_REPORTS / "figures"

# arquivos do dataset Olist que o projeto usa (Kaggle: olistbr/brazilian-ecommerce)
ARQUIVOS_OLIST = {
    "clientes": "olist_customers_dataset.csv",
    "pedidos": "olist_orders_dataset.csv",
    "itens": "olist_order_items_dataset.csv",
    "pagamentos": "olist_order_payments_dataset.csv",
    "avaliacoes": "olist_order_reviews_dataset.csv",
    "produtos": "olist_products_dataset.csv",
    "traducao_categorias": "product_category_name_translation.csv",
}

# colunas que deveriam ser data (o pandas lê como texto)
COLUNAS_DATA = {
    "pedidos": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "itens": ["shipping_limit_date"],
    "avaliacoes": ["review_creation_date", "review_answer_timestamp"],
}

# Período da série temporal. Em 2016 há poucos pedidos e com buracos entre os meses, e depois
# de set/2018 sobram só alguns registros, então uso jan/2017 a ago/2018 para a tendência
# não ficar distorcida.
PERIODO_INICIO = "2017-01"
PERIODO_FIM = "2018-08"

# meses com menos pedidos que isso não entram na série
MIN_PEDIDOS_MES = 100

# estados com menos pedidos que isso não entram na comparação
MIN_PEDIDOS_ESTADO = 100

# multiplicador do IQR para marcar outliers (valor clássico)
FATOR_IQR = 1.5
