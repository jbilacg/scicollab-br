"""
openalex_colab.py

Constrói um grafo de colaboração científica a partir da API do OpenAlex,
filtrando por universidade (instituição).

Fluxo:
  1. Busca o ID da instituição pelo nome (ex: "Universidade de Sao Paulo")
  2. Busca os pesquisadores (authors) afiliados a essa instituição
  3. Para cada pesquisador, busca suas publicações (works) e extrai coautorias
  4. Monta um grafo (networkx) onde:
       - nós = pesquisadores (autores)
       - arestas = coautoria em pelo menos 1 publicação (peso = nº de publicações em comum)
  5. Calcula métricas descritivas e detecta comunidades
  6. Exporta grafo para .gexf (abre no Gephi) e gera visualização HTML interativa

Uso:
    python openalex_colab.py --institution "Universidade de Sao Paulo" --max-authors 200 --max-works-per-author 50

Requisitos:
    pip install requests networkx python-louvain pyvis
"""

import argparse
import csv
import time
import sys
from collections import defaultdict

import requests
import networkx as nx

try:
    import community as community_louvain  # python-louvain
except ImportError:
    community_louvain = None

BASE_URL = "https://api.openalex.org"

# Coloque seu e-mail aqui: a OpenAlex pede isso na "polite pool" para dar
# prioridade e limites mais altos de requisição. Não é obrigatório, mas ajuda.
POLITE_EMAIL = "seuemail@exemplo.com"


def _get(url, params=None, retries=5, sleep=2.0):
    """GET com retry e backoff exponencial. Usa polite pool do OpenAlex (mailto)."""
    params = params or {}
    params["mailto"] = POLITE_EMAIL
    for attempt in range(retries):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = sleep * (2 ** attempt)  # 2s, 4s, 8s, 16s, 32s
            print(f"  [429] Limite de requisições. Aguardando {wait:.0f}s e tentando novamente...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
    resp.raise_for_status()


def _choose_from_results(results, format_line_fn, allow_skip=False, allow_multiple=False):
    """
    Mostra os resultados numerados e pergunta ao usuário qual(is) escolher.
    format_line_fn(i, r) -> string a exibir para o resultado r no índice i.
    Se allow_skip, aceita Enter vazio para pular a escolha manual e usar o [0].
    Se allow_multiple, aceita vários números separados por vírgula (ex: "0,2,3")
    ou a palavra "todos" para selecionar tudo, e retorna uma LISTA de índices.
    Caso contrário, retorna um único índice (int).
    """
    for i, r in enumerate(results):
        print(format_line_fn(i, r))

    if allow_multiple:
        prompt = f"\nEscolha um ou mais números separados por vírgula (ex: 0,2), 'todos'"
        prompt += " para selecionar tudo" if len(results) > 1 else ""
        prompt += ", ou Enter = usar [0]" if allow_skip else ""
        prompt += ": "
    else:
        prompt = f"\nEscolha o número [0-{len(results)-1}]"
        prompt += " (Enter = usar o [0])" if allow_skip else ""
        prompt += ": "

    while True:
        choice = input(prompt).strip()

        if allow_multiple:
            if allow_skip and choice == "":
                return [0]
            if choice.lower() in ("todos", "all"):
                return list(range(len(results)))
            parts = [p.strip() for p in choice.split(",") if p.strip()]
            if parts and all(p.isdigit() and 0 <= int(p) < len(results) for p in parts):
                return sorted(set(int(p) for p in parts))
            print(f"  Entrada inválida. Use números separados por vírgula entre 0 e {len(results)-1}, "
                  f"ou 'todos'.")
            continue

        if allow_skip and choice == "":
            return 0
        if choice.isdigit() and 0 <= int(choice) < len(results):
            return int(choice)
        print(f"  Opção inválida. Digite um número entre 0 e {len(results)-1}.")


def find_institution(name, interactive=False):
    """
    Busca a instituição pelo nome e retorna (id, display_name).
    Se interactive=True, pergunta ao usuário qual dos resultados usar;
    caso contrário, usa automaticamente o primeiro (mais relevante).
    """
    data = _get(f"{BASE_URL}/institutions", params={"search": name, "per_page": 5})
    results = data.get("results", [])
    if not results:
        raise ValueError(f"Nenhuma instituição encontrada para '{name}'")

    fmt = lambda i, r: (
        f"  [{i}] {r['display_name']} ({r.get('country_code','?')}) "
        f"- works: {r.get('works_count')} - id: {r['id']}"
    )

    print("\nInstituições encontradas:")
    if interactive and len(results) > 1:
        idx = _choose_from_results(results, fmt, allow_skip=True)
    else:
        for i, r in enumerate(results):
            print(fmt(i, r))
        idx = 0

    chosen = results[idx]
    print(f"\n-> Usando: {chosen['display_name']} ({chosen['id']})\n")
    return chosen["id"], chosen["display_name"]


# As 26 "grandes áreas" (fields) fixas do OpenAlex -- servem como sugestões
# rápidas antes de digitar um termo de busca livre, exatamente como um menu
# de autocomplete. Fonte: taxonomia de Topics do OpenAlex (nível "field").
OPENALEX_COMMON_FIELDS = [
    "Agricultural and Biological Sciences", "Arts and Humanities", "Biochemistry, Genetics and Molecular Biology",
    "Business, Management and Accounting", "Chemical Engineering", "Chemistry", "Computer Science",
    "Decision Sciences", "Dentistry", "Earth and Planetary Sciences", "Economics, Econometrics and Finance",
    "Energy", "Engineering", "Environmental Science", "Health Professions", "Immunology and Microbiology",
    "Materials Science", "Mathematics", "Medicine", "Neuroscience", "Nursing", "Pharmacology, Toxicology and Pharmaceutics",
    "Physics and Astronomy", "Psychology", "Social Sciences", "Veterinary",
    # extras úteis para contextos de bibliotecas/informação/educação, comuns no Brasil:
    "Library and Information Science", "Education",
]


def suggest_topics_before_typing():
    """
    Mostra um menu com as grandes áreas de conhecimento mais comuns do OpenAlex,
    como sugestão rápida antes do usuário digitar um termo de busca livre.
    Retorna o termo escolhido (string) ou None se o usuário preferir digitar
    algo diferente.
    """
    print("\nSugestões de áreas comuns (você pode digitar o número, ou pular e "
          "digitar livremente um termo mais específico):")
    for i, field in enumerate(OPENALEX_COMMON_FIELDS):
        print(f"  [{i:>2}] {field}")

    choice = input(
        "\nDigite o número de uma sugestão acima, ou Enter para digitar livremente: "
    ).strip()

    if choice.isdigit() and 0 <= int(choice) < len(OPENALEX_COMMON_FIELDS):
        return OPENALEX_COMMON_FIELDS[int(choice)]
    return None


def find_topic(name, interactive=False, allow_multiple=True):
    """
    Busca uma área de conhecimento via Topics (classificação atual do OpenAlex,
    que substituiu os antigos 'concepts'). Hierarquia: Domain > Field > Subfield > Topic.
    Ex: "Library and Information Science", "Bibliometrics".
    O OpenAlex indexa majoritariamente em inglês -- se a busca em português não
    achar nada, tente o termo em inglês.

    Se interactive=True, pergunta ao usuário qual(is) resultado(s) usar.
    Se allow_multiple=True (padrão) e interactive=True, permite escolher mais
    de um topic (ex: "0,2") -- os topics escolhidos são combinados com OR na
    busca (traz publicações que se encaixam em QUALQUER um deles).

    Sempre retorna uma LISTA de tuplas (id, display_name), mesmo que só um
    topic tenha sido escolhido -- assim quem usa esta função não precisa
    tratar "um" e "vários" como casos diferentes.
    """
    data = _get(f"{BASE_URL}/topics", params={"search": name, "per_page": 8})
    results = data.get("results", [])
    if not results:
        raise ValueError(
            f"Nenhum topic encontrado para '{name}'. "
            f"Tente o termo em inglês (ex: 'Library and Information Science')."
        )

    def fmt(i, r):
        subfield = r.get("subfield", {}).get("display_name", "?")
        field = r.get("field", {}).get("display_name", "?")
        domain = r.get("domain", {}).get("display_name", "?")
        return (
            f"  [{i}] {r['display_name']}\n"
            f"       subfield: {subfield} | field: {field} | domain: {domain}\n"
            f"       works: {r.get('works_count')} - id: {r['id']}"
        )

    print("\nTopics encontrados:")
    if interactive and len(results) > 1:
        chosen_idx = _choose_from_results(results, fmt, allow_skip=True, allow_multiple=allow_multiple)
        indices = chosen_idx if isinstance(chosen_idx, list) else [chosen_idx]
    else:
        for i, r in enumerate(results):
            print(fmt(i, r))
        indices = [0]

    chosen_list = [(results[i]["id"], results[i]["display_name"]) for i in indices]

    if len(chosen_list) == 1:
        print(f"\n-> Usando topic: {chosen_list[0][1]} ({chosen_list[0][0]})\n")
    else:
        print(f"\n-> Usando {len(chosen_list)} topics combinados (OR):")
        for tid, tname in chosen_list:
            print(f"     - {tname} ({tid})")
        print()

    return chosen_list


def find_concept(name):
    """
    [LEGADO] Busca uma área de conhecimento via 'concepts' -- sistema antigo do
    OpenAlex, mantido aqui só por compatibilidade. Prefira find_topic().
    Retorna (id, display_name).
    """
    data = _get(f"{BASE_URL}/concepts", params={"search": name, "per_page": 5})
    results = data.get("results", [])
    if not results:
        raise ValueError(
            f"Nenhuma área de conhecimento encontrada para '{name}'. "
            f"Tente o termo em inglês (ex: 'Library science' em vez de 'Biblioteconomia')."
        )

    print("\nÁreas de conhecimento encontradas:")
    for i, r in enumerate(results):
        print(f"  [{i}] {r['display_name']} - works: {r.get('works_count')} - id: {r['id']}")

    chosen = results[0]
    print(f"\n-> Usando área: {chosen['display_name']} ({chosen['id']})\n")
    return chosen["id"], chosen["display_name"]



def get_authors_by_institution(institution_id, max_authors=200, topic_ids=None, concept_id=None):
    """
    Busca autores afiliados à instituição, ordenados por nº de trabalhos (works_count desc).
    Se topic_ids for informado (lista de IDs do OpenAlex), filtra apenas autores
    cuja produção tem PELO MENOS UM desses topics entre seus principais temas
    (lógica OR) -- é a forma de aproximar um filtro por "faculdade"/área, já
    que o OpenAlex não modela sub-unidades da instituição diretamente.
    concept_id é o filtro legado (deprecated), mantido por compatibilidade.
    """
    authors = []
    cursor = "*"
    per_page = 200

    inst_short_id = institution_id.split("/")[-1]  # openalex usa https://openalex.org/I123...

    filter_parts = [f"affiliations.institution.id:{inst_short_id}"]
    if topic_ids:
        short_ids = [t.split("/")[-1] for t in topic_ids]
        filter_parts.append(f"topics.id:{'|'.join(short_ids)}")
    elif concept_id:
        concept_short_id = concept_id.split("/")[-1]
        filter_parts.append(f"x_concepts.id:{concept_short_id}")
    filter_str = ",".join(filter_parts)

    while len(authors) < max_authors:
        data = _get(
            f"{BASE_URL}/authors",
            params={
                "filter": filter_str,
                "sort": "works_count:desc",
                "per_page": min(per_page, max_authors - len(authors)),
                "cursor": cursor,
            },
        )
        results = data.get("results", [])
        if not results:
            break

        for a in results:
            authors.append({
                "id": a["id"],
                "name": a["display_name"],
                "works_count": a.get("works_count", 0),
                "cited_by_count": a.get("cited_by_count", 0),
            })

        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break

    print(f"Encontrados {len(authors)} pesquisadores afiliados.")
    return authors[:max_authors]


def get_coauthorships(author_ids, max_works_per_author=50, topic_ids=None, concept_id=None,
                       year_from=None, year_to=None):
    """
    Para cada autor, busca suas publicações e monta pares de coautoria.
    Se topic_ids (lista de IDs, ou concept_id legado) for informado, filtra
    também as publicações por essas áreas de conhecimento (lógica OR -- basta
    se encaixar em UM dos topics) -- isso evita que uma publicação de outra
    área "vaze" para dentro do grafo só porque um dos autores também publica
    na área de interesse.
    Se year_from/year_to forem informados, filtra as publicações a esse período
    (ambos inclusivos; qualquer um dos dois pode ser omitido para deixar o
    intervalo aberto de um dos lados).
    Retorna:
        edges: dict {(id1, id2): peso}  (id1 < id2 para evitar duplicidade)
        author_names: dict {id: nome}   (inclui coautores externos à instituição)
        works_by_year: dict {work_id: ano}  (publicações únicas, deduplicadas, para
                                              gráfico de evolução temporal)
    """
    edges = defaultdict(int)
    author_names = {}
    works_by_year = {}

    author_ids_set = set(author_ids)

    topic_short_ids = [t.split("/")[-1] for t in topic_ids] if topic_ids else None
    concept_short_id = concept_id.split("/")[-1] if (concept_id and not topic_ids) else None

    for i, author_id in enumerate(author_ids):
        short_id = author_id.split("/")[-1]
        print(f"[{i+1}/{len(author_ids)}] Buscando publicações de {short_id}...")

        filter_parts = [f"authorships.author.id:{short_id}"]
        if topic_short_ids:
            filter_parts.append(f"topics.id:{'|'.join(topic_short_ids)}")
        elif concept_short_id:
            filter_parts.append(f"concepts.id:{concept_short_id}")
        if year_from:
            filter_parts.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filter_parts.append(f"to_publication_date:{year_to}-12-31")

        try:
            data = _get(
                f"{BASE_URL}/works",
                params={
                    "filter": ",".join(filter_parts),
                    "per_page": min(max_works_per_author, 200),
                    "select": "id,authorships,publication_year",
                },
            )
        except requests.HTTPError as e:
            print(f"  Erro ao buscar {short_id}: {e}")
            continue

        works = data.get("results", [])

        for w in works:
            work_id = w.get("id")
            year = w.get("publication_year")
            if work_id and year and work_id not in works_by_year:
                works_by_year[work_id] = year

            authorships = w.get("authorships", [])
            # extrai todos os coautores da publicação
            coauthors = []
            for a in authorships:
                aid = a.get("author", {}).get("id")
                aname = a.get("author", {}).get("display_name")
                if aid:
                    coauthors.append((aid, aname))
                    author_names[aid] = aname

            # cria arestas entre todos os pares de coautores da publicação
            for x in range(len(coauthors)):
                for y in range(x + 1, len(coauthors)):
                    id1, id2 = sorted([coauthors[x][0], coauthors[y][0]])
                    if id1 == id2:
                        continue
                    edges[(id1, id2)] += 1

        time.sleep(0.4)  # gentileza com a API (evita 429 Too Many Requests)

    return edges, author_names, works_by_year


def build_graph(edges, author_names, institution_author_ids, restrict_to_institution=False):
    """Constrói o grafo networkx a partir das arestas de coautoria."""
    G = nx.Graph()

    inst_set = set(institution_author_ids)

    for (id1, id2), weight in edges.items():
        if restrict_to_institution and not (id1 in inst_set and id2 in inst_set):
            continue

        for node_id in (id1, id2):
            if node_id not in G:
                G.add_node(
                    node_id,
                    label=author_names.get(node_id, node_id),
                    is_institution_member=node_id in inst_set,
                )

        G.add_edge(id1, id2, weight=weight)

    return G


def compute_metrics(G):
    """Calcula métricas descritivas básicas do grafo."""
    print("\n===== MÉTRICAS DESCRITIVAS =====")
    print(f"Nº de nós (pesquisadores): {G.number_of_nodes()}")
    print(f"Nº de arestas (colaborações): {G.number_of_edges()}")
    print(f"Densidade: {nx.density(G):.4f}")

    if G.number_of_nodes() == 0:
        return {}

    components = list(nx.connected_components(G))
    largest_cc = max(components, key=len)
    print(f"Nº de componentes conectados: {len(components)}")
    print(f"Tamanho do maior componente: {len(largest_cc)} "
          f"({100*len(largest_cc)/G.number_of_nodes():.1f}% dos nós)")

    # Métricas de centralidade (calculadas no maior componente para eficiência)
    G_main = G.subgraph(largest_cc).copy()

    degree_cent = nx.degree_centrality(G_main)
    betweenness_cent = nx.betweenness_centrality(G_main, weight="weight")

    top_degree = sorted(degree_cent.items(), key=lambda x: -x[1])[:10]
    top_betweenness = sorted(betweenness_cent.items(), key=lambda x: -x[1])[:10]

    print("\nTop 10 pesquisadores por centralidade de grau (mais colaboradores diretos):")
    for node_id, val in top_degree:
        print(f"  {G.nodes[node_id]['label']:<40} {val:.4f}")

    print("\nTop 10 pesquisadores por intermediação (pontes entre grupos):")
    for node_id, val in top_betweenness:
        print(f"  {G.nodes[node_id]['label']:<40} {val:.4f}")

    # Comunidades (Louvain)
    communities = {}
    if community_louvain is not None:
        partition = community_louvain.best_partition(G_main, weight="weight")
        n_comm = len(set(partition.values()))
        print(f"\nNº de comunidades detectadas (Louvain): {n_comm}")
        communities = partition
        nx.set_node_attributes(G, partition, "community")
    else:
        print("\n[python-louvain não instalado — pulando detecção de comunidades]")

    return {
        "degree_centrality": degree_cent,
        "betweenness_centrality": betweenness_cent,
        "communities": communities,
        "largest_component": G_main,
    }


def _fix_pyvis_template_path():
    """
    Quando rodando dentro de um executável PyInstaller (--onefile), os arquivos
    de dados são extraídos para sys._MEIPASS em vez de ficarem no diretório do
    pacote original. O pyvis usa Jinja2 para renderizar seu template.html, mas
    o Jinja2 ainda aponta para o caminho original do pacote — que não existe no
    executável. Esta função corrige o caminho de templates do pyvis para apontar
    para sys._MEIPASS quando necessário.
    """
    import sys
    if not getattr(sys, "frozen", False):
        return  # rodando como script normal, sem ajuste necessário

    import os
    import pyvis
    meipass = sys._MEIPASS
    correct_templates = os.path.join(meipass, "pyvis", "templates")
    if os.path.isdir(correct_templates):
        pyvis.__file__ = os.path.join(meipass, "pyvis", "__init__.py")


def export_graph(G, output_prefix="grafo_colaboracao"):
    """Exporta o grafo para .gexf (Gephi) e gera visualização interativa em HTML."""
    gexf_path = f"{output_prefix}.gexf"
    nx.write_gexf(G, gexf_path, encoding="utf-8")
    print(f"\nGrafo exportado para: {gexf_path} (abra no Gephi para exploração visual avançada)")

    try:
        _fix_pyvis_template_path()
        from pyvis.network import Network

        net = Network(height="800px", width="100%", notebook=False, cdn_resources="in_line")
        # Layout mais compacto (menos repulsão entre nós) para que, ao abrir
        # o HTML, o grafo caiba na tela com um zoom onde os nomes ficam legíveis.
        net.barnes_hut(gravity=-4000, central_gravity=0.35, spring_length=110, spring_strength=0.05, damping=0.12)

        # cores por comunidade, se existir
        comm_attr = nx.get_node_attributes(G, "community")
        degree_dict = dict(G.degree())

        for node_id, attrs in G.nodes(data=True):
            comm = comm_attr.get(node_id, 0)
            degree = degree_dict.get(node_id, 1)
            net.add_node(
                node_id,
                label=attrs.get("label", node_id),
                title=f"{attrs.get('label', node_id)} (comunidade {comm})",
                group=comm,
                # nó um pouco maior para quem tem mais colaborações
                size=15 + min(degree * 2, 30),
                font={"size": 22, "color": "#222222", "strokeWidth": 3, "strokeColor": "#ffffff"},
            )

        for u, v, attrs in G.edges(data=True):
            net.add_edge(u, v, value=attrs.get("weight", 1))

        # Rótulos sempre visíveis (não só ao passar o mouse), zoom/arraste liberados,
        # e estabilização configurada para "assentar" o layout mais rápido.
        net.set_options("""
        {
          "nodes": {
            "font": {"size": 22, "face": "arial"}
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          },
          "physics": {
            "stabilization": {
              "enabled": true,
              "iterations": 300,
              "fit": true
            }
          }
        }
        """)

        html_path = f"{output_prefix}.html"
        # Gera o HTML manualmente e grava forçando UTF-8: no Windows, o
        # net.write_html() nativo do pyvis usa a codificação padrão do sistema
        # (geralmente cp1252), que quebra com nomes acentuados (ç, ã, é...).
        html_content = net.generate_html(notebook=False)

        # Desliga a física automaticamente assim que o layout estabiliza --
        # sem isso, os nós (especialmente os de grau alto) ficam se ajustando
        # infinitamente, o que dá a impressão de "tremedeira" no grafo.
        # Depois de desligada, dá pra ainda arrastar nós manualmente com o mouse.
        freeze_script = """
<script type="text/javascript">
  network.once("stabilizationIterationsDone", function () {
    network.setOptions({ physics: false });
  });
</script>
"""
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", freeze_script + "</body>")
        else:
            html_content += freeze_script

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Visualização interativa gerada em: {html_path} (abra no navegador)")
        print("  Dica: o grafo estabiliza sozinho ao abrir e a física desliga automaticamente "
              "(os nós param de se mexer). Use a roda do mouse para dar zoom.")
    except ImportError:
        print("[pyvis não instalado — pulando visualização HTML interativa]")


def generate_charts(G, metrics, authors, works_by_year, output_prefix="grafo_colaboracao"):
    """
    Gera gráficos descritivos complementares ao grafo de rede, salvos como PNG:
      1. Distribuição de grau (histograma) -- quantos colaboradores diretos cada pesquisador tem
      2. Top 15 por centralidade de grau (barras)
      3. Top 15 por intermediação/betweenness (barras)
      4. Tamanho das comunidades detectadas (barras)
      5. Publicações por ano (evolução temporal, linha)
      6. Produtividade (nº publicações) vs. centralidade de grau (dispersão)
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # sem necessidade de display
        import matplotlib.pyplot as plt
    except ImportError:
        print("[matplotlib não instalado — pulando geração de gráficos. Rode: pip install matplotlib]")
        return

    if G.number_of_nodes() == 0:
        print("[Grafo vazio — pulando gráficos]")
        return

    plt.rcParams.update({"figure.autolayout": True, "font.size": 10})

    # ---- 1. Distribuição de grau ----
    degrees = [d for _, d in G.degree()]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(degrees, bins=min(30, max(degrees)) if degrees else 1, color="#4C72B0", edgecolor="white")
    ax.set_title("Distribuição do número de colaboradores diretos por pesquisador")
    ax.set_xlabel("Nº de colaboradores diretos (grau)")
    ax.set_ylabel("Nº de pesquisadores")
    fig.savefig(f"{output_prefix}_distribuicao_grau.png", dpi=150)
    plt.close(fig)

    degree_cent = metrics.get("degree_centrality", {})
    betweenness_cent = metrics.get("betweenness_centrality", {})
    communities = metrics.get("communities", {})

    # ---- 2. Top 15 por centralidade de grau ----
    if degree_cent:
        top = sorted(degree_cent.items(), key=lambda x: -x[1])[:15]
        labels = [G.nodes[nid]["label"] for nid, _ in top][::-1]
        values = [v for _, v in top][::-1]
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(labels, values, color="#4C72B0")
        ax.set_title("Top 15 pesquisadores por centralidade de grau\n(mais colaboradores diretos)")
        ax.set_xlabel("Centralidade de grau")
        fig.savefig(f"{output_prefix}_top_centralidade_grau.png", dpi=150)
        plt.close(fig)

    # ---- 3. Top 15 por intermediação ----
    if betweenness_cent:
        top = sorted(betweenness_cent.items(), key=lambda x: -x[1])[:15]
        labels = [G.nodes[nid]["label"] for nid, _ in top][::-1]
        values = [v for _, v in top][::-1]
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(labels, values, color="#DD8452")
        ax.set_title("Top 15 pesquisadores por intermediação (betweenness)\n(pontes entre grupos de pesquisa)")
        ax.set_xlabel("Centralidade de intermediação")
        fig.savefig(f"{output_prefix}_top_intermediacao.png", dpi=150)
        plt.close(fig)

    # ---- 4. Tamanho das comunidades ----
    if communities:
        comm_sizes = defaultdict(int)
        for node_id, comm_id in communities.items():
            comm_sizes[comm_id] += 1
        sorted_comms = sorted(comm_sizes.items(), key=lambda x: -x[1])
        labels = [f"Comunidade {c}" for c, _ in sorted_comms]
        sizes = [s for _, s in sorted_comms]
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(labels, sizes, color="#55A868")
        ax.set_title("Tamanho das comunidades de colaboração detectadas (Louvain)")
        ax.set_ylabel("Nº de pesquisadores")
        plt.xticks(rotation=45, ha="right")
        fig.savefig(f"{output_prefix}_tamanho_comunidades.png", dpi=150)
        plt.close(fig)

    # ---- 5. Publicações por ano ----
    if works_by_year:
        year_counts = defaultdict(int)
        for year in works_by_year.values():
            year_counts[year] += 1
        years_sorted = sorted(year_counts.keys())
        counts = [year_counts[y] for y in years_sorted]
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(years_sorted, counts, marker="o", color="#C44E52")
        ax.set_title("Evolução do número de publicações por ano")
        ax.set_xlabel("Ano")
        ax.set_ylabel("Nº de publicações")
        ax.grid(alpha=0.3)
        fig.savefig(f"{output_prefix}_publicacoes_por_ano.png", dpi=150)
        plt.close(fig)
    else:
        print("[Sem dados de ano de publicação — pulando gráfico de evolução temporal]")

    # ---- 6. Produtividade vs. centralidade de grau ----
    if degree_cent and authors:
        works_count_by_id = {a["id"]: a.get("works_count", 0) for a in authors}
        xs, ys, labels_pts = [], [], []
        for node_id, cent in degree_cent.items():
            if node_id in works_count_by_id:
                xs.append(works_count_by_id[node_id])
                ys.append(cent)
                labels_pts.append(G.nodes[node_id]["label"])
        if xs:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(xs, ys, alpha=0.6, color="#8172B2")
            ax.set_title("Produtividade vs. centralidade na rede de colaboração")
            ax.set_xlabel("Nº total de publicações do pesquisador")
            ax.set_ylabel("Centralidade de grau na rede")
            fig.savefig(f"{output_prefix}_produtividade_vs_centralidade.png", dpi=150)
            plt.close(fig)

    print(f"\nGráficos salvos com prefixo '{output_prefix}_*.png'")


def export_csvs(G, authors, metrics, works_by_year, output_prefix="grafo_colaboracao"):
    """
    Exporta os dados coletados e as métricas calculadas em arquivos CSV
    (abrem direto no Excel/Google Sheets), para quem preferir analisar os
    dados fora do grafo ou cruzar com outras planilhas.

    Gera 5 arquivos:
      1. _pesquisadores.csv        -> um pesquisador por linha, com suas métricas individuais
      2. _colaboracoes.csv         -> uma colaboração (aresta) por linha
      3. _comunidades.csv          -> um grupo (comunidade) por linha, com a lista de membros
      4. _publicacoes_por_ano.csv  -> série temporal de publicações
      5. _resumo_metricas.csv      -> KPIs gerais da rede como um todo

    Usa encoding "utf-8-sig" (UTF-8 com BOM) para o Excel no Windows abrir
    os acentos corretamente sem precisar configurar nada na importação.
    """
    degree_cent = metrics.get("degree_centrality", {})
    betweenness_cent = metrics.get("betweenness_centrality", {})
    communities = metrics.get("communities", {})
    degree_dict = dict(G.degree())

    works_count_by_id = {a["id"]: a.get("works_count", 0) for a in authors}
    cited_by_id = {a["id"]: a.get("cited_by_count", 0) for a in authors}

    # ---- 1. Pesquisadores ----
    nodes_path = f"{output_prefix}_pesquisadores.csv"
    with open(nodes_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "nome", "membro_da_instituicao_filtrada",
            "grau_colaboradores_diretos", "centralidade_grau", "centralidade_intermediacao",
            "comunidade_id", "total_publicacoes_openalex", "total_citacoes_openalex",
        ])
        for node_id, attrs in G.nodes(data=True):
            writer.writerow([
                node_id,
                attrs.get("label", node_id),
                attrs.get("is_institution_member", False),
                degree_dict.get(node_id, 0),
                round(degree_cent[node_id], 6) if node_id in degree_cent else "",
                round(betweenness_cent[node_id], 6) if node_id in betweenness_cent else "",
                communities.get(node_id, ""),
                works_count_by_id.get(node_id, ""),
                cited_by_id.get(node_id, ""),
            ])

    # ---- 2. Colaborações (arestas) ----
    edges_path = f"{output_prefix}_colaboracoes.csv"
    with open(edges_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "pesquisador_1_id", "pesquisador_1_nome",
            "pesquisador_2_id", "pesquisador_2_nome",
            "publicacoes_em_comum",
        ])
        for u, v, attrs in G.edges(data=True):
            writer.writerow([
                u, G.nodes[u].get("label", u),
                v, G.nodes[v].get("label", v),
                attrs.get("weight", 1),
            ])

    # ---- 3. Comunidades ----
    if communities:
        comm_members = defaultdict(list)
        for node_id, comm_id in communities.items():
            comm_members[comm_id].append(G.nodes[node_id].get("label", node_id))

        comm_path = f"{output_prefix}_comunidades.csv"
        with open(comm_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["comunidade_id", "tamanho", "membros"])
            for comm_id, members in sorted(comm_members.items(), key=lambda x: -len(x[1])):
                writer.writerow([comm_id, len(members), "; ".join(sorted(members))])

    # ---- 4. Publicações por ano ----
    if works_by_year:
        year_counts = defaultdict(int)
        for year in works_by_year.values():
            year_counts[year] += 1

        year_path = f"{output_prefix}_publicacoes_por_ano.csv"
        with open(year_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ano", "numero_publicacoes"])
            for year in sorted(year_counts.keys()):
                writer.writerow([year, year_counts[year]])

    # ---- 5. Resumo geral (KPIs da rede) ----
    summary_path = f"{output_prefix}_resumo_metricas.csv"
    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["metrica", "valor"])
        writer.writerow(["numero_pesquisadores", G.number_of_nodes()])
        writer.writerow(["numero_colaboracoes", G.number_of_edges()])
        writer.writerow(["densidade", round(nx.density(G), 6) if G.number_of_nodes() > 0 else ""])

        components = list(nx.connected_components(G)) if G.number_of_nodes() > 0 else []
        writer.writerow(["numero_componentes_conectados", len(components)])
        if components:
            largest = max(components, key=len)
            writer.writerow(["tamanho_maior_componente", len(largest)])
            writer.writerow([
                "percentual_pesquisadores_no_maior_componente",
                round(100 * len(largest) / G.number_of_nodes(), 2),
            ])
        writer.writerow([
            "numero_comunidades_detectadas",
            len(set(communities.values())) if communities else "",
        ])

    print(f"\nCSVs exportados com prefixo '{output_prefix}_*.csv'")
    print("  Consulte KPI_DOCUMENTACAO.md para entender cada coluna/métrica.")


def main():
    parser = argparse.ArgumentParser(description="Grafo de colaboração científica via OpenAlex, por universidade.")
    parser.add_argument("--institution", required=False, default=None,
                         help="Nome da universidade, ex: 'Universidade de Sao Paulo'")
    parser.add_argument("--topic", required=False, default=None,
                         help="Área de conhecimento via Topics (recomendado -- classificação atual do "
                              "OpenAlex), aproxima 'faculdade'/departamento. "
                              "Ex: 'Library and Information Science' (prefira o termo em inglês)")
    parser.add_argument("--field", required=False, default=None,
                         help="[LEGADO] Área de conhecimento via Concepts (sistema antigo, deprecated "
                              "pelo OpenAlex). Prefira --topic. Ignorado se --topic for informado.")
    parser.add_argument("--topic-id", required=False, default=None,
                         help="ID(s) diretos de Topic do OpenAlex, separados por vírgula "
                              "(ex: 'T10712,T14330'). Pula a busca por nome -- mais rápido e "
                              "preciso quando você já sabe os IDs exatos. Tem prioridade sobre --topic.")
    parser.add_argument("--year-from", type=int, default=None,
                         help="Ano inicial (inclusive) das publicações a considerar, ex: 2018")
    parser.add_argument("--year-to", type=int, default=None,
                         help="Ano final (inclusive) das publicações a considerar, ex: 2024")
    parser.add_argument("--max-authors", type=int, default=100, help="Nº máximo de pesquisadores a coletar")
    parser.add_argument("--max-works-per-author", type=int, default=50, help="Nº máximo de publicações por pesquisador")
    parser.add_argument("--restrict-to-institution", action="store_true",
                         help="Se ativado, só mantém arestas entre pesquisadores da própria instituição "
                              "(exclui coautores externos)")
    parser.add_argument("--output", default="grafo_colaboracao", help="Prefixo dos arquivos de saída")
    args = parser.parse_args()

    # Modo interativo: se nenhum argumento de linha de comando foi passado
    # (ex: rodando direto pela IDE), pergunta os dados no console.
    interactive_mode = args.institution is None
    if interactive_mode:
        print("Nenhum argumento --institution informado. Modo interativo ativado.\n")
        args.institution = input("Nome da universidade (ex: Universidade de Sao Paulo): ").strip()
        while not args.institution:
            args.institution = input("Nome não pode ser vazio. Tente novamente: ").strip()

        # Sugestões de área antes de digitar livremente (menu com as grandes
        # áreas mais comuns do OpenAlex)
        suggested = suggest_topics_before_typing()
        if suggested:
            args.topic = suggested
            print(f"-> Área selecionada: {suggested}\n")
        else:
            topic_input = input(
                "Digite livremente a área de conhecimento / 'faculdade' "
                "(opcional, ex: Bibliometrics) [Enter para pular]: "
            ).strip()
            args.topic = topic_input if topic_input else None

        year_from_input = input(
            "Ano inicial das publicações a considerar (opcional, ex: 2018) [Enter para pular]: "
        ).strip()
        args.year_from = int(year_from_input) if year_from_input else None

        year_to_input = input(
            "Ano final das publicações a considerar (opcional, ex: 2024) [Enter para pular]: "
        ).strip()
        args.year_to = int(year_to_input) if year_to_input else None

        max_authors_input = input(f"Nº máximo de pesquisadores [padrão {args.max_authors}]: ").strip()
        if max_authors_input:
            args.max_authors = int(max_authors_input)

        max_works_input = input(f"Nº máximo de publicações por pesquisador [padrão {args.max_works_per_author}]: ").strip()
        if max_works_input:
            args.max_works_per_author = int(max_works_input)

        restrict_input = input("Restringir a colaborações apenas dentro da instituição? (s/N): ").strip().lower()
        args.restrict_to_institution = restrict_input == "s"
        print()

    if args.year_from and args.year_to and args.year_from > args.year_to:
        print("Aviso: --year-from é maior que --year-to. Invertendo os valores automaticamente.")
        args.year_from, args.year_to = args.year_to, args.year_from

    inst_id, inst_name = find_institution(args.institution, interactive=interactive_mode)

    topic_ids = None
    concept_id = None
    if args.topic_id:
        # IDs diretos informados via --topic-id: pula a busca por nome.
        # Aceita tanto "T10712" quanto a URL completa "https://openalex.org/T10712".
        raw_ids = [t.strip() for t in args.topic_id.split(",") if t.strip()]
        topic_ids = [t if t.startswith("http") else f"https://openalex.org/{t}" for t in raw_ids]
        print(f"\nUsando {len(topic_ids)} topic(s) informados diretamente via --topic-id: "
              f"{', '.join(raw_ids)}\n")
    elif args.topic:
        # Permite múltiplos termos de busca separados por ";" (cada termo usa o
        # resultado mais relevante automaticamente quando não-interativo).
        # No modo interativo, cada termo pode gerar múltiplas seleções manuais.
        terms = [t.strip() for t in args.topic.split(";") if t.strip()]
        topic_ids = []
        for term in terms:
            chosen = find_topic(term, interactive=interactive_mode, allow_multiple=True)
            topic_ids.extend(tid for tid, _ in chosen)
    elif args.field:
        concept_id, concept_name = find_concept(args.field)

    authors = get_authors_by_institution(
        inst_id, max_authors=args.max_authors, topic_ids=topic_ids, concept_id=concept_id
    )

    if not authors:
        print("Nenhum pesquisador encontrado. Encerrando.")
        sys.exit(1)

    author_ids = [a["id"] for a in authors]
    author_names = {a["id"]: a["name"] for a in authors}

    edges, coauthor_names, works_by_year = get_coauthorships(
        author_ids, max_works_per_author=args.max_works_per_author,
        topic_ids=topic_ids, concept_id=concept_id,
        year_from=args.year_from, year_to=args.year_to,
    )
    author_names.update(coauthor_names)

    G = build_graph(edges, author_names, author_ids, restrict_to_institution=args.restrict_to_institution)

    metrics = compute_metrics(G)
    export_graph(G, output_prefix=args.output)
    generate_charts(G, metrics, authors, works_by_year, output_prefix=args.output)
    export_csvs(G, authors, metrics, works_by_year, output_prefix=args.output)


if __name__ == "__main__":
    main()
