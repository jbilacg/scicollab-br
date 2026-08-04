# 🛠️ Como Gerar Executável e Instalador

Guia passo-a-passo para criar:
1. **Executável único** (`Grafo de Colaboracao.exe`) — sem precisar de Python
2. **Instalador profissional** (`setup_grafo.exe`) — com menu Iniciar, atalhos, desinstalador

---

## 📋 Pré-requisitos

### Windows
- Python 3.9+ instalado (já tem? teste: `python --version`)
- Conexão com internet (para baixar dependências)

### Teste Rápido
```bash
python --version
pip --version
```

Se der erro, instale Python de https://python.org (recomendado: 3.11 ou 3.12)

---

## 🔧 Passo 1: Preparar o Ambiente (5 minutos)

### 1a. Abra o terminal na pasta do projeto

No Windows:
- Clique com botão direito na pasta `grafo_colaboracao`
- Escolha "Abrir PowerShell aqui" (ou "Abrir cmd aqui")

### 1b. Instale dependências

```bash
pip install -r requirements.txt
pip install pyinstaller
```

**Isso vai:**
- Instalar todas as bibliotecas (requests, networkx, etc.)
- Instalar PyInstaller (que gera o .exe)

Vai demorar ~2-5 minutos na primeira vez.

---

## 🚀 Passo 2: Gerar o Executável Único (10-15 minutos)

No mesmo terminal, execute:

```bash
python build_exe.py
```

**Isso vai:**
- Compilar a GUI (gui_openalex.py) em um arquivo .exe
- Incluir todas as dependências dentro do .exe
- Criar a pasta `dist/` com o executável

**Saída esperada:**
```
✓ PyInstaller X.X encontrado
Gerando executável Windows (.exe)...
Isso pode levar 2-5 minutos na primeira vez...
[PyInstaller output aqui...]
✓ Executável gerado com sucesso!
Arquivo gerado:
  C:\...\grafo_colaboracao\dist\Grafo de Colaboracao.exe
  Tamanho: 150.5 MB
```

### Teste o executável

1. Navegue até `dist/`
2. Clique em `Grafo de Colaboracao.exe`
3. A interface gráfica deve abrir normalmente

✓ Pronto! Você já tem um executável que funciona **sem Python instalado**.

---

## 📦 Passo 3: Distribuir o Executável (Opção Simples)

Se você só quer distribuir o `.exe` direto:

### Opção A: Arquivo único
1. Compacte a pasta `dist/` → `Grafo_de_Colaboracao.zip` (~150 MB)
2. Mande por email, Dropbox, Google Drive, etc.
3. Usuário extrai e clica no `.exe`

### Opção B: Com documentação
1. Crie uma pasta `Grafo_de_Colaboracao_v1.0/`
2. Copie `dist/Grafo de Colaboracao.exe` para lá
3. Copie `COMECE_AQUI.md` para lá também
4. Compacte tudo → `Grafo_de_Colaboracao_v1.0.zip`
5. Distribua

---

## 🎯 Passo 4: Gerar Instalador Profissional (Opcional, 10 minutos)

Se quer um instalador de verdade com Setup.exe (como programas normais):

### 4a. Instale NSIS

Baixe de https://nsis.sourceforge.io/Download

Windows vai instalar em: `C:\Program Files (x86)\NSIS\`

### 4b. Compile o instalador

No terminal, na pasta do projeto:

```bash
"C:\Program Files (x86)\NSIS\makensis.exe" setup_grafo.nsi
```

Ou mais fácil: abra o arquivo `setup_grafo.nsi` com o NSIS e clique em "Compile NSI Script".

**Resultado:**
```
setup_grafo.exe (~5-10 MB)
```

### 4c. Teste o instalador

Clique em `setup_grafo.exe`:
- Mostra tela de boas-vindas
- Pergunta onde instalar (padrão: C:\Program Files\GrafoColaboracao)
- Cria atalhos no Desktop e menu Iniciar
- Oferece desinstalar depois

---

## 📊 Comparação: Qual Distribuir?

| Opção | Tamanho | Facilidade | Profissional |
|-------|---------|-----------|--------------|
| `.exe` só | ~150 MB | ⭐⭐⭐ Muito fácil | ⭐⭐ OK |
| `.exe` + docs | ~150 MB | ⭐⭐⭐ Muito fácil | ⭐⭐ OK |
| `setup.exe` | ~5-10 MB | ⭐⭐⭐ Instala normal | ⭐⭐⭐⭐⭐ Pro |

**Recomendação:**
- Para distribuição **rápida** → compacte `dist/Grafo de Colaboracao.exe`
- Para distribuição **profissional** → use `setup_grafo.exe`

---

## 🔄 Atualizações Futuras

Se você corrigir bugs ou adicionar funcionalidades no código:

1. **Edite** `gui_openalex.py` ou `openalex_colab.py`
2. **Rode** `python build_exe.py` de novo
3. **Distribua** a nova versão do `dist/Grafo de Colaboracao.exe`

---

## 🐛 Troubleshooting

### "PyInstaller não encontrado"
```bash
pip install pyinstaller
```

### "NSIS não encontrado"
Instale de https://nsis.sourceforge.io/Download

### "Erro durante compilação PyInstaller"
1. Certifique-se de que todas as dependências foram instaladas: `pip install -r requirements.txt`
2. Feche qualquer aplicação antivírus temporariamente
3. Tente rodar como administrador (clique direito → "Executar como administrador")

### ".exe não abre"
1. Verifique se o arquivo foi gerado: `ls dist/` (ou abra a pasta em Explorer)
2. Tente rodar pelo terminal: `dist\Grafo de Colaboracao.exe`
3. Se der erro, copie a saída do erro e avise

### "Arquivo muito grande"
Sim, o `.exe` tem ~150 MB porque inclui Python + todas as bibliotecas dentro dele. É normal.

---

## 📝 Resumo Visual

```
Código Python
  ↓
[python build_exe.py]
  ↓
PyInstaller compila
  ↓
dist/Grafo de Colaboracao.exe (~150 MB)
  ↓
[Opcional: NSIS compila]
  ↓
setup_grafo.exe (~5-10 MB) ← Instalador profissional
```

---

## ✅ Checklist de Distribuição

- [ ] Testei o `.exe` localmente (funciona?)
- [ ] Testei o `setup.exe` (instala e desinstala corretamente?)
- [ ] Copiei documentação junto (COMECE_AQUI.md, etc.)
- [ ] Compactei tudo em ZIP
- [ ] Testei extrair o ZIP e rodar de novo (tudo funciona?)
- [ ] Fiz upload/enviei para os usuários
- [ ] Avisei aos usuários para extrair antes de rodar

---

## 🎉 Pronto!

Agora seus usuários podem:
- **Executar** sem ter Python instalado
- **Instalar** profissionalmente como qualquer programa Windows
- **Desinstalar** normalmente via "Adicionar/Remover Programas"

Sucesso! 🚀
