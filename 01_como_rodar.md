# Como rodar os scripts no QGIS

## Onde os scripts rodam
Estes scripts usam a API interna do QGIS (PyQGIS). Eles **não** rodam no
terminal comum nem no Python do sistema — rodam no **Console Python do QGIS**,
que já tem tudo carregado.

## Passo a passo
1. Abra o QGIS (versão LTR recomendada — qgis.org).
2. `Complementos → Console Python` (ou `Ctrl+Alt+P`).
3. Clique em **Mostrar editor** (ícone de bloco de notas no console).
4. **Abrir script** → escolha o arquivo do passo.
5. **Executar** (triângulo verde) ou `Ctrl+Shift+E`.

## Ajuste obrigatório antes de começar
Abra `scripts/passo_0_verificar_ambiente.py` e edite a linha:

```python
RAIZ = os.path.expanduser("~/qgis-mineradora")
```

- Se você descompactou a pasta em `Documentos`, por exemplo, ponha o caminho
  completo. No Windows use `r"C:\Users\SEU_USUARIO\Documents\qgis-mineradora"`.
- Rode o passo 0. Se ele listar os dados de exemplo, está tudo certo.

Os passos 1 a 5 usam o mesmo caminho — mantenha igual em todos (ou, se preferir,
rode o passo 0 primeiro e copie o valor que funcionou).

## Ordem
Rode 0 → 1 → 2 → 3 → 4 → 5. Cada script diz, no fim, qual é o próximo.

## Se der erro
Erros de caminho e de versão do QGIS são comuns e normais. Duas saídas:
- Leia a mensagem: quase sempre é o caminho `RAIZ` errado.
- Abra a pasta no **Claude Code** e peça para ele rodar e corrigir — ele vê a
  sua instalação real e itera até funcionar.

## Lições do primeiro teste real (QGIS 4.2.0, agosto/2026)

Os passos 0–2 foram testados com sucesso no QGIS 4.2.0 "Belém do Pará".
O que aprendemos no caminho:

- **Caminho no Windows:** escreva com `r` antes das aspas e sem barra final:
  `RAIZ = r"C:\Users\SEU_USUARIO\Downloads\tcampo2-mineradora-qgiz-main"`.
  O caminho certo é o da pasta que contém `scripts/` e `dados/` — copie da
  barra de endereço do Explorador de Arquivos para não errar.
- **Cada novo download do ZIP zera o `RAIZ`:** os arquivos baixados voltam
  com o valor de fábrica; re-edite a linha nos scripts que for usar.
- **Baixe o ZIP do branch certo:** no GitHub, selecione o branch com os
  scripts (botão de branch, acima da lista de arquivos) **antes** de
  `Code → Download ZIP` — o ZIP do `main` pode não ter a pasta `scripts/`.
- **Nunca use `sys.exit()`/`SystemExit` em script do console do QGIS:**
  em vez de parar só o script, **fecha o QGIS inteiro**. Por isso os
  scripts usam uma exceção própria (`PareAqui`), que interrompe mostrando
  a mensagem de erro em vermelho e mantém o programa aberto.
- **A partir do passo 3, o `RAIZ` se detecta sozinho** quando o projeto
  `mineradora_calcario.qgz` já está aberto no QGIS.
