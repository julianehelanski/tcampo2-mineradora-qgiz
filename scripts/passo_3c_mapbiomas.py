# -*- coding: utf-8 -*-
"""
PASSO 3c — Uso do solo AUTOMÁTICO (MapBiomas)
=============================================
Roda no Console Python do QGIS, com o projeto do passo 1 aberto.

"Dá para identificar os territórios em volta automaticamente?" — dá, e o
trabalho pesado já foi feito: o MapBiomas classifica, por satélite e
algoritmos, o uso do solo do Brasil inteiro, ano a ano (30 m de resolução).
Este script carrega esse dado e aplica a legenda com as cores oficiais.

ANTES DE RODAR, baixe o recorte do MapBiomas (uma vez só):
  1. Busque "MapBiomas plataforma" e abra o módulo COBERTURA E USO DO SOLO.
  2. Escolha o ano mais recente e o território (ex.: município de Bodoquena
     ou o estado do MS) e use a opção de download do GeoTIFF (.tif).
  3. Salve o arquivo em dados/reais/ com "mapbiomas" no nome
     (ex.: mapbiomas_MS_2023.tif).

O que este script faz:
  1. Encontra o .tif do MapBiomas em dados/reais/.
  2. Carrega como camada raster e aplica a legenda oficial (cada código
     de classe vira nome + cor: pastagem, mata, água, urbano, mineração...).
  3. Posiciona a camada acima do satélite e abaixo das camadas de desenho.

Comparação que vale ouro: a classe "Mineração" do MapBiomas × a pegada que
VOCÊ desenhou × a poligonal do SIGMINE — três versões do mesmo território
(o automático, o do olhar treinado, o do papel).
"""

import glob
import os

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsPalettedRasterRenderer,
)
from qgis.PyQt.QtGui import QColor

# ─────────────────────────────────────────────────────────────────────────────
# Edite esta linha SOMENTE se a detecção automática falhar (o script avisa).
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS.

    (Não use SystemExit/sys.exit() em scripts do console do QGIS:
    isso fecha o programa inteiro.)
    """


NOME_CAMADA = "MapBiomas — uso do solo (automático)"

# Classes do MapBiomas relevantes para o MS (código, nome, cor da legenda).
# Cores conforme a legenda oficial das coleções recentes; classes ausentes
# no seu recorte simplesmente não aparecem.
CLASSES = [
    (3,  "Formação florestal",          "#1f8d49"),
    (4,  "Formação savânica (Cerrado)", "#7dc975"),
    (9,  "Silvicultura",                "#7a5900"),
    (11, "Campo alagado / pantanoso",   "#519799"),
    (12, "Formação campestre",          "#d6bc74"),
    (15, "Pastagem",                    "#edde8e"),
    (20, "Cana-de-açúcar",              "#db7093"),
    (21, "Mosaico de usos",             "#ffefc3"),
    (23, "Praia / duna / areal",        "#ffa07a"),
    (24, "Área urbanizada",             "#d4271e"),
    (25, "Outras áreas não vegetadas",  "#db4d4f"),
    (29, "Afloramento rochoso",         "#ffaa5f"),
    (30, "MINERAÇÃO",                   "#9c0027"),
    (31, "Aquicultura",                 "#091077"),
    (33, "Rio, lago e oceano",          "#2532e4"),
    (39, "Soja",                        "#f5b3c8"),
    (40, "Arroz",                       "#c71585"),
    (41, "Outras lavouras temporárias", "#f54ca9"),
    (46, "Café",                        "#d68fe2"),
    (48, "Outras lavouras perenes",     "#e6ccff"),
    (62, "Algodão",                     "#660066"),
]

print("=" * 60)
print("PASSO 3c — MAPBIOMAS (USO DO SOLO AUTOMÁTICO)")
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
    print("  Ou abra antes o projeto mineradora_calcario.qgz (passo 1),")
    print("  ou edite a linha RAIZ = ... no topo deste script.")
    raise PareAqui("caminho RAIZ não encontrado (veja acima)")

arquivo_projeto = os.path.join(RAIZ, "projeto", "mineradora_calcario.qgz")
if not projeto.fileName() and os.path.isfile(arquivo_projeto):
    projeto.read(arquivo_projeto)
    print("✔ Projeto reaberto")

# 2. Encontrar o .tif do MapBiomas -------------------------------------------
pasta_reais = os.path.join(RAIZ, "dados", "reais")
candidatos = sorted(
    glob.glob(os.path.join(pasta_reais, "*mapbiomas*.tif"))
    + glob.glob(os.path.join(pasta_reais, "*MapBiomas*.tif"))
    + glob.glob(os.path.join(pasta_reais, "*MAPBIOMAS*.tif"))
)
if not candidatos:
    print(f"✘ Não achei nenhum .tif do MapBiomas em: {pasta_reais}")
    print("  Baixe o recorte (veja o guia no topo deste script) e salve lá,")
    print("  com 'mapbiomas' no nome do arquivo. Ex.: mapbiomas_MS_2023.tif")
    raise PareAqui("arquivo do MapBiomas ainda não baixado (veja acima)")
arquivo_tif = candidatos[-1]  # nomes têm o ano no fim: o último é o mais recente
if len(candidatos) > 1:
    print(f"⚠ Achei {len(candidatos)} arquivos; usando o mais recente.")
    print("  (para carregar outro ano — ex.: 1985 —, renomeie-o ou troque")
    print("   'candidatos[-1]' pelo índice desejado nesta linha do script)")
print(f"✔ MapBiomas encontrado: {os.path.basename(arquivo_tif)}")

# Evita duplicar a camada ao re-rodar
for antiga in projeto.mapLayersByName(NOME_CAMADA):
    projeto.removeMapLayer(antiga.id())

camada = QgsRasterLayer(arquivo_tif, NOME_CAMADA)
if not camada.isValid():
    print(f"✘ ERRO: o QGIS não conseguiu abrir o raster: {arquivo_tif}")
    print("  Confira se o download terminou e se o arquivo é um GeoTIFF.")
    raise PareAqui("falha ao abrir o raster do MapBiomas (veja acima)")

# 3. Legenda oficial ---------------------------------------------------------
classes_renderer = [
    QgsPalettedRasterRenderer.Class(codigo, QColor(cor), nome)
    for codigo, nome, cor in CLASSES
]
renderer = QgsPalettedRasterRenderer(camada.dataProvider(), 1, classes_renderer)
renderer.setOpacity(0.7)  # deixa o satélite aparecer por baixo
camada.setRenderer(renderer)
print(f"✔ Legenda aplicada ({len(CLASSES)} classes, cores oficiais)")

# 4. Posicionar: acima do satélite, abaixo dos desenhos ----------------------
projeto.addMapLayer(camada, False)
raiz_arvore = projeto.layerTreeRoot()
filhos = raiz_arvore.children()
posicao = len(filhos)  # padrão: por último (fundo)
for i, no in enumerate(filhos):
    if no.name().startswith("Satélite"):
        posicao = i  # logo acima da primeira camada de satélite
        break
raiz_arvore.insertLayer(posicao, camada)

if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 3c CONCLUÍDO ✔")
print("A classificação AUTOMÁTICA do território está no mapa. Repare:")
print(" • vinho-escuro = classe MINERAÇÃO detectada pelo MapBiomas;")
print(" • compare com a pegada que VOCÊ desenhou e com o SIGMINE —")
print("   três versões do mesmo território (algoritmo, olhar, papel).")
print(" • Ligue/desligue a camada no painel para alternar as leituras;")
print("   ela fica translúcida de propósito, com o satélite por baixo.")
print("Onde o automático erra ou simplifica, o seu desenho e o campo")
print("corrigem — anote as divergências: são dado de pesquisa.")
print("=" * 60)
