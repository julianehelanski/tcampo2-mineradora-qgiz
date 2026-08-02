# -*- coding: utf-8 -*-
"""
PASSO 3 — Camada da pegada: o território de FATO
================================================
Roda no Console Python do QGIS, DEPOIS do passo 2 (ou com o projeto
mineradora_calcario.qgz aberto).

O que este script faz:
  1. Descobre o caminho RAIZ sozinho, a partir do projeto aberto
     (se não conseguir, usa a linha RAIZ abaixo — edite só nesse caso).
  2. Cria o arquivo dados/pegada_fato.gpkg com uma camada de polígonos
     vazia, pronta para você DESENHAR sobre o satélite o que a mineradora
     realmente ocupa. Se o arquivo já existe, só reabre (não apaga nada!).
  3. Configura o formulário: o campo "tipo" vira um menu de opções
     (extração, beneficiamento, calcinação, rejeito, água, logística).
  4. Aplica a paleta pastel do projeto — cada tipo com sua cor.
  5. Põe a camada no topo, salva o projeto e imprime o guia de desenho.

O desenho em si é manual — e é proposital: delimitar a pegada olhando o
satélite é o exercício que treina o olhar geográfico (03_desenhar_pegada.md).
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


NOME_CAMADA = "Pegada da mineradora (FATO)"

# Tipos de área e paleta pastel do projeto (convenção do repositório)
TIPOS = [
    # (valor gravado, rótulo no formulário, cor RGB pastel)
    ("extracao",       "Extração (cava)",           "244,166,192"),  # rosa
    ("beneficiamento", "Beneficiamento (britagem)", "180,220,180"),  # verde
    ("calcinacao",     "Calcinação (fornos)",       "170,200,235"),  # azul
    ("rejeito",        "Rejeito / estéril",         "205,180,230"),  # lilás
    ("agua",           "Água (lagoa, decantação)",  "170,220,215"),  # verde-água
    ("logistica",      "Logística (pátio, estrada)","245,225,150"),  # amarelo
    ("outro",          "Outro (anote em obs)",      "210,210,210"),  # cinza
]

print("=" * 60)
print("PASSO 3 — CAMADA DA PEGADA (TERRITÓRIO DE FATO)")
print("=" * 60)

# 1. Descobrir RAIZ ----------------------------------------------------------
projeto = QgsProject.instance()
if not os.path.isdir(RAIZ):
    arquivo_aberto = projeto.fileName()  # ex.: .../RAIZ/projeto/mineradora_calcario.qgz
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

# Garante que o projeto do passo 1/2 está aberto
arquivo_projeto = os.path.join(RAIZ, "projeto", "mineradora_calcario.qgz")
if not projeto.fileName() and os.path.isfile(arquivo_projeto):
    projeto.read(arquivo_projeto)
    print("✔ Projeto reaberto")

# 2. Criar (ou reabrir) o GeoPackage da pegada -------------------------------
caminho_gpkg = os.path.join(RAIZ, "dados", "pegada_fato.gpkg")

if not os.path.isfile(caminho_gpkg):
    # Monta uma camada vazia em memória e grava como GeoPackage.
    # Usamos o SRC do projeto (UTM, metros): áreas saem direto em m²/ha.
    definicao = (
        f"Polygon?crs={projeto.crs().authid()}"
        "&field=tipo:string(30)"
        "&field=nome:string(80)"
        "&field=obs:string(254)"
    )
    memoria = QgsVectorLayer(definicao, "pegada_fato", "memory")
    opcoes = QgsVectorFileWriter.SaveVectorOptions()
    opcoes.driverName = "GPKG"
    opcoes.layerName = "pegada_fato"
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

pegada = QgsVectorLayer(f"{caminho_gpkg}|layername=pegada_fato", NOME_CAMADA, "ogr")
if not pegada.isValid():
    print(f"✘ ERRO ao abrir a camada em: {caminho_gpkg}")
    raise PareAqui("falha ao abrir a camada da pegada (veja acima)")

# 3. Formulário amigável: campo "tipo" vira menu de opções -------------------
indice_tipo = pegada.fields().indexOf("tipo")
mapa_opcoes = [{rotulo: valor} for valor, rotulo, _ in TIPOS]
pegada.setEditorWidgetSetup(
    indice_tipo, QgsEditorWidgetSetup("ValueMap", {"map": mapa_opcoes})
)
print("✔ Formulário configurado: 'tipo' com menu de opções")

# 4. Paleta pastel por tipo --------------------------------------------------
categorias = []
for valor, rotulo, cor in TIPOS:
    simbolo = QgsFillSymbol.createSimple({
        "color": cor + ",150",              # semitransparente: satélite aparece
        "outline_color": "80,80,80,220",
        "outline_width": "0.4",
    })
    categorias.append(QgsRendererCategory(valor, simbolo, rotulo))
pegada.setRenderer(QgsCategorizedSymbolRenderer("tipo", categorias))
print("✔ Paleta pastel aplicada (rosa=extração, verde=beneficiamento, ...)")

# 5. Adicionar no topo e salvar ----------------------------------------------
projeto.addMapLayer(pegada, False)
projeto.layerTreeRoot().insertLayer(0, pegada)

if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")

# Fim: guia de desenho -------------------------------------------------------
print("=" * 60)
print("PASSO 3 CONCLUÍDO ✔ — agora é DESENHAR (guia rápido):")
print("")
print(" 1. Dê zoom na mineradora escolhida (satélite bem visível).")
print(" 2. Clique na camada 'Pegada da mineradora (FATO)' no painel")
print("    de camadas, para deixá-la selecionada.")
print(" 3. Clique no LÁPIS amarelo (Alternar edição) na barra superior.")
print(" 4. Clique no ícone de polígono verde ('Adicionar polígono').")
print(" 5. Clique ponto a ponto contornando a área (ex.: a cava);")
print("    clique DIREITO para fechar o polígono.")
print(" 6. No formulário que abre, escolha o TIPO no menu, dê um nome")
print("    e (se quiser) uma observação → OK.")
print(" 7. Repita para cada área: pilhas, pátio, fornos, lagoa...")
print(" 8. Ao terminar: clique no lápis de novo e SALVE as edições.")
print("")
print("Dica: desenhe primeiro a pegada que você SUPÕE, antes do campo;")
print("depois da visita, corrija — a diferença entre as duas versões é")
print("dado de pesquisa (Lemonnier, cap. 2).")
print("PRÓXIMO: passo 4 — pontos coletados no campo.")
print("=" * 60)
