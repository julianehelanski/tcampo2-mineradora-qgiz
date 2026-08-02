# Contexto para o Claude Code

## O que é este repositório
Passo a passo do mapeamento de uma **mineradora de calcário** no QGIS, para a
disciplina Trabalho de Campo Interdisciplinar em Geografia II (Bacharelado,
UEMS). Método de Lemonnier (Cap. 2): delimitar o território no gabinete antes
do campo. Pergunta central: diferença entre território de DIREITO (poligonal
SIGMINE) e território de FATO (pegada real no satélite).

## Cinco passos (scripts PyQGIS, rodam no Console do QGIS)
0. verificar ambiente · 1. projeto + satélite · 2. poligonal (direito) ·
3. camada da pegada (fato) · 4. pontos do campo · 5. layout + exportar.

## Estado e primeira tarefa
Os scripts foram escritos mas **não testados em QGIS real** (o ambiente de
origem não tinha QGIS). A primeira tarefa do Claude Code é: **rodar o passo 0 e
o passo 1 no QGIS da usuária e corrigir erros de caminho/versão da API PyQGIS.**
A API muda entre versões do QGIS (3.28, 3.34, 3.40…); detecte a versão e ajuste.

## Perfil da usuária
- Juliane: doutoranda em ciências sociais, professora substituta de Geografia.
- **Iniciante em QGIS.** Explique cada passo; não pressuponha domínio da API.
- Português do Brasil em todo output.
- Valoriza reprodutibilidade (scripts versionados, como no GitHub da tese).

## Tarefas prováveis
1. Rodar passos 0–1 e corrigir o caminho `RAIZ` e a criação de camadas XYZ.
2. Integrar dados reais: shapefile do SIGMINE (ANM) e recorte de satélite.
3. Ajustar o layout do passo 5 (posição de legenda/título) ao gosto da usuária.
4. `git init` + primeiro commit; publicar no GitHub.

## Convenções
- Comentários e docstrings em português.
- Paleta pastel consistente (extração rosa, beneficiamento verde, calcinação
  azul, rejeito lilás, água verde-água, logística amarelo).
- Não reformatar os scripts sem necessidade; edições mínimas e explicadas.
