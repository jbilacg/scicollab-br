# SciCollab-BR

**Mapas de rede de colaboração científica por universidade**, construídos a
partir de dados públicos do [OpenAlex](https://openalex.org) — sem captcha,
sem chave obrigatória, sem paywall.

Dá pra pesquisadores, bibliotecários e gestores acadêmicos visualizarem
rapidamente **quem colabora com quem** dentro (ou fora) de uma universidade:
o grafo de coautoria, métricas de rede (centralidade, intermediação,
comunidades) e gráficos descritivos, tudo gerado automaticamente a partir do
nome da instituição.

📥 **[Baixe o executável para Windows na página de Releases](../../releases/latest)**
— não precisa instalar Python.

---

## Por que esse projeto existe

A ideia original era buscar essas colaborações direto na **Plataforma
Lattes** (CNPq), como já fazem dois projetos ótimos que nos inspiraram:

- [**lucylattes**](https://github.com/rafatieppo/lucylattes)
- [**scriptLattes**](https://scriptlattes.sourceforge.net/)

Mas o Lattes hoje exige **captcha** para consultar currículos em lote, o que
inviabiliza qualquer coleta automatizada em escala — não dá pra construir um
grafo de centenas de pesquisadores clicando captcha um por um.

Por isso migramos a coleta para a **API pública do OpenAlex**: cobertura
internacional de publicações (incluindo grande parte da produção científica
brasileira), sem captcha, sem necessidade de chave de API, e com dados
estruturados (afiliação, coautoria, ano, área de conhecimento) prontos para
montar o grafo direto.

**Trade-off importante**: o OpenAlex não é o Lattes — nem toda publicação
brasileira está indexada, há viés para produção em inglês, e a
desambiguação de nomes homônimos (comum em nomes brasileiros) às vezes
falha. Para o propósito de mapear *redes* de colaboração (não currículos
individuais completos), o ganho de conseguir coletar em escala, sem
bloqueio, compensou essa diferença de cobertura.

---

## O que ele gera

A partir do nome de uma universidade (+ filtros opcionais de área e
período):

- **Grafo interativo** em HTML (zoom, arraste, física de nós) via `pyvis`
- **Rede de colaboração entre universidades/instituições** (também em HTML
  interativo), montada a partir das afiliações dos coautores
- **Arquivos `.gexf`** para abrir no [Gephi](https://gephi.org)
- **7 gráficos** descritivos em PNG (distribuição de grau, ranking de
  centralidade/intermediação, publicações por ano, tamanho de comunidades,
  principais instituições parceiras…)
- **7 planilhas CSV** com os dados brutos (pesquisadores, coautorias,
  comunidades, métricas resumo, instituições e colaborações entre elas)

Métricas calculadas: grau, centralidade de grau/intermediação, detecção de
comunidades (algoritmo Louvain), densidade da rede, entre outras — ver
[`docs/KPI_DOCUMENTACAO.md`](docs/KPI_DOCUMENTACAO.md) para o que cada uma
significa.

---

## Como usar

### Opção 1 — Executável (Windows, recomendado para não-técnicos)

1. Baixe `Grafo.de.Colaboracao.exe` na [página de Releases](../../releases/latest)
2. Dê dois cliques para abrir
3. Preencha universidade (+ filtros opcionais) na interface gráfica
4. Clique em **▶ Executar Análise**

Veja [`docs/COMECE_AQUI.md`](docs/COMECE_AQUI.md) para o passo a passo
ilustrado.

### Opção 2 — Linha de comando (Python)

```bash
pip install -r requirements.txt
python openalex_colab.py --institution "Universidade de Sao Paulo"
```

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `--institution` | Nome da universidade | (obrigatório) |
| `--max-authors` | Nº máximo de pesquisadores a coletar | 100 |
| `--max-works-per-author` | Nº máximo de publicações por pesquisador | 50 |
| `--restrict-to-institution` | Só mantém arestas entre pesquisadores da própria instituição | desativado |
| `--max-institutions` | Nº máximo de instituições na rede entre universidades | 100 |
| `--max-authors-per-work` | Ignora nas redes publicações com mais autores que isso (autoria em massa); 0 = sem limite | 50 |
| `--output` | Prefixo dos arquivos de saída | `grafo_colaboracao` |

Exemplo — rede interna da UFRJ, mais enxuta:

```bash
python openalex_colab.py \
  --institution "Universidade Federal do Rio de Janeiro" \
  --max-authors 150 \
  --restrict-to-institution \
  --output ufrj_rede_interna
```

Edite a constante `POLITE_EMAIL` no topo de `openalex_colab.py` (ou informe
seu e-mail direto na GUI) — o OpenAlex usa isso para priorizar suas
requisições na "polite pool" e evitar rate limiting.

### Opção 3 — Rodar a partir do código-fonte com interface gráfica

```bash
pip install -r requirements.txt
python gui_openalex.py
```

---

## Documentação

| Arquivo | Conteúdo |
|---|---|
| [`docs/COMECE_AQUI.md`](docs/COMECE_AQUI.md) | Guia rápido para usuários não-técnicos |
| [`docs/README_INSTALACAO.md`](docs/README_INSTALACAO.md) | Instalação manual via terminal |
| [`docs/KPI_DOCUMENTACAO.md`](docs/KPI_DOCUMENTACAO.md) | Explicação de cada métrica/KPI gerada |
| [`docs/BUILD_EXECUTAVEL.md`](docs/BUILD_EXECUTAVEL.md) | Como gerar o `.exe` você mesmo (PyInstaller) |
| [`docs/PROJETO_RESUMO.md`](docs/PROJETO_RESUMO.md) | Visão geral técnica do projeto e estrutura de código |

## Limitações conhecidas

- Cobertura do OpenAlex não é completa para produção brasileira (viés para
  publicações em inglês)
- Desambiguação de nomes homônimos pode falhar
- Comunidades são estatísticas (algoritmo Louvain), não correspondem
  necessariamente a departamentos/faculdades reais
- Sem modo offline — cada execução consulta a API novamente
- Instituições grandes (USP, UFRJ) têm milhares de pesquisadores; o
  parâmetro `--max-authors` limita a coleta inicial aos mais produtivos

## Próximos passos possíveis

- Cruzar com ORCID para desambiguar nomes homônimos
- Cachear dados coletados para reprocessar sem recoletar (SQLite)
- Comparação lado a lado de duas universidades
- Relatório automático em PDF

## Contribuindo

Pull requests são bem-vindos — otimização de coleta, novos
gráficos/análises, suporte a outras bases, melhorias de UI/UX.

## Licença

[MIT](LICENSE)
