# -*- coding: utf-8 -*-
"""
PASSO 2b — Bella Pedra por minério, no projeto principal
========================================================
Roda no Console Python do QGIS, DEPOIS do passo 1 (pode ser antes ou
depois do passo 2 — ele só acrescenta camadas ao projeto principal).

É o molde do passo 2, mas em vez do calcário colorido por FASE, a camada
destacada são os 7 processos da BELLA PEDRA CRISTAL LTDA com as
categorias POR MINÉRIO (mesmas cores do projeto bella_pedra.qgz):
quartzo e ametista em rosas, areia em azul, calcita em verde, minério de
ferro em laranja — com legenda no painel de camadas.

O que este script faz:
  1. Reabre o projeto salvo no passo 1 (satélite + SRC configurado).
  2. Garante a camada de contexto "SIGMINE MS — todos os processos"
     (cinza discreto, desligada) — sem duplicar se o passo 2 já a criou.
  3. Cria a camada "Bella Pedra — por minério": polígono translúcido +
     ponto colorido no centro (visível no zoom de estado) + rótulo.
  4. Aproxima o mapa dos 7 processos e salva o projeto.
"""

import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsCentroidFillSymbolLayer,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtGui import QColor

# ─────────────────────────────────────────────────────────────────────────────
# AJUSTE OBRIGATÓRIO: use o MESMO caminho dos passos 0 e 1.
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS.

    (Não use SystemExit/sys.exit() em scripts do console do QGIS:
    isso fecha o programa inteiro.)
    """


print("=" * 60)
print("PASSO 2b — BELLA PEDRA POR MINÉRIO (PROJETO PRINCIPAL)")
print("=" * 60)

# 1. Reabrir o projeto do passo 1 --------------------------------------------
projeto = QgsProject.instance()
arquivo_projeto = os.path.join(RAIZ, "projeto", "mineradora_calcario.qgz")
if os.path.isfile(arquivo_projeto):
    if projeto.fileName() != arquivo_projeto:
        projeto.read(arquivo_projeto)
    print(f"✔ Projeto aberto: {arquivo_projeto}")
else:
    print(f"✘ ERRO: não achei o projeto: {arquivo_projeto}")
    print("  Rode o passo 1 primeiro (e confira o caminho RAIZ).")
    raise PareAqui("projeto do passo 1 não encontrado (veja acima)")

# 2. Localizar o shapefile do SIGMINE ----------------------------------------
shp_pasta = os.path.join(RAIZ, "dados", "reais", "sigmine_MS", "MS.shp")
zip_sigmine = os.path.join(RAIZ, "dados", "reais", "sigmine_MS.zip")
shp_solto = os.path.join(RAIZ, "dados", "reais", "MS.shp")
if os.path.isfile(shp_pasta):
    fonte = shp_pasta
elif os.path.isfile(zip_sigmine):
    fonte = "/vsizip/" + zip_sigmine.replace("\\", "/") + "/MS.shp"
elif os.path.isfile(shp_solto):
    fonte = shp_solto
else:
    print("✘ ERRO: não achei o SIGMINE em dados/reais/")
    print(f"  Esperava: {shp_pasta}")
    print("  Confira se RAIZ aponta para a pasta do repositório baixado.")
    raise PareAqui("shapefile do SIGMINE não encontrado (veja acima)")


def nova_camada_sigmine(nome):
    """Carrega o shapefile como uma nova camada (uma instância por chamada)."""
    camada = QgsVectorLayer(fonte, nome, "ogr")
    if not camada.isValid():
        print(f"✘ ERRO ao carregar o shapefile: {fonte}")
        raise PareAqui("falha ao carregar o shapefile (veja acima)")
    camada.setProviderEncoding("UTF-8")
    return camada


# 3. Camada de contexto: todos os processos (cinza, desligada) ---------------
NOME_TODOS = "SIGMINE MS — todos os processos"
if projeto.mapLayersByName(NOME_TODOS):
    print(f"• Já estava no projeto (mantida): {NOME_TODOS}")
else:
    todos = nova_camada_sigmine(NOME_TODOS)
    todos.renderer().setSymbol(QgsFillSymbol.createSimple({
        "color": "200,200,200,40",
        "outline_color": "130,130,130,180",
        "outline_width": "0.25",
    }))
    projeto.addMapLayer(todos)
    no_todos = projeto.layerTreeRoot().findLayer(todos.id())
    if no_todos:
        no_todos.setItemVisibilityChecked(False)
    print(f"✔ Camada de contexto adicionada (desligada): "
          f"{todos.featureCount()} processos no MS")

# 4. Camada principal: Bella Pedra por minério -------------------------------
NOME_BELLA = "Bella Pedra — por minério"
for repetida in projeto.mapLayersByName(NOME_BELLA):
    projeto.removeMapLayer(repetida.id())   # recriar do zero se rodar de novo

bella = nova_camada_sigmine(NOME_BELLA)
bella.setSubsetString("\"NOME\" LIKE 'BELLA PEDRA%'")
print(f"✔ Filtro aplicado: {bella.featureCount()} processos da Bella Pedra")

# Mesmas cores do projeto bella_pedra.qgz (famílias dos gráficos)
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
print("✔ Estilo por minério aplicado (legenda no painel). Processos:")
for feicao in bella.getFeatures():
    print(f"   {feicao['PROCESSO']} · {feicao['SUBS']} · {feicao['FASE']}")

# 5. Aproximar dos 7 processos -----------------------------------------------
try:
    from qgis.utils import iface
    from qgis.core import QgsCoordinateTransform

    transf = QgsCoordinateTransform(
        bella.crs(), projeto.crs(), projeto.transformContext())
    extensao = transf.transformBoundingBox(bella.extent())
    extensao.scale(1.15)
    iface.mapCanvas().setExtent(extensao)
    iface.mapCanvas().refresh()
    print("✔ Mapa enquadrado nos 7 processos")
except Exception as erro:
    print(f"⚠ Não consegui ajustar o zoom automaticamente: {erro}")

# 6. Salvar ------------------------------------------------------------------
if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")
else:
    print(f"⚠ Não consegui salvar em: {arquivo_projeto}")

print("=" * 60)
print("PASSO 2b CONCLUÍDO ✔")
print("Os 7 processos da Bella Pedra estão sobre o satélite, um por cor")
print("de minério (legenda no painel de camadas). Aproxime o zoom num")
print("ponto para ver a poligonal e o que o satélite mostra lá dentro.")
print("Dica: 'Identificar feições' (Ctrl+Shift+I) num polígono mostra")
print("processo, fase e área.")
print("=" * 60)
