# Instalação — Grafo de Colaboração Científica (OpenAlex)

## Pré-requisito

- **Python 3.9 ou superior** instalado.
  Verifique com:
  ```bash
  python3 --version
  ```

## Instalação das dependências

### Opção 1 — usando requirements.txt (recomendado)

Na mesma pasta do arquivo `openalex_colab.py` e `requirements.txt`, rode:

```bash
pip install -r requirements.txt
```

### Opção 2 — instalando manualmente, uma por uma

```bash
pip install requests networkx python-louvain pyvis matplotlib
```

## O que cada dependência faz

| Biblioteca | Para que serve |
|---|---|
| `requests` | Faz as chamadas HTTP para a API do OpenAlex |
| `networkx` | Constrói e analisa o grafo de colaboração (centralidade, componentes, etc.) |
| `python-louvain` | Detecta comunidades de colaboração (algoritmo Louvain) |
| `pyvis` | Gera a visualização interativa do grafo em HTML |
| `matplotlib` | Gera os gráficos descritivos (barras, histogramas, dispersão) |

Todas são de uso livre e gratuito — não é preciso nenhuma chave de API paga.

## Ambiente virtual (opcional, mas recomendado)

Para não misturar essas dependências com outros projetos Python na sua máquina:

```bash
# criar o ambiente
python3 -m venv venv

# ativar (Linux/Mac)
source venv/bin/activate

# ativar (Windows)
venv\Scripts\activate

# instalar as dependências dentro do ambiente
pip install -r requirements.txt
```

Para sair do ambiente virtual depois: `deactivate`

## Problemas comuns

**Erro `pip: command not found`**
Use `pip3` no lugar de `pip`, ou `python3 -m pip install -r requirements.txt`.

**Erro de permissão ao instalar (`Permission denied`)**
Não use `sudo pip install`. Prefira o ambiente virtual acima, ou instale só para o seu usuário:
```bash
pip install --user -r requirements.txt
```

**PyCharm/VSCode não reconhece as bibliotecas depois de instaladas**
Verifique se o interpretador Python selecionado na IDE é o mesmo onde você rodou o `pip install` (especialmente se estiver usando ambiente virtual — selecione o interpretador dentro da pasta `venv`).

## Testando se está tudo certo

Depois de instalar, rode:

```bash
python3 -c "import requests, networkx, community, pyvis, matplotlib; print('Tudo certo!')"
```

Se aparecer `Tudo certo!` sem erros, as dependências estão prontas e você já pode rodar o `openalex_colab.py`.
