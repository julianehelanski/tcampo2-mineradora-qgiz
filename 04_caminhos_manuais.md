# Caminhos manuais: fazendo cada passo pelos menus do QGIS

Este guia ensina a montar o projeto da mineradora **sem Python**: cada seção
refaz um dos scripts (`passo_0` a `passo_5`) usando só menus e botões.

**Para que serve?** Duas coisas ao mesmo tempo:

1. **Aprender QGIS de verdade** — os menus ensinam os conceitos (camada,
   SRC, simbologia, filtro) que o script executa em silêncio;
2. **Dar aula** — cada seção funciona como um roteiro de exercício. Uma
   sugestão didática ao final de cada uma aparece marcada com 🎓.

A relação com os scripts é de espelho: quem fez o caminho manual entende o
que o script automatiza; quem rodou o script pode conferir aqui o que
aconteceu nos bastidores. Reprodutibilidade (script) e compreensão (manual)
se completam — vale discutir isso com a turma.

> Escrito para QGIS 4.x em português; no 3.x os nomes mudam pouco.
> Antes de começar, deixe visíveis os painéis **Camadas** e **Navegador**:
> menu `Exibir → Painéis`.

---

## Caminho 1 — Projeto novo + satélite (espelho do `passo_1`)

### 1a. Criar o projeto e definir o SRC

1. `Projeto → Novo`.
2. `Projeto → Propriedades… → SRC`.
3. No campo de busca, digite **31981** e selecione
   **SIRGAS 2000 / UTM zone 21S (EPSG:31981)** → OK.
   - *Por quê:* é um SRC **em metros** que cobre o MS — essencial para medir
     áreas e distâncias depois. Coordenadas de GPS (graus) são reprojetadas
     pelo QGIS automaticamente.
4. `Projeto → Salvar como…` → dentro da pasta do repositório, em
   `projeto\`, com o nome que quiser (o dos scripts é
   `mineradora_calcario.qgz`).

### 1b. Adicionar o satélite (camada XYZ)

1. No painel **Navegador**, localize **XYZ Tiles** e clique com o botão
   direito → **Nova conexão…**
2. Nome: `Esri World Imagery`. URL (uma linha só):
   ```
   https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}
   ```
   Zoom máx.: 19 → OK.
3. Dê **dois cliques** na conexão criada: a camada entra no mapa.
4. (Opcional) Repita para o Google: nome `Google Satellite`, URL:
   ```
   https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}
   ```
5. Navegue até a região de Bodoquena–Bonito (MS) com zoom e arrasto.

🎓 *Sugestão: peça aos alunos que encontrem "de olho" uma mineradora no
satélite antes de qualquer outra camada — o que parece mina? Por quê?*

---

## Caminho 2 — SIGMINE: o território de direito (espelho do `passo_2`)

### 2a. Carregar o shapefile

1. Abra a pasta do repositório no Explorador de Arquivos e localize a
   pasta `dados\reais\sigmine_MS\` (shapefile completo do SIGMINE, já
   descompactado).
2. **Arraste o arquivo `MS.shp`** para dentro do mapa do QGIS. Os outros
   arquivos da pasta (`.dbf`, `.prj`, `.shx`…) são partes do mesmo
   shapefile — precisam ficar juntos, mas só o `.shp` é arrastado.

### 2b. Filtrar só o calcário

1. Botão direito na camada → **Filtrar…** (abre o Construtor de consulta).
2. Cole a expressão:
   ```sql
   "SUBS" LIKE 'CALC%' AND "SUBS" <> 'CALCITA'
   ```
3. OK. Dos ~3.785 processos de MS restam ~170, os de calcário.
   - *Por quê `LIKE 'CALC%'`:* pega CALCÁRIO, CALCÁRIO DOLOMÍTICO e
     CALCÁRIO CALCÍTICO sem depender de acento; excluímos CALCITA
     (mineral, outro contexto).

### 2c. Colorir por fase do processo

1. Botão direito na camada → `Propriedades → Simbologia`.
2. No topo, troque **Símbolo simples** por **Categorizado**.
3. Em **Valor**, escolha o campo `FASE` → botão **Classificar**.
4. Dê dois cliques na cor de cada fase para ajustar. Sugestão do projeto:
   tons pastel para as fases "de papel" e **rosa forte para CONCESSÃO DE
   LAVRA** (é onde a extração é autorizada de fato).
5. Para o satélite aparecer por baixo: em cada símbolo, reduza a
   **opacidade** (~50%) — ou use a opacidade da camada, aba *Renderização*.

### 2d. Explorar

- Ferramenta **Identificar feições** (`Ctrl+Shift+I`) → clique num
  polígono → veja `NOME` (titular), `PROCESSO`, `AREA_HA`.
- Botão direito na camada → **Abrir tabela de atributos** para ver todos.

🎓 *Sugestão: cada dupla escolhe uma concessão de lavra, anota titular e
área, e responde: a pegada visível no satélite ocupa o polígono todo?*

---

## Caminho 3 — Desenhar a pegada de fato (espelho do `passo_3`)

### 3a. Criar a camada de desenho (GeoPackage)

1. `Camada → Criar camada → Nova camada GeoPackage…`
2. **Banco de dados:** botão `…` → salve como `dados\pegada_fato.gpkg`.
3. **Nome da tabela:** `pegada_fato`. **Tipo de geometria:** Polígono.
   **SRC:** o mesmo do projeto (EPSG:31981).
4. Em **Novo campo**, crie três campos de texto: `tipo`, `nome`, `obs`
   (adicione um a um) → OK.

### 3b. Menu de opções para o campo `tipo`

1. Botão direito na camada → `Propriedades → Formulário de atributos`.
2. Clique no campo `tipo`. Em **Tipo de ferramenta**, troque *Edição de
   texto* por **Mapa de valor**.
3. Preencha a tabelinha (Valor → Descrição):
   | Valor | Descrição |
   |---|---|
   | extracao | Extração (cava) |
   | beneficiamento | Beneficiamento (britagem) |
   | calcinacao | Calcinação (fornos) |
   | rejeito | Rejeito / estéril |
   | agua | Água (lagoa, decantação) |
   | logistica | Logística (pátio, estrada) |
   | outro | Outro (anote em obs) |
4. OK. Agora, ao desenhar, o `tipo` vira um menu — sem erro de digitação.

### 3c. Cores por tipo (paleta do projeto)

`Propriedades → Simbologia → Categorizado`, valor `tipo`, **Classificar**,
e ajuste as cores (use os valores RGB para fidelidade à paleta):

| tipo | cor pastel | RGB |
|---|---|---|
| extracao | rosa | 244,166,192 |
| beneficiamento | verde | 180,220,180 |
| calcinacao | azul | 170,200,235 |
| rejeito | lilás | 205,180,230 |
| agua | verde-água | 170,220,215 |
| logistica | amarelo | 245,225,150 |
| outro | cinza | 210,210,210 |

Deixe os símbolos semitransparentes (opacidade ~60%).

### 3d. Desenhar

1. Selecione a camada no painel; clique no **lápis amarelo** (Alternar
   edição).
2. **Adicionar feição de polígono** (ícone verde) → clique ponto a ponto
   contornando a cava → **botão direito** fecha → escolha o tipo → OK.
3. Repita para pilhas, pátio, fornos, lagoa…
4. Lápis de novo → **Salvar** as edições.

🎓 *Sugestão: a turma desenha a pegada ANTES do campo (hipótese) e a
corrige DEPOIS. Guardem as duas versões: a diferença é o dado.*

---

## Caminho 3b — Territórios do entorno (espelho do `passo_3b`)

Mesma receita do Caminho 3, mudando:

- Arquivo: `dados\entorno_territorios.gpkg`, tabela `entorno_territorios`;
- Valores do mapa de valor: `pastagem`, `agricultura`, `vegetacao`, `agua`,
  `urbano`, `turismo`, `comunidade`, `outro`;
- Na simbologia, use **linha tracejada** no contorno (em cada símbolo:
  *Linha simples → Estilo de traço → Linha tracejada*) — é o código visual
  que distingue entorno (tracejado) de mineradora (contínuo);
- Posicione a camada **abaixo** da pegada no painel (arraste).

🎓 *Sugestão: discutir o que é "entorno" — até onde vai? quem define? O
recorte espacial já é uma decisão de pesquisa.*

---

## Caminho 3c — MapBiomas: o uso do solo automático (espelho do `passo_3c`)

1. Arraste `dados\reais\mapbiomas_bodoquena_2023.tif` para o mapa.
2. Botão direito na camada → `Propriedades → Simbologia`.
3. Troque **Banda cinza simples** por **Paleta/Valores únicos**.
4. Clique em **Classificar**: o QGIS lista os códigos presentes (3, 4, 12,
   15, 30, 33…). Cada código é uma classe do MapBiomas.
5. Dê dois cliques em cada linha para pôr **cor e nome** — tabela mínima:

   | código | classe | cor (hex) |
   |---|---|---|
   | 3 | Formação florestal | #1f8d49 |
   | 4 | Formação savânica (Cerrado) | #7dc975 |
   | 11 | Campo alagado / pantanoso | #519799 |
   | 12 | Formação campestre | #d6bc74 |
   | 15 | Pastagem | #edde8e |
   | 21 | Mosaico de usos | #ffefc3 |
   | 24 | Área urbanizada | #d4271e |
   | 30 | **Mineração** | #9c0027 |
   | 33 | Rio, lago | #2532e4 |
   | 39 | Soja | #f5b3c8 |

   (a legenda completa está no site do MapBiomas, busque "MapBiomas
   legenda códigos"; o script `passo_3c` traz 21 classes prontas)
6. Aba **Renderização** (ou Transparência): opacidade ~70%.
7. No painel, arraste a camada para **cima do satélite e abaixo** do
   SIGMINE e das camadas de desenho.

🎓 *Sugestão: este é o momento "quem mapeia o mapa?" — comparar a classe
Mineração (algoritmo), a poligonal SIGMINE (Estado) e o desenho da turma
(olhar treinado). Onde discordam? Quem está "certo"?*

---

## Caminho 4 — Pontos do campo (espelho do `passo_4`)

1. `Camada → Adicionar camada → Adicionar camada de texto delimitado…`
2. **Nome do arquivo:** `dados\reais\pontos_campo.csv` (ou o modelo em
   `dados\exemplo\pontos_campo_modelo.csv` para testar).
3. Confira: formato **CSV**; **Campo X** = `lon`; **Campo Y** = `lat`;
   **SRC da geometria** = EPSG:4326 (WGS 84 — o padrão do GPS).
4. **Adicionar** → os pontos entram no mapa (o QGIS reprojeta sozinho).
5. Cores por tipo: `Propriedades → Simbologia → Categorizado` no campo
   `tipo` (mesma lógica de sempre).
6. Rótulos: `Propriedades → Rótulos` → **Rótulos simples** → valor `nome`;
   em *Buffer*, ative o **halo branco** (legibilidade sobre o satélite).

> Formato da planilha: colunas `nome,tipo,lon,lat,obs`, decimais com
> **ponto**. No Google Maps, toque longo mostra `lat, lon` — **inverta**
> ao preencher! A camada CSV é só leitura; para editar pontos, edite a
> planilha e recarregue (ou botão direito → *Recarregar*).

🎓 *Sugestão: antes do campo, cada aluno cria 2 pontos do tipo `duvida`
("o que é isso no satélite?"). No campo, a missão é respondê-los.*

---

## Caminho 5 — Layout de impressão (espelho do `passo_5`)

1. Enquadre o mapa na tela como quer no papel.
2. `Projeto → Novo layout de impressão…` → dê um nome.
3. Na janela do layout, botão direito na página → `Propriedades da
   página`: A4, Paisagem.
4. **Adicionar item → Adicionar mapa** → desenhe o retângulo do mapa.
   - Para reenquadrar: `Propriedades do item → Definir extensão do mapa
     para a extensão da tela`, ou mova com a ferramenta *Mover conteúdo
     do item*.
5. **Adicionar item → Adicionar rótulo** → título (fonte ~17 pt, negrito);
   outro rótulo menor para o subtítulo; outro (7 pt) para os créditos:
   > Fontes: ANM/SIGMINE; MapBiomas col. 9; Esri World Imagery.
   > Elaboração: [turma/ano]. SRC: SIRGAS 2000 / UTM 21S.
6. **Adicionar item → Adicionar legenda**. Nas propriedades da legenda,
   **desmarque "Atualização automática"** e remova (botão −) as camadas
   que não devem aparecer (satélites, MapBiomas se quiser legenda curta).
7. **Adicionar item → Adicionar barra de escala** (ligada ao mapa).
8. **Adicionar item → Adicionar seta de norte** (ou um rótulo "N ▲").
9. Exportar: `Layout → Exportar como imagem…` (PNG, 200 dpi) e
   `Exportar como PDF…` → salve em `saidas\`.

🎓 *Sugestão: avaliar o mapa dos alunos com a pergunta clássica — alguém
que nunca viu a área entende o mapa sem explicação oral?*

---

## Quadro-síntese para a aula

| Conceito | Onde aparece | Menu-chave |
|---|---|---|
| SRC / projeção | Caminho 1 | Projeto → Propriedades → SRC |
| Camada raster remota (XYZ) | Caminho 1 | Navegador → XYZ Tiles |
| Camada vetorial + filtro SQL | Caminho 2 | Botão direito → Filtrar |
| Simbologia categorizada | Caminhos 2–4 | Propriedades → Simbologia |
| Edição vetorial (digitalizar) | Caminhos 3/3b | Lápis amarelo |
| Formulário (mapa de valor) | Caminhos 3/3b | Propriedades → Formulário |
| Raster classificado (paleta) | Caminho 3c | Simbologia → Paleta/Valores únicos |
| Importar CSV com coordenadas | Caminho 4 | Camada → Texto delimitado |
| Rótulos | Caminho 4 | Propriedades → Rótulos |
| Layout e exportação | Caminho 5 | Projeto → Novo layout |

Fechamento possível da aula: os scripts `passo_0` a `passo_5` fazem
exatamente estes caminhos, em segundos e sempre iguais. O manual ensina o
**conceito**; o script garante a **reprodutibilidade** — ciência precisa
dos dois.
