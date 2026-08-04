#!/usr/bin/env python3
"""
gui_openalex.py

Interface gráfica (Tkinter) para openalex_colab.py.
Permite rodar a análise de grafo de colaboração sem tocar no terminal.

Uso:
  python3 gui_openalex.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading
import traceback
from pathlib import Path

# Importado no topo para que o PyInstaller inclua o módulo no executável.
import openalex_colab

# ------------------------------------------------------------
# Áreas de conhecimento sugeridas (mesma lista do openalex_colab)
# ------------------------------------------------------------
OPENALEX_COMMON_FIELDS = [
    "Agricultural and Biological Sciences",
    "Arts and Humanities",
    "Biochemistry, Genetics and Molecular Biology",
    "Business, Management and Accounting",
    "Chemical Engineering",
    "Chemistry",
    "Computer Science",
    "Decision Sciences",
    "Dentistry",
    "Earth and Planetary Sciences",
    "Economics, Econometrics and Finance",
    "Education",
    "Energy",
    "Engineering",
    "Environmental Science",
    "Health Professions",
    "Immunology and Microbiology",
    "Library and Information Science",
    "Materials Science",
    "Mathematics",
    "Medicine",
    "Neuroscience",
    "Nursing",
    "Pharmacology, Toxicology and Pharmaceutics",
    "Physics and Astronomy",
    "Psychology",
    "Social Sciences",
    "Veterinary",
]

OPENALEX_BASE = "https://api.openalex.org"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_results_dir() -> Path:
    d = get_app_dir() / "resultados"
    d.mkdir(exist_ok=True)
    return d


class TextRedirector:
    """Redireciona stdout/stderr para um widget Text do Tkinter (thread-safe)."""

    def __init__(self, widget: tk.Text):
        self.widget = widget

    def write(self, text: str):
        if text:
            self.widget.after(0, self._insert, text)

    def _insert(self, text: str):
        try:
            self.widget.insert(tk.END, text)
            self.widget.see(tk.END)
        except tk.TclError:
            pass

    def flush(self):
        pass


# ------------------------------------------------------------
# Verificador de dependências
# ------------------------------------------------------------

class DependencyInstaller:

    DEPENDENCIES = {
        "requests": "requests",
        "networkx": "networkx",
        "community": "python-louvain",
        "pyvis": "pyvis",
        "matplotlib": "matplotlib",
    }

    @staticmethod
    def check_and_install(root: tk.Tk) -> bool:
        if getattr(sys, "frozen", False):
            return True

        missing = [
            (mod, pkg)
            for mod, pkg in DependencyInstaller.DEPENDENCIES.items()
            if not _can_import(mod)
        ]
        if not missing:
            return True

        msg = "Dependências faltando:\n\n"
        msg += "\n".join(f"  • {pkg} (módulo: {mod})" for mod, pkg in missing)
        msg += "\n\nDeseja instalar automaticamente agora?"

        if messagebox.askyesno("Dependências", msg):
            return DependencyInstaller._install(missing, root)

        messagebox.showerror(
            "Dependências",
            "Não é possível continuar sem as dependências.\n\n"
            "Para instalar manualmente:\n"
            "pip install -r requirements.txt",
        )
        return False

    @staticmethod
    def _install(packages, root: tk.Tk) -> bool:
        win = tk.Toplevel(root)
        win.title("Instalando Dependências")
        win.geometry("520x320")

        ttk.Label(win, text="Instalando pacotes...", font=("Arial", 12)).pack(pady=15)
        bar = ttk.Progressbar(win, mode="indeterminate")
        bar.pack(pady=5, padx=20, fill=tk.X)
        bar.start()
        txt = tk.Text(win, height=10, width=62)
        txt.pack(pady=8, padx=10, fill=tk.BOTH, expand=True)
        win.update()

        cmd = [sys.executable, "-m", "pip", "install"] + [p for _, p in packages]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            txt.insert(tk.END, result.stdout)
            if result.returncode != 0:
                txt.insert(tk.END, f"\nErro:\n{result.stderr}")
                messagebox.showerror("Instalação", "Erro ao instalar dependências.")
                win.destroy()
                return False
            txt.insert(tk.END, "\n✓ Instalação concluída!")
        except Exception as exc:
            txt.insert(tk.END, f"Erro: {exc}")
            messagebox.showerror("Instalação", f"Erro: {exc}")
            win.destroy()
            return False

        win.after(2500, win.destroy)
        return True


def _can_import(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


# ------------------------------------------------------------
# Interface principal
# ------------------------------------------------------------

class OpenAlexGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Grafo de Colaboração Científica — OpenAlex")
        self.root.geometry("880x1020")
        self.root.resizable(True, True)

        self.results_dir = get_results_dir()
        self.output_files: list[str] = []

        # Estado da busca de instituições
        self._inst_results: list[dict] = []   # resultados da API
        self._selected_inst: dict = {}         # {"id": ..., "name": ...}

        self._build_ui()

    # ----------------------------------------------------------
    # Construção da interface
    # ----------------------------------------------------------

    def _build_ui(self):
        ttk.Label(
            self.root,
            text="Grafo de Colaboração Científica via OpenAlex",
            font=("Arial", 14, "bold"),
        ).pack(pady=(16, 2))
        ttk.Label(
            self.root,
            text="Visualize redes de coautoria entre pesquisadores",
            font=("Arial", 10),
            foreground="gray",
        ).pack()

        outer = ttk.Frame(self.root)
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        self._canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._form_frame = ttk.Frame(self._canvas)

        self._form_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        form_window = self._canvas.create_window((0, 0), window=self._form_frame, anchor="nw")
        # Mantém o formulário esticado na largura total do canvas — sem isso,
        # ao maximizar/redimensionar a janela o conteúdo fica ancorado à
        # esquerda com um vão vazio do lado (o canvas cresce, o frame não).
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(form_window, width=e.width),
        )
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Scroll do mouse só ativo enquanto o cursor está sobre este canvas
        # (bind local, não bind_all — evita vazar para outras janelas).
        self._canvas.bind(
            "<Enter>",
            lambda e: self._canvas.bind_all(
                "<MouseWheel>",
                lambda ev: self._canvas.yview_scroll(-1 * (ev.delta // 120), "units"),
            ),
        )
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._build_form(self._form_frame)

        btn_bar = ttk.Frame(self.root)
        btn_bar.pack(pady=14, fill=tk.X, padx=20)
        ttk.Button(btn_bar, text="▶  Executar Análise", command=self._run).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_bar, text="📁  Ver Resultados",  command=self._open_results).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="❓  Ajuda",           command=self._help).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="✕  Sair",            command=self.root.quit).pack(side=tk.RIGHT, padx=8)

    # helpers de layout ----------------------------------------

    def _section(self, parent, title: str) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text=title, padding=(10, 6))
        f.pack(fill=tk.X, pady=6, padx=4)
        return f

    def _hint(self, parent, text: str):
        ttk.Label(parent, text=text, font=("Arial", 8), foreground="gray").pack(
            anchor=tk.W, padx=4
        )

    def _center_on_root(self, win: tk.Toplevel, width: int, height: int):
        """Centraliza uma janela secundária sobre a janela principal (em vez
        de deixá-la cair no canto da tela, parecendo um app separado)."""
        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        x = rx + max(0, (rw - width) // 2)
        y = ry + max(0, (rh - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    # ----------------------------------------------------------
    # Formulário
    # ----------------------------------------------------------

    def _build_form(self, parent):
        self.fields: dict = {}

        self._build_institution_section(parent)
        self._build_topic_section(parent)
        self._build_period_section(parent)
        self._build_limits_section(parent)
        self._build_options_section(parent)

    # ---- Seção 1: Instituição --------------------------------

    def _build_institution_section(self, parent):
        sec = self._section(parent, "1. Universidade / Instituição  (obrigatório)")

        # Barra de busca
        search_row = ttk.Frame(sec)
        search_row.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(search_row, text="Buscar:", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self._inst_search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_row, textvariable=self._inst_search_var, width=52, font=("Arial", 10)
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<Return>", lambda e: self._search_institutions())

        self._inst_search_btn = ttk.Button(
            search_row, text="🔍 Buscar", command=self._search_institutions
        )
        self._inst_search_btn.pack(side=tk.LEFT, padx=(6, 0))

        self._hint(sec, "Digite o nome da universidade e clique em Buscar (ou pressione Enter)")

        # Listbox de resultados
        lb_frame = ttk.Frame(sec)
        lb_frame.pack(fill=tk.X, pady=(6, 2))

        lb_scroll = ttk.Scrollbar(lb_frame)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._inst_listbox = tk.Listbox(
            lb_frame,
            height=5,
            yscrollcommand=lb_scroll.set,
            font=("Arial", 10),
            activestyle="dotbox",
            selectbackground="#1a7abf",
            selectforeground="white",
        )
        self._inst_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lb_scroll.config(command=self._inst_listbox.yview)
        self._inst_listbox.bind("<<ListboxSelect>>", self._on_institution_select)

        self._inst_listbox.insert(tk.END, "← Digite um nome acima e clique em Buscar")
        self._inst_listbox.config(state=tk.DISABLED)

        # Exibe a instituição selecionada
        sel_row = ttk.Frame(sec)
        sel_row.pack(fill=tk.X, pady=(6, 2))

        ttk.Label(sel_row, text="Selecionada:", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self._inst_selected_var = tk.StringVar(value="(nenhuma)")
        ttk.Label(
            sel_row,
            textvariable=self._inst_selected_var,
            font=("Arial", 10),
            foreground="#1a7abf",
            wraplength=600,
        ).pack(side=tk.LEFT)

        # Campo oculto que guarda o nome para a análise
        self.fields["institution"] = tk.StringVar()

    # ---- Seção 2: Área de conhecimento -----------------------

    def _build_topic_section(self, parent):
        sec = self._section(
            parent, "2. Área de Conhecimento  (opcional — deixe em branco para toda a universidade)"
        )

        ttk.Label(
            sec,
            text="Clique para selecionar uma área  •  Ctrl+clique para selecionar várias",
            font=("Arial", 9),
            foreground="#444",
        ).pack(anchor=tk.W, pady=(0, 4))

        lb_frame = ttk.Frame(sec)
        lb_frame.pack(fill=tk.X)

        lb_scroll = ttk.Scrollbar(lb_frame)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._topic_listbox = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            height=8,
            exportselection=False,
            yscrollcommand=lb_scroll.set,
            font=("Arial", 10),
            activestyle="dotbox",
            selectbackground="#1a7abf",
            selectforeground="white",
        )
        for field in OPENALEX_COMMON_FIELDS:
            self._topic_listbox.insert(tk.END, field)
        self._topic_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lb_scroll.config(command=self._topic_listbox.yview)

        ttk.Button(sec, text="Limpar seleção", command=self._clear_topic_sel).pack(
            anchor=tk.W, pady=(4, 8)
        )

        ttk.Label(
            sec,
            text="Ou digite livremente (separe múltiplas áreas com  ;  )",
            font=("Arial", 9),
            foreground="#444",
        ).pack(anchor=tk.W)
        self._hint(sec, "Ex: Bibliometrics   |   Computer Science;Information Systems")

        self.fields["topic"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["topic"], width=72).pack(
            anchor=tk.W, padx=4, fill=tk.X, pady=(2, 8)
        )

        # Topic IDs avançado
        ttk.Label(sec, text="Topic IDs diretos (avançado):", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self._hint(sec, "Cole IDs do OpenAlex separados por vírgula — tem prioridade sobre as seleções acima")
        self._hint(sec, "Ex: T10712,T14330")
        self.fields["topic_id"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["topic_id"], width=72).pack(
            anchor=tk.W, padx=4, fill=tk.X, pady=(2, 0)
        )

    # ---- Seção 3: Período ------------------------------------

    def _build_period_section(self, parent):
        sec = self._section(parent, "3. Período  (opcional)")
        row = ttk.Frame(sec)
        row.pack(fill=tk.X)

        ttk.Label(row, text="Ano Inicial:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 6))
        self.fields["year_from"] = tk.StringVar()
        ttk.Entry(row, textvariable=self.fields["year_from"], width=8).pack(side=tk.LEFT)

        ttk.Label(row, text="   Ano Final:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(14, 6))
        self.fields["year_to"] = tk.StringVar()
        ttk.Entry(row, textvariable=self.fields["year_to"], width=8).pack(side=tk.LEFT)

        self._hint(sec, "Deixe em branco para considerar todos os anos")

    # ---- Seção 4: Limites ------------------------------------

    def _build_limits_section(self, parent):
        sec = self._section(parent, "4. Limites de Coleta")
        row = ttk.Frame(sec)
        row.pack(fill=tk.X)

        ttk.Label(row, text="Máx. pesquisadores:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 6))
        self.fields["max_authors"] = tk.IntVar(value=100)
        ttk.Spinbox(row, from_=1, to=5000, textvariable=self.fields["max_authors"], width=7).pack(side=tk.LEFT)

        ttk.Label(row, text="   Máx. publicações/pesquisador:", font=("Arial", 10)).pack(
            side=tk.LEFT, padx=(14, 6)
        )
        self.fields["max_works"] = tk.IntVar(value=50)
        ttk.Spinbox(row, from_=1, to=500, textvariable=self.fields["max_works"], width=7).pack(side=tk.LEFT)

    # ---- Seção 5: Opções -------------------------------------

    def _build_options_section(self, parent):
        sec = self._section(parent, "5. Opções")

        r = ttk.Frame(sec)
        r.pack(fill=tk.X, pady=3)
        self.fields["restrict"] = tk.BooleanVar()
        ttk.Checkbutton(r, variable=self.fields["restrict"]).pack(side=tk.LEFT)
        ttk.Label(
            r,
            text="Restringir a colaborações internas  (excluir coautores externos à universidade)",
            font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=6)

        ttk.Label(sec, text="Nome dos arquivos de saída:", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, pady=(8, 0)
        )
        self._hint(sec, "Padrão: grafo_colaboracao")
        self.fields["output"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["output"], width=40).pack(anchor=tk.W, padx=4)

        ttk.Label(
            sec,
            text=f"Arquivos serão salvos em:  {self.results_dir}",
            font=("Arial", 9),
            foreground="#1a7abf",
        ).pack(anchor=tk.W, pady=(8, 2))

        ttk.Separator(sec, orient="horizontal").pack(fill=tk.X, pady=(10, 6))

        ttk.Label(sec, text="Seu e-mail (recomendado):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self._hint(sec, "Fornecido ao OpenAlex para acesso à 'polite pool' — aumenta limite de requisições e reduz erros 429")
        self._hint(sec, "Ex: nome@universidade.br")
        self.fields["email"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["email"], width=50).pack(anchor=tk.W, padx=4, pady=(2, 0))

    # ----------------------------------------------------------
    # Busca de instituições (thread separada)
    # ----------------------------------------------------------

    def _search_institutions(self):
        query = self._inst_search_var.get().strip()
        if not query:
            messagebox.showinfo("Busca", "Digite um nome para buscar.")
            return

        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_listbox.insert(tk.END, "Buscando...")
        self._inst_listbox.config(state=tk.DISABLED)
        self._inst_search_btn.config(state=tk.DISABLED)

        threading.Thread(
            target=self._fetch_institutions_thread, args=(query,), daemon=True
        ).start()

    def _fetch_institutions_thread(self, query: str):
        """
        Busca instituições com estratégia em camadas para maximizar os resultados:
          1. Autocomplete com a query original  (endpoint otimizado para busca parcial)
          2. Autocomplete com a query sem acentos/diacríticos
          3. Search normal com a query original  (fallback)
          4. Search normal sem acentos           (fallback final)
        """
        import requests
        import unicodedata

        def strip_accents(s: str) -> str:
            """Remove acentos e diacríticos: 'São Paulo' → 'Sao Paulo'."""
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )

        def normalize(raw: list) -> list:
            """Uniformiza campos entre o retorno do autocomplete e do search."""
            out = []
            for r in raw:
                if "hint" in r:          # formato autocomplete
                    hint = r.get("hint", "")
                    # hint costuma ser "Cidade, PAÍS" ou só "PAÍS"
                    country = hint.rsplit(",", 1)[-1].strip() if "," in hint else hint.strip()
                    out.append({
                        "id":           r["id"],
                        "display_name": r["display_name"],
                        "country_code": country,
                        "works_count":  r.get("works_count", 0),
                    })
                else:                    # formato search normal
                    out.append(r)
            return out

        try:
            stripped = strip_accents(query)
            queries  = [query] if stripped == query else [query, stripped]

            results = []

            # Fase 1 e 2: autocomplete (mais tolerante a buscas parciais)
            for q in queries:
                resp = requests.get(
                    f"{OPENALEX_BASE}/autocomplete/institutions",
                    params={"q": q, "mailto": openalex_colab.POLITE_EMAIL},
                    timeout=12,
                )
                if resp.ok:
                    raw = resp.json().get("results", [])
                    if raw:
                        results = normalize(raw)
                        break

            # Fase 3 e 4: search normal (fallback)
            if not results:
                for q in queries:
                    resp = requests.get(
                        f"{OPENALEX_BASE}/institutions",
                        params={
                            "search":   q,
                            "per_page": 10,
                            "mailto":   openalex_colab.POLITE_EMAIL,
                        },
                        timeout=12,
                    )
                    if resp.ok:
                        raw = resp.json().get("results", [])
                        if raw:
                            results = normalize(raw)
                            break

            self.root.after(0, self._update_inst_listbox, results)

        except Exception as exc:
            self.root.after(0, self._inst_search_error, str(exc))

    def _update_inst_listbox(self, results: list):
        self._inst_results = results
        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_search_btn.config(state=tk.NORMAL)

        if not results:
            self._inst_listbox.insert(
                tk.END,
                "Nenhum resultado. Tente o nome em inglês, sem abreviações ou sem acentos.",
            )
            return

        for r in results:
            country = r.get("country_code", "?")
            works   = r.get("works_count", 0)
            name    = r.get("display_name", "?")
            self._inst_listbox.insert(
                tk.END, f"{name}  ({country})  —  {works:,} publicações"
            )

    def _inst_search_error(self, msg: str):
        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_listbox.insert(tk.END, f"Erro na busca: {msg}")
        self._inst_search_btn.config(state=tk.NORMAL)

    def _on_institution_select(self, event):
        sel = self._inst_listbox.curselection()
        if not sel or not self._inst_results:
            return
        idx = sel[0]
        if idx >= len(self._inst_results):
            return
        r = self._inst_results[idx]
        self._selected_inst = {"id": r["id"], "name": r["display_name"]}
        self.fields["institution"].set(r["display_name"])
        country = r.get("country_code", "?")
        works   = r.get("works_count", 0)
        self._inst_selected_var.set(
            f"{r['display_name']}  ({country})  —  {works:,} publicações"
        )

    # ----------------------------------------------------------
    # Helpers de formulário
    # ----------------------------------------------------------

    def _clear_topic_sel(self):
        self._topic_listbox.selection_clear(0, tk.END)

    def _validate(self) -> bool:
        if not self.fields["institution"].get().strip():
            messagebox.showerror(
                "Validação",
                "Selecione uma universidade usando a busca acima.",
            )
            return False
        for key in ("year_from", "year_to"):
            val = self.fields[key].get().strip()
            if val:
                try:
                    int(val)
                except ValueError:
                    messagebox.showerror("Validação", "O campo de ano deve ser um número inteiro.")
                    return False
        return True

    def _collect_params(self) -> dict:
        lb_sel    = [self._topic_listbox.get(i) for i in self._topic_listbox.curselection()]
        txt_topics = [t.strip() for t in self.fields["topic"].get().split(";") if t.strip()]
        all_topics = lb_sel + [t for t in txt_topics if t not in lb_sel]

        return {
            "institution": self.fields["institution"].get().strip(),
            "institution_id": self._selected_inst.get("id", ""),
            "topic_id":    self.fields["topic_id"].get().strip(),
            "topic":       ";".join(all_topics),
            "year_from":   self.fields["year_from"].get().strip() or None,
            "year_to":     self.fields["year_to"].get().strip() or None,
            "max_authors": int(self.fields["max_authors"].get()),
            "max_works":   int(self.fields["max_works"].get()),
            "restrict":    bool(self.fields["restrict"].get()),
            "output":      self.fields["output"].get().strip() or "grafo_colaboracao",
            "email":       self.fields["email"].get().strip(),
        }

    # ----------------------------------------------------------
    # Execução da análise
    # ----------------------------------------------------------

    def _run(self):
        if not self._validate():
            return

        params = self._collect_params()

        # Se há termos de área (sem IDs diretos), mostra o diálogo de seleção
        # de topics antes de iniciar a análise, para que o usuário confirme
        # quais subtopics incluir.
        if params["topic"] and not params["topic_id"]:
            terms = [t.strip() for t in params["topic"].split(";") if t.strip()]
            self._fetch_topics_then_dialog(terms, params)
        else:
            # IDs diretos ou sem filtro de área: inicia imediatamente
            params["_resolved_topic_ids"] = None
            self._open_progress_and_run(params)

    def _fetch_topics_then_dialog(self, terms: list, params: dict):
        """Busca os topics na API (em thread) e depois abre o diálogo de seleção."""
        loading = tk.Toplevel(self.root)
        loading.title("Buscando áreas…")
        loading.resizable(False, False)
        self._center_on_root(loading, 380, 110)
        ttk.Label(
            loading, text="Consultando OpenAlex, aguarde…", font=("Arial", 10)
        ).pack(pady=(18, 6))
        bar = ttk.Progressbar(loading, mode="indeterminate")
        bar.pack(padx=24, fill=tk.X)
        bar.start()
        loading.update()

        def fetch():
            import requests
            results_by_term: dict[str, list] = {}
            for term in terms:
                try:
                    resp = requests.get(
                        f"{OPENALEX_BASE}/topics",
                        params={
                            "search": term,
                            "per_page": 10,
                            "mailto": openalex_colab.POLITE_EMAIL,
                        },
                        timeout=12,
                    )
                    results_by_term[term] = resp.json().get("results", []) if resp.ok else []
                except Exception:
                    results_by_term[term] = []
            self.root.after(
                0, lambda: self._on_topics_fetched(loading, results_by_term, params)
            )

        threading.Thread(target=fetch, daemon=True).start()

    def _on_topics_fetched(
        self, loading: tk.Toplevel, results_by_term: dict, params: dict
    ):
        loading.destroy()
        resolved_ids = self._show_topic_selection_dialog(results_by_term)
        if resolved_ids is None:
            return  # usuário cancelou
        params["_resolved_topic_ids"] = resolved_ids or None
        self._open_progress_and_run(params)

    def _show_topic_selection_dialog(self, results_by_term: dict) -> list | None:
        """
        Mostra um diálogo modal com todos os topics encontrados por termo.
        Todos ficam pré-marcados. O usuário pode desmarcar os que não quiser.
        Retorna lista de IDs selecionados, ou None se cancelado.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Selecionar Topics do OpenAlex")
        dialog.resizable(True, True)
        self._center_on_root(dialog, 740, 560)
        dialog.grab_set()   # modal

        result_holder: list[list | None] = [None]
        check_vars: list[tuple[tk.BooleanVar, str, str]] = []  # (var, id, nome)

        # Cabeçalho
        ttk.Label(
            dialog,
            text="Confirme os subtopics que deseja incluir na análise",
            font=("Arial", 11, "bold"),
        ).pack(anchor=tk.W, padx=14, pady=(12, 0))
        ttk.Label(
            dialog,
            text="Todos estão pré-selecionados. Desmarque os que não quiser usar.",
            font=("Arial", 9),
            foreground="gray",
        ).pack(anchor=tk.W, padx=14, pady=(2, 8))

        # Área scrollável
        outer = ttk.Frame(dialog)
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        cvs = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=cvs.yview)
        inner = ttk.Frame(cvs)
        inner.bind(
            "<Configure>",
            lambda e: cvs.configure(scrollregion=cvs.bbox("all")),
        )
        inner_window = cvs.create_window((0, 0), window=inner, anchor="nw")
        cvs.bind("<Configure>", lambda e: cvs.itemconfig(inner_window, width=e.width))
        cvs.configure(yscrollcommand=vsb.set)
        cvs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Scroll do mouse só ligado enquanto o cursor está sobre este canvas,
        # e desligado ao fechar o diálogo — bind_all sem unbind_all fazia o
        # binding sobreviver à destruição do canvas e disparar
        # "_tkinter.TclError: invalid command name" a cada scroll depois.
        cvs.bind(
            "<Enter>",
            lambda e: cvs.bind_all(
                "<MouseWheel>",
                lambda ev: cvs.yview_scroll(-1 * (ev.delta // 120), "units"),
            ),
        )
        cvs.bind("<Leave>", lambda e: cvs.unbind_all("<MouseWheel>"))
        dialog.bind("<Destroy>", lambda e: cvs.unbind_all("<MouseWheel>"))

        # Popula topics por termo de busca
        for term, results in results_by_term.items():
            ttk.Label(
                inner,
                text=f'Área buscada: "{term}"',
                font=("Arial", 10, "bold"),
                foreground="#1a7abf",
            ).pack(anchor=tk.W, padx=6, pady=(10, 2))

            if not results:
                ttk.Label(
                    inner,
                    text="  Nenhum topic encontrado para este termo.",
                    font=("Arial", 9),
                    foreground="gray",
                ).pack(anchor=tk.W, padx=22)
                continue

            for r in results:
                var = tk.BooleanVar(value=True)  # pré-marcado
                tid  = r["id"]
                name = r["display_name"]
                subfield = r.get("subfield", {}).get("display_name", "?")
                field    = r.get("field",    {}).get("display_name", "?")
                domain   = r.get("domain",   {}).get("display_name", "?")
                works    = r.get("works_count", 0)

                check_vars.append((var, tid, name))

                row = ttk.Frame(inner)
                row.pack(fill=tk.X, padx=14, pady=2)

                ttk.Checkbutton(row, variable=var).pack(side=tk.LEFT, padx=(0, 4))

                info_frame = ttk.Frame(row)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                ttk.Label(
                    info_frame,
                    text=name,
                    font=("Arial", 10, "bold"),
                ).pack(anchor=tk.W)
                ttk.Label(
                    info_frame,
                    text=f"  {domain} › {field} › {subfield}   —   {works:,} publicações",
                    font=("Arial", 8),
                    foreground="#555",
                ).pack(anchor=tk.W)

                ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, padx=14, pady=1)

        # Botões
        btn_row = ttk.Frame(dialog)
        btn_row.pack(fill=tk.X, padx=12, pady=10)

        def on_ok():
            result_holder[0] = [tid for var, tid, _ in check_vars if var.get()]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()  # result_holder permanece None

        ttk.Button(
            btn_row, text="✓  Confirmar e executar", command=on_ok
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_row,
            text="Marcar tudo",
            command=lambda: [v.set(True) for v, _, _ in check_vars],
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_row,
            text="Desmarcar tudo",
            command=lambda: [v.set(False) for v, _, _ in check_vars],
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Cancelar", command=on_cancel).pack(side=tk.RIGHT, padx=4)

        dialog.wait_window()
        return result_holder[0]

    def _open_progress_and_run(self, params: dict):
        """Abre a janela de progresso e inicia a thread de análise."""
        pw = tk.Toplevel(self.root)
        pw.title("Executando Análise")
        self._center_on_root(pw, 680, 500)

        ttk.Label(pw, text="Processando… aguarde.", font=("Arial", 11, "bold")).pack(pady=10)

        tf = ttk.Frame(pw)
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        txt = tk.Text(tf, height=26, width=80, wrap=tk.WORD, font=("Courier", 9))
        scr = ttk.Scrollbar(tf, command=txt.yview)
        txt.configure(yscrollcommand=scr.set)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pw.update()

        threading.Thread(
            target=self._analysis_thread,
            args=(params, txt, pw),
            daemon=True,
        ).start()

    def _analysis_thread(self, params: dict, log: tk.Text, pw: tk.Toplevel):
        old_out, old_err = sys.stdout, sys.stderr
        redir = TextRedirector(log)
        sys.stdout = sys.stderr = redir

        try:
            prefix = str(self.results_dir / params["output"])

            # Aplica o email do usuário ao módulo para o polite pool do OpenAlex
            if params.get("email"):
                openalex_colab.POLITE_EMAIL = params["email"]

            # 1. Instituição
            if params["institution_id"]:
                inst_id   = params["institution_id"]
                inst_name = params["institution"]
                print(f"Usando instituição selecionada: {inst_name}\n  ID: {inst_id}\n")
            else:
                inst_id, inst_name = openalex_colab.find_institution(
                    params["institution"], interactive=False
                )

            # 2. Áreas de conhecimento
            topic_ids  = None
            concept_id = None

            if params.get("_resolved_topic_ids") is not None:
                # IDs já resolvidos pelo diálogo de seleção (podem ser lista vazia
                # se o usuário desmarcou tudo — nesse caso filtra sem área)
                topic_ids = params["_resolved_topic_ids"] or None
                if topic_ids:
                    print(f"Usando {len(topic_ids)} topic(s) selecionado(s) pelo usuário.\n")
                else:
                    print("Nenhum topic selecionado — buscando sem filtro de área.\n")

            elif params["topic_id"]:
                raw = [t.strip() for t in params["topic_id"].split(",") if t.strip()]
                topic_ids = [
                    t if t.startswith("http") else f"https://openalex.org/{t}"
                    for t in raw
                ]
                print(f"Usando {len(topic_ids)} topic(s) por ID: {', '.join(raw)}\n")

            # 3. Pesquisadores
            authors = openalex_colab.get_authors_by_institution(
                inst_id,
                max_authors=params["max_authors"],
                topic_ids=topic_ids,
                concept_id=concept_id,
            )
            if not authors:
                print("Nenhum pesquisador encontrado. Verifique os filtros.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Sem resultados",
                    "Nenhum pesquisador encontrado para os filtros informados.\n\n"
                    "Dicas:\n"
                    "• Verifique o nome da universidade\n"
                    "• Tente sem filtro de área\n"
                    "• Use um período mais amplo",
                ))
                return

            author_ids   = [a["id"] for a in authors]
            author_names = {a["id"]: a["name"] for a in authors}

            # 4. Coautorias
            year_from = int(params["year_from"]) if params["year_from"] else None
            year_to   = int(params["year_to"])   if params["year_to"]   else None

            edges, coauthor_names, works_by_year = openalex_colab.get_coauthorships(
                author_ids,
                max_works_per_author=params["max_works"],
                topic_ids=topic_ids,
                concept_id=concept_id,
                year_from=year_from,
                year_to=year_to,
            )
            author_names.update(coauthor_names)

            # 5. Grafo
            G = openalex_colab.build_graph(
                edges, author_names, author_ids,
                restrict_to_institution=params["restrict"],
            )

            # 6. Métricas + exportação (HTML, GEXF, PNGs e CSVs)
            metrics = openalex_colab.compute_metrics(G)
            openalex_colab.export_graph(G, output_prefix=prefix)
            openalex_colab.generate_charts(G, metrics, authors, works_by_year, output_prefix=prefix)
            openalex_colab.export_csvs(G, authors, metrics, works_by_year, output_prefix=prefix)

            print(f"\n✓ Concluído! Arquivos salvos em:\n  {self.results_dir}")
            self._collect_output_files(params["output"])
            rdir = str(self.results_dir)
            out  = params["output"]
            self.root.after(0, lambda: messagebox.showinfo(
                "Análise concluída",
                f"Todos os arquivos foram gerados!\n\n"
                f"Pasta: {rdir}\n\n"
                f"Arquivos:\n"
                f"  • {out}.html          (grafo interativo)\n"
                f"  • {out}.gexf          (Gephi)\n"
                f"  • {out}_pesquisadores.csv\n"
                f"  • {out}_colaboracoes.csv\n"
                f"  • {out}_comunidades.csv\n"
                f"  • {out}_publicacoes_por_ano.csv\n"
                f"  • {out}_resumo_metricas.csv\n"
                f"  • 6 gráficos .png",
            ))

        except Exception:
            detail = traceback.format_exc()
            print(f"\n✗ Erro:\n{detail}")
            last = detail.strip().splitlines()[-1]
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro durante análise:\n{last}"))

        finally:
            sys.stdout, sys.stderr = old_out, old_err

    # ----------------------------------------------------------
    # Utilitários
    # ----------------------------------------------------------

    def _collect_output_files(self, prefix: str):
        self.output_files = []
        exts = [
            ".html", ".gexf",
            "_pesquisadores.csv", "_colaboracoes.csv", "_comunidades.csv",
            "_publicacoes_por_ano.csv", "_resumo_metricas.csv",
            "_distribuicao_grau.png", "_top_centralidade_grau.png",
            "_top_intermediacao.png", "_tamanho_comunidades.png",
            "_publicacoes_por_ano.png", "_produtividade_vs_centralidade.png",
        ]
        for ext in exts:
            p = self.results_dir / f"{prefix}{ext}"
            if p.exists():
                self.output_files.append(str(p))

    def _open_results(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.results_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.results_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.results_dir)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

    def _help(self):
        hw = tk.Toplevel(self.root)
        hw.title("Ajuda — Como usar")
        self._center_on_root(hw, 740, 680)

        txt = tk.Text(hw, wrap=tk.WORD, font=("Courier", 10), padx=12, pady=10)
        scr = ttk.Scrollbar(hw, command=txt.yview)
        txt.configure(yscrollcommand=scr.set)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.insert(tk.END, """
GUIA DE USO — Grafo de Colaboração Científica via OpenAlex
===========================================================

1. UNIVERSIDADE (obrigatório)
   Digite o nome e clique em "Buscar" (ou pressione Enter).
   Os resultados aparecem na lista — clique para selecionar.
   A universidade selecionada fica destacada em azul.

2. ÁREA DE CONHECIMENTO (opcional)
   Filtra por faculdade/área de pesquisa dentro da universidade.

   → PELA LISTA: clique em uma área. Ctrl+clique para várias.
   → DIGITANDO: use o campo de texto (separe com ponto-e-vírgula):
       "Computer Science;Information Systems"
   → Topic IDs: cole IDs diretos do OpenAlex (ex: T10712,T14330)
     para maior precisão — tem prioridade sobre o restante.

   Deixe tudo em branco para buscar toda a universidade.

3. PERÍODO (opcional)
   Filtra publicações por ano.  Ex: 2018 a 2024.

4. LIMITES
   • Máx. pesquisadores: quantos autores buscar (padrão 100)
   • Máx. publicações/pesquisador: obras a verificar (padrão 50)
   Valores maiores = análise mais completa, porém mais lenta.

5. OPÇÕES
   • Colaborações internas: só vínculos dentro da universidade.
   • Nome dos arquivos: prefixo para nomear os resultados.

ARQUIVOS GERADOS (pasta "resultados/")
=======================================
  • *.html     → Grafo interativo — abra no navegador
  • *.gexf     → Abra no Gephi para análise avançada
  • _pesquisadores.csv
  • _colaboracoes.csv
  • _comunidades.csv
  • _publicacoes_por_ano.csv
  • _resumo_metricas.csv
  • 6 gráficos .png
""")
        txt.config(state=tk.DISABLED)


# ------------------------------------------------------------
# Entrada
# ------------------------------------------------------------

def main():
    root = tk.Tk()
    if not DependencyInstaller.check_and_install(root):
        root.destroy()
        sys.exit(1)
    OpenAlexGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
