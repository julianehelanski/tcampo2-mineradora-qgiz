# -*- coding: utf-8 -*-
"""
PROJETO EXTRA — Só a Bella Pedra: os 7 processos no mapa
========================================================
Roda no Console Python do QGIS. É INDEPENDENTE dos passos 0–5: cria um
projeto NOVO (projeto/bella_pedra.qgz), separado do principal — bom para
abrir numa segunda janela do QGIS, lado a lado com o outro.

O que este script faz:
  1. Cria um projeto novo com satélite (Esri) + nomes de cidades.
  2. Carrega do shapefile do SIGMINE apenas os 7 processos da
     BELLA PEDRA CRISTAL LTDA.
  3. Estiliza: polígono rosa com contorno forte + um PONTO (bolinha) no
     centro de cada processo — sem o ponto, os polígonos somem quando o
     zoom mostra o estado inteiro.
  4. Rotula cada processo (nº + substância) e enquadra o mapa nos 7.
  5. Salva em projeto/bella_pedra.qgz.

ATENÇÃO: rode numa janela do QGIS SEM trabalho aberto (ele cria um
projeto novo — o que estiver na tela será fechado, perguntando se salva).
"""

import os
import urllib.parse

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsCentroidFillSymbolLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

# ─────────────────────────────────────────────────────────────────────────────
# AJUSTE OBRIGATÓRIO: use o MESMO caminho dos outros passos.
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS."""


print("=" * 60)
print("PROJETO EXTRA — BELLA PEDRA (7 PROCESSOS)")
print("=" * 60)

# 1. Localizar o shapefile do SIGMINE (antes de mexer no projeto) ------------
shp_pasta = os.path.join(RAIZ, "dados", "reais", "sigmine_MS", "MS.shp")
zip_sigmine = os.path.join(RAIZ, "dados", "reais", "sigmine_MS.zip")
if os.path.isfile(shp_pasta):
    fonte = shp_pasta
elif os.path.isfile(zip_sigmine):
    fonte = "/vsizip/" + zip_sigmine.replace("\\", "/") + "/MS.shp"
else:
    print("✘ ERRO: não achei o SIGMINE em dados/reais/")
    print(f"  Esperava: {shp_pasta}")
    print("  Confira se RAIZ aponta para a pasta do repositório baixado.")
    raise PareAqui("shapefile do SIGMINE não encontrado (veja acima)")

# 2. Projeto novo ------------------------------------------------------------
try:
    from qgis.utils import iface
    iface.newProject(False)
except Exception:
    QgsProject.instance().clear()
projeto = QgsProject.instance()
projeto.setTitle("Bella Pedra Cristal — 7 processos minerários (SIGMINE)")
projeto.setCrs(QgsCoordinateReferenceSystem("EPSG:31981"))
print("✔ Projeto novo criado (SRC EPSG:31981)")


def camada_xyz(nome, url, zmax=19):
    url_cod = urllib.parse.quote(url, safe="")
    return QgsRasterLayer(f"type=xyz&url={url_cod}&zmin=0&zmax={zmax}",
                          nome, "wms")


satelite = camada_xyz(
    "Satélite — Esri World Imagery",
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}")
nomes = camada_xyz(
    "Referência — nomes de cidades e lugares (Esri)",
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}")
for camada in (satelite, nomes):
    if camada.isValid():
        projeto.addMapLayer(camada)
        print(f"✔ Camada adicionada: {camada.name()}")
    else:
        print(f"⚠ Falha ao criar: {camada.name()} — verifique a internet.")

# 3. Só os processos da Bella Pedra ------------------------------------------
bella = QgsVectorLayer(fonte, "Bella Pedra Cristal (7 processos)", "ogr")
if not bella.isValid():
    print(f"✘ ERRO ao carregar o shapefile: {fonte}")
    raise PareAqui("falha ao carregar o shapefile (veja acima)")
bella.setProviderEncoding("UTF-8")
bella.setSubsetString("\"NOME\" LIKE 'BELLA PEDRA%'")
print(f"✔ Filtro aplicado: {bella.featureCount()} processos da Bella Pedra")

# 4. Estilo: polígono rosa + bolinha no centro (visível de longe) ------------
simbolo = QgsFillSymbol.createSimple({
    "color": "244,204,224,120",          # rosa da planilha
    "outline_color": "198,47,123,255",   # contorno rosa escuro
    "outline_width": "0.9",
})
ponto_central = QgsCentroidFillSymbolLayer()
ponto_central.setSubSymbol(QgsMarkerSymbol.createSimple({
    "name": "circle",
    "color": "198,47,123,255",
    "outline_color": "255,255,255,230",
    "outline_width": "0.5",
    "size": "3.4",
}))
simbolo.appendSymbolLayer(ponto_central)
bella.renderer().setSymbol(simbolo)

# Rótulo: nº do processo + substância, com halo branco
rotulo = QgsPalLayerSettings()
rotulo.fieldName = "\"PROCESSO\" || '\\n' || \"SUBS\""
rotulo.isExpression = True
formato = QgsTextFormat()
formato.setSize(9)
formato.setColor(QColor(120, 20, 70))
halo = QgsTextBufferSettings()
halo.setEnabled(True)
halo.setSize(1.2)
halo.setColor(QColor(255, 255, 255))
formato.setBuffer(halo)
rotulo.setFormat(formato)
bella.setLabeling(QgsVectorLayerSimpleLabeling(rotulo))
bella.setLabelsEnabled(True)

projeto.addMapLayer(bella)
print("✔ Estilo aplicado (rosa + ponto central + rótulos). Processos:")
for feicao in bella.getFeatures():
    print(f"   {feicao['PROCESSO']} · {feicao['SUBS']} · {feicao['FASE']}")

# 5. Enquadrar os 7 processos ------------------------------------------------
try:
    from qgis.utils import iface
    transf = QgsCoordinateTransform(bella.crs(), projeto.crs(),
                                    projeto.transformContext())
    extensao = transf.transformBoundingBox(bella.extent())
    extensao.scale(1.15)
    iface.mapCanvas().setExtent(extensao)
    iface.mapCanvas().refresh()
    print("✔ Mapa enquadrado nos 7 processos")
except Exception as erro:
    print(f"⚠ Não consegui ajustar o zoom automaticamente: {erro}")

# 6. Salvar ------------------------------------------------------------------
arquivo_projeto = os.path.join(RAIZ, "projeto", "bella_pedra.qgz")
os.makedirs(os.path.dirname(arquivo_projeto), exist_ok=True)
if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")
else:
    print(f"⚠ Não consegui salvar em: {arquivo_projeto}")

print("=" * 60)
print("PROJETO BELLA PEDRA CONCLUÍDO ✔")
print("Os 7 processos ficam a até ~300 km uns dos outros — as bolinhas")
print("rosas marcam onde estão. Aproxime o zoom numa bolinha para ver o")
print("polígono e o que o satélite mostra lá dentro.")
print("Nas próximas vezes, abra direto: projeto/bella_pedra.qgz")
print("=" * 60)
