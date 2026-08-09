# -*- coding: utf-8 -*-
"""
PASSO 5b — Prancha da Bella Pedra + exportação (PNG e PDF)
==========================================================
Roda no Console Python do QGIS, com UM destes projetos aberto:
  • projeto/bella_pedra.qgz          (o mapa do estado, projeto extra), ou
  • projeto/mineradora_calcario.qgz  (o principal, depois do passo 2b).

O script detecta qual camada da Bella Pedra existe no projeto aberto e
monta a prancha A4 paisagem: mapa, título, subtítulo, legenda (com as
formas e cores por minério), barra de escala, norte e créditos — depois
exporta para saidas/mapa_bella_pedra.png (200 dpi) e .pdf.

Enquadramento: se o projeto tiver o limite de MS (IBGE), a prancha sai
com o ESTADO inteiro; senão, enquadra os 7 processos. Quer outro recorte?
Enquadre na tela e mude ENQUADRAR_PELA_TELA para True.

Pode rodar de novo à vontade: o layout é recriado do zero a cada
execução (ajustes manuais no layout são perdidos ao re-rodar — deixe-os
por último, pelo menu Projeto → Layouts).
"""

import os

from qgis.core import (
    QgsProject,
    QgsPrintLayout,
    QgsLayoutItemMap,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemScaleBar,
    QgsLayoutItemPage,
    QgsLayoutExporter,
    QgsLayoutPoint,
    QgsLayoutSize,
)
from qgis.PyQt.QtGui import QFont

# ─────────────────────────────────────────────────────────────────────────────
# Edite esta linha SOMENTE se a detecção automática falhar (o script avisa).
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")

# True = a prancha fotografa o enquadramento atual da tela (como o passo 5)
ENQUADRAR_PELA_TELA = False

# Textos do mapa — edite à vontade!
TITULO = "Bella Pedra Cristal Ltda.: processos minerários em Mato Grosso do Sul"
SUBTITULO = ("Território de direito registrado na ANM — 7 processos ativos, "
             "por substância requerida (protocolos de 2021 a 2025)")
CREDITOS = ("Fontes: ANM/SIGMINE (poligonais, extração ago. 2026); IBGE "
            "(limite estadual); Esri World Imagery. Elaboração: Trabalho de "
            "Campo Interdisciplinar em Geografia II — UEMS, 2026. "
            "SRC: SIRGAS 2000 / UTM 21S.")

# Nomes possíveis da camada da Bella Pedra (projeto extra e passo 2b)
NOMES_BELLA = [
    "Bella Pedra Cristal (7 processos)",
    "Bella Pedra — por minério",
]
NOME_LIMITE = "Mato Grosso do Sul (limite IBGE)"
NOME_LAYOUT = "Mapa — Bella Pedra (MS)"


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS.

    (Não use SystemExit/sys.exit() em scripts do console do QGIS:
    isso fecha o programa inteiro.)
    """


def mm(largura, altura=None):
    """Tamanho/posição em milímetros, compatível com QGIS 3 e 4."""
    try:
        from qgis.core import QgsUnitTypes
        unidade = QgsUnitTypes.LayoutMillimeters
    except AttributeError:
        from qgis.core import Qgis
        unidade = Qgis.LayoutUnit.Millimeters
    if altura is None:
        return unidade
    return QgsLayoutSize(largura, altura, unidade)


print("=" * 60)
print("PASSO 5b — PRANCHA DA BELLA PEDRA")
print("=" * 60)

# 1. Descobrir RAIZ e a camada da Bella Pedra --------------------------------
projeto = QgsProject.instance()
if not os.path.isdir(RAIZ):
    arquivo_aberto = projeto.fileName()
    if arquivo_aberto:
        candidato = os.path.dirname(os.path.dirname(arquivo_aberto))
        if os.path.isdir(candidato):
            RAIZ = candidato
            print(f"✔ RAIZ detectado pelo projeto aberto: {RAIZ}")
if not os.path.isdir(RAIZ):
    print(f"✘ ERRO: não encontrei a pasta do projeto: {RAIZ}")
    raise PareAqui("caminho RAIZ não encontrado (veja acima)")

bella = None
for nome in NOMES_BELLA:
    camadas = projeto.mapLayersByName(nome)
    if camadas:
        bella = camadas[0]
        break
if bella is None:
    print("✘ ERRO: não achei nenhuma camada da Bella Pedra neste projeto.")
    print("  Abra projeto/bella_pedra.qgz (script projeto_bella_pedra.py)")
    print("  ou rode o passo_2b no projeto principal, e tente de novo.")
    raise PareAqui("camada da Bella Pedra não encontrada (veja acima)")
print(f"✔ Camada encontrada: {bella.name()}")

# 2. Enquadramento -----------------------------------------------------------
extensao = None
if ENQUADRAR_PELA_TELA:
    try:
        from qgis.utils import iface
        extensao = iface.mapCanvas().extent()
        print("✔ Enquadramento copiado da tela")
    except Exception:
        pass
if extensao is None:
    from qgis.core import QgsCoordinateTransform
    limites = projeto.mapLayersByName(NOME_LIMITE)
    referencia = limites[0] if limites else bella
    transf = QgsCoordinateTransform(referencia.crs(), projeto.crs(),
                                    projeto.transformContext())
    extensao = transf.transformBoundingBox(referencia.extent())
    extensao.scale(1.08 if limites else 1.2)
    print(f"✔ Enquadramento: {referencia.name()}")

# 3. Criar o layout (recriando se já existir) --------------------------------
gerente = projeto.layoutManager()
antigo = gerente.layoutByName(NOME_LAYOUT)
if antigo:
    gerente.removeLayout(antigo)

layout = QgsPrintLayout(projeto)
layout.initializeDefaults()
layout.setName(NOME_LAYOUT)

pagina = layout.pageCollection().page(0)
try:
    pagina.setPageSize("A4", QgsLayoutItemPage.Orientation.Landscape)
except AttributeError:
    pagina.setPageSize("A4", QgsLayoutItemPage.Landscape)
gerente.addLayout(layout)
print("✔ Prancha A4 paisagem criada")

# A4 paisagem = 297 × 210 mm; faixa direita reservada para a legenda.
# 4. O mapa ------------------------------------------------------------------
mapa = QgsLayoutItemMap(layout)
mapa.setRect(0, 0, 10, 10)  # tamanho provisório; o real vem abaixo
layout.addLayoutItem(mapa)
mapa.attemptMove(QgsLayoutPoint(8, 26, mm(0)))
mapa.attemptResize(mm(216, 168))
mapa.setExtent(extensao)
mapa.setFrameEnabled(True)
mapa.refresh()

# 5. Título e subtítulo ------------------------------------------------------
titulo = QgsLayoutItemLabel(layout)
titulo.setText(TITULO)
fonte_titulo = QFont()
fonte_titulo.setPointSize(16)
fonte_titulo.setBold(True)
titulo.setFont(fonte_titulo)
layout.addLayoutItem(titulo)
titulo.attemptMove(QgsLayoutPoint(8, 6, mm(0)))
titulo.attemptResize(mm(281, 10))

subtitulo = QgsLayoutItemLabel(layout)
subtitulo.setText(SUBTITULO)
fonte_sub = QFont()
fonte_sub.setPointSize(10)
fonte_sub.setItalic(True)
subtitulo.setFont(fonte_sub)
layout.addLayoutItem(subtitulo)
subtitulo.attemptMove(QgsLayoutPoint(8, 16, mm(0)))
subtitulo.attemptResize(mm(281, 7))

# 6. Legenda (a camada da Bella Pedra, com formas e cores por minério) -------
legenda = QgsLayoutItemLegend(layout)
legenda.setLinkedMap(mapa)
legenda.setTitle("Substância requerida")
legenda.setAutoUpdateModel(False)
raiz_leg = legenda.model().rootGroup()
for filho in list(raiz_leg.children()):
    raiz_leg.removeChildNode(filho)
raiz_leg.addLayer(bella)
layout.addLayoutItem(legenda)
legenda.attemptMove(QgsLayoutPoint(228, 26, mm(0)))
legenda.attemptResize(mm(63, 150))
print("✔ Legenda com as categorias por minério")

# 7. Barra de escala e norte -------------------------------------------------
escala = QgsLayoutItemScaleBar(layout)
escala.setStyle("Single Box")
escala.setLinkedMap(mapa)
escala.applyDefaultSize()
layout.addLayoutItem(escala)
escala.attemptMove(QgsLayoutPoint(8, 196, mm(0)))

norte = QgsLayoutItemLabel(layout)
norte.setText("N\n▲")
fonte_norte = QFont()
fonte_norte.setPointSize(14)
fonte_norte.setBold(True)
norte.setFont(fonte_norte)
layout.addLayoutItem(norte)
norte.attemptMove(QgsLayoutPoint(213, 30, mm(0)))
norte.attemptResize(mm(10, 14))

# 8. Créditos ----------------------------------------------------------------
creditos = QgsLayoutItemLabel(layout)
creditos.setText(CREDITOS)
fonte_cred = QFont()
fonte_cred.setPointSize(7)
creditos.setFont(fonte_cred)
layout.addLayoutItem(creditos)
creditos.attemptMove(QgsLayoutPoint(78, 197, mm(0)))
creditos.attemptResize(mm(211, 10))

# 9. Exportar ----------------------------------------------------------------
pasta_saidas = os.path.join(RAIZ, "saidas")
os.makedirs(pasta_saidas, exist_ok=True)
exportador = QgsLayoutExporter(layout)

caminho_png = os.path.join(pasta_saidas, "mapa_bella_pedra.png")
opcoes_png = QgsLayoutExporter.ImageExportSettings()
opcoes_png.dpi = 200
resultado_png = exportador.exportToImage(caminho_png, opcoes_png)

caminho_pdf = os.path.join(pasta_saidas, "mapa_bella_pedra.pdf")
opcoes_pdf = QgsLayoutExporter.PdfExportSettings()
resultado_pdf = exportador.exportToPdf(caminho_pdf, opcoes_pdf)

if resultado_png == QgsLayoutExporter.Success:
    print(f"✔ PNG exportado: {caminho_png}")
else:
    print(f"⚠ Falha ao exportar PNG (código {resultado_png})")
if resultado_pdf == QgsLayoutExporter.Success:
    print(f"✔ PDF exportado: {caminho_pdf}")
else:
    print(f"⚠ Falha ao exportar PDF (código {resultado_pdf})")

if projeto.fileName() and projeto.write(projeto.fileName()):
    print("✔ Projeto salvo (layout incluído)")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 5b CONCLUÍDO ✔")
print("Prancha pronta em saidas/mapa_bella_pedra.png e .pdf.")
print("Ajustes: edite TITULO/SUBTITULO/CREDITOS no topo e re-rode; ou")
print("abra Projeto → Layouts → 'Mapa — Bella Pedra (MS)' e arraste os")
print("elementos à mão (por ÚLTIMO: re-rodar o script recria o layout).")
print("Para uma prancha aproximada de UM processo: enquadre-o na tela,")
print("mude ENQUADRAR_PELA_TELA para True e rode de novo (renomeie antes")
print("os arquivos em saidas/ para não sobrescrever).")
print("=" * 60)
