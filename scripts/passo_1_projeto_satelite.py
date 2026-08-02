# -*- coding: utf-8 -*-
"""
PASSO 1 — Projeto + imagem de satélite
======================================
Roda no Console Python do QGIS, DEPOIS do passo 0.

O que este script faz:
  1. Cria um projeto novo do QGIS com SRC adequado ao MS
     (SIRGAS 2000 / UTM 21S — EPSG:31981, em metros: bom para medir a pegada).
  2. Adiciona duas camadas de satélite online (XYZ, sem baixar nada):
       • Esri World Imagery  → ligada (a principal, zoom até ~19)
       • Google Satellite    → desligada (reserva, para comparar)
  3. Aproxima o mapa da região calcária de Bodoquena–Bonito (MS).
  4. Salva o projeto em projeto/mineradora_calcario.qgz.

Sobre o acesso: essas imagens são mosaicos públicos e gratuitos.
Qualquer pessoa pode usá-los — é o mesmo tipo de fundo do Google Maps.
"""

import os
import urllib.parse

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsRectangle,
)

# ─────────────────────────────────────────────────────────────────────────────
# AJUSTE OBRIGATÓRIO: use o MESMO caminho que funcionou no passo 0.
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")

# SRC do projeto: SIRGAS 2000 / UTM zona 21 Sul (cobre a região de
# Bodoquena/Bonito/Corumbá; unidades em metros)
EPSG_PROJETO = "EPSG:31981"

# Janela inicial do mapa (graus, WGS 84): região calcária Bodoquena–Bonito
LON_MIN, LON_MAX = -57.1, -56.3
LAT_MIN, LAT_MAX = -21.3, -20.3

print("=" * 60)
print("PASSO 1 — PROJETO + SATÉLITE")
print("=" * 60)

if not os.path.isdir(RAIZ):
    print(f"✘ ERRO: a pasta não existe: {RAIZ}")
    print("  Rode o passo 0 primeiro e use aqui o mesmo caminho RAIZ.")
    raise SystemExit


def camada_xyz(nome, url, zmax=19):
    """Monta uma camada XYZ a partir da URL do serviço de mosaico.

    A URL precisa ser 'percent-encoded' (& vira %26 etc.) porque ela entra
    dentro de outra string de conexão — este é o erro mais comum ao criar
    camadas XYZ por script, e é por isso que usamos urllib.parse.quote.
    """
    url_cod = urllib.parse.quote(url, safe="")
    uri = f"type=xyz&url={url_cod}&zmin=0&zmax={zmax}"
    return QgsRasterLayer(uri, nome, "wms")


# 1. Projeto novo ------------------------------------------------------------
projeto = QgsProject.instance()
projeto.clear()  # limpa o que estiver aberto (evita camadas duplicadas ao re-rodar)
projeto.setTitle("Mineradora de calcário — território de direito × de fato")
projeto.setCrs(QgsCoordinateReferenceSystem(EPSG_PROJETO))
print(f"✔ Projeto novo criado (SRC {EPSG_PROJETO})")

# 2. Camadas de satélite -----------------------------------------------------
esri = camada_xyz(
    "Satélite — Esri World Imagery",
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}",
)
google = camada_xyz(
    "Satélite — Google (reserva)",
    "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
)

for camada in (esri, google):
    if camada.isValid():
        projeto.addMapLayer(camada)
        print(f"✔ Camada adicionada: {camada.name()}")
    else:
        print(f"⚠ Falha ao criar a camada: {camada.name()}")
        print("  Verifique sua conexão com a internet e rode de novo.")

# Deixa a camada do Google desligada (é só uma reserva para comparação)
no_google = projeto.layerTreeRoot().findLayer(google.id())
if no_google:
    no_google.setItemVisibilityChecked(False)

# 3. Aproximar da região calcária -------------------------------------------
try:
    from qgis.utils import iface

    ret_wgs84 = QgsRectangle(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)
    transf = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"),
        projeto.crs(),
        projeto.transformContext(),
    )
    iface.mapCanvas().setExtent(transf.transformBoundingBox(ret_wgs84))
    iface.mapCanvas().refresh()
    print("✔ Mapa aproximado da região Bodoquena–Bonito (MS)")
except Exception as erro:
    # Sem interface gráfica (ex.: teste automatizado) o zoom não é possível;
    # o projeto continua válido.
    print(f"⚠ Não consegui ajustar o zoom automaticamente: {erro}")

# 4. Salvar ------------------------------------------------------------------
arquivo_projeto = os.path.join(RAIZ, "projeto", "mineradora_calcario.qgz")
os.makedirs(os.path.dirname(arquivo_projeto), exist_ok=True)
if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")
else:
    print(f"⚠ Não consegui salvar em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 1 CONCLUÍDO ✔")
print("Explore o mapa: as cavas de calcário aparecem como manchas claras,")
print("rosadas/esbranquiçadas, com estradas de acesso e pilhas ao redor.")
print("PRÓXIMO: passo 2 — poligonal do SIGMINE (território de DIREITO).")
print("=" * 60)
