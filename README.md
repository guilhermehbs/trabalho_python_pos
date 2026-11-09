# Análise Exploratória — Brazilian E-Commerce (Olist)

Trabalho prático da disciplina de Python — Pós-graduação em Engenharia de Dados.
Pipeline completo: ingestão → ETL → qualidade de dados → EDA → visualizações → relatório.

## Fonte dos dados

Olist. *Brazilian E-Commerce Public Dataset by Olist*. Kaggle.
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## Estrutura

```
projeto/
├── data/
│   ├── raw/          # 7 CSVs originais do Olist (Kaggle), sem nenhuma alteração
│   └── processed/    # dados limpos gerados pelo ETL
├── src/
│   ├── config.py        # caminhos e parâmetros
│   ├── ingestao.py      # leitura dos dados brutos
│   ├── qualidade.py     # diagnóstico de nulos, duplicatas, tipos e outliers
│   ├── etl.py           # limpeza, derivação de variáveis e gravação
│   ├── analise.py       # perguntas de pesquisa (pandas/numpy)
│   ├── visualizacao.py  # gráficos (matplotlib)
│   └── main.py          # orquestra o pipeline
├── reports/          # diagnósticos (.csv) e figuras (.png) gerados
├── relatorio.pdf
├── README.md
└── requirements.txt
```

## Como executar

Requer Python 3.10+.

```bash
# 1. (opcional) ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. dependências
pip install -r requirements.txt

# 3. dados brutos: os 7 CSVs usados já estão em data/raw/ (o pipeline usa 7 dos 9 arquivos
#    do Kaggle; geolocalização e vendedores não são necessários). Para obtê-los novamente,
#    baixe o zip no Kaggle (link acima) e extraia os CSVs em data/raw/.

# 4. pipeline completo (ingestão -> qualidade -> ETL -> EDA -> gráficos)
python src/main.py
```

Opções: `python src/main.py --somente-eda` reaproveita os dados já limpos em `data/processed/`.

## Saídas geradas

- `data/processed/pedidos_limpo.csv` (99.441 pedidos x 23 colunas) e `itens_limpo.csv`: dados limpos.
- `relatorio.pdf`: relatório final (3 páginas) com os resultados desta execução.
- `reports/diagnostico_*.csv`: diagnóstico inicial de qualidade.
- `reports/figures/*.png`: gráficos usados no relatório.
- `reports/resultados_eda.txt`: números das análises.

## Perguntas de pesquisa

1. Como evoluíram o volume de pedidos e a receita ao longo do tempo?
2. Quais categorias concentram a receita e qual o ticket médio de cada uma?
3. Atrasos na entrega reduzem a nota de avaliação dos clientes?
4. Estados mais distantes têm entrega mais lenta e frete mais caro?
