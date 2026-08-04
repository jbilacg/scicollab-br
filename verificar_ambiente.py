#!/usr/bin/env python3
"""
verificar_ambiente.py

Verifica se o ambiente está totalmente preparado para gerar o executável.
Execute isso ANTES de rodar build_exe.py

Verifica:
  ✓ Versão do Python
  ✓ Arquivos necessários
  ✓ Dependências instaladas
  ✓ PyInstaller
  ✓ Espaço em disco

Uso:
  python verificar_ambiente.py
"""

import sys
import subprocess
from pathlib import Path


class Colors:
    OK = "\033[92m"      # Verde
    FAIL = "\033[91m"    # Vermelho
    WARN = "\033[93m"    # Amarelo
    INFO = "\033[94m"    # Azul
    RESET = "\033[0m"


def check_python_version():
    """Verifica versão do Python."""
    print(f"\n{Colors.INFO}➊ Verificando Python...{Colors.RESET}")
    
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info < (3, 9):
        print(f"{Colors.FAIL}❌ Python {version_str} — Mínimo: 3.9{Colors.RESET}")
        return False
    else:
        print(f"{Colors.OK}✓ Python {version_str} OK{Colors.RESET}")
        return True


def check_required_files():
    """Verifica se os arquivos necessários existem."""
    print(f"\n{Colors.INFO}➋ Verificando Arquivos...{Colors.RESET}")
    
    script_dir = Path(__file__).parent
    required_files = {
        "gui_openalex.py": "Interface gráfica",
        "openalex_colab.py": "Script principal",
        "requirements.txt": "Dependências",
    }
    
    all_exist = True
    for fname, description in required_files.items():
        fpath = script_dir / fname
        if fpath.exists():
            size_kb = fpath.stat().st_size / 1024
            print(f"{Colors.OK}✓ {fname:<25} ({description}) — {size_kb:.1f} KB{Colors.RESET}")
        else:
            print(f"{Colors.FAIL}❌ {fname:<25} ({description}) — NÃO ENCONTRADO{Colors.RESET}")
            all_exist = False
    
    if not all_exist:
        print(f"\n{Colors.WARN}⚠ Solução:{Colors.RESET}")
        print("  Certifique-se de ter baixado TODOS os arquivos do projeto.")
        print(f"  Caminho esperado: {script_dir}")
        print("\n  Arquivos devem estar na mesma pasta que este script.")
    
    return all_exist


def check_pip_packages():
    """Verifica se as dependências foram instaladas."""
    print(f"\n{Colors.INFO}➌ Verificando Dependências (pip)...{Colors.RESET}")
    
    # Lê requirements.txt
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print(f"{Colors.WARN}⚠ requirements.txt não encontrado, pulando verificação{Colors.RESET}")
        return True
    
    packages = []
    with open(req_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove especificadores de versão
                pkg = line.split(">=")[0].split("==")[0].split("<")[0].strip()
                packages.append(pkg)
    
    all_installed = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"{Colors.OK}✓ {pkg:<20} instalado{Colors.RESET}")
        except ImportError:
            print(f"{Colors.FAIL}❌ {pkg:<20} NÃO instalado{Colors.RESET}")
            all_installed = False
    
    if not all_installed:
        print(f"\n{Colors.WARN}⚠ Solução:{Colors.RESET}")
        print("  Execute: pip install -r requirements.txt")
    
    return all_installed


def check_pyinstaller():
    """Verifica se PyInstaller está instalado."""
    print(f"\n{Colors.INFO}➍ Verificando PyInstaller...{Colors.RESET}")
    
    try:
        import PyInstaller
        version = PyInstaller.__version__
        print(f"{Colors.OK}✓ PyInstaller {version} instalado{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.FAIL}❌ PyInstaller NÃO instalado{Colors.RESET}")
        print(f"\n{Colors.WARN}⚠ Solução:{Colors.RESET}")
        print("  Execute: pip install pyinstaller")
        return False


def check_disk_space():
    """Verifica se há espaço em disco suficiente."""
    print(f"\n{Colors.INFO}➎ Verificando Espaço em Disco...{Colors.RESET}")
    
    script_dir = Path(__file__).parent
    
    # Estatísticas de disco
    import shutil
    total, used, free = shutil.disk_usage(script_dir)
    free_gb = free / (1024**3)
    
    if free_gb < 1:
        print(f"{Colors.FAIL}❌ Apenas {free_gb:.2f} GB livres — Mínimo: 1 GB{Colors.RESET}")
        return False
    else:
        print(f"{Colors.OK}✓ {free_gb:.2f} GB livres (mínimo: 1 GB){Colors.RESET}")
        return True


def main():
    """Executa todas as verificações."""
    print("="*60)
    print("Verificador de Ambiente — Grafo de Colaboração")
    print("="*60)
    
    checks = [
        ("Python", check_python_version),
        ("Arquivos", check_required_files),
        ("Dependências", check_pip_packages),
        ("PyInstaller", check_pyinstaller),
        ("Espaço em Disco", check_disk_space),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"{Colors.FAIL}❌ Erro ao verificar {name}: {e}{Colors.RESET}")
            results[name] = False
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    
    all_ok = all(results.values())
    
    for name, status in results.items():
        symbol = f"{Colors.OK}✓{Colors.RESET}" if status else f"{Colors.FAIL}❌{Colors.RESET}"
        print(f"{symbol} {name:<20} {'OK' if status else 'PROBLEMA'}")
    
    print("\n" + "="*60)
    
    if all_ok:
        print(f"{Colors.OK}✓ AMBIENTE PRONTO!{Colors.RESET}")
        print("\nAgora você pode rodar:")
        print("  python build_exe.py")
        print("\nIsso vai gerar:")
        print("  dist/Grafo de Colaboracao.exe (~150 MB)")
    else:
        print(f"{Colors.FAIL}❌ AMBIENTE COM PROBLEMAS{Colors.RESET}")
        print("\nResolva os problemas acima e tente novamente.")
        sys.exit(1)
    
    print("="*60)


if __name__ == "__main__":
    main()
