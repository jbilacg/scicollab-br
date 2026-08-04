# Documentação de KPIs e Métricas — Grafo de Colaboração Científica

Este documento explica **cada métrica calculada**, **o que significam as comunidades**,
e **o que tem dentro de cada arquivo gerado** pelo `openalex_colab.py`.

---

## 1. O que é o grafo, afinal

- **Nó (ponto)** = um pesquisador
- **Aresta (linha entre dois nós)** = os dois pesquisadores publicaram pelo menos
  um trabalho juntos
- **Peso da aresta** = quantos trabalhos eles têm em comum (quanto mais
  publicações juntos, mais "forte" a colaboração)

A partir dessa estrutura básica, calculamos as métricas abaixo.

---

## 2. Métricas por pesquisador (arquivo `_pesquisadores.csv`)

### `grau_colaboradores_diretos`
**O que é:** quantidade de pessoas diferentes com quem aquele pesquisador já
publicou (não importa quantas vezes, só *com quantas pessoas diferentes*).

**Como interpretar:** um número alto indica um pesquisador com uma rede de
parcerias ampla. Um número baixo (1 ou 2) indica colaborações mais restritas,
possivelmente dentro de um único grupo fixo.

**Limitação:** não diferencia "muitos colaboradores esporádicos" de "muitos
colaboradores frequentes" — para isso, olhe também o peso das arestas em
`_colaboracoes.csv`.

---

### `centralidade_grau` (*degree centrality*)
**O que é:** a mesma ideia do grau acima, mas **normalizada** — o número de
colaboradores diretos dividido pelo total possível de colaboradores na rede
coletada. Fica sempre entre 0 e 1.

**Como interpretar:** permite comparar pesquisadores de redes de tamanhos
diferentes. Um valor de 0.5 significa que a pessoa colabora diretamente com
metade de todos os outros pesquisadores presentes na rede coletada.

**Limitação:** é sensível ao tamanho da amostra que você coletou
(`--max-authors`). Se você aumentar a amostra, os valores tendem a cair, pois
o "total possível" aumenta.

---

### `centralidade_intermediacao` (*betweenness centrality*)
**O que é:** mede o quanto um pesquisador funciona como **ponte** entre
grupos que, sem ele, estariam desconectados (ou mais distantes) entre si.
Tecnicamente: a proporção de "caminhos mais curtos" entre todos os pares de
pesquisadores da rede que passam por aquele nó.

**Como interpretar:** um valor alto indica alguém estrategicamente
posicionado — muitas vezes é quem conecta duas linhas de pesquisa diferentes,
ou quem tem colaborações internacionais/interinstitucionais que ninguém mais
do grupo tem. Remover essa pessoa da rede tende a fragmentar mais a
colaboração do que remover alguém com betweenness baixo.

**Limitação:** só é calculada para pesquisadores que estão no **maior
componente conectado** da rede (veja seção 4). Pesquisadores isolados ou em
sub-grupos pequenos desconectados do resto ficam com esse campo vazio no CSV.

---

### `comunidade_id`
**O que é:** o identificador do grupo de colaboração ao qual o algoritmo
Louvain atribuiu aquele pesquisador. Veja a seção 3 completa abaixo.

---

### `total_publicacoes_openalex` / `total_citacoes_openalex`
**O que é:** vêm direto do perfil do pesquisador no OpenAlex — é o total de
trabalhos e citações **de toda a carreira dele registrada na base**, não
apenas os que entraram no seu grafo (que pode estar filtrado por
`--topic`/`--year-from`/`--year-to`).

**Cuidado:** por isso, esses dois números **não são exclusivos da sua
amostra** — servem mais para dar contexto de quão prolífico/citado é o
pesquisador de modo geral.

---

## 3. O que são as "Comunidades" — explicação completa

### O algoritmo: Louvain

As comunidades são calculadas pelo **algoritmo de Louvain**, um método de
detecção de comunidades baseado em **modularidade**. Em termos simples: o
algoritmo tenta encontrar a forma de dividir a rede em grupos tal que
**pesquisadores dentro do mesmo grupo colaborem muito mais entre si do que
com pesquisadores de fora do grupo**.

Não é um agrupamento por departamento, currículo ou linha de pesquisa
declarada — é **inteiramente estatístico**, baseado apenas em "quem publicou
com quem" dentro dos dados que você coletou.

### O que uma comunidade *pode* representar, na prática

- Um grupo de pesquisa formal (laboratório, núcleo, LATTES grupo certificado)
- Um projeto financiado específico com um conjunto fixo de colaboradores
- Uma linha de pesquisa informal que se consolidou ao longo do tempo
- Um conjunto de orientandos de um mesmo orientador (padrão muito comum)
- Colaborações internacionais recorrentes com um mesmo grupo estrangeiro

### O que uma comunidade **não** garante

- Não significa necessariamente "mesmo departamento" ou "mesma faculdade" —
  colegas do mesmo departamento que nunca publicaram juntos podem cair em
  comunidades diferentes; pesquisadores de departamentos diferentes que
  colaboram bastante podem cair na mesma comunidade.
- O resultado pode mudar se você rodar de novo com uma amostra de dados
  diferente (`--max-authors` maior, período diferente, etc.), porque o
  algoritmo reagrupa com base no que está presente na rede coletada naquele
  momento.
- Comunidades muito pequenas (2-3 pessoas) geralmente são só um par ou trio
  de coautores que publicaram algumas vezes juntos, não um "grupo" no sentido
  formal.

### Como interpretar de forma responsável

Trate as comunidades como **hipóteses a investigar**, não como fato
institucional. Se uma comunidade te chamar atenção, vale olhar manualmente os
nomes em `_comunidades.csv` e confirmar se ela de fato corresponde a um grupo
de pesquisa conhecido, ou se é uma coincidência de coautoria pontual.

---

## 4. Métricas da rede como um todo (arquivo `_resumo_metricas.csv`)

### `numero_pesquisadores` / `numero_colaboracoes`
Contagem simples de nós e arestas do grafo final (depois de aplicar todos os
filtros escolhidos: instituição, área/topic, período, `--restrict-to-institution`).

### `densidade`
**O que é:** proporção de colaborações que existem em relação a **todas as
colaborações possíveis** se cada pesquisador tivesse publicado com todos os
outros. Vai de 0 (ninguém colabora com ninguém) a 1 (todo mundo já publicou
com todo mundo).

**Como interpretar:** redes de colaboração científica quase sempre têm
densidade baixa (frequentemente abaixo de 0.05 em redes grandes) — isso é
normal e não indica "pouca colaboração", só reflete que ninguém consegue
colaborar com centenas de pessoas ao mesmo tempo. Densidade é mais útil para
**comparar duas redes entre si** (ex: faculdade A vs. faculdade B) do que
para julgar uma rede isoladamente.

### `numero_componentes_conectados`
**O que é:** quantos "pedaços" separados existem na rede — grupos de
pesquisadores que têm colaborações entre si, mas nenhuma conexão (nem
indireta) com o restante da rede.

**Como interpretar:** um número alto de componentes pequenos sugere uma
comunidade acadêmica fragmentada, com vários grupos isolados que não
colaboram entre si, mesmo estando na mesma instituição/área.

### `tamanho_maior_componente` / `percentual_pesquisadores_no_maior_componente`
**O que é:** o tamanho do maior "pedaço conectado" da rede, e que fração do
total de pesquisadores coletados ele representa.

**Como interpretar:** se esse percentual for baixo (ex: 40%), significa que
mais da metade dos pesquisadores da sua amostra estão em ilhas isoladas sem
conexão com o núcleo principal de colaboração.

**Nota técnica:** as métricas de centralidade (grau e intermediação) e a
detecção de comunidades só são calculadas **dentro do maior componente**,
porque essas métricas dependem de caminhos entre os nós — em componentes
desconectados do resto, "distância até os outros" não existe matematicamente.

### `numero_comunidades_detectadas`
Quantos grupos o algoritmo Louvain encontrou dentro do maior componente
conectado. Veja seção 3 para interpretação.

---

## 5. Gráficos gerados (arquivos `_*.png`)

| Arquivo | O que mostra | Serve para |
|---|---|---|
| `_distribuicao_grau.png` | Histograma de quantos colaboradores diretos cada pesquisador tem | Ver se a rede é dominada por poucos "hubs" muito conectados ou se é mais uniforme |
| `_top_centralidade_grau.png` | Ranking dos 15 pesquisadores com mais colaboradores diretos | Identificar quem tem a rede de parcerias mais ampla |
| `_top_intermediacao.png` | Ranking dos 15 pesquisadores com maior betweenness | Identificar as "pontes" estratégicas entre grupos |
| `_tamanho_comunidades.png` | Tamanho de cada comunidade detectada | Visualizar rapidamente se há um grupo dominante ou vários grupos parecidos em tamanho |
| `_publicacoes_por_ano.png` | Evolução do nº de publicações ao longo do tempo | Ver se a produção do grupo está crescendo, estável ou caindo |
| `_produtividade_vs_centralidade.png` | Relação entre total de publicações e centralidade de grau | Ver se quem mais publica é também quem mais colabora, ou se são perfis diferentes (ex: alguém muito produtivo mas que trabalha sozinho) |

---

## 6. Arquivos CSV gerados

| Arquivo | Conteúdo | Uma linha representa |
|---|---|---|
| `_pesquisadores.csv` | Todas as métricas individuais descritas na seção 2 | Um pesquisador |
| `_colaboracoes.csv` | Pares de pesquisadores e quantas publicações têm em comum | Uma colaboração (aresta) |
| `_comunidades.csv` | Lista de membros de cada comunidade detectada | Uma comunidade |
| `_publicacoes_por_ano.csv` | Contagem de publicações únicas por ano | Um ano |
| `_resumo_metricas.csv` | KPIs agregados da rede inteira (seção 4) | Uma métrica |

Todos os CSVs são salvos em UTF-8 com BOM (`utf-8-sig`), formato que o Excel
no Windows reconhece automaticamente e exibe os acentos corretamente, sem
precisar configurar nada na hora de abrir.

---

## 7. Limitações gerais a ter em mente

- **Desambiguação de nomes**: o OpenAlex às vezes separa um mesmo
  pesquisador em dois perfis diferentes (ou junta dois pesquisadores
  homônimos em um só). Isso pode distorcer levemente grau e centralidade.
- **Cobertura**: nem toda publicação brasileira está indexada no OpenAlex,
  especialmente produções mais antigas, capítulos de livro, ou publicações
  em veículos muito locais. A rede reflete o que está indexado, não
  necessariamente 100% da produção real do pesquisador.
- **Amostra limitada por `--max-authors`**: se a instituição tem mais
  pesquisadores do que o limite definido, o script pega primeiro os mais
  produtivos (`sort=works_count desc`). Isso significa que pesquisadores
  menos prolíficos (mas talvez importantes para colaborações específicas)
  podem não entrar na amostra.
- **Comunidades não são departamentos**: repetindo o ponto da seção 3,
  porque é o erro de interpretação mais comum.
