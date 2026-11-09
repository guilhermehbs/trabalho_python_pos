"""Gráficos (matplotlib).

Padrão dos gráficos: um eixo y só, título e eixos com unidade, azul para o dado
principal, laranja para destaque e cinza para referência.
"""
import matplotlib

matplotlib.use("Agg")  # só salva imagem, não abre janela
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DIR_FIGURAS

AZUL = "#2A6FBB"
LARANJA = "#D9822B"
CINZA = "#8A8F98"
TEXTO = "#222222"


def _estilo() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "axes.edgecolor": CINZA,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#E3E5E8",
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "text.color": TEXTO,
            "axes.labelcolor": TEXTO,
            "xtick.color": TEXTO,
            "ytick.color": TEXTO,
        }
    )


def _salvar(fig: plt.Figure, nome: str) -> None:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    caminho = DIR_FIGURAS / nome
    fig.savefig(caminho, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[viz] salvo {caminho.name}")


def _brl_mil(x, _pos=None) -> str:
    return f"{x / 1000:,.0f}".replace(",", ".")


def grafico_distribuicoes(itens: pd.DataFrame) -> None:
    """Histogramas de preço e frete (distribuição bem assimétrica)."""
    _estilo()
    fig, eixos = plt.subplots(1, 2, figsize=(8, 3.2))
    for ax, col, titulo, cor in [
        (eixos[0], "price", "Preço do item", AZUL),
        (eixos[1], "freight_value", "Frete do item", LARANJA),
    ]:
        valores = itens[col][itens[col] > 0]
        # começa no percentil 0,1 para não sobrar um pedaço vazio à esquerda na escala log
        bins = np.logspace(np.log10(valores.quantile(0.001)), np.log10(valores.max()), 40)
        ax.hist(valores, bins=bins, color=cor, edgecolor="white", linewidth=0.4)
        ax.axvline(valores.median(), color=TEXTO, linestyle="--", linewidth=1)
        ax.text(valores.median() * 1.1, ax.get_ylim()[1] * 0.92,
                f"mediana R$ {valores.median():,.0f}".replace(",", "."), fontsize=8)
        ax.set_xscale("log")
        ax.set_title(titulo)
        ax.set_xlabel("Valor (R$, escala logarítmica)")
        ax.set_ylabel("Nº de itens")
    fig.tight_layout()
    _salvar(fig, "00_distribuicao_preco_frete.png")


def grafico_serie_mensal(mensal: pd.DataFrame) -> None:
    """P1: pedidos (barras) e receita (linha) por mês."""
    _estilo()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
    x = np.arange(len(mensal))

    ax1.bar(x, mensal["n_pedidos"], color=AZUL, width=0.7)
    ax1.set_title("Pedidos entregues por mês")
    ax1.set_ylabel("Nº de pedidos")

    ax2.plot(x, mensal["receita"], color=LARANJA, linewidth=2, marker="o", markersize=4)
    pico = mensal["receita"].to_numpy().argmax()
    ax2.annotate(
        f"pico: R$ {mensal['receita'].iloc[pico] / 1000:,.0f} mil".replace(",", "."),
        (pico, mensal["receita"].iloc[pico]),
        textcoords="offset points", xytext=(-10, 8), ha="right", fontsize=8,
    )
    ax2.set_ylim(top=mensal["receita"].max() * 1.12)  # espaço para o rótulo do pico
    ax2.set_title("Receita de produtos por mês")
    ax2.set_ylabel("Receita (R$ mil)")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(_brl_mil))
    ax2.set_xlabel("Mês da compra")
    passo = 2
    ax2.set_xticks(x[::passo])
    ax2.set_xticklabels(mensal.index[::passo], rotation=45, ha="right")
    fig.tight_layout()
    _salvar(fig, "01_serie_mensal.png")


def grafico_categorias(cat: pd.DataFrame, n_top: int = 10) -> None:
    """P2: top categorias por receita e curva de Pareto."""
    _estilo()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [1.3, 1]})

    top = cat.head(n_top).iloc[::-1]
    nomes = [n.replace("_", " ") for n in top.index]
    ax1.barh(nomes, top["receita"], color=AZUL, height=0.65)
    for i, (rec, pct) in enumerate(zip(top["receita"], top["pct_receita"])):
        ax1.text(rec, i, f"  {pct:.1f}%", va="center", fontsize=8)
    ax1.set_title(f"Top {n_top} categorias por receita")
    ax1.set_xlabel("Receita (R$ mil)")
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(_brl_mil))
    ax1.set_xlim(0, top["receita"].max() * 1.18)
    ax1.grid(axis="y", visible=False)

    pos = np.arange(1, len(cat) + 1)
    ax2.plot(pos, cat["pct_acumulado"], color=AZUL, linewidth=2)
    ax2.axhline(80, color=CINZA, linestyle="--", linewidth=1)
    n80 = int(np.searchsorted(cat["pct_acumulado"].to_numpy(), 80) + 1)
    ax2.plot([n80], [cat["pct_acumulado"].iloc[n80 - 1]], "o", color=LARANJA, markersize=7)
    ax2.annotate(f"{n80} categorias\n≈ 80% da receita", (n80, 80), textcoords="offset points",
                 xytext=(12, -32), fontsize=8)
    ax2.set_title("Concentração da receita (Pareto)")
    ax2.set_xlabel("Nº de categorias (ordenadas por receita)")
    ax2.set_ylabel("% acumulado da receita")
    ax2.set_ylim(0, 102)
    fig.tight_layout()
    _salvar(fig, "02_categorias.png")


def grafico_atraso_nota(tabela: pd.DataFrame) -> None:
    """P3: nota média e % de notas baixas em cada faixa de atraso."""
    _estilo()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.6))
    faixas = list(tabela.index.astype(str))
    cores = [AZUL] + [LARANJA] * (len(faixas) - 1)

    b1 = ax1.bar(faixas, tabela["nota_media"], color=cores, width=0.65)
    ax1.set_title("Nota média por faixa de atraso")
    ax1.set_ylabel("Nota média (1 a 5)")
    ax1.set_ylim(0, 6)
    ax1.set_yticks(range(0, 6))
    for bar, v, n in zip(b1, tabela["nota_media"], tabela["n_pedidos"]):
        # deslocamento em pontos para o rótulo ficar sempre logo acima da barra
        ax1.annotate(f"{v:.2f}\n(n={n:,})".replace(",", "."), (bar.get_x() + bar.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8)

    b2 = ax2.bar(faixas, tabela["pct_notas_baixas"], color=cores, width=0.65)
    ax2.set_title("Avaliações negativas (nota 1 ou 2)")
    ax2.set_ylabel("% dos pedidos")
    ax2.set_ylim(0, max(tabela["pct_notas_baixas"].max() * 1.25, 1))
    for bar, v in zip(b2, tabela["pct_notas_baixas"]):
        ax2.annotate(f"{v:.1f}%", (bar.get_x() + bar.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8)

    for ax in (ax1, ax2):
        ax.set_xlabel("Atraso em relação à data prevista")
        ax.tick_params(axis="x", labelrotation=20)
        ax.grid(axis="x", visible=False)
    fig.tight_layout()
    _salvar(fig, "03_atraso_nota.png")


def grafico_estados(est: pd.DataFrame, pearson: float) -> None:
    """P4: dispersão do prazo de entrega contra o frete mediano por estado, com reta de tendência."""
    _estilo()
    fig, ax = plt.subplots(figsize=(7, 4.4))
    x = est["dias_entrega_medio"].to_numpy()
    y = est["frete_mediano"].to_numpy()
    tamanho = 30 + est["n_pedidos"].to_numpy() / est["n_pedidos"].max() * 250
    ax.scatter(x, y, s=tamanho, color=AZUL, alpha=0.75, edgecolor="white", linewidth=0.8)

    a, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, a * xs + b, color=LARANJA, linewidth=1.8, linestyle="--")

    # Para os rótulos das UFs não ficarem um em cima do outro, testo várias posições ao
    # redor de cada ponto e fico com a primeira que não bate em outro rótulo ou ponto.
    fig.canvas.draw()
    candidatos = [
        (5, 5), (5, -11), (-17, 5), (-17, -11), (5, 15), (-17, 15), (5, -21), (-17, -21),
        (22, 5), (22, -11), (-34, 5), (-34, -11), (5, 27), (-17, 27), (5, -33), (-17, -33),
    ]
    dpi_pt = fig.dpi / 72  # converte pontos em pixels
    pontos_px = [ax.transData.transform((xi, yi)) for xi, yi in zip(x, y)]
    colocados: list[tuple[float, float]] = []  # rótulos já colocados (em pixels)
    for uf, xi, yi in sorted(zip(est.index, x, y), key=lambda t: -est.loc[t[0], "n_pedidos"]):
        px, py = ax.transData.transform((xi, yi))
        escolhido = candidatos[0]
        for dx, dy in candidatos:
            lx, ly = px + dx * dpi_pt, py + dy * dpi_pt
            livre_rotulos = all(abs(lx - ox) > 30 or abs(ly - oy) > 18 for ox, oy in colocados)
            livre_pontos = all(abs(lx + 8 - qx) > 14 or abs(ly + 4 - qy) > 12 for qx, qy in pontos_px)
            if livre_rotulos and livre_pontos:
                escolhido = (dx, dy)
                break
        colocados.append((px + escolhido[0] * dpi_pt, py + escolhido[1] * dpi_pt))
        ax.annotate(uf, (xi, yi), textcoords="offset points", xytext=escolhido, fontsize=7.5)

    ax.set_title("Prazo de entrega e frete por estado")
    ax.set_xlabel("Prazo médio de entrega (dias)")
    ax.set_ylabel("Frete mediano por pedido (R$)")
    ax.text(0.03, 0.95, f"correlação de Pearson = {pearson:.2f}\n(tamanho do ponto = nº de pedidos)",
            transform=ax.transAxes, va="top", fontsize=8)
    fig.tight_layout()
    _salvar(fig, "04_estados_prazo_frete.png")
