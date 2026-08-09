# Onde baixar dados reais para o mapa da mineradora

Os dados de exemplo em `dados/exemplo/` são sintéticos, só para o repositório
rodar. Para o mapa real da mineradora que vocês vão visitar, use as fontes
públicas brasileiras abaixo. Baixe para `dados/reais/` e ajuste o caminho nos
scripts (ou peça ao Claude Code que ajuste).

> **Verifique cada fonte antes de usar**: URLs de portais governamentais mudam.
> Os nomes dos órgãos e sistemas abaixo estavam corretos em 2026, mas confirme
> o endereço atual buscando pelo nome do sistema.

---

## 1. Poligonais dos processos minerários — SIGMINE (ANM)

O **SIGMINE**, da Agência Nacional de Mineração, publica as áreas de todos os
processos minerários do país (requerimento, autorização de pesquisa, concessão
de lavra). É a camada mais importante: mostra o polígono legal da mineradora.

- Busque por: **"SIGMINE ANM download shapefile"**
- Formato: shapefile (`.shp`) por unidade da federação (baixe o de MS).
- No script: é uma camada de polígonos; carregue com `geopandas.read_file()`
  ou, no QGIS, arraste o `.shp` para o mapa.

## 2. Uso e cobertura do solo — MapBiomas

O **MapBiomas** tem uma coleção temática dedicada à **mineração**, além do uso
geral do solo. Serve para mostrar a pegada da mineração no território ao longo
do tempo.

- Busque por: **"MapBiomas mineração download"** e **"MapBiomas coleção uso do solo"**
- Formatos: raster (`.tif`) para download, ou acesso via Google Earth Engine.

## 3. Base cartográfica — IBGE

Limites municipais, hidrografia, malha viária, sedes urbanas. Contexto do mapa.

- Busque por: **"IBGE malha municipal download"** e **"IBGE bcim"** (Base
  Cartográfica Contínua).

## 4. Imagens de satélite — Sentinel-2 / Landsat

Para ver a cava, as pilhas e a barragem diretamente na imagem.

- **Copernicus Browser** (Sentinel-2, gratuito, 10 m de resolução).
- **USGS Earth Explorer** (Landsat).
- Busque por: **"Copernicus Browser Sentinel-2"**.

## 5. Barragens de mineração — SIGBM (ANM)

O **Sistema Integrado de Gestão de Barragens de Mineração** lista as barragens
de rejeito, com nível de risco e dano potencial. Relevante para a discussão de
risco no campo.

- Busque por: **"ANM SIGBM barragens de mineração"**.

## 6. Unidades de conservação e terras indígenas — CNUC/MMA e FUNAI

Para discutir o entorno da mineração (o Parque Nacional da Serra da
Bodoquena fica na mesma região calcária), baixe as poligonais oficiais:

- **Unidades de conservação**: busque por **"CNUC MMA download shapefile
  unidades de conservação"**. Salve o conteúdo descompactado em
  `dados/reais/unidades_conservacao/`.
- **Terras indígenas**: busque por **"FUNAI geoserver download shapefile
  terras indígenas"**. Salve em `dados/reais/terras_indigenas/`.
- O script `passo_1b_referencias.py` detecta essas duas pastas e carrega
  os shapefiles automaticamente, já estilizados. Sem elas, o
  OpenStreetMap (também adicionado pelo `passo_1b`) já mostra parques e
  reservas em verde, o que resolve para visualização.

---

## Como levar isso para os scripts

- **Pontos que vocês mesmos coletarem no campo** (com GPS ou celular): anotem
  `nome, tipo, lon, lat` numa planilha no mesmo formato de
  `dados/exemplo/pontos_tecnicos.csv`, salvem em `dados/reais/` e apontem o
  script para lá.
- **Camadas baixadas** (SIGMINE, MapBiomas): são shapefiles/rasters; o script
  `03b` pode ser estendido para carregá-las como fundo. Peça ao Claude Code:
  *"adicione a poligonal do SIGMINE como camada de fundo no script 03b"*.

---

## Nota sobre a coleta em campo (ética e segurança)

Mineradoras têm regras de acesso e segurança. Combinem antes com a empresa o que
pode ser fotografado e georreferenciado. O registro em vídeo/foto de sequências
(que Lemonnier recomenda) pode exigir autorização. Isso, aliás, é material de
discussão em aula: as **escolhas sobre o que se pode ver** já são um dado sobre
as representações sociais da tecnologia.
