# -*- coding: utf-8 -*-
"""
Análise temporal dos processos minerários do SIGMINE/ANM (MS).

Este script NÃO roda no QGIS — é Python comum (pandas + openpyxl + matplotlib).
Ele lê a planilha SIGMINE_MS_processos_minerarios_BellaPedra.xlsx e:

1. Extrai as informações temporais escondidas em colunas de texto:
   - Ano de abertura  → parte final do nº do processo (NNNNNN/AAAA);
   - Data do último evento → trecho "EM DD/MM/AAAA" da coluna "Último evento".
2. Grava uma aba nova "Dados temporais" com as colunas extraídas.
3. Grava uma aba "Séries e gráficos" com tabelas agregadas e gráficos
   nativos do Excel (série temporal e por substância).
4. Exporta os mesmos gráficos como PNG na pasta graficos/.

Uso (na raiz do repositório):
    python scripts/analise_temporal_sigmine.py [caminho_da_planilha.xlsx]

Limitação da fonte: o SIGMINE informa apenas o ÚLTIMO evento de cada
processo, não o histórico completo. O ano no nº do processo é o ano do
PROTOCOLO do pedido na ANM, não do início da extração real.
"""

import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------- parâmetros

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA_PADRAO = RAIZ / "dados" / "reais" / "SIGMINE_MS_BellaPedra_temporal.xlsx"
PASTA_GRAFICOS = RAIZ / "graficos"

ABA_DADOS = "Todos os processos (MS)"
ABA_NOVA = "Dados temporais"
ABA_GRAFICOS = "Séries e gráficos"

# Data de referência para calcular idade e tempo sem movimentação.
DATA_REF = date(2026, 8, 9)

# Recorte da série por substância (antes de 2000 os dados são esparsos).
ANO_CORTE = 2000

# Convenções visuais do arquivo original (mantidas nas abas novas)
AZUL_ESCURO = "1F4E79"   # cabeçalhos
ROSA_BELLA = "F4CCE0"    # linhas da Bella Pedra
FONTE = "Arial"

# Paleta categórica dos gráficos (uma cor fixa por substância)
CORES_SERIES = ["2A78D6", "EB6834", "1BAF7A", "EDA100", "E87BA4"]
COR_TOTAL = "256ABF"     # série agregada (todos os processos)
COR_CALCARIO = "008300"  # grupo do calcário (foco do trabalho de campo)

SUBSTANCIAS_CALCARIO = [
    "CALCÁRIO", "CALCÁRIO CALCÍTICO", "CALCÁRIO DOLOMÍTICO", "CALCITA",
]

# ---------------------------------------------------------------- extração


def extrair_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Devolve o DataFrame com as colunas temporais extraídas."""
    saida = df[["Processo", "Titular", "Substância", "Fase",
                "Área (ha)", "Uso"]].copy()

    saida["Ano_abertura"] = pd.to_numeric(
        df["Processo"].str.extract(r"/(\d{4})$")[0])

    evento = df["Último evento"].fillna("")
    saida["Cod_evento"] = pd.to_numeric(
        evento.str.extract(r"^(\d+)\s*-")[0], errors="coerce")
    saida["Desc_evento"] = (
        evento.str.replace(r"^\d+\s*-\s*", "", regex=True)
              .str.replace(r"\s*(?:PROTOC\s+)?EM\s+\d{2}/\d{2}/\d{4}\s*$",
                           "", regex=True)
              .str.strip())

    data_txt = evento.str.extract(r"EM (\d{2}/\d{2}/\d{4})")[0]
    saida["Data_ultimo_evento"] = pd.to_datetime(
        data_txt, format="%d/%m/%Y", errors="coerce")
    saida["Ano_ultimo_evento"] = saida["Data_ultimo_evento"].dt.year

    saida["Idade_processo_anos"] = DATA_REF.year - saida["Ano_abertura"]
    saida["Anos_sem_movimentacao"] = (
        (pd.Timestamp(DATA_REF) - saida["Data_ultimo_evento"]).dt.days
        / 365.25).round(1)

    saida["Bella_Pedra"] = df["Titular"].str.contains(
        "BELLA PEDRA", na=False).map({True: "Sim", False: ""})
    return saida


# ---------------------------------------------------------------- planilha


def _cabecalho(ws, linha, textos, larguras=None):
    fill = PatternFill("solid", fgColor=AZUL_ESCURO)
    for j, texto in enumerate(textos, start=1):
        c = ws.cell(row=linha, column=j, value=texto)
        c.font = Font(name=FONTE, size=9, bold=True, color="FFFFFF")
        c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical="center")
    if larguras:
        for j, larg in enumerate(larguras, start=1):
            ws.column_dimensions[get_column_letter(j)].width = larg


def _titulo(ws, texto, subtitulo, n_colunas):
    c = ws.cell(row=1, column=1, value=texto)
    c.font = Font(name=FONTE, size=12, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=AZUL_ESCURO)
    for j in range(2, n_colunas + 1):
        ws.cell(row=1, column=j).fill = PatternFill("solid",
                                                    fgColor=AZUL_ESCURO)
    s = ws.cell(row=2, column=1, value=subtitulo)
    s.font = Font(name=FONTE, size=8, color="595959")


def gravar_aba_dados(wb, dados: pd.DataFrame):
    if ABA_NOVA in wb.sheetnames:
        del wb[ABA_NOVA]
    ws = wb.create_sheet(ABA_NOVA)

    _titulo(
        ws,
        "DADOS TEMPORAIS EXTRAÍDOS — processos minerários de MS "
        "(SIGMINE/ANM)",
        "Gerado por scripts/analise_temporal_sigmine.py em "
        f"{DATA_REF.strftime('%d/%m/%Y')} (data de referência dos cálculos "
        "de idade). Ano_abertura = ano do protocolo no nº do processo. "
        "O SIGMINE traz só o ÚLTIMO evento, não o histórico completo. "
        "Linhas em rosa = Bella Pedra Cristal Ltda.",
        len(dados.columns))

    _cabecalho(ws, 4, list(dados.columns),
               larguras=[13, 26, 22, 24, 10, 16, 9, 9, 34, 13, 9, 10, 12, 9])

    rosa = PatternFill("solid", fgColor=ROSA_BELLA)
    fnt = Font(name=FONTE, size=9)
    fnt_bp = Font(name=FONTE, size=9, bold=True)
    for i, linha in enumerate(dados.itertuples(index=False), start=5):
        eh_bp = linha[-1] == "Sim"
        for j, valor in enumerate(linha, start=1):
            if pd.isna(valor):
                valor = None
            elif isinstance(valor, pd.Timestamp):
                valor = valor.date()
            c = ws.cell(row=i, column=j, value=valor)
            c.font = fnt_bp if eh_bp else fnt
            if eh_bp:
                c.fill = rosa
            if dados.columns[j - 1] == "Data_ultimo_evento":
                c.number_format = "DD/MM/YYYY"
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(dados.columns))}" \
                         f"{4 + len(dados)}"


def _estilo_serie(serie, cor, linha=False):
    serie.graphicalProperties.solidFill = cor
    if linha:
        serie.graphicalProperties.line.solidFill = cor
        serie.graphicalProperties.line.width = 20000  # ~2 px
        serie.smooth = False
    else:
        serie.graphicalProperties.line.noFill = True


def gravar_aba_graficos(wb, dados: pd.DataFrame):
    if ABA_GRAFICOS in wb.sheetnames:
        del wb[ABA_GRAFICOS]
    ws = wb.create_sheet(ABA_GRAFICOS)

    _titulo(ws,
            "SÉRIES TEMPORAIS E RECORTES POR SUBSTÂNCIA",
            "Tabelas agregadas a partir da aba 'Dados temporais'. "
            "Os gráficos ao lado são nativos do Excel e podem ser editados. "
            "Versões em PNG estão na pasta graficos/ do repositório.",
            8)

    # ---- T1: aberturas por ano (todos os processos) -----------------------
    anos = range(int(dados["Ano_abertura"].min()),
                 int(dados["Ano_abertura"].max()) + 1)
    por_ano = dados["Ano_abertura"].value_counts().reindex(anos, fill_value=0)

    lin = 4
    _cabecalho(ws, lin, ["Ano", "Processos abertos"], larguras=[10, 16])
    for ano, qtd in por_ano.items():
        lin += 1
        ws.cell(row=lin, column=1, value=ano).font = Font(name=FONTE, size=9)
        ws.cell(row=lin, column=2, value=int(qtd)).font = Font(name=FONTE,
                                                               size=9)
    fim_t1 = lin

    g1 = LineChart()
    g1.title = "Processos minerários abertos por ano — MS (SIGMINE/ANM)"
    g1.y_axis.title = "Processos abertos"
    g1.x_axis.title = "Ano do protocolo"
    g1.height, g1.width = 9, 24
    g1.add_data(Reference(ws, min_col=2, min_row=4, max_row=fim_t1),
                titles_from_data=True)
    g1.set_categories(Reference(ws, min_col=1, min_row=5, max_row=fim_t1))
    _estilo_serie(g1.series[0], COR_TOTAL, linha=True)
    g1.legend = None
    ws.add_chart(g1, "D4")

    # ---- T2: processos por substância (top 10 + outras) -------------------
    contagem = dados["Substância"].value_counts()
    top10 = contagem.head(10)
    outras = int(contagem.iloc[10:].sum())

    lin0 = fim_t1 + 3
    _cabecalho(ws, lin0, ["Substância", "Processos"], larguras=None)
    lin = lin0
    for nome, qtd in top10.items():
        lin += 1
        ws.cell(row=lin, column=1, value=nome).font = Font(name=FONTE, size=9)
        ws.cell(row=lin, column=2, value=int(qtd)).font = Font(name=FONTE,
                                                               size=9)
    lin += 1
    ws.cell(row=lin, column=1, value="OUTRAS").font = Font(name=FONTE, size=9,
                                                           italic=True)
    ws.cell(row=lin, column=2, value=outras).font = Font(name=FONTE, size=9,
                                                         italic=True)
    fim_t2 = lin

    g2 = BarChart()
    g2.type = "col"
    g2.title = "Processos por substância — MS (top 10 + outras)"
    g2.y_axis.title = "Processos"
    g2.height, g2.width = 9, 24
    g2.add_data(Reference(ws, min_col=2, min_row=lin0, max_row=fim_t2),
                titles_from_data=True)
    g2.set_categories(Reference(ws, min_col=1, min_row=lin0 + 1,
                                max_row=fim_t2))
    _estilo_serie(g2.series[0], CORES_SERIES[0])
    g2.legend = None
    g2.gapWidth = 40
    ws.add_chart(g2, f"D{lin0}")

    # ---- T3: série por substância (top 5, a partir de ANO_CORTE) ----------
    top5 = list(contagem.head(5).index)
    recorte = dados[dados["Ano_abertura"] >= ANO_CORTE]
    tabela = (recorte[recorte["Substância"].isin(top5)]
              .pivot_table(index="Ano_abertura", columns="Substância",
                           values="Processo", aggfunc="count", fill_value=0)
              .reindex(range(ANO_CORTE, DATA_REF.year + 1), fill_value=0)
              [top5])

    lin0 = fim_t2 + 3
    _cabecalho(ws, lin0, ["Ano"] + top5)
    lin = lin0
    for ano, valores in tabela.iterrows():
        lin += 1
        ws.cell(row=lin, column=1, value=int(ano)).font = Font(name=FONTE,
                                                               size=9)
        for j, v in enumerate(valores, start=2):
            ws.cell(row=lin, column=j, value=int(v)).font = Font(name=FONTE,
                                                                 size=9)
    fim_t3 = lin

    pct = 100 * len(recorte) / len(dados)
    nota = ws.cell(row=fim_t3 + 1, column=1,
                   value=f"Recorte {ANO_CORTE}–{DATA_REF.year} "
                         f"({pct:.0f}% dos processos).")
    nota.font = Font(name=FONTE, size=8, italic=True, color="595959")

    g3 = LineChart()
    g3.title = (f"Aberturas por ano — 5 substâncias com mais processos "
                f"({ANO_CORTE}–{DATA_REF.year})")
    g3.y_axis.title = "Processos abertos"
    g3.x_axis.title = "Ano do protocolo"
    g3.height, g3.width = 10, 24
    g3.add_data(Reference(ws, min_col=2, max_col=6, min_row=lin0,
                          max_row=fim_t3), titles_from_data=True)
    g3.set_categories(Reference(ws, min_col=1, min_row=lin0 + 1,
                                max_row=fim_t3))
    for serie, cor in zip(g3.series, CORES_SERIES):
        _estilo_serie(serie, cor, linha=True)
    ws.add_chart(g3, f"D{lin0}")

    # ---- T4: grupo do calcário por ano ------------------------------------
    calc = dados[dados["Substância"].isin(SUBSTANCIAS_CALCARIO)]
    por_ano_calc = (calc["Ano_abertura"].value_counts()
                    .reindex(range(ANO_CORTE, DATA_REF.year + 1),
                             fill_value=0))

    lin0 = fim_t3 + 4
    _cabecalho(ws, lin0, ["Ano", "Processos (grupo do calcário)"])
    lin = lin0
    for ano, qtd in por_ano_calc.items():
        lin += 1
        ws.cell(row=lin, column=1, value=int(ano)).font = Font(name=FONTE,
                                                               size=9)
        ws.cell(row=lin, column=2, value=int(qtd)).font = Font(name=FONTE,
                                                               size=9)
    fim_t4 = lin

    antes = int((calc["Ano_abertura"] < ANO_CORTE).sum())
    nota = ws.cell(
        row=fim_t4 + 1, column=1,
        value=f"Grupo: {', '.join(SUBSTANCIAS_CALCARIO)} — "
              f"{len(calc)} processos no total ({antes} antes de "
              f"{ANO_CORTE}, fora do gráfico).")
    nota.font = Font(name=FONTE, size=8, italic=True, color="595959")

    g4 = BarChart()
    g4.type = "col"
    g4.title = (f"Aberturas por ano — grupo do calcário "
                f"({ANO_CORTE}–{DATA_REF.year})")
    g4.y_axis.title = "Processos abertos"
    g4.x_axis.title = "Ano do protocolo"
    g4.height, g4.width = 9, 24
    g4.add_data(Reference(ws, min_col=2, min_row=lin0, max_row=fim_t4),
                titles_from_data=True)
    g4.set_categories(Reference(ws, min_col=1, min_row=lin0 + 1,
                                max_row=fim_t4))
    _estilo_serie(g4.series[0], COR_CALCARIO)
    g4.legend = None
    g4.gapWidth = 40
    ws.add_chart(g4, f"D{lin0}")

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 16
    for col in "CDEF":
        ws.column_dimensions[col].width = 12

    return {"por_ano": por_ano, "top10": top10, "outras": outras,
            "tabela_top5": tabela, "por_ano_calc": por_ano_calc}


# ---------------------------------------------------------------- PNGs


def gerar_pngs(agregados, dados):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PASTA_GRAFICOS.mkdir(exist_ok=True)
    SUPERFICIE, TINTA, MUDO, GRADE = "#fcfcfb", "#0b0b0b", "#898781", "#e1e0d9"
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 10,
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE,
        "axes.edgecolor": GRADE, "axes.labelcolor": MUDO,
        "xtick.color": MUDO, "ytick.color": MUDO,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlecolor": TINTA, "axes.titlesize": 12,
        "axes.titleweight": "bold",
    })

    def salvar(fig, nome):
        caminho = PASTA_GRAFICOS / nome
        fig.savefig(caminho, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  PNG: {caminho.relative_to(RAIZ)}")

    # 1 — série temporal geral
    por_ano = agregados["por_ano"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(por_ano.index, por_ano.values, color="#256abf", linewidth=2)
    ax.set_title("Processos minerários abertos por ano — MS (SIGMINE/ANM)",
                 loc="left")
    ax.set_xlabel("Ano do protocolo")
    ax.set_ylabel("Processos abertos")
    ax.grid(axis="x", visible=False)
    salvar(fig, "serie_temporal_geral.png")

    # 2 — barras por substância
    top10, outras = agregados["top10"], agregados["outras"]
    nomes = list(top10.index) + ["OUTRAS"]
    valores = list(top10.values) + [outras]
    fig, ax = plt.subplots(figsize=(9, 5))
    y = range(len(nomes))[::-1]
    ax.barh(y, valores, color="#2a78d6", height=0.62)
    ax.barh(y[-1], valores[-1], color="#c3c2b7", height=0.62)
    ax.set_yticks(y, nomes)
    for yi, v in zip(y, valores):
        ax.text(v + 12, yi, f"{v:,}".replace(",", "."),
                va="center", color=TINTA, fontsize=9)
    ax.set_title("Processos por substância — MS (top 10 + outras)",
                 loc="left")
    ax.set_xlabel("Processos")
    ax.grid(axis="y", visible=False)
    salvar(fig, "processos_por_substancia.png")

    # 3 — série por substância (top 5)
    tabela = agregados["tabela_top5"]
    cores = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    fig, ax = plt.subplots(figsize=(10, 5))
    for coluna, cor in zip(tabela.columns, cores):
        ax.plot(tabela.index, tabela[coluna], color=cor, linewidth=2,
                label=coluna)
        ax.annotate(coluna, xy=(tabela.index[-1], tabela[coluna].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=TINTA)
    ax.set_title("Aberturas por ano — 5 substâncias com mais processos",
                 loc="left")
    ax.set_xlabel("Ano do protocolo")
    ax.set_ylabel("Processos abertos")
    ax.legend(loc="upper left", frameon=False, fontsize=8.5,
              labelcolor=TINTA)
    ax.grid(axis="x", visible=False)
    ax.set_xlim(tabela.index[0], tabela.index[-1] + 4)
    salvar(fig, "serie_por_substancia_top5.png")

    # 4 — grupo do calcário
    por_ano_calc = agregados["por_ano_calc"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(por_ano_calc.index, por_ano_calc.values, color="#008300",
           width=0.7)
    ax.set_title("Aberturas por ano — grupo do calcário "
                 "(calcário, calcítico, dolomítico e calcita)", loc="left")
    ax.set_xlabel("Ano do protocolo")
    ax.set_ylabel("Processos abertos")
    ax.grid(axis="x", visible=False)
    salvar(fig, "serie_calcario.png")


# ---------------------------------------------------------------- principal


def principal():
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else ENTRADA_PADRAO
    if not entrada.exists():
        raise SystemExit(f"Arquivo não encontrado: {entrada}")

    print(f"Lendo {entrada.name} …")
    df = pd.read_excel(entrada, sheet_name=ABA_DADOS, header=3)
    print(f"  {len(df)} processos na aba '{ABA_DADOS}'.")

    dados = extrair_temporal(df)
    sem_data = int(dados["Data_ultimo_evento"].isna().sum())
    print(f"  Ano de abertura extraído em 100% das linhas; "
          f"data do último evento ausente em {sem_data} linha(s).")

    wb = load_workbook(entrada)
    gravar_aba_dados(wb, dados)
    agregados = gravar_aba_graficos(wb, dados)
    wb.save(entrada)
    print(f"Abas '{ABA_NOVA}' e '{ABA_GRAFICOS}' gravadas em {entrada.name}.")

    gerar_pngs(agregados, dados)
    print("Concluído.")


if __name__ == "__main__":
    principal()
