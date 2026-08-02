# -*- coding: utf-8 -*-
"""
PASSO 3b — Territórios do ENTORNO da mineradora
===============================================
Roda no Console Python do QGIS, a qualquer momento depois do passo 3.

A mineradora não existe isolada: ela faz fronteira (e disputa espaço) com
pastagem, agricultura, mata, turismo, comunidades. Este script cria uma
SEGUNDA camada de desenho, "Territórios do entorno", para você mapear esses
vizinhos — e enxergar a mina como parte de um território maior.

O que este script faz:
  1. Descobre o RAIZ sozinho (pelo projeto aberto), como no passo 3.
  2. Cria dados/entorno_territorios.gpkg com uma camada de polígonos vazia.
     Se já existir, só reabre (desenhos preservados).
  3. Campo "tipo" com menu de opções (pastagem, agricultura, mata, água,
     urbano, turismo, comunidade) e cores próprias, com BORDA TRACEJADA
     para não confundir com a pegada da mineradora.
  4. Posiciona a camada logo ABAIXO da pegada e salva o projeto.

O desenho é manual, igual ao passo 3: lápis amarelo → polígono → tipo → OK.
"""

import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsFillSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsEditorWidgetSetup,
)

# ─────────────────────────────────────────────────────────────────────────────
# Edite esta linha SOMENTE se a detecção automática falhar (o script avisa).
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")


class PareAqui(Exception):
    """Interrompe o script mostrando a mensagem, SEM fechar o QGIS.

    (Não use SystemExit/sys.exit() em scripts do console do QGIS:
    isso fecha o programa inteiro.)
    """


NOME_CAMADA = "Territórios do entorno"
NOME_CAMADA_PEGADA = "Pegada da mineradora (FATO)"

# Tipos de território do entorno e suas cores (tons próprios, diferentes da
# paleta da pegada; a borda tracejada também ajuda a distinguir no mapa)
TIPOS = [
    # (valor gravado, rótulo no formulário, cor RGB)
    ("pastagem",    "Pastagem / pecuária",            "228,238,188"),  # verde-amarelado
    ("agricultura", "Agricultura (lavoura)",          "245,222,179"),  # palha
    ("vegetacao",   "Vegetação nativa / mata",        "163,201,168"),  # verde-mata
    ("agua",        "Rio / córrego / nascente",       "173,216,230"),  # azul-claro
    ("urbano",      "Área urbana / vila",             "229,204,204"),  # cinza-rosado
    ("turismo",     "Turismo (balneário, gruta)",     "250,213,165"),  # pêssego
    ("comunidade",  "Assentamento / comunidade",      "214,199,236"),  # lavanda
    ("outro",       "Outro (anote em obs)",           "215,215,215"),  # cinza
]

print("=" * 60)
print("PASSO 3b — TERRITÓRIOS DO ENTORNO")
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

# 2. Criar (ou reabrir) o GeoPackage do entorno ------------------------------
caminho_gpkg = os.path.join(RAIZ, "dados", "entorno_territorios.gpkg")

if not os.path.isfile(caminho_gpkg):
    definicao = (
        f"Polygon?crs={projeto.crs().authid()}"
        "&field=tipo:string(30)"
        "&field=nome:string(80)"
        "&field=obs:string(254)"
    )
    memoria = QgsVectorLayer(definicao, "entorno_territorios", "memory")
    opcoes = QgsVectorFileWriter.SaveVectorOptions()
    opcoes.driverName = "GPKG"
    opcoes.layerName = "entorno_territorios"
    resultado = QgsVectorFileWriter.writeAsVectorFormatV3(
        memoria, caminho_gpkg, projeto.transformContext(), opcoes
    )
    if resultado[0] != QgsVectorFileWriter.NoError:
        print(f"✘ ERRO ao criar o arquivo: {caminho_gpkg}")
        print(f"  Detalhe: {resultado}")
        raise PareAqui("falha ao criar o GeoPackage (veja acima)")
    print(f"✔ Arquivo criado: {caminho_gpkg}")
else:
    print(f"✔ Arquivo já existia (desenhos preservados): {caminho_gpkg}")

# Evita duplicar a camada ao re-rodar
for antiga in projeto.mapLayersByName(NOME_CAMADA):
    projeto.removeMapLayer(antiga.id())

entorno = QgsVectorLayer(
    f"{caminho_gpkg}|layername=entorno_territorios", NOME_CAMADA, "ogr"
)
if not entorno.isValid():
    print(f"✘ ERRO ao abrir a camada em: {caminho_gpkg}")
    raise PareAqui("falha ao abrir a camada do entorno (veja acima)")

# 3. Formulário: campo "tipo" com menu de opções -----------------------------
indice_tipo = entorno.fields().indexOf("tipo")
mapa_opcoes = [{rotulo: valor} for valor, rotulo, _ in TIPOS]
entorno.setEditorWidgetSetup(
    indice_tipo, QgsEditorWidgetSetup("ValueMap", {"map": mapa_opcoes})
)
print("✔ Formulário configurado: 'tipo' com menu de opções")

# 4. Estilo: cores próprias, borda tracejada, bem transparente ---------------
categorias = []
for valor, rotulo, cor in TIPOS:
    simbolo = QgsFillSymbol.createSimple({
        "color": cor + ",100",           # mais transparente que a pegada
        "outline_color": "70,70,70,200",
        "outline_width": "0.35",
        "outline_style": "dash",         # tracejado = entorno (≠ mineradora)
    })
    categorias.append(QgsRendererCategory(valor, simbolo, rotulo))
entorno.setRenderer(QgsCategorizedSymbolRenderer("tipo", categorias))
print("✔ Estilo aplicado (borda tracejada = território do entorno)")

# 5. Posicionar logo abaixo da pegada e salvar -------------------------------
projeto.addMapLayer(entorno, False)
raiz_arvore = projeto.layerTreeRoot()
posicao = 0
camadas_pegada = projeto.mapLayersByName(NOME_CAMADA_PEGADA)
if camadas_pegada:
    no_pegada = raiz_arvore.findLayer(camadas_pegada[0].id())
    if no_pegada and no_pegada.parent() == raiz_arvore:
        posicao = raiz_arvore.children().index(no_pegada) + 1
raiz_arvore.insertLayer(posicao, entorno)

if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 3b CONCLUÍDO ✔ — desenhe os vizinhos da mineradora:")
print("")
print(" • Selecione 'Territórios do entorno' no painel de camadas,")
print("   lápis amarelo → polígono verde → contorne → botão direito →")
print("   escolha o tipo → OK (igual ao passo 3).")
print(" • Sugestão: comece pelo que faz FRONTEIRA com a mina — a fazenda")
print("   ao lado, a mata que sobrou, o rio que passa perto, a estrada.")
print(" • No campo 'obs', anote relações, não só usos: 'poeira chega aqui?',")
print("   'quem trabalha na mina mora onde?', 'o rio abastece o quê?'.")
print("")
print("Leitura do mapa: borda CONTÍNUA = pegada da mineradora;")
print("borda TRACEJADA = territórios do entorno.")
print("=" * 60)
