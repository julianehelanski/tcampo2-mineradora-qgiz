# -*- coding: utf-8 -*-
"""
PASSO 4 — Pontos coletados no CAMPO
===================================
Roda no Console Python do QGIS, com o projeto do passo 1 aberto.

Durante a visita, vocês anotam pontos numa planilha simples (no celular
mesmo): nome, tipo, lon, lat, obs. Este script importa essa planilha e
desenha os pontos no mapa, coloridos por tipo e com rótulos.

Como preparar a planilha do campo:
  1. Copie o modelo dados/exemplo/pontos_campo_modelo.csv (abra no Excel,
     Google Planilhas ou bloco de notas) e veja o formato.
  2. No campo, para pegar lon/lat: no Google Maps, toque e segure no local
     → as coordenadas aparecem (lat, lon — ATENÇÃO: a planilha usa a ordem
     lon, lat!). Ou use um app de GPS (GPS Essentials, Avenza...).
  3. Salve como CSV (separado por vírgulas, decimais com PONTO) em:
        dados/reais/pontos_campo.csv
  4. Rode este script. Pode rodar quantas vezes quiser: ele recarrega o
     arquivo e substitui a camada (bom para ir vendo os pontos no mapa).

Enquanto o CSV real não existe, o script usa o modelo de exemplo — assim
você já vê como vai ficar e pode testar antes da visita.

Tipos previstos (mesma paleta do projeto + tipos de campo):
  extracao, beneficiamento, calcinacao, rejeito, agua, logistica,
  entrevista, foto, duvida — outros valores aparecem em cinza.
"""

import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsMarkerSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
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


NOME_CAMADA = "Pontos do campo"

# Cores por tipo: as seis da paleta do projeto + tipos específicos de campo
CORES_TIPO = {
    "extracao":       "244,166,192",  # rosa
    "beneficiamento": "180,220,180",  # verde
    "calcinacao":     "170,200,235",  # azul
    "rejeito":        "205,180,230",  # lilás
    "agua":           "170,220,215",  # verde-água
    "logistica":      "245,225,150",  # amarelo
    "entrevista":     "216,160,220",  # roxo-claro
    "foto":           "190,190,210",  # cinza-azulado
    "duvida":         "250,160,140",  # salmão (chama atenção: é pergunta!)
}
COR_PADRAO = "200,200,200"            # cinza p/ tipos fora da lista

print("=" * 60)
print("PASSO 4 — PONTOS DO CAMPO")
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

# 2. Achar o CSV: o real, ou o modelo de exemplo -----------------------------
csv_real = os.path.join(RAIZ, "dados", "reais", "pontos_campo.csv")
csv_modelo = os.path.join(RAIZ, "dados", "exemplo", "pontos_campo_modelo.csv")
if os.path.isfile(csv_real):
    caminho_csv = csv_real
    print(f"✔ Usando os pontos REAIS do campo: {caminho_csv}")
elif os.path.isfile(csv_modelo):
    caminho_csv = csv_modelo
    print("⚠ Ainda não existe dados/reais/pontos_campo.csv —")
    print("  usando o MODELO de exemplo (pontos fictícios) por enquanto.")
else:
    print("✘ ERRO: não achei nem o CSV real nem o modelo de exemplo.")
    print(f"  Esperava: {csv_real}")
    print(f"  ou:       {csv_modelo}")
    raise PareAqui("nenhum CSV de pontos encontrado (veja acima)")

# 3. Carregar o CSV como camada de pontos ------------------------------------
# O provedor 'delimitedtext' lê o CSV direto; lon/lat em WGS 84 (EPSG:4326),
# que é o que o GPS/Google Maps fornece. O QGIS reprojeta sozinho.
uri = (
    "file:///" + caminho_csv.replace("\\", "/")
    + "?type=csv&delimiter=,&xField=lon&yField=lat&crs=EPSG:4326"
)
pontos = QgsVectorLayer(uri, NOME_CAMADA, "delimitedtext")
if not pontos.isValid():
    print("✘ ERRO: o QGIS não conseguiu ler o CSV.")
    print(f"  Caminho: {caminho_csv}")
    print("  Confira: separador vírgula, decimais com ponto, colunas")
    print("  nome,tipo,lon,lat,obs (nessa grafia, sem acento).")
    raise PareAqui("falha ao ler o CSV de pontos (veja acima)")
pontos.setProviderEncoding("UTF-8")
print(f"✔ CSV lido: {pontos.featureCount()} pontos")

# Evita duplicar ao re-rodar
for antiga in projeto.mapLayersByName(NOME_CAMADA):
    projeto.removeMapLayer(antiga.id())

# 4. Estilo: bolinha colorida por tipo ---------------------------------------
indice_tipo = pontos.fields().indexOf("tipo")
tipos_presentes = sorted(
    str(v) for v in pontos.uniqueValues(indice_tipo) if v is not None
)
categorias = []
for tipo in tipos_presentes:
    cor = CORES_TIPO.get(tipo, COR_PADRAO)
    simbolo = QgsMarkerSymbol.createSimple({
        "name": "circle",
        "color": cor,
        "outline_color": "60,60,60",
        "outline_width": "0.4",
        "size": "3.2",
    })
    categorias.append(QgsRendererCategory(tipo, simbolo, tipo))
pontos.setRenderer(QgsCategorizedSymbolRenderer("tipo", categorias))
print(f"✔ Estilo aplicado ({len(categorias)} tipos de ponto)")

# 5. Rótulos com o nome do ponto ---------------------------------------------
rotulo = QgsPalLayerSettings()
rotulo.fieldName = "nome"
formato = QgsTextFormat()
formato.setSize(9)
buffer = formato.buffer()
buffer.setEnabled(True)      # halo branco: legível sobre o satélite
buffer.setSize(1.2)
formato.setBuffer(buffer)
rotulo.setFormat(formato)
pontos.setLabeling(QgsVectorLayerSimpleLabeling(rotulo))
pontos.setLabelsEnabled(True)
print("✔ Rótulos ligados (campo 'nome')")

# 6. Adicionar no topo e salvar ----------------------------------------------
projeto.addMapLayer(pontos, False)
projeto.layerTreeRoot().insertLayer(0, pontos)

if projeto.write(arquivo_projeto):
    print(f"✔ Projeto salvo em: {arquivo_projeto}")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("PASSO 4 CONCLUÍDO ✔")
if caminho_csv == csv_modelo:
    print("Os pontos na tela são o EXEMPLO. Depois do campo:")
    print(" 1. preencha a planilha com os pontos reais;")
    print(" 2. salve como dados/reais/pontos_campo.csv;")
    print(" 3. rode este passo de novo — ele troca sozinho.")
else:
    print("Pontos reais do campo no mapa! Re-rode após qualquer edição")
    print("do CSV para atualizar.")
print("Dica: pontos do tipo 'duvida' (salmão) são as perguntas que o")
print("gabinete deixou para o campo responder.")
print("PRÓXIMO: passo 5 — layout final e exportação (PNG/PDF).")
print("=" * 60)
