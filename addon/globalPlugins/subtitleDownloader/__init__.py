# -*- coding: utf-8 -*-

import globalPluginHandler
import scriptHandler
import ui
import api
import os
import sys
import wx
import threading
import gettext
import addonHandler
import subprocess
import re
import json
from pathlib import Path

# Setup localization
addonHandler.initTranslation()
_ = gettext.gettext

# Construct path to the bundled 'lib' directory
addon_dir = os.path.dirname(__file__)
lib_path = os.path.join(addon_dir, "lib")

# Add lib_path to sys.path if it's not already there and exists
if os.path.isdir(lib_path) and lib_path not in sys.path:
    sys.path.insert(0, lib_path)
# For debugging purposes, print the sys.path to NVDA error log
# import traceback
# print(f"SubtitleDownloader: Modified sys.path: {sys.path}")
# print(f"SubtitleDownloader: Expected lib_path: {lib_path}, Exists: {os.path.isdir(lib_path)}")
# print(f"SubtitleDownloader: Content of lib_path: {os.listdir(lib_path) if os.path.isdir(lib_path) else 'Not a dir or does not exist'}")

# Try to import yt-dlp, handling potential import errors
try:
    import yt_dlp
except ImportError:
    addon_dir_for_error = os.path.dirname(__file__)
    lib_path_for_error = os.path.join(addon_dir_for_error, "lib")
    expected_yt_dlp_path = os.path.join(lib_path_for_error, "yt_dlp")
    ui.message(
        _("yt-dlp library not found. Please download it and place the 'yt_dlp' directory inside the add-on's 'lib' folder. Expected location for 'yt_dlp': {}")
        .format(expected_yt_dlp_path)
    )
    # For debugging:
    # print(f"SubtitleDownloader: yt-dlp import failed. Checked sys.path: {sys.path}")
    # print(f"SubtitleDownloader: Current working directory: {os.getcwd()}")
    # print(f"SubtitleDownloader: Listing addon_dir_for_error ({addon_dir_for_error}): {os.listdir(addon_dir_for_error) if os.path.isdir(addon_dir_for_error) else 'Not found'}")
    # print(f"SubtitleDownloader: Listing lib_path_for_error ({lib_path_for_error}): {os.listdir(lib_path_for_error) if os.path.isdir(lib_path_for_error) else 'Not found'}")
    yt_dlp = None # Indicate that yt-dlp is not available

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """NVDA Global Plugin to download video subtitles."""

    scriptCategory = _("Subtitle Downloader")
    # Class variable to prevent multiple simultaneous downloads
    _download_thread = None

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        # Placeholder for potential future settings
        # self.load_settings()

    def _get_video_url(self):
        """Tries to get the URL of the video from the foreground application."""
        try:
            focusObject = api.getFocusObject()
            appModule = focusObject.appModule
            # Initial logging of appName and windowClassName
            print(f"SubtitleDownloader: _get_video_url: appName='{appModule.appName if appModule else 'Unknown'}', windowClassName='{focusObject.windowClassName}'")
            
            window_name = appModule.appName if appModule else "" # Ensure window_name is a string

            # Browser detection (more robust)
            if window_name in ["firefox", "chrome", "msedge", "brave", "opera", "vivaldi"]: # Added more browsers
                # 1. Try appModule.browser.url (most reliable for supported browsers)
                print("SubtitleDownloader: Trying appModule.browser.url")
                if hasattr(appModule, 'browser') and hasattr(appModule.browser, 'url'):
                    url = appModule.browser.url
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        print(f"SubtitleDownloader: Found URL via appModule.browser.url: {url}")
                        return url

                # 2. Try focusObject.document.URL
                print("SubtitleDownloader: Trying focusObject.document.URL")
                if hasattr(focusObject, 'document') and hasattr(focusObject.document, 'URL'):
                    url = focusObject.document.URL
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        print(f"SubtitleDownloader: Found URL via focusObject.document.URL: {url}")
                        return url

                # 3. Try focusObject.simpleParent.document.URL
                print("SubtitleDownloader: Trying focusObject.simpleParent.document.URL")
                if hasattr(focusObject, 'simpleParent') and \
                   hasattr(focusObject.simpleParent, 'document') and \
                   hasattr(focusObject.simpleParent.document, 'URL'):
                    url = focusObject.simpleParent.document.URL
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        print(f"SubtitleDownloader: Found URL via focusObject.simpleParent.document.URL: {url}")
                        return url
                
                # 4. Fallback: Check if focusObject itself has 'value' (e.g., URL bar)
                print("SubtitleDownloader: Trying focusObject.value")
                if hasattr(focusObject, 'value') and focusObject.role == api.controlTypes.ROLE_EDITABLETEXT:
                    url = focusObject.value
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        print(f"SubtitleDownloader: Found URL via focusObject.value: {url}")
                        return url
                
                # 5. Fallback: Iterate upwards to find a document object with URL
                print("SubtitleDownloader: Trying upward search for document with URL")
                doc_obj = focusObject.simpleParent
                # Limit upward search to prevent infinite loops in weird object hierarchies
                for i in range(5): # Check up to 5 levels up
                    print(f"SubtitleDownloader: Upward search iteration {i+1}: current_obj role: {doc_obj.role if doc_obj else 'None'}, has URL: {hasattr(doc_obj, 'URL') if doc_obj else 'N/A'}")
                    if not doc_obj:
                        break
                    if doc_obj.role == api.controlTypes.ROLE_DOCUMENT and hasattr(doc_obj, 'URL'):
                        url = doc_obj.URL
                        if url and (url.startswith("http://") or url.startswith("https://")):
                            print(f"SubtitleDownloader: Found URL via upward search (doc_obj.URL): {url}")
                            return url
                    doc_obj = doc_obj.simpleParent
            
            # Add logic for other applications/platforms if needed
            # For example, for media players, the URL might be in a different property
            print("SubtitleDownloader: URL not found through browser-specific methods or standard fallbacks.")

        except Exception as e:
            obj_info = ""
            if focusObject:
                obj_info = f"role={focusObject.role}, name='{focusObject.name}'"
            # More specific error message for debugging
            print(f"SubtitleDownloader: Error getting URL from {appModule.appName if appModule else 'unknown app'} ({obj_info}): {e}")
            # ui.message(_("Could not determine video URL.")) # User message is handled by the caller script
        return None

    def _download_subtitle_thread(self, url):
        """Worker thread to handle the download process."""
        if not yt_dlp:
            ui.message(_("yt-dlp library is not available."))
            GlobalPlugin._download_thread = None
            return

        ui.message(_("Attempting to download subtitles..."))
        try:
            downloads_path = str(Path.home() / "Downloads")
            if not os.path.exists(downloads_path):
                os.makedirs(downloads_path)
                ui.message(_("Created Downloads folder."))

            # yt-dlp options
            ydl_opts = {
                'writesubtitles': True,
                'subtitleslangs': ['all'], # Download all available languages initially
                'skip_download': True,      # Don't download the video itself
                'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'), # Base template
                'quiet': True,
                'noprogress': True,
                'ignoreerrors': True,
                'logtostderr': False, # Avoid polluting NVDA speech/braille
                'verbose': False,
                'listsubtitles': True, # List available subtitles
                'paths': {'home': downloads_path} # Specify download directory
            }

            available_subs = {}
            video_title = "video" # Default title

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'video')
                # Sanitize title for filename
                video_title = re.sub(r'[\/*?":<>|]', "_", video_title)
                subtitles = info_dict.get('subtitles', {})
                if not subtitles:
                    ui.message(_("No subtitles found for this video."))
                    GlobalPlugin._download_thread = None
                    return

                available_subs = {lang: subs for lang, subs in subtitles.items() if any(s.get('ext') == 'vtt' or s.get('ext') == 'srv3' or s.get('ext') == 'srv2' or s.get('ext') == 'srv1' or s.get('ext') == 'ttml' for s in subs)}
            
            if not available_subs:
                 ui.message(_("No suitable subtitle formats found (VTT, SRV, TTML)."))
                 GlobalPlugin._download_thread = None
                 return

            languages = list(available_subs.keys())
            selected_lang = None

            if len(languages) == 1:
                selected_lang = languages[0]
                ui.message(_("Found subtitles in: {lang}").format(lang=selected_lang))
            else:
                # Need to ask the user - requires wxPython on the main thread
                wx.CallAfter(self._ask_language, languages, video_title, url, downloads_path)
                # The rest of the process continues in _finish_download after user selection
                return # Exit thread here, main thread will handle UI

            # If only one language or selection already made (this part is now handled in _finish_download)
            self._finish_download(selected_lang, video_title, url, downloads_path)

        except yt_dlp.utils.DownloadError as e:
            ui.message(_("Download Error: Could not retrieve subtitle information."))
            print(f"yt-dlp error: {e}")
        except Exception as e:
            ui.message(_("An unexpected error occurred during download."))
            print(f"Error in download thread: {e}")
        finally:
            # Ensure the thread reference is cleared unless waiting for UI
            if GlobalPlugin._download_thread and not wx.IsMainThread(): # Check if we are still waiting for UI
                 GlobalPlugin._download_thread = None

    def _ask_language(self, languages, video_title, url, downloads_path):
        """Runs on the main thread to show the language selection dialog."""
        try:
            # Simple wx Dialog to choose language
            dialog = wx.SingleChoiceDialog(None, _("Multiple subtitle languages found. Please choose one:"), _("Select Subtitle Language"), languages)
            if dialog.ShowModal() == wx.ID_OK:
                selected_lang = dialog.GetStringSelection()
                # Run the final download part in a new thread to avoid blocking UI
                GlobalPlugin._download_thread = threading.Thread(target=self._finish_download, args=(selected_lang, video_title, url, downloads_path))
                GlobalPlugin._download_thread.start()
            else:
                ui.message(_("Subtitle download cancelled."))
                GlobalPlugin._download_thread = None # Clear thread reference if cancelled
            dialog.Destroy()
        except Exception as e:
            ui.message(_("Error showing language selection dialog."))
            print(f"Error in ask_language: {e}")
            GlobalPlugin._download_thread = None # Clear thread reference on error

    def _finish_download(self, lang_code, video_title, url, downloads_path):
        """Handles the actual download and conversion after language selection."""
        if not yt_dlp:
            ui.message(_("yt-dlp library is not available."))
            GlobalPlugin._download_thread = None
            return
            
        ui.message(_("Downloading subtitles for language: {lang}").format(lang=lang_code))
        try:
            # Define output template specifically for the chosen language subtitle
            # yt-dlp handles conversion to specified format if possible
            output_template = os.path.join(downloads_path, f"{video_title}.{lang_code}.txt")
            
            ydl_opts_final = {
                'writesubtitles': True,
                'subtitleslangs': [lang_code],
                'subtitlesformat': 'vtt/srv3/srv2/srv1/ttml', # Preferred formats
                'skip_download': True,
                'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'), # Temporary template for yt-dlp internal naming
                'quiet': True,
                'noprogress': True,
                'ignoreerrors': False, # Be stricter on the final download
                'logtostderr': False,
                'verbose': False,
                'paths': {'home': downloads_path},
                'postprocessors': [{
                    'key': 'FFmpegSubtitlesConvertor', # Use FFmpeg for conversion
                    'format': 'srt' # Convert to SRT first (common intermediate)
                },{
                    'key': 'FFmpegSubtitlesConvertor', # Then convert SRT to TXT (requires custom handling or a simpler approach)
                    'format': 'txt' # This might not be directly supported - need to check yt-dlp/ffmpeg capabilities
                    # Alternative: Download as VTT/SRT and convert manually
                }]
            }

            # Simpler approach: Download best format and convert manually if needed
            # Let's download as VTT first, as it's text-based and easier to parse than SRT
            vtt_template = os.path.join(downloads_path, f"{video_title}.{lang_code}.vtt")
            ydl_opts_final_vtt = {
                'writesubtitles': True,
                'subtitleslangs': [lang_code],
                'subtitlesformat': 'vtt/best', # Prioritize VTT
                'skip_download': True,
                'outtmpl': vtt_template.replace('.vtt', ''), # yt-dlp adds extension
                'quiet': True,
                'noprogress': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'verbose': False,
                'paths': {'home': downloads_path},
            }

            with yt_dlp.YoutubeDL(ydl_opts_final_vtt) as ydl:
                ydl.download([url])
            
            # Find the downloaded VTT file (yt-dlp might add details to filename)
            actual_vtt_path = None
            # Construct expected path based on sanitized title and lang code
            expected_vtt_path = os.path.join(downloads_path, f"{video_title}.{lang_code}.vtt")
            if os.path.exists(expected_vtt_path):
                 actual_vtt_path = expected_vtt_path
            else:
                 # Fallback: Search for *.{lang_code}.vtt in Downloads
                 for filename in os.listdir(downloads_path):
                      if filename.endswith(f".{lang_code}.vtt") and video_title in filename:
                           actual_vtt_path = os.path.join(downloads_path, filename)
                           break
            
            if not actual_vtt_path or not os.path.exists(actual_vtt_path):
                 ui.message(_("Failed to locate downloaded subtitle file."))
                 GlobalPlugin._download_thread = None
                 return

            # Convert VTT to TXT (simple conversion: remove timestamps and metadata)
            txt_path = os.path.join(downloads_path, f"{video_title}.{lang_code}.txt")
            try:
                with open(actual_vtt_path, 'r', encoding='utf-8') as vtt_file, \
                     open(txt_path, 'w', encoding='utf-8') as txt_file:
                    lines = vtt_file.readlines()
                    # Basic VTT parsing - skip header, metadata, timestamps
                    for line in lines:
                        line = line.strip()
                        if not line or line == 'WEBVTT' or '-->' in line or line.isdigit():
                            continue
                        # Remove VTT tags like <v Roger Bingham> or <i>
                        line = re.sub(r'<[^>]+>', '', line)
                        txt_file.write(line + '\n')
                
                os.remove(actual_vtt_path) # Remove intermediate VTT file
                ui.message(_("Subtitles downloaded and saved as TXT: {filename}").format(filename=os.path.basename(txt_path)))

            except Exception as conv_err:
                ui.message(_("Error converting subtitle to TXT."))
                print(f"Conversion error: {conv_err}")
                # Keep the VTT file if conversion fails
                ui.message(_("Subtitle saved in VTT format: {filename}").format(filename=os.path.basename(actual_vtt_path)))

        except yt_dlp.utils.DownloadError as e:
            ui.message(_("Download Error: Could not download selected subtitle."))
            print(f"yt-dlp final download error: {e}")
        except Exception as e:
            ui.message(_("An unexpected error occurred during final download/conversion."))
            print(f"Error in finish_download: {e}")
        finally:
            GlobalPlugin._download_thread = None # Clear thread reference

    # --- Script Handler --- 
    @scriptHandler.script(
        # Translators: Input gesture description
        description=_("Downloads subtitles for the current video"),
        category=_("Subtitle Downloader"),
        gesture="kb:NVDA+Shift+L"
    )
    def script_downloadSubtitles(self, gesture):
        if GlobalPlugin._download_thread and GlobalPlugin._download_thread.is_alive():
            ui.message(_("Subtitle download already in progress."))
            return

        url = self._get_video_url()
        if not url:
            ui.message(_("Could not detect a video URL in the current context."))
            return

        # Start download in a separate thread to avoid blocking NVDA
        GlobalPlugin._download_thread = threading.Thread(target=self._download_subtitle_thread, args=(url,))
        GlobalPlugin._download_thread.start()

    def terminate(self):
        # Clean up if necessary
        # self.save_settings()
        pass

    # --- Settings Handling (Placeholder) ---
    # def load_settings(self):
    #     pass
    # def save_settings(self):
    #     pass

