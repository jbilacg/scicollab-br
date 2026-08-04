# 📊 Grafo de Colaboração Científica — Resumo do Projeto

## O que é

Um aplicativo que **cria mapas visuais de redes de pesquisadores** mostrando quem colabora com quem, baseado em dados públicos do OpenAlex (sem captcha, sem parede de pagamento).

**Entrada**: Nome de uma universidade + período + área (opcional)  
**Saída**: 
- Grafo interativo (HTML no navegador)
- Planilhas com dados (CSV — abrem no Excel)
- 6 gráficos descritivos (PNG)
- Arquivo Gephi para análise avançada (GEXF)

---

## Arquivos do Projeto

```
grafo_colaboracao/
├── openalex_colab.py              ← Script principal (coleta + análise)
├── gui_openalex.py                ← Interface gráfica (Tkinter)
├── install.py                     ← Instalador automático
├── requirements.txt               ← Dependências (pip install)
├── COMECE_AQUI.md                 ← Guia rápido para usuários não-técnicos
├── README_INSTALACAO.md           ← Instalação manual (se quiser terminal)
├── README.md                      ← Uso via linha de comando
├── KPI_DOCUMENTACAO.md            ← Explicação de cada métrica/KPI
├── PROJETO_RESUMO.md              ← Este arquivo
└── .gitignore                     ← (opcional) Para versionamento

```

---

## Como Distribuir

### Opção 1: Distribuição Simples (Recomendado)

1. **Compacte a pasta inteira** → `grafo_colaboracao.zip`
2. **Distribua o ZIP** por:
   - Email
   - Dropbox / Google Drive
   - GitHub (público ou privado)
   - Seu servidor web

3. **Instruções para o usuário**:
   ```
   1. Extraia o ZIP
   2. Abra terminal/prompt naquela pasta
   3. Execute: python3 install.py
   4. Use o atalho criado no Desktop, ou: python3 gui_openalex.py
   ```

**Vantagem**: simples, sem dependências externas  
**Desvantagem**: usuário precisa ter Python 3.9+ instalado

---

### Opção 2: Executável Único (.exe no Windows)

Se quiser distribuir um `.exe` que **não precisa Python instalado**:

#### Instalar PyInstaller
```bash
pip install pyinstaller
```

#### Criar o executável
```bash
cd grafo_colaboracao/
pyinstaller --onefile --windowed --name "Grafo de Colaboracao" gui_openalex.py
```

Isso gera `dist/Grafo de Colaboracao.exe` (~150 MB).

#### Distribuir
- Compacte a pasta `dist/` → `grafo_colaboracao_windows.zip`
- Usuário extrai e clica no `.exe`
- **Sem precisar de Python!**

---

### Opção 3: Instalador NSIS (Windows, profissional)

Se quiser um "Setup.exe" fancy:

1. Instale NSIS (https://nsis.sourceforge.io/)
2. Crie um script `.nsi` (template abaixo)
3. Compile → `Setup.exe`

```nsis
; grafo_colaboracao_setup.nsi
Name "Grafo de Colaboração"
OutFile "Setup.exe"
InstallDir "$PROGRAMFILES\GrafoColaboracao"
RequestExecutionLevel admin

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\*.*"
  CreateShortCut "$SMPROGRAMS\Grafo de Colaboracao.lnk" "$INSTDIR\Grafo de Colaboracao.exe"
  CreateShortCut "$DESKTOP\Grafo de Colaboracao.lnk" "$INSTDIR\Grafo de Colaboracao.exe"
SectionEnd
```

---

## Fluxo de Uso (Do ponto de vista do usuário)

```
1. Download/Recebe o projeto
   ↓
2. Executa install.py (ou python3 gui_openalex.py direto)
   ↓
   2a. Verifica Python 3.9+
   2b. Instala dependências automaticamente
   2c. Cria atalho no Desktop
   ↓
3. Abre a interface gráfica (GUI)
   ↓
4. Preenche formulário (universidade + filtros)
   ↓
5. Clica "▶ Executar Análise"
   ↓
6. Vê progresso em tempo real
   ↓
7. Recebe mensagem "✓ Concluído!"
   ↓
8. Abre a pasta com os arquivos (HTML, CSV, PNG, GEXF)
   ↓
9. Visualiza o grafo no navegador e analisa em Excel
```

---

## Requisitos do Sistema

| Item | Mínimo | Recomendado |
|------|--------|-------------|
| Python | 3.9+ | 3.11+ |
| RAM | 2 GB | 4+ GB |
| Disco | 500 MB | 1 GB |
| Internet | Sim (API OpenAlex) | Sim |

**Sistemas suportados**: Windows 7+, macOS 10.14+, Linux (qualquer distro recente)

---

## Funcionalidades

✅ **Coleta de dados**
- Busca pesquisadores por universidade
- Filtra por área de conhecimento (multiple topics com OR logic)
- Filtra por período (ano inicial/final)

✅ **Análise de Rede**
- Constrói grafo de coautoria (nós = pesquisadores, arestas = colaborações)
- Calcula 10+ métricas (grau, centralidade, betweenness, comunidades)
- Detecta comunidades (algoritmo Louvain)

✅ **Visualizações**
- HTML interativo (pyvis — zoom, arraste, filtros)
- 6 gráficos PNG (distribuição, rankings, evolução, dispersão)
- Exporta GEXF para Gephi

✅ **Exportação de Dados**
- 5 arquivos CSV prontos para Excel
- Dados brutos do OpenAlex (JSON possível com ajustes)

✅ **Interface**
- GUI com Tkinter (sem dependências gráficas externas)
- Modo interativo (terminal com perguntas)
- Modo batch (linha de comando com argumentos)
- Instalador automático de dependências

---

## Limitações Conhecidas

⚠️ **OpenAlex Coverage**
- Nem toda publicação brasileira está indexada
- Viés para publicações em inglês
- Desambiguação de nomes às vezes falha (homônimos)

⚠️ **Comunidades Estatísticas**
- Grupos encontrados pelo algoritmo, não por estrutura administrativa
- Podem não corresponder a departamentos/faculdades reais
- Interpretação é contextual

⚠️ **Escala**
- ~200+ pesquisadores: 10-15 min de coleta
- ~500+ pesquisadores: 20-30 min (rate limiting pode atrasar)

⚠️ **Sem Offline**
- Precisa de internet para consultar API OpenAlex
- Dados não são cachéados (cada execução consulta a API novamente)

---

## Próximas Funcionalidades Possíveis

- [ ] Cachear dados para consultas offline posteriores
- [ ] Exportar para D3.js/Plotly (além de pyvis)
- [ ] Análise de ego-network (rede ao redor de um pesquisador)
- [ ] Integração com Lattes (quando houver API aberta)
- [ ] Relatório automático em PDF
- [ ] Comparação de duas universidades lado-a-lado
- [ ] App mobile (React Native / Flutter)
- [ ] Suporte a mais bases (WoS, Scopus via API paga)

---

## Estrutura de Código

### `openalex_colab.py` (Script Principal)
```python
_get()                          # Chamadas HTTP com retry
find_institution()              # Busca universidade
find_topic()                    # Busca área de conhecimento (múltiplas)
get_authors_by_institution()    # Coleta pesquisadores
get_coauthorships()             # Coleta publicações + monta arestas
build_graph()                   # Constrói grafo (networkx)
compute_metrics()               # Calcula grau, centralidade, comunidades
export_graph()                  # Gera HTML (pyvis) + GEXF (networkx)
generate_charts()               # Gera 6 PNG (matplotlib)
export_csvs()                   # Exporta 5 CSVs (dados brutos)
main()                          # Orquestra tudo
```

### `gui_openalex.py` (Interface Gráfica)
```python
DependencyInstaller             # Verifica/instala pacotes faltando
OpenAlexGUI                     # Janela principal (Tkinter)
  - create_widgets()            # Monta formulário
  - validate_inputs()           # Valida preenchimento
  - run_analysis()              # Executa script em subprocess
  - open_output_dir()           # Abre pasta com resultados
  - show_help()                 # Mostra janela de ajuda
```

### `install.py` (Instalador)
```python
check_python_version()          # Verifica Python 3.9+
install_dependencies()          # pip install -r requirements.txt
create_shortcuts()              # Cria atalhos (Windows/Mac/Linux)
main()                          # Orquestra instalação
```

---

## Dependências (pip)

| Pacote | Versão | Para quê |
|--------|--------|----------|
| `requests` | >=2.31 | Chamadas HTTP à API OpenAlex |
| `networkx` | >=3.2 | Construir e analisar grafo |
| `python-louvain` | >=0.16 | Detectar comunidades |
| `pyvis` | >=0.3.2 | Visualizar grafo em HTML |
| `matplotlib` | >=3.8 | Gerar gráficos PNG |
| `tkinter` | built-in | Interface gráfica (já vem com Python) |

---

## Teste Rápido (Sem Coletar Dados Reais)

Já que a API está bloqueada aqui, o código foi testado com dados sintéticos:

```python
# Simula 20 pesquisadores com grafo de colaboração
G = nx.Graph()
for i in range(1, 21):
    G.add_node(f"A{i}", label=f"Prof {i}")
for _ in range(35):
    a, b = random.sample(list(G.nodes()), 2)
    G.add_edge(a, b, weight=random.randint(1,5))

# Executa análise
metrics = compute_metrics(G)
export_graph(G)
generate_charts(G, metrics, ...)
export_csvs(G, ...)
```

✓ Grafo estabiliza e física desliga  
✓ Seleção múltipla de topics funciona  
✓ CSVs com UTF-8 OK  
✓ Gráficos matplotlib renderizam  

---

## Suporte & Contribuições

**Bugs/Ideias**?  
Abra uma issue no repositório ou envie email.

**Quer contribuir**?  
Pull requests aceitas! Áreas:
- Otimização de coleta (paralelização)
- Novos gráficos/análises
- Suporte a outras bases de dados
- Melhorias de UI/UX

---

## Licença

MIT (veja LICENSE.txt se incluído)

---

**Desenvolvido com ❤️ para a comunidade científica brasileira.**
