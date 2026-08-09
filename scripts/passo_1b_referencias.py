# -*- coding: utf-8 -*-
"""
PASSO 1b — Camadas de referência: cidades, rodovias, parques e reservas
=======================================================================
Roda no Console Python do QGIS, a qualquer momento DEPOIS do passo 1
(pode ser antes ou depois do passo 2 — ele só acrescenta camadas).

O que este script faz:
  1. Reabre o projeto salvo no passo 1.
  2. Adiciona camadas de referência online (XYZ, sem baixar nada):
       • "Nomes de cidades e lugares (Esri)" → SOBRE o satélite, ligada
       • "Rodovias (Esri)"                   → SOBRE o satélite, ligada
       • "OpenStreetMap"                     → SOB o satélite: desligue a
         camada de satélite para ver o mapa de ruas completo, com parques
         e reservas em verde, cidades, estradas com número (BR-262 etc.)
  3. Se você tiver baixado os shapefiles oficiais (veja 02_dados_reais.md),
     carrega também:
       • dados/reais/unidades_conservacao/*.shp  (CNUC/MMA — parques etc.)
       • dados/reais/terras_indigenas/*.shp      (FUNAI)
  4. Salva o projeto.

As duas camadas da Esri são "transparentes": só têm os nomes e as linhas,
desenhados por cima da imagem de satélite — é assim que o próprio Google
Maps monta o modo híbrido.
"""

import glob
import os
import urllib.parse

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFillSymbol,
)

# ─────────────────────────────────────────────────────────────────────────────
# AJUSTE OBRIGATÓRIO: use o MESMO caminho dos passos anteriores.
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS.

    (Não use SystemExit/sys.exit() em scripts do console do QGIS:
    isso fecha o programa inteiro.)
    """


print("=" * 60)
print("PASSO 1b — CAMADAS DE REFERÊNCIA (CIDADES, RODOVIAS, RESERVAS)")
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

arvore = projeto.layerTreeRoot()


def camada_xyz(nome, url, zmax=19):
    """Monta uma camada XYZ (mesma técnica do passo 1)."""
    url_cod = urllib.parse.quote(url, safe="")
    uri = f"type=xyz&url={url_cod}&zmin=0&zmax={zmax}"
    return QgsRasterLayer(uri, nome, "wms")


def ja_existe(nome):
    """Evita duplicar a camada se o script rodar duas vezes."""
    return bool(projeto.mapLayersByName(nome))


# 2. Sobreposições sobre o satélite (nomes e rodovias) -----------------------
SOBREPOSICOES = [
    ("Referência — rodovias (Esri)",
     "https://server.arcgisonline.com/ArcGIS/rest/services/"
     "Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"),
    ("Referência — nomes de cidades e lugares (Esri)",
     "https://server.arcgisonline.com/ArcGIS/rest/services/"
     "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"),
]
for nome, url in SOBREPOSICOES:
    if ja_existe(nome):
        print(f"• Já estava no projeto: {nome}")
        continue
    camada = camada_xyz(nome, url)
    if camada.isValid():
        projeto.addMapLayer(camada, False)
        arvore.insertLayer(0, camada)          # topo da pilha de camadas
        print(f"✔ Sobreposição adicionada: {nome}")
    else:
        print(f"⚠ Falha ao criar: {nome} — verifique a internet e rode de novo.")

# 3. OpenStreetMap como fundo alternativo ------------------------------------
# Fica EMBAIXO do satélite: desligue a camada de satélite (caixinha no painel
# de camadas) para ver o mapa de ruas — parques e reservas aparecem em verde,
# com nome; rodovias com número; cidades e povoados.
NOME_OSM = "Referência — OpenStreetMap (fundo alternativo)"
if not ja_existe(NOME_OSM):
    osm = camada_xyz(NOME_OSM,
                     "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    if osm.isValid():
        projeto.addMapLayer(osm, False)
        arvore.addLayer(osm)                   # fim da lista = fundo da pilha
        print(f"✔ Fundo alternativo adicionado: {NOME_OSM}")
        print("  (desligue o satélite para vê-lo)")
    else:
        print(f"⚠ Falha ao criar: {NOME_OSM}")
else:
    print(f"• Já estava no projeto: {NOME_OSM}")

# 4. Shapefiles oficiais, se já baixados (opcional) --------------------------
# Veja 02_dados_reais.md, seção "Unidades de conservação e terras indígenas".
OFICIAIS = [
    (os.path.join(RAIZ, "dados", "reais", "unidades_conservacao"),
     "Unidades de conservação (CNUC/MMA)",
     {"color": "160,215,160,60", "outline_color": "20,110,40,230",
      "outline_width": "0.6", "outline_style": "dash"}),
    (os.path.join(RAIZ, "dados", "reais", "terras_indigenas"),
     "Terras indígenas (FUNAI)",
     {"color": "240,200,150,50", "outline_color": "170,90,20,230",
      "outline_width": "0.6", "outline_style": "dash"}),
]
algum_oficial = False
for pasta, nome, estilo in OFICIAIS:
    shps = sorted(glob.glob(os.path.join(pasta, "*.shp")))
    if not shps:
        continue
    algum_oficial = True
    if ja_existe(nome):
        print(f"• Já estava no projeto: {nome}")
        continue
    camada = QgsVectorLayer(shps[0], nome, "ogr")
    if not camada.isValid():
        print(f"⚠ Achei mas não consegui ler: {shps[0]}")
        continue
    camada.setProviderEncoding("UTF-8")
    camada.renderer().setSymbol(QgsFillSymbol.createSimple(estilo))
    projeto.addMapLayer(camada, False)
    arvore.insertLayer(0, camada)
    print(f"✔ Camada oficial adicionada: {nome} ({camada.featureCount()} áreas)")

if not algum_oficial:
    print("• Sem shapefiles oficiais em dados/reais/ (tudo bem: o")
    print("  OpenStreetMap já mostra parques e reservas em verde).")
    print("  Para as poligonais oficiais, veja 02_dados_reais.md, seção 6.")

# 5. Salvar ------------------------------------------------------------------
if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")
else:
    print(f"⚠ Não consegui salvar em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 1b CONCLUÍDO ✔")
print("Com o satélite LIGADO: nomes de cidades e rodovias por cima da imagem.")
print("Com o satélite DESLIGADO: mapa de ruas completo (OpenStreetMap), com")
print("parques e reservas em verde — ex.: o Parque Nacional da Serra da")
print("Bodoquena, vizinho da região calcária.")
print("=" * 60)
