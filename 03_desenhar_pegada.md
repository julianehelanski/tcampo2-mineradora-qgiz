# Desenhar a pegada real (território de fato) — passo a passo do clique

Este é o coração manual do mapeamento: desenhar, sobre a imagem de satélite, o
que a mineradora **de fato** ocupa. O passo 3 já cria a camada; aqui está como
desenhar nela.

## Por que desenhar à mão
Delimitar a pegada olhando o satélite é o que treina o olhar geográfico: você
aprende a reconhecer uma cava, uma pilha de estéril, um pátio, um forno. É a
"observação" de Lemonnier aplicada à imagem, antes da observação em campo.

## Passo a passo no QGIS
1. Rode o `passo_3` — ele cria a camada **"Território de fato (desenhar)"**.
2. No painel de camadas, **clique nessa camada** para selecioná-la.
3. Clique no **lápis** (Alternar edição) na barra de ferramentas.
4. Escolha a ferramenta **Adicionar polígono** (ícone de polígono com um `+`).
5. **Clique** ponto a ponto ao redor da feição (a cava, por exemplo). Para
   fechar o polígono, **clique com o botão direito**.
6. Aparece a janela de atributos: preencha **classe** (ex.: `cava`,
   `planta_industrial`, `pilha_esteril`, `patio`) e, se quiser, `descricao`.
7. Repita para cada feição visível.
8. Clique no **lápis** de novo e **salve** as edições.

## Dicas
- Aumente o zoom para desenhar com precisão; a imagem Esri chega a ~19 níveis.
- Se errar um vértice, use `Ctrl+Z` ainda em modo de edição.
- Compare sempre com a poligonal vermelha do **território de direito** (passo 2):
  a pegada real cabe dentro dela? Ultrapassa? Fica muito menor? Essa é a pergunta.

## Exportar como shapefile permanente
A camada criada é temporária (em memória). Para guardar:
- Botão direito na camada → **Exportar → Salvar feições como…** → formato
  **GeoPackage** ou **Shapefile** → salve em `dados/reais/pegada_real.gpkg`.

## Antes x depois
- **Antes do campo:** desenhe a pegada que você *supõe*, só pelo satélite.
- **Depois do campo:** corrija com o que viu (limites que a imagem não mostrava,
  feições novas, áreas que não eram o que pareciam). A diferença entre os dois
  desenhos também é um dado.
