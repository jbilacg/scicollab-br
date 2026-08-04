; setup_grafo.nsi
;
; Instalador profissional para "Grafo de Colaboração Científica"
; Cria um Setup.exe que instala e cria atalhos no menu Iniciar e Desktop
;
; Pré-requisitos:
;   1. Ter PyInstaller gerado dist/Grafo de Colaboracao.exe
;   2. Ter NSIS instalado (https://nsis.sourceforge.io/)
;
; Como compilar:
;   Clique com botão direito → Compile NSIS Script
;   Ou na linha de comando:
;   "C:\Program Files (x86)\NSIS\makensis.exe" setup_grafo.nsi
;
; Resultado:
;   setup_grafo.exe (instalador que usuários rodaram no Windows)

!include "MUI2.nsh"

; Configurações básicas
Name "Grafo de Colaboração Científica"
OutFile "setup_grafo.exe"
InstallDir "$PROGRAMFILES\GrafoColaboracao"
RequestExecutionLevel admin

; Ícone (descomente e aponte um .ico se quiser)
; Icon "icon.ico"

; Configurações de interface
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "PortugueseBR"

; Seção de instalação
Section "Instalar Grafo de Colaboração"
  SetOutPath "$INSTDIR"
  
  ; Copia os arquivos executáveis
  File "dist\Grafo de Colaboracao.exe"
  
  ; Copia arquivos de documentação
  File "COMECE_AQUI.md"
  File "KPI_DOCUMENTACAO.md"
  File "PROJETO_RESUMO.md"
  File "README.md"
  File "requirements.txt"
  
  ; Copia os scripts Python (para referência)
  File "openalex_colab.py"
  File "gui_openalex.py"
  
  ; Cria atalho no menu Iniciar
  CreateDirectory "$SMPROGRAMS\Grafo de Colaboração"
  CreateShortCut "$SMPROGRAMS\Grafo de Colaboração\Iniciar Aplicação.lnk" "$INSTDIR\Grafo de Colaboracao.exe"
  CreateShortCut "$SMPROGRAMS\Grafo de Colaboração\Desinstalar.lnk" "$INSTDIR\uninstall.exe"
  CreateShortCut "$SMPROGRAMS\Grafo de Colaboração\Leia-me.lnk" "$INSTDIR\COMECE_AQUI.md"
  
  ; Cria atalho no Desktop
  CreateShortCut "$DESKTOP\Grafo de Colaboração.lnk" "$INSTDIR\Grafo de Colaboracao.exe"
  
  ; Cria desinstalador
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Registra no Windows (para aparecer em "Adicionar/Remover Programas")
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrafoColaboracao" \
    "DisplayName" "Grafo de Colaboração Científica"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrafoColaboracao" \
    "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrafoColaboracao" \
    "DisplayVersion" "1.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrafoColaboracao" \
    "Publisher" "Comunidade Científica"
SectionEnd

; Seção de desinstalação
Section "Uninstall"
  Delete "$INSTDIR\Grafo de Colaboracao.exe"
  Delete "$INSTDIR\COMECE_AQUI.md"
  Delete "$INSTDIR\KPI_DOCUMENTACAO.md"
  Delete "$INSTDIR\PROJETO_RESUMO.md"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\requirements.txt"
  Delete "$INSTDIR\openalex_colab.py"
  Delete "$INSTDIR\gui_openalex.py"
  Delete "$INSTDIR\uninstall.exe"
  
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\Grafo de Colaboração\Iniciar Aplicação.lnk"
  Delete "$SMPROGRAMS\Grafo de Colaboração\Desinstalar.lnk"
  Delete "$SMPROGRAMS\Grafo de Colaboração\Leia-me.lnk"
  RMDir "$SMPROGRAMS\Grafo de Colaboração"
  
  Delete "$DESKTOP\Grafo de Colaboração.lnk"
  
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrafoColaboracao"
SectionEnd
