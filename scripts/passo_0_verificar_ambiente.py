# -*- coding: utf-8 -*-
"""
PASSO 0 — Verificar o ambiente
==============================
Roda no Console Python do QGIS (Complementos → Console Python → Mostrar editor).

O que este script faz:
  1. Mostra a versão do QGIS e avisa se for muito antiga.
  2. Confere se o caminho RAIZ (a pasta deste projeto) existe.
  3. Cria as subpastas que os próximos passos usam (dados/, projeto/, saidas/).
  4. Lista os dados que já estão na pasta.

Se tudo terminar com "AMBIENTE OK", pode ir para o passo 1.
"""

import os

# ─────────────────────────────────────────────────────────────────────────────
# AJUSTE OBRIGATÓRIO: caminho da pasta do projeto no SEU computador.
# Exemplos:
#   Windows:  RAIZ = r"C:\Users\SEU_USUARIO\Documents\qgis-mineradora"
#   Linux/Mac: RAIZ = os.path.expanduser("~/qgis-mineradora")
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = os.path.expanduser("~/qgis-mineradora")

# Subpastas que o projeto usa (criadas aqui se não existirem)
SUBPASTAS = [
    "dados/exemplo",   # dados sintéticos que acompanham o repositório
    "dados/reais",     # dados baixados (SIGMINE, MapBiomas, IBGE...)
    "projeto",         # arquivo .qgz do QGIS
    "saidas",          # mapas exportados (PNG/PDF) pelo passo 5
]

print("=" * 60)
print("PASSO 0 — VERIFICAÇÃO DO AMBIENTE")
print("=" * 60)

# 1. Versão do QGIS ----------------------------------------------------------
try:
    from qgis.core import Qgis
    versao = Qgis.QGIS_VERSION            # ex.: "3.34.12-Prizren"
    versao_int = Qgis.QGIS_VERSION_INT    # ex.: 33412
    print(f"✔ QGIS detectado: versão {versao}")
    if versao_int < 32800:
        print("  ⚠ Sua versão é anterior à 3.28. Os scripts foram pensados")
        print("    para 3.28+. Considere atualizar (qgis.org, versão LTR).")
except ImportError:
    print("✘ ERRO: não encontrei a API do QGIS (PyQGIS).")
    print("  Este script deve rodar DENTRO do QGIS, no Console Python,")
    print("  e não no terminal comum. Veja 01_como_rodar.md.")
    raise SystemExit

# 2. Caminho RAIZ ------------------------------------------------------------
if os.path.isdir(RAIZ):
    print(f"✔ Pasta do projeto encontrada: {RAIZ}")
else:
    print(f"✘ ERRO: a pasta não existe: {RAIZ}")
    print("  Edite a linha RAIZ = ... no topo deste script com o caminho")
    print("  onde você salvou a pasta do projeto, e rode de novo.")
    raise SystemExit

# 3. Subpastas ---------------------------------------------------------------
for sub in SUBPASTAS:
    caminho = os.path.join(RAIZ, *sub.split("/"))
    if os.path.isdir(caminho):
        print(f"✔ Subpasta ok: {sub}")
    else:
        os.makedirs(caminho)
        print(f"＋ Subpasta criada: {sub}")

# 4. Listar dados ------------------------------------------------------------
print("-" * 60)
print("Conteúdo de dados/:")
pasta_dados = os.path.join(RAIZ, "dados")
achou_algo = False
for raiz_atual, _, arquivos in os.walk(pasta_dados):
    for arq in sorted(arquivos):
        rel = os.path.relpath(os.path.join(raiz_atual, arq), RAIZ)
        print(f"   • {rel}")
        achou_algo = True
if not achou_algo:
    print("   (vazio por enquanto — sem problema: o passo 1 usa satélite")
    print("    online e não precisa de arquivos locais)")

# Fim ------------------------------------------------------------------------
print("=" * 60)
print("AMBIENTE OK ✔")
print("PRÓXIMO: abra e rode scripts/passo_1_projeto_satelite.py")
print("         (lembre de usar o MESMO caminho RAIZ lá)")
print("=" * 60)
