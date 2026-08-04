#!/usr/bin/env python3
"""
build_exe.py

Gera um executável Windows (.exe) a partir da interface gráfica.
Depois disso, usuários podem rodar SEM ter Python instalado.

Pré-requisito:
    pip install pyinstaller

Uso:
    python3 build_exe.py

Resultado:
    dist/Grafo de Colaboracao.exe (~150-200 MB)
"""

import subprocess
import sys
import os
from pathlib import Path


def check_pyinstaller():
    """Verifica se PyInstaller está instalado."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} encontrado")
        return True
    except ImportError:
        print("❌ PyInstaller não está instalado.")
        print("\nPara instalar, execute:")
        print("  pip install pyinstaller")
        return False


def check_required_files():
    """Verifica se todos os arquivos necessários existem."""
    script_dir = Path(__file__).parent
    required_files = ["gui_openalex.py", "openalex_colab.py", "requirements.txt"]
    
    print("\n📁 Verificando arquivos...")
    missing = []
    
    for fname in required_files:
        fpath = script_dir / fname
        if fpath.exists():
            print(f"  ✓ {fname}")
        else:
            print(f"  ❌ {fname} NÃO ENCONTRADO")
            missing.append(fname)
    
    if missing:
        print(f"\n❌ Faltam {len(missing)} arquivo(s):")
        for f in missing:
            print(f"     - {f}")
        print(f"\nTodos os arquivos devem estar em: {script_dir}")
        print("\nBaixe os arquivos faltando do repositório:")
        print("  https://github.com/seu-usuario/grafo_colaboracao")
        return False
    
    print("\n✓ Todos os arquivos necessários encontrados!")
    return True


def build_exe():
    """Constrói o executável usando PyInstaller."""
    print("\n" + "="*60)
    print("Gerando executável Windows (.exe)...")
    print("="*60)
    
    script_dir = Path(__file__).parent
    gui_script = script_dir / "gui_openalex.py"
    
    if not gui_script.exists():
        print(f"❌ Arquivo gui_openalex.py não encontrado em {script_dir}")
        print(f"\nCaminho esperado: {gui_script}")
        print("\nSolução: Certifique-se de ter baixado TODOS os arquivos do projeto")
        return False
    
    # Localiza os arquivos de template do pyvis para incluir no executável.
    # Sem isso, pyvis lança jinja2.exceptions.TemplateNotFound: template.html
    # porque o PyInstaller não copia arquivos de dados de pacotes automaticamente.
    import pyvis as _pyvis
    pyvis_templates = str(Path(_pyvis.__file__).parent / "templates")
    pyvis_lib       = str(Path(_pyvis.__file__).parent / "templates" / "lib")
    add_pyvis       = f"{pyvis_templates}{os.pathsep}pyvis/templates"
    add_pyvis_lib   = f"{pyvis_lib}{os.pathsep}pyvis/templates/lib"

    # Comando PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",                                    # Arquivo único
        "--windowed",                                   # Sem console (sem terminal)
        "--name", "Grafo de Colaboracao",              # Nome do executável
        "--distpath", str(script_dir / "dist"),        # Pasta de saída
        "--workpath", str(script_dir / "build"),       # Pasta temporária
        "--specpath", str(script_dir),                 # Onde salvar .spec
        # Templates do pyvis (Jinja2) — obrigatório para gerar o HTML do grafo
        "--add-data", add_pyvis,
        "--add-data", add_pyvis_lib,
        # openalex_colab é importado diretamente (não como subprocess)
        "--hidden-import=openalex_colab",
        "--hidden-import=tkinter",
        "--hidden-import=networkx",
        "--hidden-import=community",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=pyvis",
        "--hidden-import=pyvis.network",
        str(gui_script),                               # Script a compilar
    ]
    
    print("\nComando sendo executado:")
    print(" ".join(cmd))
    print("\nIsso pode levar 2-5 minutos na primeira vez...\n")
    
    try:
        # Usar shell=False (padrão) e passar arguments como lista
        # Isso funciona corretamente com caminhos que contêm espaços
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao compilar: {e}")
        print("\n💡 Dica: Se o problema for 'espaços no caminho', tente:")
        print("   1. Mover a pasta para: C:\\grafo_colaboracao")
        print("   2. Ou renomear a pasta removendo os espaços")
        print("   3. Depois rodar o script novamente")
        return False


def create_shortcut_script():
    """Cria um script .bat para colocar a pasta inteira em atalho."""
    script_dir = Path(__file__).parent
    batch_file = script_dir / "Executar Grafo.bat"
    
    batch_content = f"""@echo off
cd /d "{script_dir}\\dist"
"Grafo de Colaboracao.exe"
"""
    
    try:
        with open(batch_file, "w", encoding="utf-8") as f:
            f.write(batch_content)
        print(f"✓ Atalho .bat criado: {batch_file}")
        return True
    except Exception as e:
        print(f"⚠ Não foi possível criar atalho .bat: {e}")
        return False


def main():
    """Executa o build."""
    print("="*60)
    print("Build de Executável — Grafo de Colaboração")
    print("="*60)
    
    # 1. Verifica arquivos
    if not check_required_files():
        sys.exit(1)
    
    # 2. Verifica PyInstaller
    if not check_pyinstaller():
        print("\n💡 Instale com: pip install pyinstaller")
        sys.exit(1)
    
    # 3. Build
    if not build_exe():
        sys.exit(1)
    
    # 3. Cria atalho
    create_shortcut_script()
    
    # 4. Resumo
    print("\n" + "="*60)
    print("✓ Executável gerado com sucesso!")
    print("="*60)
    
    dist_path = Path(__file__).parent / "dist" / "Grafo de Colaboracao.exe"
    print(f"\nArquivo gerado:")
    print(f"  {dist_path}")
    
    file_size_mb = dist_path.stat().st_size / (1024 * 1024)
    print(f"  Tamanho: {file_size_mb:.1f} MB")
    
    print("\n📦 Próximos passos:")
    print("  1. Copie a pasta 'dist' ou o arquivo .exe para onde quiser distribuir")
    print("  2. Usuários podem executar diretamente, SEM Python instalado!")
    print("\n  Opção A (distribuição simples):")
    print(f"    Zip a pasta 'dist' → 'Grafo de Colaboracao.zip'")
    print("\n  Opção B (mais profissional):")
    print("    Use o arquivo 'setup_nsis.nsi' para criar Setup.exe")
    print("="*60)


if __name__ == "__main__":
    main()
