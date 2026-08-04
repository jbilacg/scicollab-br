# 🚀 Grafo de Colaboração Científica — Comece Aqui

Bem-vindo! Este aplicativo cria visualizações e análises de redes de colaboração entre pesquisadores, a partir de dados do **OpenAlex** (base de dados académica aberta, sem captcha).

## ⚡ Instalação Rápida (5 minutos)

### Windows, Mac ou Linux

1. **Baixe e extraia** os arquivos do projeto
2. **Abra o terminal** ou prompt de comando naquela pasta
3. **Digite**:
   ```
   python3 install.py
   ```
   Isso vai:
   - ✓ Verificar sua versão do Python
   - ✓ Instalar as bibliotecas necessárias automaticamente
   - ✓ Criar um atalho no seu Desktop
   - ✓ Oferecer rodar a interface gráfica na hora

4. **Pronto!** Agora pode fechar o terminal. Use o atalho criado no Desktop, ou execute:
   ```
   python3 gui_openalex.py
   ```

---

## 🖱️ Como Usar

### Passo 1: Abra a Interface Gráfica

Execute `gui_openalex.py` (ou clique no atalho no Desktop).

Uma janela vai abrir com um formulário. Preencha:

### Passo 2: Formulário Principal

| Campo | O quê fazer | Exemplo |
|-------|-----------|---------|
| **Universidade*** | Nome completo da instituição | "Universidade de Sao Paulo" |
| **Área de Conhecimento** | (Opcional) Deixe em branco para trazer a universidade toda, ou especifique | "Computer Science" |
| **Topic IDs** | (Avançado) Se já tem IDs do OpenAlex | "T10712,T14330" |
| **Ano Inicial** | (Opcional) Só publicações de 2018 em diante | "2018" |
| **Ano Final** | (Opcional) Só publicações até 2024 | "2024" |
| **Nº Máximo de Pesquisadores** | Quantos pesquisadores coletar (padrão: 100) | "150" |
| **Nº Máximo de Publicações** | Quantas publicações por pesquisador (padrão: 50) | "50" |
| **Restringir a Colaborações Internas** | Marque ✓ se quiser VER APENAS colaborações entre pesquisadores da mesma universidade | — |
| **Nome do Arquivo de Saída** | Nome dos arquivos que vão ser salvos (padrão: grafo_colaboracao) | "usp_rede_2024" |

\* = obrigatório

### Passo 3: Clique em "▶ Executar Análise"

Uma janela vai aparecer mostrando o progresso em tempo real. Dependendo do tamanho da coleta, pode levar de 2 a 10 minutos.

Quando terminar, você vê **✓ Análise concluída com sucesso!** e uma lista dos arquivos gerados.

### Passo 4: Veja os Resultados

Clique em **"📁 Pasta de Saída"** para abrir a pasta com os arquivos gerados.

---

## 📊 O que você recebe

Após a análise, você terá:

### 1. **Visualização Interativa** (`grafo_colaboracao.html`)
- Abra no navegador (Chrome, Firefox, Edge, etc.)
- Cada ponto = um pesquisador
- Linhas conectando = colaboração (coautoria)
- Zooma com a roda do mouse
- Cores diferentes = grupos (comunidades) de pesquisa

### 2. **Planilhas Excel** (`.csv`)
- `_pesquisadores.csv` — cada pesquisador com suas métricas
- `_colaboracoes.csv` — quem colaborou com quem
- `_comunidades.csv` — grupos de pesquisa detectados
- `_publicacoes_por_ano.csv` — série temporal
- `_resumo_metricas.csv` — números gerais da rede

Abra todos estes em Excel, Google Sheets, ou LibreOffice Calc.

### 3. **Gráficos** (`.png`)
6 gráficos descritivos em forma de imagem:
- Quem mais colabora
- Quem é "ponte" entre grupos
- Tamanho dos grupos
- Crescimento de publicações ao longo do tempo
- E mais

### 4. **Arquivo Gephi** (`grafo_colaboracao.gexf`)
Para análise mais avançada em software de redes (Gephi — gratuito, https://gephi.org).

---

## ❓ Dúvidas Comuns

### "Que universidades posso usar?"
Qualquer uma no Brasil ou mundo que tenha pesquisadores indexados no OpenAlex. Exemplos:
- Universidade de Sao Paulo
- Universidade Federal do Rio de Janeiro
- Universidade Federal de Minas Gerais
- Universidade Estadual de Campinas
- PUC-Rio, etc.

### "E se digitar errado o nome da universidade?"
Sem problema. O programa vai procurar na base de dados e mostrar as opções mais parecidas. Você escolhe qual é a correta.

### "Posso combinar múltiplas áreas de conhecimento?"
Sim! Digite assim: `Computer Science;Information Systems` (separe com ponto-e-vírgula).

### "Quanto tempo leva?"
Depende do tamanho da universidade e do período escolhido:
- 100 pesquisadores, últimos 5 anos: ~3-5 minutos
- 300 pesquisadores, últimos 10 anos: ~10-15 minutos

### "Dá pra baixar SEM internet?"
Não. O programa precisa buscar dados do OpenAlex online (API aberta, gratuita, sem cadastro).

### "Preciso ter o Python instalado?"
Sim, mas só pra rodar isto. Se quiser um executável único (.exe no Windows), avise que a gente gera com PyInstaller.

---

## 📖 Para Entender os Resultados

Veja o arquivo **`KPI_DOCUMENTACAO.md`** que explica em linguagem simples:
- O que são as "comunidades" detectadas
- Cada métrica (centralidade, intermediação, densidade)
- Como interpretar os gráficos

---

## 🐛 Se der erro

1. Tente de novo — às vezes a API do OpenAlex está lenta
2. Verifique se tem internet
3. Tente uma universidade menor (menos pesquisadores) e um período menor (ex: últimos 2 anos)
4. Se continuar, abra um **issue** no repositório

---

## 💾 Onde os arquivos ficam salvos?

Tudo fica na mesma pasta do programa (`grafo_colaboracao_*.*`). 

Você pode:
- Copiar os arquivos pra outro lugar
- Mudar o nome dos outputs no formulário

---

## 📧 Feedback

Se tem ideias, encontrou um bug, ou quer mais funcionalidades, avise!

---

**Divirta-se explorando suas redes de colaboração científica!** 🎉
