# -*- coding: utf-8 -*-
"""
PASSO 5 — Layout final + exportação (PNG e PDF)
===============================================
Roda no Console Python do QGIS, com o projeto aberto e as camadas prontas.

IMPORTANTE — antes de rodar: ENQUADRE o mapa como você quer que ele saia
no papel (zoom na mineradora escolhida, camadas ligadas/desligadas a gosto).
O layout fotografa o enquadramento atual da tela.

O que este script faz:
  1. Cria uma prancha A4 paisagem com: o mapa, título, subtítulo, legenda
     (só das camadas principais, para não virar um poster de legenda),
     barra de escala, indicação do norte e créditos das fontes.
  2. Exporta para saidas/mapa_mineradora.png (200 dpi) e .pdf.
  3. Deixa o layout salvo no projeto: menu Projeto → Layouts →
     "Mapa — mineradora de calcário" para ajustar posições à mão
     (arrastar título, legenda etc.) e re-exportar pelo próprio QGIS.

Pode rodar de novo à vontade: o layout é recriado do zero a cada execução
(ajustes manuais no layout são perdidos ao re-rodar — faça-os por último).
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

# Textos do mapa — edite à vontade!
TITULO = "Mineradora de calcário: território de direito e de fato"
SUBTITULO = ("Serra da Bodoquena (MS) — mapeamento de gabinete para o "
             "trabalho de campo")
CREDITOS = ("Fontes: ANM/SIGMINE; MapBiomas col. 9 (1985/2023); Esri World "
            "Imagery. Elaboração: Trabalho de Campo Interdisciplinar em "
            "Geografia II — UEMS, 2026. SRC: SIRGAS 2000 / UTM 21S.")

# Camadas que entram na legenda (as demais ficam fora para não poluir)
CAMADAS_LEGENDA = [
    "Pontos do campo",
    "Pegada da mineradora (FATO)",
    "Territórios do entorno",
    "SIGMINE MS — calcário (DIREITO)",
]

NOME_LAYOUT = "Mapa — mineradora de calcário"


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
print("PASSO 5 — LAYOUT FINAL E EXPORTAÇÃO")
print("=" * 60)

# 1. Descobrir RAIZ ----------------------------------------------------------
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

if not projeto.mapLayers():
    print("✘ ERRO: o projeto está vazio — rode os passos 1 a 3 antes.")
    raise PareAqui("projeto sem camadas (veja acima)")

# 2. Enquadramento: o que está na tela agora ---------------------------------
try:
    from qgis.utils import iface
    extensao = iface.mapCanvas().extent()
    print("✔ Enquadramento copiado da tela")
except Exception:
    extensao = None
    for nome in CAMADAS_LEGENDA[1:]:
        camadas = projeto.mapLayersByName(nome)
        if camadas:
            extensao = camadas[0].extent()
            break
    if extensao is None:
        raise PareAqui("não consegui definir o enquadramento do mapa")

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

# A4 paisagem = 297 × 210 mm. Reservamos a faixa direita para legenda.
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
fonte_titulo.setPointSize(17)
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

# 6. Legenda (só as camadas principais) --------------------------------------
legenda = QgsLayoutItemLegend(layout)
legenda.setLinkedMap(mapa)
legenda.setTitle("Legenda")
legenda.setAutoUpdateModel(False)
raiz_leg = legenda.model().rootGroup()
for filho in list(raiz_leg.children()):
    raiz_leg.removeChildNode(filho)
for nome in CAMADAS_LEGENDA:
    camadas = projeto.mapLayersByName(nome)
    if camadas:
        raiz_leg.addLayer(camadas[0])
layout.addLayoutItem(legenda)
legenda.attemptMove(QgsLayoutPoint(228, 26, mm(0)))
legenda.attemptResize(mm(63, 150))
print("✔ Legenda com as camadas principais")

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

caminho_png = os.path.join(pasta_saidas, "mapa_mineradora.png")
opcoes_png = QgsLayoutExporter.ImageExportSettings()
opcoes_png.dpi = 200
resultado_png = exportador.exportToImage(caminho_png, opcoes_png)

caminho_pdf = os.path.join(pasta_saidas, "mapa_mineradora.pdf")
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

if projeto.write(os.path.join(RAIZ, "projeto", "mineradora_calcario.qgz")):
    print("✔ Projeto salvo (layout incluído)")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 5 CONCLUÍDO ✔")
print("Arquivos prontos na pasta saidas/ — bons para relatório e slides.")
print("Quer ajustar posições, textos, tamanhos? Dois caminhos:")
print(" • edite as constantes TITULO/SUBTITULO/CREDITOS no topo e re-rode;")
print(" • ou abra Projeto → Layouts → 'Mapa — mineradora de calcário' e")
print("   arraste os elementos à mão (faça isso por ÚLTIMO: re-rodar o")
print("   script recria o layout e desfaz ajustes manuais).")
print("Para outra versão do mapa (outra mina, outro zoom): enquadre na")
print("tela, renomeie os arquivos antigos em saidas/ e rode de novo.")
print("=" * 60)
