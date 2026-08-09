# -*- coding: utf-8 -*-
"""
PROJETO EXTRA — Só a Bella Pedra: os 7 processos no mapa
========================================================
Roda no Console Python do QGIS. É INDEPENDENTE dos passos 0–5: cria um
projeto NOVO (projeto/bella_pedra.qgz), separado do principal — bom para
abrir numa segunda janela do QGIS, lado a lado com o outro.

O que este script faz:
  1. Cria um projeto novo com SATÉLITE (Esri), o mesmo fundo do projeto
     principal. SÓ O MS aparece: o limite oficial do IBGE é baixado na
     primeira execução e uma máscara esmaece tudo fora do estado.
     (Há também um fundo claro CARTO Positron, DESLIGADO — ligue a
     caixinha dele e desligue o satélite se quiser um mapa mais limpo.)
  2. Carrega do shapefile do SIGMINE apenas os 7 processos da
     BELLA PEDRA CRISTAL LTDA.
  3. Estiliza POR MINÉRIO (uma cor para cada substância, com legenda no
     painel de camadas): polígono translúcido + um ponto colorido no
     centro — sem o ponto, os polígonos somem no zoom de estado inteiro.
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
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsSingleSymbolRenderer,
    QgsInvertedPolygonRenderer,
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


# Satélite (ligado, como no projeto principal) + fundo claro (desligado)
fundo = camada_xyz(
    "Fundo claro — CARTO Positron (alternativa)",
    "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", zmax=20)
satelite = camada_xyz(
    "Satélite — Esri World Imagery",
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}")
for camada in (fundo, satelite):
    if camada.isValid():
        projeto.addMapLayer(camada)
        print(f"✔ Camada adicionada: {camada.name()}")
    else:
        print(f"⚠ Falha ao criar: {camada.name()} — verifique a internet.")

# O fundo claro começa desligado; para trocar de estilo, inverta as duas
# caixinhas no painel de camadas (satélite OFF, fundo claro ON).
no_fundo = projeto.layerTreeRoot().findLayer(fundo.id())
if no_fundo:
    no_fundo.setItemVisibilityChecked(False)

# 2b. Só o estado de MS: máscara com o limite oficial do IBGE ----------------
# Na primeira execução o limite é baixado da API do IBGE e salvo em
# dados/reais/limite_MS.geojson; depois é lido do disco. A "máscara" pinta
# de branco translúcido tudo o que está FORA de MS (renderizador de
# polígono invertido) — sobra o estado, com a divisa desenhada.
caminho_limite = os.path.join(RAIZ, "dados", "reais", "limite_MS.geojson")
if not os.path.isfile(caminho_limite):
    try:
        import urllib.request
        url_ibge = (
            "https://servicodados.ibge.gov.br/api/v3/malhas/estados/50"
            "?formato=application/vnd.geo+json&qualidade=intermediaria")
        pedido = urllib.request.Request(url_ibge,
                                        headers={"User-Agent": "QGIS"})
        with urllib.request.urlopen(pedido, timeout=30) as resposta, \
                open(caminho_limite, "wb") as arquivo:
            arquivo.write(resposta.read())
        print("✔ Limite de MS baixado do IBGE → dados/reais/limite_MS.geojson")
    except Exception as erro:
        print(f"⚠ Não consegui baixar o limite de MS do IBGE: {erro}")
        print("  O mapa segue sem a máscara do estado (só desta vez;")
        print("  rode de novo com internet que ele tenta outra vez).")

limite = None
if os.path.isfile(caminho_limite):
    limite = QgsVectorLayer(caminho_limite,
                            "Mato Grosso do Sul (limite IBGE)", "ogr")
    if limite.isValid():
        mascara = QgsFillSymbol.createSimple({
            "color": "252,252,251,215",      # véu branco fora do estado
            "outline_color": "110,110,110,255",
            "outline_width": "0.5",
        })
        limite.setRenderer(
            QgsInvertedPolygonRenderer(QgsSingleSymbolRenderer(mascara)))
        projeto.addMapLayer(limite)
        print("✔ Máscara aplicada: só MS visível, divisa desenhada")
    else:
        limite = None
        print("⚠ Baixei o limite mas não consegui lê-lo; sigo sem máscara.")

# 3. Só os processos da Bella Pedra ------------------------------------------
bella = QgsVectorLayer(fonte, "Bella Pedra Cristal (7 processos)", "ogr")
if not bella.isValid():
    print(f"✘ ERRO ao carregar o shapefile: {fonte}")
    raise PareAqui("falha ao carregar o shapefile (veja acima)")
bella.setProviderEncoding("UTF-8")
bella.setSubsetString("\"NOME\" LIKE 'BELLA PEDRA%'")
print(f"✔ Filtro aplicado: {bella.featureCount()} processos da Bella Pedra")

# 4. Estilo por minério: uma cor por substância, com legenda -----------------
# As cores seguem as famílias dos gráficos do repositório: gemas em rosa,
# areia em azul, calcita em verde, ferro em laranja.
CORES_SUBS = {
    "QUARTZO": "232,123,164",
    "AMETISTA": "182,80,126",
    "AREIA": "42,120,214",
    "CALCITA": "0,131,0",
    "MINÉRIO DE FERRO": "235,104,52",
}


def simbolo_processo(rgb):
    """Polígono translúcido + ponto colorido no centro (visível de longe)."""
    preenchimento = QgsFillSymbol.createSimple({
        "color": f"{rgb},55",
        "outline_color": f"{rgb},255",
        "outline_width": "0.8",
    })
    centro = QgsCentroidFillSymbolLayer()
    centro.setSubSymbol(QgsMarkerSymbol.createSimple({
        "name": "circle",
        "color": f"{rgb},255",
        "outline_color": "255,255,255,255",
        "outline_width": "0.8",
        "size": "4.2",
    }))
    preenchimento.appendSymbolLayer(centro)
    return preenchimento


categorias = [QgsRendererCategory(subs, simbolo_processo(rgb), subs)
              for subs, rgb in CORES_SUBS.items()]
# categoria "guarda-chuva" para qualquer substância fora da lista
categorias.append(QgsRendererCategory("", simbolo_processo("137,135,129"),
                                      "outras"))
bella.setRenderer(QgsCategorizedSymbolRenderer("SUBS", categorias))

# Rótulo: nº do processo + substância, afastado do ponto, com halo branco
rotulo = QgsPalLayerSettings()
rotulo.fieldName = "\"PROCESSO\" || '\\n' || lower(\"SUBS\")"
rotulo.isExpression = True
try:  # QGIS ≥ 3.26
    from qgis.core import Qgis
    rotulo.placement = Qgis.LabelPlacement.AroundPoint
except Exception:  # versões mais antigas
    rotulo.placement = QgsPalLayerSettings.AroundPoint
rotulo.dist = 2.0
formato = QgsTextFormat()
formato.setSize(8.5)
formato.setColor(QColor(60, 60, 60))
halo = QgsTextBufferSettings()
halo.setEnabled(True)
halo.setSize(1.3)
halo.setColor(QColor(255, 255, 255))
formato.setBuffer(halo)
rotulo.setFormat(formato)
bella.setLabeling(QgsVectorLayerSimpleLabeling(rotulo))
bella.setLabelsEnabled(True)

projeto.addMapLayer(bella)
print("✔ Estilo aplicado (uma cor por minério + rótulos). Processos:")
for feicao in bella.getFeatures():
    print(f"   {feicao['PROCESSO']} · {feicao['SUBS']} · {feicao['FASE']}")

# 5. Enquadrar o estado (ou, sem o limite, os 7 processos) -------------------
try:
    from qgis.utils import iface
    referencia = limite if limite is not None else bella
    transf = QgsCoordinateTransform(referencia.crs(), projeto.crs(),
                                    projeto.transformContext())
    extensao = transf.transformBoundingBox(referencia.extent())
    extensao.scale(1.06)
    iface.mapCanvas().setExtent(extensao)
    iface.mapCanvas().refresh()
    print(f"✔ Mapa enquadrado: {referencia.name()}")
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
print("MS em satélite (como no projeto principal), com os 7 pontos")
print("coloridos — um por minério; legenda no painel de camadas.")
print("Prefere um mapa mais limpo? Desligue o satélite e ligue o")
print("'Fundo claro — CARTO Positron' no painel de camadas.")
print("Nas próximas vezes, abra direto: projeto/bella_pedra.qgz")
print("=" * 60)
