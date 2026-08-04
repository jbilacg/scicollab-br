# ✅ Checklist de Download — Arquivos Necessários

Antes de rodar qualquer coisa, certifique-se de ter baixado **TODOS** estes arquivos do projeto:

---

## 🔴 **OBRIGATÓRIOS** (sem estes não roda nada)

- [ ] `gui_openalex.py` — Interface gráfica (Tkinter)
- [ ] `openalex_colab.py` — Script principal de análise
- [ ] `requirements.txt` — Lista de dependências (pip)

Verifique se eles estão **na mesma pasta** que você está.

---

## 🟡 **Para Gerar Executável** (opcional, mas recomendado)

- [ ] `build_exe.py` — Script que gera o `.exe`
- [ ] `verificar_ambiente.py` — Verifica se tudo está certo antes de compilar

---

## 🟢 **Documentação** (recomendado ler)

- [ ] `COMECE_AQUI.md` — Guia para usuários finais
- [ ] `BUILD_EXECUTAVEL.md` — Como gerar `.exe` e `setup.exe`
- [ ] `KPI_DOCUMENTACAO.md` — Explicação de cada métrica
- [ ] `PROJETO_RESUMO.md` — Resumo técnico do projeto

---

## 🔵 **Para Instalador Profissional** (opcional)

- [ ] `setup_grafo.nsi` — Template NSIS para setup.exe

---

## 📋 Passo a Passo Completo

### 1️⃣ Baixar os Arquivos

Baixe do repositório ou do link fornecido:

```
grafo_colaboracao/
├── gui_openalex.py              ← OBRIGATÓRIO
├── openalex_colab.py            ← OBRIGATÓRIO
├── requirements.txt             ← OBRIGATÓRIO
├── build_exe.py                 ← Recomendado
├── verificar_ambiente.py        ← Recomendado
├── COMECE_AQUI.md               ← Leia!
├── BUILD_EXECUTAVEL.md          ← Leia!
└── setup_grafo.nsi              ← Opcional
```

### 2️⃣ Verificar Pasta

Abra o explorador de arquivos e **confirme visualmente** que os 3 arquivos obrigatórios estão lá.

**Caminho esperado** (Windows):
```
C:\Users\SEU_USUARIO\Downloads\grafo_colaboracao\
  ├── gui_openalex.py ✓
  ├── openalex_colab.py ✓
  └── requirements.txt ✓
```

### 3️⃣ Verificar o Ambiente

Abra PowerShell/Terminal naquela pasta e rode:

```bash
python verificar_ambiente.py
```

Deve aparecer:
```
✓ Python 3.11 OK
✓ gui_openalex.py (Interface gráfica) — 15.2 KB
✓ openalex_colab.py (Script principal) — 42.5 KB
✓ requirements.txt (Dependências) — 0.1 KB
✓ requests instalado
✓ networkx instalado
[... mais dependências ...]
✓ PyInstaller 6.1.0 instalado
✓ 50.25 GB livres

✓ AMBIENTE PRONTO!
```

Se aparecer **❌** em qualquer coisa, leia a solução mostrada.

### 4️⃣ Gerar Executável

```bash
python build_exe.py
```

Aguarde 5-15 minutos. Ao final:

```
✓ Executável gerado com sucesso!
Arquivo gerado:
  C:\...\grafo_colaboracao\dist\Grafo de Colaboracao.exe
  Tamanho: 150.5 MB
```

### 5️⃣ Testar

1. Vá para a pasta `dist/`
2. Clique em `Grafo de Colaboracao.exe`
3. A interface gráfica deve abrir

---

## 🆘 Erros Comuns e Soluções

### Erro: "Arquivo gui_openalex.py não encontrado"

**Causa**: O arquivo não foi baixado ou está em pasta diferente.

**Solução**:
1. Confirme visualmente que `gui_openalex.py` existe na pasta
2. Se não existe, baixe de novo do repositório
3. Certifique-se de extrair o ZIP completamente (não tente rodar de dentro do ZIP)

### Erro: "PyInstaller não encontrado"

**Causa**: PyInstaller não foi instalado.

**Solução**:
```bash
pip install pyinstaller
```

Então rode `verificar_ambiente.py` de novo.

### Erro: "requirements.txt não encontrado"

**Causa**: O arquivo não foi baixado.

**Solução**:
1. Baixe `requirements.txt` do repositório
2. Coloque na mesma pasta que `gui_openalex.py`

### Erro: "Apenas 0.5 GB livres"

**Causa**: Espaço em disco insuficiente.

**Solução**: Libere espaço (o `.exe` vai ter ~150 MB + arquivos temporários).

---

## 📦 Onde Baixar

**Opção 1: GitHub**
```
https://github.com/[seu-usuario]/grafo_colaboracao
→ Code → Download ZIP
```

**Opção 2: Link fornecido**
Clique no link que foi mandado para você.

**Opção 3: Dropbox / Google Drive**
Acesse o compartilhamento que foi enviado.

---

## ✅ Verificação Final

Antes de rodar `build_exe.py`, execute este checklist:

- [ ] Pasta contém os 3 arquivos obrigatórios
- [ ] `python --version` mostra 3.9+
- [ ] `python verificar_ambiente.py` mostra ✓ em tudo
- [ ] Tenho pelo menos 1 GB livre em disco
- [ ] Tenho internet (para baixar dependências se necessário)

Se todos os checkboxes marcados → está pronto!

---

## 🎉 Sucesso!

Se chegou aqui e `python verificar_ambiente.py` mostrou ✓ em tudo, parabéns!

Agora é só rodar:
```bash
python build_exe.py
```

E seu `.exe` estará pronto em alguns minutos! 🚀
