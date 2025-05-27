# Guia do Desenvolvedor - Complemento Subtitle Downloader

Este guia fornece instruções para desenvolvedores que desejam modificar, compilar ou contribuir para o complemento Subtitle Downloader para NVDA.

## Pré-requisitos

*   **Python 3:** Certifique-se de ter o Python 3 instalado (a versão deve ser compatível com a versão do NVDA alvo, geralmente Python 3.7+).
*   **SCons:** O sistema de construção padrão para complementos NVDA. Instale via pip: `pip install scons`.
*   **gettext (opcional, para traduções):** Ferramentas `gettext` são necessárias para gerar arquivos `.pot` e compilar `.po` para `.mo`. Podem ser obtidas do projeto GNU gettext ou via gerenciadores de pacotes (ex: `apt install gettext` no Debian/Ubuntu).
*   **Poedit (recomendado, para traduções):** Um editor gráfico para arquivos `.po` que facilita o processo de tradução.

## Estrutura do Diretório

O complemento segue a estrutura padrão de diretórios do NVDA:

```
SubtitleDownloader/
├── doc/
│   └── pt_BR/
│       └── readme.html       # Documentação do usuário
├── globalPlugins/
│   └── subtitleDownloader/
│       ├── __init__.py       # Código principal do plugin
│       └── lib/              # Dependências empacotadas (ex: yt-dlp)
│           └── yt_dlp/       # Pasta da biblioteca yt-dlp
├── locale/
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       └── SubtitleDownloader.mo # Inglês compilado
│   │       └── SubtitleDownloader.po # Inglês fonte
│   ├── pt_BR/
│   │   └── LC_MESSAGES/
│   │       └── SubtitleDownloader.mo # Português compilado
│   │       └── SubtitleDownloader.po # Português fonte
│   └── SubtitleDownloader.pot    # Template de tradução
└── manifest.ini              # Metadados do complemento
```

## Dependências

*   **yt-dlp:** A principal dependência para baixar legendas. Para distribuição, esta biblioteca **deve ser empacotada** dentro do complemento.
    *   **Como Empacotar:**
        1.  Instale `yt-dlp` em um ambiente temporário: `pip install yt-dlp -t temp_ytdlp`
        2.  Copie o diretório `yt_dlp` de dentro de `temp_ytdlp` para `SubtitleDownloader/globalPlugins/subtitleDownloader/lib/`.
        3.  O código em `__init__.py` já está configurado para tentar importar de `lib/`.
    *   **Nota:** `yt-dlp` pode ter suas próprias dependências. Certifique-se de que a versão empacotada funcione no ambiente Python do NVDA. Testes são essenciais.

## Internacionalização (i18n)

O complemento usa `gettext` para tradução.

1.  **Marcar Strings:** Use `_("Texto para traduzir")` no código Python (`__init__.py`) e no `manifest.ini`.
2.  **Gerar Template (`.pot`):**
    *   Navegue até o diretório raiz do complemento (`SubtitleDownloader`).
    *   Execute `pygettext.py -k _ -o locale/SubtitleDownloader.pot globalPlugins/subtitleDownloader/*.py manifest.ini` (ajuste o caminho para `pygettext.py` se necessário).
3.  **Criar/Atualizar Arquivos de Idioma (`.po`):**
    *   Para um novo idioma (ex: `fr` - Francês), copie `SubtitleDownloader.pot` para `locale/fr/LC_MESSAGES/SubtitleDownloader.po`.
    *   Para atualizar um `.po` existente, use `msgmerge`: `msgmerge -U locale/pt_BR/LC_MESSAGES/SubtitleDownloader.po locale/SubtitleDownloader.pot`.
    *   Edite os arquivos `.po` (usando Poedit ou um editor de texto) para adicionar as traduções.
4.  **Compilar Traduções (`.mo`):**
    *   Use `msgfmt`: `msgfmt locale/pt_BR/LC_MESSAGES/SubtitleDownloader.po -o locale/pt_BR/LC_MESSAGES/SubtitleDownloader.mo`.
    *   Repita para cada idioma.
    *   Os arquivos `.mo` são os que o NVDA utiliza.

## Compilando o Complemento (`.nvda-addon`) com SCons

Com o arquivo `SConstruct` presente na raiz do diretório do complemento, o processo de compilação é simplificado e padronizado:

1.  **Pré-requisitos:** Certifique-se de ter o Python e o SCons instalados e acessíveis no seu terminal.
2.  **Dependências:** Garanta que a dependência `yt-dlp` foi copiada para `SubtitleDownloader/globalPlugins/subtitleDownloader/lib/` conforme descrito na seção "Dependências". O `SConstruct` não baixa dependências automaticamente, ele apenas empacota o que já está lá.
3.  **Traduções:** Certifique-se de que os arquivos `.mo` das traduções estão compilados e presentes nas pastas `locale` corretas.
4.  **Execute o SCons:**
    *   Abra um terminal ou prompt de comando.
    *   Navegue até o diretório raiz do complemento (`/home/ubuntu/SubtitleDownloader` neste ambiente).
    *   Execute o comando: `scons`
5.  **Resultado:** O SCons usará as instruções do arquivo `SConstruct` para:
    *   Limpar builds anteriores (se existirem, usando `scons clean` primeiro é uma boa prática).
    *   Copiar todos os arquivos e pastas necessários (definidos em `include_files` e `include_dirs` no `SConstruct`) para uma pasta temporária de "staging" dentro de `build/`.
    *   Criar um arquivo ZIP a partir da pasta de staging.
    *   Renomear o arquivo ZIP para `SubtitleDownloader-X.Y.nvda-addon` (onde X.Y é a versão do `manifest.ini`) no diretório raiz.

Este arquivo `.nvda-addon` gerado pelo `scons` é o pacote final pronto para distribuição e instalação.

**Comandos Úteis:**
*   `scons`: Compila o complemento.
*   `scons clean`: Remove a pasta `build/` e o arquivo `.nvda-addon` anterior.

*   Teste extensivamente em diferentes versões do NVDA (conforme `minimumNVDAVersion` e `lastTestedNVDAVersion`).
*   Teste em diferentes plataformas de vídeo (YouTube, Vimeo, etc.).
*   Teste com vídeos sem legendas, com uma legenda e com múltiplas legendas.
*   Teste a funcionalidade de seleção de idioma.
*   Verifique se os arquivos são salvos corretamente na pasta Downloads.
*   Teste em diferentes idiomas configurados no NVDA para verificar a internacionalização.
*   Lembre-se das limitações de autenticação/captcha e teste em um ambiente logado quando necessário.


