# -*- coding: utf-8 -*-
# Build variables for the NVDA add-on
# Copyright (C) 2024 Your Name or Organisation
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.

# Initialize gettext for buildVars strings
import gettext
import os

# Try to use the dummy _ function if running outside NVDA/SCons context
# This prevents errors when importing buildVars directly for other purposes
try:
    _ = gettext.translation("nvda", localedir=os.path.join("addon", "locale"), fallback=True).gettext
except FileNotFoundError:
    # Fallback if locale files don't exist yet or path is wrong
    _ = gettext.gettext

# Please modify the following variables to match your add-on.
# It is recommended to keep this file as small as possible.

# Add-on information.
#  The variables are used in the manifest.ini file for the add-on
#  Here, list only the basic information variables for the add-on.
#  Translateable strings should be placed between _() marks.
#  This will ensure that they are placed in the pot file for translation.
# Note: If you are using non-English characters, make sure this file is encoded as UTF-8.
addon_info = {
    # Add-on name
    # Translators: Add-on name
    "addon_name": "SubtitleDownloader",
    # Add-on summary
    # Translators: Add-on summary
    "addon_summary": _("Downloads video subtitles from various platforms"),
    # Add-on description
    # Translators: Add-on description
    "addon_description": _(
        """Allows users to download subtitles for videos from platforms like YouTube, Vimeo, Coursera, etc., using a keyboard shortcut (Insert+Shift+L). 
It saves subtitles as TXT files in the Downloads folder, using the video title as the filename. 
If multiple languages are available, it prompts the user to select one."""
    ),
    # Version
    "addon_version": "1.0",
    # Author(s)
    "addon_author": _("Manus AI <support@example.com>"),
    # URL for the add-on website or repository (optional)
    "addon_url": None,
    # Documentation file name
    "addon_docFileName": "readme.html",
    # Minimum NVDA version required (e.g. "2023.1")
    "addon_minimumNVDAVersion": "2023.1",
    # Last NVDA version tested with (e.g. "2024.1")
    "addon_lastTestedNVDAVersion": "2024.4",
    # Update channel for the add-on.
    # "stable" is recommended for published releases.
    # "dev" should be used for development snapshots.
    # None or empty string disables update checks.
    "addon_updateChannel": "stable",
}

# Files and folders that should not be copied in the final add-on build.
excludedFiles = []

# Root folder where the add-on sources are located.
# This is the folder that will be zipped for the add-on bundle.
addonSources = "addon"

# List of Python files/folders that contain the source code for the add-on
# Paths should be relative to the addonSources folder
pythonSources = ["globalPlugins"]

# List of files/folders containing message contexts for translation
# Paths should be relative to the addonSources folder
i18nSources = [addonSources, "manifest.ini.tpl"]

# Files that should be copied to the add-on documentation folder
docFiles = ["readme.md", "changelog.md"]

# Base language for the add-on
baseLanguage = "pt_BR" # Set to the primary language of your initial readme

# Markdown extensions for converting documentation to HTML
# see https://python-markdown.github.io/extensions/ for details
markdownExtensions = ["markdown.extensions.fenced_code", "markdown.extensions.tables"]

