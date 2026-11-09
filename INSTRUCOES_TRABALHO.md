# Trabalho Prático de Python — Pós-graduação em Engenharia de Dados

## Informações gerais

| Item | Detalhe |
|---|---|
| **Peso** | 70% da nota final da disciplina |
| **Modalidade** | Individual ou em duplas |
| **Prazo de entrega** | 15/11/2026 até 23h59 (horário de Brasília). Entregas após o prazo não serão aceitas |
| **Formato de entrega** | Arquivos do projeto (`.py` e/ou `.ipynb`) + relatório em PDF, compactados em um único `.zip` |

## 1. Objetivos

Consolidar os principais conteúdos da disciplina, exigindo que o aluno seja capaz de:

- Realizar a ingestão de dados a partir de uma fonte externa (arquivo local, API ou download programático).
- Aplicar uma rotina simples de ETL (Extract, Transform, Load), documentando as decisões tomadas.
- Tratar problemas comuns de qualidade de dados (valores ausentes, duplicatas, tipos inadequados, outliers).
- Conduzir uma análise exploratória de dados (EDA) com perguntas de pesquisa bem definidas, utilizando `pandas` e `numpy`.
- Comunicar achados por meio de visualizações com `matplotlib` e de um relatório escrito.

## 2. Descrição do trabalho

O aluno (ou dupla) deverá conduzir um projeto completo de análise exploratória, partindo de um dataset bruto e entregando um relatório com os principais achados, organizado em etapas:

### Etapa 1 — Ingestão e ETL
Carregar os dados brutos, aplicar as transformações necessárias (renomear colunas, ajustar tipos, derivar novas variáveis quando relevante) e salvar uma versão "limpa" do dataset em arquivo separado. Toda decisão de transformação deve estar **comentada no código** e **justificada no relatório**.

### Etapa 2 — Qualidade dos dados
Inspecionar e tratar valores ausentes, duplicatas e inconsistências. Apresentar um pequeno diagnóstico inicial (nulos por coluna, duplicatas encontradas, tipos inferidos vs. esperados) e descrever no relatório as decisões tomadas e por quê.

### Etapa 3 — Análise exploratória
Definir **ao menos 3 perguntas de pesquisa** respondidas com base nos dados. Cada pergunta deve ter pelo menos uma análise (estatística descritiva, agrupamento, correlação, distribuição, comparação entre grupos etc.) acompanhada de pelo menos uma visualização.

### Etapa 4 — Relatório
Documento em PDF de **1 a 3 páginas**, contendo:

1. Breve contexto do dataset e da fonte.
2. Resumo do processo de ETL e das decisões de qualidade de dados.
3. Perguntas de pesquisa e respostas, com gráficos.
4. Conclusões e limitações da análise.

## 3. Escolha do dataset

Liberdade para escolher um dataset de interesse, desde que atenda aos critérios mínimos:

- Pelo menos **1.000 linhas** e **6 colunas**.
- Mistura de variáveis **numéricas e categóricas**.
- Fonte **pública e citável** (Kaggle, portais de dados abertos, IBGE, World Bank, APIs públicas etc.).

Dataset default, caso o aluno prefira não escolher: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## 4. Requisitos técnicos

- **Linguagem:** Python 3.10+.
- **Bibliotecas obrigatórias:** `pandas`, `numpy`, `matplotlib`.
- **Bibliotecas permitidas:** `requests` (para ingestão via API), além de bibliotecas padrão do Python.
- O código deve estar **modularizado em funções** (não é aceitável um notebook monolítico com um único bloco de 200 linhas).
- O projeto deve incluir um `README.md` com instruções de execução e um `requirements.txt`.

Estrutura de pastas sugerida (não obrigatória):

```
projeto/
├── data/
│   ├── raw/
│   └── processed/
├── src/  (ou notebook único bem organizado)
├── relatorio.pdf
├── README.md
└── requirements.txt
```

## 5. Rubrica de avaliação

| Critério | Peso | O que será avaliado |
|---|---|---|
| Organização do projeto e qualidade do código | 15% | Modularização, legibilidade, nomes claros, presença de README e requirements, reprodutibilidade |
| Ingestão e ETL | 20% | Carregamento da fonte, transformações aplicadas, separação entre dados brutos e processados, documentação das decisões |
| Qualidade dos dados | 10% | Diagnóstico inicial e tratamento adequado de nulos, duplicatas e tipos |
| Análise exploratória | 25% | Pertinência das perguntas, uso correto de pandas/numpy, profundidade da análise |
| Visualizações | 15% | Clareza, adequação ao dado, títulos e eixos rotulados, escolha apropriada do tipo de gráfico |
| Relatório em PDF | 15% | Estrutura, escrita, articulação entre análise e conclusões, citação da fonte do dataset |

> Os níveis de desempenho de cada critério no Canvas são: **Domínio** (atingiu plenamente), **Próximo** (atende com algumas lacunas), **Abaixo** (atende parcialmente) e **Sem evidências** (não demonstrou).

## 6. Observações finais

- Trabalhos em dupla devem identificar claramente a contribuição de cada integrante no relatório.
