#!/usr/bin/env python3
"""
install.py

Script de instalação automática para o Grafo de Colaboração Científica (OpenAlex).

Faz:
  1. Verifica Python 3.9+
  2. Instala dependências (pip install -r requirements.txt)
  3. Cria atalho para a GUI (Windows/Mac/Linux)
  4. Oferece executar a GUI após instalação

Uso:
  python3 install.py
"""

import sys
import subprocess
import os
import platform
from pathlib import Path


def check_python_version():
    """Verifica se é Python 3.9+"""
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ é necessário. Você tem Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} OK")


def install_dependencies():
    """Instala as dependências via pip."""
    print("\n📦 Instalando dependências...")
    
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print("❌ Arquivo requirements.txt não encontrado!")
        sys.exit(1)
    
    cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", str(req_file)]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✓ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def create_shortcuts():
    """Cria atalhos para executar a GUI."""
    script_dir = Path(__file__).parent
    gui_script = script_dir / "gui_openalex.py"
    system = platform.system()

    print("\n🔗 Criando atalhos...")

    if system == "Windows":
        # Cria atalho no Desktop
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "Grafo de Colaboração.bat"
        
        batch_content = f"""@echo off
cd /d "{script_dir}"
python gui_openalex.py
pause
"""
        try:
            with open(shortcut_path, "w") as f:
                f.write(batch_content)
            print(f"✓ Atalho criado em: {shortcut_path}")
        except Exception as e:
            print(f"⚠ Não foi possível criar atalho no Desktop: {e}")

    elif system == "Darwin":  # macOS
        # Cria app alias
        app_path = script_dir / "Grafo de Colaboração.command"
        script_content = f"""#!/bin/bash
cd "{script_dir}"
python3 gui_openalex.py
"""
        try:
            with open(app_path, "w") as f:
                f.write(script_content)
            os.chmod(app_path, 0o755)
            print(f"✓ App criado em: {app_path}")
        except Exception as e:
            print(f"⚠ Não foi possível criar app: {e}")

    elif system == "Linux":
        # Cria atalho no Desktop
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "grafo_colaboracao.desktop"
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Grafo de Colaboração Científica
Exec=python3 {gui_script}
Icon=folder
Terminal=true
Categories=Science;
Path={script_dir}
"""
        try:
            with open(shortcut_path, "w") as f:
                f.write(desktop_content)
            os.chmod(shortcut_path, 0o755)
            print(f"✓ Atalho criado em: {shortcut_path}")
        except Exception as e:
            print(f"⚠ Não foi possível criar atalho: {e}")


def main():
    """Executa o instalador."""
    print("="*60)
    print("Instalador — Grafo de Colaboração Científica (OpenAlex)")
    print("="*60)

    # 1. Verifica Python
    check_python_version()

    # 2. Instala dependências
    if not install_dependencies():
        sys.exit(1)

    # 3. Cria atalhos
    create_shortcuts()

    # 4. Resumo
    print("\n" + "="*60)
    print("✓ Instalação concluída com sucesso!")
    print("="*60)
    print("\nPróximos passos:")
    print("  1. Execute: python3 gui_openalex.py")
    print("  Ou use o atalho criado no Desktop/pasta da aplicação")
    print("\nDocumentação:")
    print("  • KPI_DOCUMENTACAO.md — Explicação de cada métrica")
    print("  • README.md — Como usar o script via linha de comando")
    print("="*60)

    # Oferece executar a GUI
    try:
        response = input("\nDeseja executar a interface gráfica agora? (s/N): ").strip().lower()
        if response in ("s", "sim", "y", "yes"):
            script_dir = Path(__file__).parent
            gui_script = script_dir / "gui_openalex.py"
            subprocess.run([sys.executable, str(gui_script)])
    except KeyboardInterrupt:
        print("\n\nInstalação finalizada.")


if __name__ == "__main__":
    main()
