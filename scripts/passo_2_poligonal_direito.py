# -*- coding: utf-8 -*-
"""
PASSO 2 — Poligonal do SIGMINE: o território de DIREITO
=======================================================
Roda no Console Python do QGIS, DEPOIS do passo 1.

O que este script faz:
  1. Reabre o projeto salvo no passo 1 (satélite + SRC configurado).
  2. Carrega o shapefile do SIGMINE-MS direto de dentro do zip
     (dados/reais/sigmine_MS.zip) — sem precisar descompactar.
  3. Cria DUAS camadas a partir dele:
       • "SIGMINE MS — todos os processos"  → cinza discreto, desligada
       • "SIGMINE MS — calcário (DIREITO)"  → filtrada, colorida por FASE
  4. Pinta cada FASE com um tom pastel e destaca a CONCESSÃO DE LAVRA
     (rosa mais forte): são as áreas onde a extração é autorizada de fato.
  5. Aproxima o mapa dos polígonos de calcário e salva o projeto.

Ideia do método (Lemonnier, cap. 2): esta camada mostra onde a mineração
existe NO PAPEL. Comparar com o satélite (passo 3) revela o território de fato.
"""

import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFillSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
)

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
print("PASSO 2 — POLIGONAL SIGMINE (TERRITÓRIO DE DIREITO)")
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
# Preferência: a pasta dados/reais/sigmine_MS/ (shapefile completo, extraído,
# que também pode ser aberto direto no QGIS arrastando o MS.shp para o mapa).
# Alternativas: o zip antigo (o QGIS lê dentro de zip pelo prefixo /vsizip/,
# recurso do GDAL) ou um MS.shp solto em dados/reais/.
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
    print("  (o arquivo está no repositório; confira se a pasta RAIZ")
    print("   é a pasta do repositório baixado)")
    raise PareAqui("shapefile do SIGMINE não encontrado (veja acima)")


def nova_camada_sigmine(nome):
    """Carrega o shapefile como uma nova camada (uma instância por chamada)."""
    camada = QgsVectorLayer(fonte, nome, "ogr")
    if not camada.isValid():
        print(f"✘ ERRO ao carregar o shapefile: {fonte}")
        raise PareAqui("falha ao carregar o shapefile (veja acima)")
    camada.setProviderEncoding("UTF-8")
    return camada


# 3. Camada de fundo: todos os processos (desligada) -------------------------
todos = nova_camada_sigmine("SIGMINE MS — todos os processos")
simbolo_cinza = QgsFillSymbol.createSimple({
    "color": "200,200,200,40",          # cinza quase transparente
    "outline_color": "130,130,130,180",
    "outline_width": "0.25",
})
todos.renderer().setSymbol(simbolo_cinza)
projeto.addMapLayer(todos)
no_todos = projeto.layerTreeRoot().findLayer(todos.id())
if no_todos:
    no_todos.setItemVisibilityChecked(False)
print(f"✔ Camada de contexto adicionada (desligada): {todos.featureCount()} processos no MS")

# 4. Camada principal: só calcário -------------------------------------------
# Filtro em SQL do OGR. 'CALC%' pega CALCÁRIO, CALCÁRIO DOLOMÍTICO,
# CALCÁRIO CALCÍTICO e CALCITA; excluímos a calcita (mineral, outro contexto).
calcario = nova_camada_sigmine("SIGMINE MS — calcário (DIREITO)")
calcario.setSubsetString("\"SUBS\" LIKE 'CALC%' AND \"SUBS\" <> 'CALCITA'")
print(f"✔ Filtro aplicado: {calcario.featureCount()} processos de calcário")

# 5. Estilo por FASE (paleta pastel; concessão de lavra em destaque) ---------
# Lemos as fases existentes no próprio dado — assim o script não depende de
# acentuação nem de mudanças de grafia da ANM.
indice_fase = calcario.fields().indexOf("FASE")
fases = sorted(v for v in calcario.uniqueValues(indice_fase) if v)

PASTEIS = [  # tons suaves para as fases "de papel"
    "255,228,181",  # amarelo areia
    "204,229,255",  # azul claro
    "221,255,221",  # verde claro
    "230,220,250",  # lilás
    "255,240,200",  # creme
    "215,235,235",  # verde-água
    "245,222,235",  # rosa bem claro
    "235,235,215",  # bege
]

categorias = []
i_pastel = 0
for fase in fases:
    if "CONCESS" in fase.upper():           # CONCESSÃO DE LAVRA → destaque
        simbolo = QgsFillSymbol.createSimple({
            "color": "255,105,140,110",      # rosa forte (extração!)
            "outline_color": "200,30,80,255",
            "outline_width": "0.8",
        })
    else:
        simbolo = QgsFillSymbol.createSimple({
            "color": PASTEIS[i_pastel % len(PASTEIS)] + ",90",
            "outline_color": "120,120,120,200",
            "outline_width": "0.35",
        })
        i_pastel += 1
    categorias.append(QgsRendererCategory(fase, simbolo, fase))

calcario.setRenderer(QgsCategorizedSymbolRenderer("FASE", categorias))
projeto.addMapLayer(calcario)
print("✔ Estilo por FASE aplicado (concessão de lavra em rosa forte)")

# Resumo no console: quantos processos por fase
print("-" * 60)
contagem = {}
for feicao in calcario.getFeatures():
    contagem[feicao["FASE"]] = contagem.get(feicao["FASE"], 0) + 1
for fase, n in sorted(contagem.items(), key=lambda x: -x[1]):
    print(f"   {n:4d} × {fase}")
print("-" * 60)

# 6. Aproximar dos polígonos de calcário -------------------------------------
try:
    from qgis.utils import iface
    from qgis.core import QgsCoordinateTransform

    transf = QgsCoordinateTransform(
        calcario.crs(), projeto.crs(), projeto.transformContext()
    )
    extensao = transf.transformBoundingBox(calcario.extent())
    extensao.scale(1.1)  # folga de 10% nas bordas
    iface.mapCanvas().setExtent(extensao)
    iface.mapCanvas().refresh()
    print("✔ Mapa aproximado dos processos de calcário")
except Exception as erro:
    print(f"⚠ Não consegui ajustar o zoom automaticamente: {erro}")

# 7. Salvar ------------------------------------------------------------------
if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")
else:
    print(f"⚠ Não consegui salvar em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 2 CONCLUÍDO ✔")
print("Dica: use a ferramenta 'Identificar feições' (Ctrl+Shift+I) e clique")
print("num polígono rosa para ver o titular (NOME), o processo e a área.")
print("Compare: dentro da poligonal, o que o satélite mostra de verdade?")
print("PRÓXIMO: passo 3 — desenhar a pegada real (território de FATO);")
print("         leia também 03_desenhar_pegada.md.")
print("=" * 60)
