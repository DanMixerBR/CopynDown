import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile
from tkinter import filedialog
from tkinter import messagebox

import customtkinter as ctk
import requests
from PIL import Image

try:
    import pywinstyles
except ImportError:
    pywinstyles = None
    
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(os.path.realpath(sys.executable))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

bin_path = os.path.join(base_dir, "bin").replace("\\", "/")
os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ==========================================
        # CONSTANTES DE NOMENCLATURA DAS ABAS (MUDE AQUI!)
        # ==========================================
        self.TAB_VID = "Save Video"
        self.TAB_AUD = "Save Audio"
        self.TAB_C_VID = "Convert Video"
        self.TAB_C_AUD = "Convert Audio"
        # ==========================================

        self.version = "25.1"
        self.title(f"CopynDown")
        self.center_window(self, 830, 650)
        self.resizable(False, False)
        self.configure(fg_color="#181a1f") 

        self.status_id = None
        self.log_window = None
        self.current_process = None
        self.current_playlist_item = ""
        self.is_cancelling = False
        self.is_busy = False
        self.is_updating = False
        self.download_queue = []
        self.is_queue_running = False
        self.queue_window = None

        # ===================================================
        # [LINUX/MAC FIX] DETECÇÃO DE SISTEMA OPERACIONAL
        # ===================================================
        self.is_windows = os.name == 'nt'
        self.exe = ".exe" if self.is_windows else ""
        
        self.current_category = ctk.StringVar(value=self.TAB_VID)
        self.manual_selection_var = ctk.BooleanVar(value=False)

        self.config_file = os.path.join("bin", "config.txt").replace("\\", "/")
        self.ytdlp_path = os.path.join("bin", f"yt-dlp{self.exe}").replace("\\", "/") # <- Dinâmico
        self.cookies_path_default = os.path.join("bin", "cookies.txt").replace("\\", "/")
        self.version_file = os.path.join("bin", "version.txt").replace("\\", "/")
        
        self.re_progress = re.compile(r'(\d+\.\d+)%')
        
        self.valid_domains = [
            "youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", 
            "x.com", "facebook.com", "fb.watch", "twitch.tv", "clips.twitch.tv", 
            "vimeo.com", "reddit.com", "dailymotion.com", "dai.ly", "soundcloud.com",
            "linkedin.com", "pinterest.com", "snapchat.com", "bilibili.com", 
            "rumble.com", "bandcamp.com", "mixcloud.com", "kick.com", "odysee.com",
            "kwai.com", "kw.ai"
        ]
        
        self.full_logs = "--- Program Logs ---\n"
        
        self.DEF_AUTO_PASTE = True
        self.DEF_USE_COOKIES = True
        self.DEF_HIDE_OPTS = False

        self.config_data = {
            "General": {
                "auto_paste": self.DEF_AUTO_PASTE, "use_cookies": self.DEF_USE_COOKIES, 
                "cookies_path": self.cookies_path_default, "hide_options": self.DEF_HIDE_OPTS,
                "video_path": "~/Videos/CopynDown",
                "audio_path": "~/Music/CopynDown"
            },
            self.TAB_VID: {"thumb": True, "meta": False, "native_subs": False, "auto_subs": False, "embed_subs": False, "langs": "en", "trans_langs": "none"},
            self.TAB_AUD: {"thumb": True, "meta": True}
        }
        self.load_config()

        self.last_folder = self.config_data["General"]["video_path"]
        self.vcmd = (self.register(self.validate_url), '%P')

        self.startupinfo = None
        if self.is_windows: # <- Dinâmico
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE

        self.apply_window_icon(self)
        self.build_ui()
        self.select_pill(self.TAB_VID)
        
        self.bind("<FocusIn>", self.on_focus)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.check_ytdlp_updates, daemon=True).start()
        
    def on_closing(self):
        # Trava de Segurança: Mata processos pendentes antes de fechar
        if getattr(self, 'current_process', None):
            try:
                if self.is_windows:
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], capture_output=True, creationflags=0x08000000)
                else:
                    self.current_process.terminate()
            except: pass

        if getattr(self, 'status_id', None):
            self.after_cancel(self.status_id)
        self.destroy()
        os._exit(0)

    def safe_ui(self, func, *args, **kwargs):
        if self.winfo_exists():
            self.after(0, lambda: func(*args, **kwargs))

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=40, pady=(25, 0))

        logo_path = os.path.join("bin", "logo.png").replace("\\", "/")
        self.logo_img = None 

        if os.path.exists(logo_path):
            try:
                logo_img_data = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=logo_img_data, dark_image=logo_img_data, size=(32, 32))
            except Exception as e:
                print(f">>> Warning: Failed to load logo.png: {e}")
        else:
            print(">>> Warning: logo.png not found in bin folder.")        
            

        title_group = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_group.pack(side="left", padx=(0, 20))

        if self.logo_img:
            ctk.CTkLabel(title_group, image=self.logo_img, text="").pack(side="left", padx=(0, 8))

        text_column = ctk.CTkFrame(title_group, fg_color="transparent")
        text_column.pack(side="left")
       
        self.lbl_title = ctk.CTkLabel(text_column, text="CopynDown", font=("Segoe UI", 16, "bold"), text_color="#e0e0e0", height=18)
        self.lbl_title.pack(anchor="w", pady=(2, 0))

        self.lbl_version = ctk.CTkLabel(text_column, text=f"Version {self.version}", font=("Segoe UI", 11), text_color="gray", height=12)
        self.lbl_version.pack(anchor="w", pady=(0, 2), padx=(1, 0))

        self.nav_frame = ctk.CTkFrame(top_bar, fg_color="#21252b", corner_radius=20, height=40)
        self.nav_frame.pack(side="left", padx=(10, 0))

        self.pills = {}
        categories = [self.TAB_VID, self.TAB_AUD, self.TAB_C_VID, self.TAB_C_AUD]
        for cat in categories:
            btn = ctk.CTkButton(
                self.nav_frame, text=cat, width=95, height=35, corner_radius=18,
                font=("Segoe UI", 12, "bold"), fg_color="transparent", text_color="gray",
                hover_color="#282c34", command=lambda c=cat: self.select_pill(c)
            )
            btn.pack(side="left", padx=3, pady=3)
            self.pills[cat] = btn

        self.btn_settings = ctk.CTkButton(
            top_bar, text="⚙ Settings", width=90, height=35, corner_radius=10,
            font=("Segoe UI", 12), fg_color="#21252b", hover_color="#2c313a",
            command=self.show_settings
        )
        self.btn_settings.pack(side="right")

        self.main_card = ctk.CTkFrame(self, fg_color="#21252b", corner_radius=20)
        self.main_card.pack(fill="both", expand=True, padx=40, pady=(20, 20))

        self.desc_label = ctk.CTkLabel(self.main_card, text="", font=("Segoe UI", 13), text_color="gray")
        self.desc_label.pack(pady=(25, 5))

        # ==========================================================
        # 1. INPUT UNIVERSAL (0% Flicker)
        # ==========================================================
        self.input_frame = ctk.CTkFrame(self.main_card, corner_radius=10, border_width=1, border_color="#3a3f4b", fg_color="#181a1f")
        
        self.main_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Paste URL here", placeholder_text_color="#8a939e", height=38, font=("Segoe UI", 13), border_width=0, fg_color="transparent", bg_color="transparent", validate="key", validatecommand=self.vcmd)
        self.main_entry.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=5)
        self.main_entry.bind("<KeyRelease>", self.evaluate_ui_state)
        
        self.main_btn = ctk.CTkButton(self.input_frame, text="Paste", width=70, height=36, corner_radius=8, font=("Segoe UI", 12, "bold"), fg_color="#1f538d", hover_color="#14375e", command=self.paste_url_btn)
        self.main_btn.pack(side="right", padx=(0, 6), pady=6)

        # Apelidos mágicos para o código de download não quebrar!
        self.url_entry = self.main_entry
        self.src_entry = self.main_entry

        # O contêiner dinâmico voltou à vida!
        self.dynamic_container = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.dynamic_container.pack(fill="both", expand=True)

        self.divider = ctk.CTkFrame(self.dynamic_container, height=1, fg_color="#3a3f4b")
        self.divider.pack(fill="x", padx=40, pady=(15, 15))

        # ==========================================================
        # 2. PAINEL DE OPÇÕES UNIVERSAL (0% Flicker)
        # ==========================================================
        self.options_frame = ctk.CTkFrame(self.dynamic_container, fg_color="transparent")
        self.options_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_1 = ctk.CTkLabel(self.options_frame, text="Quality", font=("Segoe UI", 12), text_color="gray")
        self.lbl_1.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.menu_1 = ctk.CTkOptionMenu(self.options_frame, values=["1080p (H.264)", "720p"], height=35, font=("Segoe UI", 12), corner_radius=8, fg_color="#181a1f", button_color="#2c3e50")
        self.menu_1.grid(row=1, column=0, sticky="ew", padx=(0, 20), pady=(0, 15))

        self.lbl_2 = ctk.CTkLabel(self.options_frame, text="Format", font=("Segoe UI", 12), text_color="gray")
        self.lbl_2.grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.menu_2 = ctk.CTkOptionMenu(self.options_frame, values=["MP4", "MKV", "WEBM"], height=35, font=("Segoe UI", 12), corner_radius=8, fg_color="#181a1f", button_color="#2c3e50")
        self.menu_2.grid(row=1, column=1, sticky="ew", pady=(0, 15))

        self.lbl_3 = ctk.CTkLabel(self.options_frame, text="Video Codec", font=("Segoe UI", 12), text_color="gray")
        self.lbl_3.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.menu_3 = ctk.CTkOptionMenu(self.options_frame, values=["Original", "H.264", "H.265", "VP9"], height=35, font=("Segoe UI", 12), corner_radius=8, fg_color="#181a1f", button_color="#2c3e50")
        self.menu_3.grid(row=3, column=0, sticky="ew", padx=(0, 20))

        self.lbl_4 = ctk.CTkLabel(self.options_frame, text="Audio Codec", font=("Segoe UI", 12), text_color="gray")
        self.lbl_4.grid(row=2, column=1, sticky="w", pady=(0, 5))
        self.menu_4 = ctk.CTkOptionMenu(self.options_frame, values=["Original", "AAC", "MP3", "FLAC", "Opus", "None (Video Only)"], height=35, font=("Segoe UI", 12), corner_radius=8, fg_color="#181a1f", button_color="#2c3e50")
        self.menu_4.grid(row=3, column=1, sticky="ew")

        # Mais apelidos mágicos!
        self.quality_menu = self.menu_1
        self.format_menu = self.menu_2
        self.menu_conv_1 = self.menu_1
        self.menu_conv_2 = self.menu_2
        self.menu_conv_3 = self.menu_3
        self.menu_conv_4 = self.menu_4

        self.switch_advanced = ctk.CTkSwitch(
            self.dynamic_container, text="Advanced selection", 
            variable=self.manual_selection_var, font=("Segoe UI", 12),
            command=self.on_advanced_toggle
        )
        
        self.extract_audio_var = ctk.BooleanVar(value=False)
        self.switch_extract_audio = ctk.CTkSwitch(
            self.dynamic_container, text="Extract original audio", 
            variable=self.extract_audio_var, font=("Segoe UI", 12),
            command=self.on_extract_audio_toggle
        )

        self.action_frame = ctk.CTkFrame(self.dynamic_container, fg_color="transparent")
        
        inner_action = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        inner_action.pack(anchor="center")
        
        self.btn_download = ctk.CTkButton(
            inner_action, text="Download media", height=40, width=150, corner_radius=10,
            font=("Segoe UI", 13, "bold"), fg_color="#1f538d", hover_color="#14375e",
            command=self.handle_unified_download
        )
        self.btn_download.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(
            inner_action, text="Cancel", height=40, width=150, corner_radius=10,
            font=("Segoe UI", 13, "bold"), fg_color="#2c313a", hover_color="#a94442", state="disabled",
            command=self.cancel_download
        )
        self.btn_cancel.pack(side="left", padx=10)

        self.status_frame = ctk.CTkFrame(self.dynamic_container, fg_color="transparent")

        self.progress_label = ctk.CTkLabel(self.status_frame, text="Starting...", font=("Segoe UI", 11), text_color="gray")
        self.progress_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, height=6, progress_color="#1f538d", fg_color="#15171b")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(2, 0))

        # 3. RODAPÉ
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=(0, 20), padx=40)
        
        util_font = ("Segoe UI", 12)
        btn_style = {"fg_color": "#21252b", "hover_color": "#2c313a", "corner_radius": 10, "text_color": "#e0e0e0"}
        
        self.btn_open_folder = ctk.CTkButton(footer, text="📁 Open location", width=140, height=35, font=util_font, command=self.open_folder, **btn_style)
        self.btn_open_folder.pack(side="left")

        # NOVO BOTÃO DA FILA
        self.btn_queue = ctk.CTkButton(footer, text="📥 Queue (0)", width=110, height=35, font=util_font, command=self.show_queue, **btn_style)
        self.btn_queue.pack(side="left", padx=(10, 0))

        self.btn_about = ctk.CTkButton(footer, text="About", width=80, height=35, font=util_font, command=self.show_about, **btn_style)
        self.btn_about.pack(side="right")

        self.btn_show_logs = ctk.CTkButton(footer, text="View logs", width=100, height=35, font=util_font, command=self.show_logs, **btn_style)
        self.btn_show_logs.pack(side="right", padx=(0, 10))

    def browse_source(self):
        # Cria os filtros de extensão para a janela do Windows/Linux
        filetypes = [
            ("Media Files", "*.mp4 *.mkv *.webm *.avi *.mov *.mp3 *.m4a *.wav *.flac *.ogg *.opus *.aac"),
            ("Video Files", "*.mp4 *.mkv *.webm *.avi *.mov"),
            ("Audio Files", "*.mp3 *.m4a *.wav *.flac *.ogg *.opus *.aac"),
            ("All Files", "*.*")
        ]
        
        # Adiciona o parâmetro filetypes na chamada do filedialog
        file = filedialog.askopenfilename(title="Select Media File", filetypes=filetypes)
        
        if file:
            self.src_entry.delete(0, 'end')
            self.src_entry.insert(0, file.replace("\\", "/"))
            self.evaluate_ui_state()

    def select_pill(self, category):
        self.current_category.set(category)
        self.update_folder_context()
        
        for cat, btn in self.pills.items():
            if cat == category:
                btn.configure(fg_color="#1f538d", text_color="white", hover_color="#14375e")
            else:
                btn.configure(fg_color="transparent", text_color="gray", hover_color="#282c34")

        desc_map = {
            self.TAB_VID: "Video Downloader",
            self.TAB_AUD: "Audio Downloader",
            self.TAB_C_VID: "Video Converter",
            self.TAB_C_AUD: "Audio Converter"
        }
        self.desc_label.configure(text=desc_map.get(category, ""))
        
        # --- Limpeza Inteligente do Input ---
        is_convert = category in [self.TAB_C_VID, self.TAB_C_AUD]
        if getattr(self, 'last_tab_is_convert', None) != is_convert:
            self.main_entry.delete(0, 'end')
        self.last_tab_is_convert = is_convert

        if is_convert:
            self.main_entry.configure(placeholder_text="Select source media file...")
            self.main_btn.configure(text="Browse", fg_color="#34495e", hover_color="#2c3e50", command=self.browse_source)
        else:
            self.main_entry.configure(placeholder_text="Paste URL here")
            self.main_btn.configure(text="Paste", fg_color="#1f538d", hover_color="#14375e", command=self.paste_url_btn)

        # --- Painel Universal ---
        if category == self.TAB_VID:
            self.lbl_1.configure(text="Quality")
            self.menu_1.configure(values=["2160p (4K)", "1440p (QHD)", "1080p (AV1/VP9)", "1080p (H.264)", "720p", "480p", "360p"])
            self.menu_1.set("2160p (4K)")

            self.lbl_2.configure(text="Format")
            self.menu_2.configure(values=["MP4", "MKV", "WEBM"])
            self.menu_2.set("MP4")

            self.lbl_3.grid_remove()
            self.menu_3.grid_remove()
            self.lbl_4.grid_remove()
            self.menu_4.grid_remove()
            
        elif category == self.TAB_AUD:
            self.lbl_1.configure(text="Quality")
            self.menu_1.configure(values=["Auto", "High (320 kbps)", "Medium (192 kbps)", "Low (128 kbps)"])
            self.menu_1.set("Auto")

            self.lbl_2.configure(text="Format")
            self.menu_2.configure(values=["M4A", "MP3", "FLAC", "WAV", "Opus"])
            self.menu_2.set("M4A")

            self.lbl_3.grid_remove()
            self.menu_3.grid_remove()
            self.lbl_4.grid_remove()
            self.menu_4.grid_remove()

        elif category == self.TAB_C_VID:
            self.lbl_1.configure(text="Resolution")
            self.menu_1.configure(values=["Original", "2160p (4K)", "1440p (QHD)", "1080p", "720p", "480p", "360p"])
            self.menu_1.set("Original")

            self.lbl_2.configure(text="Output Format")
            self.menu_2.configure(values=["MP4", "MKV", "WEBM", "MOV", "AVI"])
            self.menu_2.set("MP4")

            self.lbl_3.configure(text="Video Codec")
            self.menu_3.configure(values=["Original", "H.264", "H.265", "VP9"])
            self.menu_3.set("Original")
            self.lbl_3.grid()
            self.menu_3.grid()

            self.lbl_4.configure(text="Audio Codec")
            self.menu_4.configure(values=["Original", "AAC", "MP3", "FLAC", "Opus", "None (Video Only)"])
            self.menu_4.set("Original")
            self.lbl_4.grid()
            self.menu_4.grid()

        elif category == self.TAB_C_AUD:
            self.lbl_1.configure(text="Bitrate")
            self.menu_1.configure(values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps"])
            self.menu_1.set("Auto")

            self.lbl_2.configure(text="Output Format")
            self.menu_2.configure(values=["M4A", "MP3", "FLAC", "WAV", "Opus", "Ogg"])
            self.menu_2.set("M4A")

            self.lbl_3.configure(text="Audio Channels")
            self.menu_3.configure(values=["Original", "Stereo (2.0)", "Mono (1.0)"])
            self.menu_3.set("Original")
            self.lbl_3.grid()
            self.menu_3.grid()

            self.lbl_4.configure(text="Sample Rate")
            self.menu_4.configure(values=["Original", "48000 Hz", "44100 Hz"])
            self.menu_4.set("Original")
            self.lbl_4.grid()
            self.menu_4.grid()

        self.evaluate_ui_state()
    
    def on_advanced_toggle(self):
        self.evaluate_ui_state() 
        if self.manual_selection_var.get():
            self.handle_unified_download()
    
    def on_extract_audio_toggle(self):
        if self.extract_audio_var.get():
            self.menu_1.configure(state="disabled")
            self.menu_3.configure(state="disabled")
            self.menu_4.configure(state="disabled")
        else:
            self.menu_1.configure(state="normal")
            self.menu_3.configure(state="normal")
            self.menu_4.configure(state="normal")
    
    def evaluate_ui_state(self, *args):
        cat = self.current_category.get()
        is_conv_vid = (cat == self.TAB_C_VID)
        is_conv_aud = (cat == self.TAB_C_AUD)
        is_convert = is_conv_vid or is_conv_aud
        
        hide_mode = self.config_data.get("General", {}).get("hide_options", self.DEF_HIDE_OPTS)
        
        if is_convert:
            is_valid = bool(self.main_entry.get().strip())
            is_playlist = False
        else:
            is_valid = self.is_valid_media_url(self.main_entry.get().strip())
            is_playlist = is_valid and "list=" in self.main_entry.get().lower()
            
        current_state = (cat, is_valid, self.is_updating, self.manual_selection_var.get(), is_playlist, hide_mode)
        if getattr(self, "last_ui_state", None) == current_state:
            return 
            
        self.last_ui_state = current_state

        # ==========================================================
        # O SEGREDO ANTI-PISCAR V2: Empacotador Inteligente (Smart Pack)
        # ==========================================================
        def smart_pack(widget, show, **kwargs):
            is_packed = (widget.winfo_manager() == "pack")
            if show:
                if not is_packed:
                    # Primeira vez: empacota na ordem certa
                    widget.pack(**kwargs)
                else:
                    # Atualização (O BUG MORRE AQUI): Removemos a ordem para forçar o Tkinter a ler as novas margens!
                    kwargs.pop('before', None)
                    widget.pack_configure(**kwargs)
            elif not show and is_packed:
                widget.pack_forget()

        # Se estiver atualizando o app...
        if self.is_updating:
            smart_pack(self.input_frame, False)
            smart_pack(self.options_frame, False)
            smart_pack(self.switch_advanced, False)
            smart_pack(self.switch_extract_audio, False)
            smart_pack(self.action_frame, False)
            smart_pack(self.status_frame, True, fill="x", padx=40, pady=(10, 0))
            return 

        # 1. Área do Topo SEMPRE FIXA
        smart_pack(self.input_frame, show=True, fill="x", padx=40, pady=(0, 10), before=self.dynamic_container)

        if is_convert:
            self.btn_download.configure(text="Convert media")
        else:
            self.btn_download.configure(text="Download media")

        show_options = True
        if not is_convert and hide_mode and not is_valid:
            show_options = False
            
        show_status = show_options or getattr(self, 'is_queue_running', False)
        
        # ======================================================
        # LÓGICA DE ESPAÇAMENTO DINÂMICO (PIXEL PERFECT)
        # ======================================================
        if cat == self.TAB_C_AUD:
            btn_pady = (15, 10) 
        elif cat == self.TAB_C_VID:
            # 45px compensa exatamente a ausência do Switch para o botão não pular de uma aba pra outra!
            btn_pady = (45, 10)
        else:
            btn_pady = (15, 10)

        status_pady = (15, 0)
        # ======================================================

        # A. Barra de Status
        smart_pack(self.status_frame, show=show_status, fill="x", padx=40, pady=status_pady)
        
        # B. Botões 
        smart_pack(self.action_frame, show=show_status, fill="x", padx=40, pady=btn_pady, before=self.status_frame)

        # C. Painel Único de Opções
        smart_pack(self.options_frame, show=show_options, fill="x", padx=40, pady=0, before=self.action_frame)
        
        # D. Switches 
        smart_pack(self.switch_extract_audio, show=(show_options and is_conv_aud), anchor="w", padx=40, pady=(15, 0), before=self.action_frame)
        smart_pack(self.switch_advanced, show=(show_options and not is_convert), anchor="w", padx=40, pady=(0, 15), before=self.action_frame)

        # 4. Controle do Switch Avançado
        if is_valid and not is_convert:
            if is_playlist:
                self.switch_advanced.configure(state="disabled")
                if self.manual_selection_var.get():
                    self.manual_selection_var.set(False)
            else:
                self.switch_advanced.configure(state="normal")
        else:
            self.switch_advanced.configure(state="disabled")
            if self.manual_selection_var.get():
                self.manual_selection_var.set(False)

    def build_base_cmd(self, is_json=False):
        cmd = [self.ytdlp_path, "-i"]
        gen_cfg = self.config_data.get("General", {})
        
        if gen_cfg.get("use_cookies", True):
            c_path = gen_cfg.get("cookies_path", self.cookies_path_default)
            try:
                if os.path.exists(c_path) and os.path.getsize(c_path) > 0:
                    cmd.extend(["--cookies", c_path])
                else:
                    self.safe_ui(self.add_to_log, f"Warning: Cookies.txt file not found or empty. Continuing without cookies.")
            except Exception as e:
                self.safe_ui(self.add_to_log, f"Warning: Error verifying cookies.txt ({e}). Continuing without cookies.")
        
        if is_json: cmd.append("-J")
        else: cmd.append("--newline")
        return cmd

    def apply_window_icon(self, window):
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        
        if self.is_windows:
            # 1. Ícone do Windows
            icon_path = os.path.join(base_dir, "bin", "icon.ico").replace("\\", "/")
            if os.path.exists(icon_path):
                try: 
                    window.after(200, lambda: window.iconbitmap(icon_path))
                except Exception as e: 
                    print(f">>> Warning: Failed to load icon.ico: {e}")
            else:
                print(">>> Warning: icon.ico not found in bin folder.") 
                
            # 2. Barra Escura Universal (Com Filtro Anti-Recursão)
            if pywinstyles:
                def apply_header(event=None):
                    # A TRAVA DE SEGURANÇA: Só executa se o evento veio da própria janela
                    if event and event.widget != window:
                        return
                    try:
                        pywinstyles.change_header_color(window, color="#181a1f")
                    except Exception as e:
                        print(f">>> Warning: Failed to apply header color: {e}")
                
                # Pinta a barra assim que a janela nasce
                window.after(100, apply_header)
                
                # O Vigia: Repinta a barra se a janela for minimizada e restaurada
                window.bind("<Map>", lambda e: window.after(10, lambda: apply_header(e)), add="+")
                    
        else:
            # 3. Ícone do Linux/Mac
            icon_path = os.path.join(base_dir, "bin", "icon.png").replace("\\", "/")
            if os.path.exists(icon_path):
                try: 
                    from tkinter import PhotoImage
                    img_tk = PhotoImage(file=icon_path)
                    window.after(200, lambda: window.iconphoto(False, img_tk))
                except Exception as e: 
                    print(f">>> Warning: Failed to load icon.png: {e}")
            else:
                print(">>> Warning: icon.png not found in bin folder.") 

    def show_logs(self):
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = ctk.CTkToplevel(self)
            self.apply_window_icon(self.log_window)
            self.log_window.title("Execution Logs")
            self.center_window(self.log_window, 600, 400)
            self.log_window.transient(self)
            self.log_window.resizable(False, False)
            self.log_window.configure(fg_color="#181a1f")
            
            self.log_textbox = ctk.CTkTextbox(self.log_window, width=580, height=310, font=("Consolas", 11))
            self.log_textbox.pack(padx=10, pady=10, fill="both", expand=True)
            self.log_textbox.insert("0.0", self.full_logs)
            self.log_textbox.see("end")
            
            log_btn_frame = ctk.CTkFrame(self.log_window, fg_color="transparent")
            log_btn_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkButton(log_btn_frame, text="Copy All", width=100, height=28, fg_color="#1f538d", hover_color="#14375e", command=self.copy_logs).pack(side="left", padx=(0, 10))
            ctk.CTkButton(log_btn_frame, text="Clear Log", width=100, height=28, fg_color="#2c313a", hover_color="#a94442", command=self.clear_logs).pack(side="left")
        else:
            self.log_window.deiconify()

    def copy_logs(self):
        self.clipboard_clear()
        self.clipboard_append(self.log_textbox.get("1.0", "end-1c"))
        self.add_to_log(">>> Logs copied to clipboard.")

    def clear_logs(self):
        self.full_logs = ""
        self.log_textbox.delete("1.0", "end")
        self.add_to_log(">>> Logs cleared.")
    
    def add_to_log(self, text):
        self.full_logs += text + "\n"
        if self.log_window and self.log_window.winfo_exists():
            self.log_textbox.insert("end", text + "\n")
            self.log_textbox.see("end")

    def cancel_download(self):
        if self.current_process and not self.is_cancelling:
            self.btn_cancel.configure(state="disabled", text="Cancelling...")
            try:
                self.is_cancelling = True
                self.add_to_log(">>> Attempting to force close process...")
                # ===================================================
                # [LINUX/MAC FIX] FECHAR PROCESSOS DE FORMA NATIVA
                # ===================================================
                if self.is_windows:
                    result = subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], encoding='oem', errors='replace', capture_output=True, startupinfo=self.startupinfo)
                    if result.stdout: self.add_to_log(result.stdout.strip())
                    if result.stderr: self.add_to_log(result.stderr.strip())
                else:
                    self.current_process.terminate()
            except Exception as e:
                self.add_to_log(f">>> Failed to close process: {e}")
                self.is_cancelling = False

    def on_focus(self, event):
        try:
            if not self.config_data.get("General", {}).get("auto_paste", True): return
            
            if self.current_category.get() in [self.TAB_C_VID, self.TAB_C_AUD]: return
                
            text = self.clipboard_get()[:2000]
            if self.is_valid_media_url(text):
                if self.url_entry.get() != text:
                    if self.status_id: 
                        self.after_cancel(self.status_id)
                        self.status_id = None
                    self.url_entry.delete(0, 'end')
                    self.url_entry.insert(0, text)
                    
                    self.evaluate_ui_state()
                    
                    if not getattr(self, 'is_busy', False) and not getattr(self, 'is_updating', False):
                        if self.status_id: 
                            self.after_cancel(self.status_id)
                            self.status_id = None
                        self.reset_status(text="URL Auto-Detected!")
                        self.schedule_reset(5000)
        except Exception as e:
            pass

    def paste_url_btn(self):
        try:
            clipboard = self.clipboard_get()[:2000]
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, clipboard)
            
            self.evaluate_ui_state()
            
            if not getattr(self, 'is_busy', False) and not getattr(self, 'is_updating', False):
                if self.is_valid_media_url(clipboard):
                    self.reset_status(text="URL Detected!")
                    self.schedule_reset(5000)
                else:
                    self.reset_status("Invalid URL!", color="#f85149")
                    self.schedule_reset(5000)
                    
        except Exception as e:
            if e.__class__.__name__ != 'TclError': 
                self.add_to_log(f">>> Unexpected error reading clipboard: {e}")
            
    def validate_url(self, P): return len(P) <= 2000
    
    def is_valid_media_url(self, text_url):
        if not text_url or len(text_url) < 12: return False
        return text_url.startswith("https://") and any(d in text_url.lower() for d in self.valid_domains)
        
    def center_window(self, win, width, height):
        win.update_idletasks() 
        x = int((win.winfo_screenwidth() / 2) - (width / 2))
        y = int((win.winfo_screenheight() / 2) - (height / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")
        
    def apply_modal_fix(self, modal_win):
        # Resolve o congelamento fatal do Windows ao minimizar janelas com grab_set
        def on_unmap(e):
            if e.widget is self and modal_win.winfo_exists():
                modal_win.grab_release() # Solta o bloqueio ao minimizar

        def on_map(e):
            if e.widget is self and modal_win.winfo_exists():
                modal_win.grab_set()     # Restaura o bloqueio ao voltar à tela

        id_unmap = self.bind("<Unmap>", on_unmap, add="+")
        id_map = self.bind("<Map>", on_map, add="+")

        # Limpa os eventos da memória quando a janela for fechada (Prevenção de Memory Leak)
        def on_destroy(e):
            if e.widget is modal_win:
                self.unbind("<Unmap>", id_unmap)
                self.unbind("<Map>", id_map)
                
        modal_win.bind("<Destroy>", on_destroy, add="+")

    def reset_status(self, text="Ready!", color="gray"):
        if self.status_id: 
            self.after_cancel(self.status_id)
            self.status_id = None
        self.progress_label.configure(text=text, text_color=color)
        if self.current_category.get() in [self.TAB_C_VID, self.TAB_C_AUD] and self.is_busy:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.stop()
            self.progress_bar.set(0)
            self.progress_bar.configure(progress_color="#1f538d")
        self.evaluate_ui_state()

    def schedule_reset(self, time=5000):
        if self.status_id: self.after_cancel(self.status_id)
        self.status_id = self.after(time, self.reset_status)

    def set_terminal_state(self, label_text, log_msg=""):
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.stop()
        self.progress_label.configure(text=label_text, text_color="#f85149")
        self.progress_bar.configure(progress_color="#f85149")
        self.progress_bar.set(1)
        if log_msg: self.add_to_log(log_msg)

    def status_error(self, log_msg=""):
        self.set_terminal_state("Process Error!", log_msg)
        
    def status_canceled(self, log_msg=">>> Process Canceled!"):
        self.set_terminal_state("Canceled!", log_msg)        
        
    def status_update_error(self, filename=None, size_mb=None, custom_msg=None):
        # FIX: Define o fallback seguro dependendo do sistema operacional
        fallback_name = "CopynDown_Windows.zip" if self.is_windows else "CopynDown_Linux.zip"
        
        f_name = filename if filename else fallback_name
        f_size = f"{size_mb:.1f} MB" if size_mb is not None else "Unknown size"
        error_msg = custom_msg if custom_msg else f"ERROR: The file '{f_name}' ({f_size}) appears corrupted.\nDeleted for safety."
        
        self.set_terminal_state("Update Aborted!", error_msg)
        
        parent_win = self.about_win if (hasattr(self, 'about_win') and self.about_win.winfo_exists()) else self
        self.safe_ui(messagebox.showerror, "Aborted", error_msg, parent=parent_win)
           

    def add_subtitle_args(self, base_cmd, cfg):
        has_subs = False
        if cfg.get("native_subs"):
            base_cmd.append("--write-subs")
            has_subs = True
        if cfg.get("auto_subs"):
            base_cmd.append("--write-auto-subs")
            has_subs = True
            
        if has_subs:
            source = cfg.get("langs", "en")
            target = cfg.get("trans_langs", "none")
            sub_lang_str = f"{target}-{source}*" if target != "none" else f"{source}*"
            base_cmd.extend(["--sub-langs", sub_lang_str, "--convert-subs", "srt"])
            if cfg.get("embed_subs"): base_cmd.append("--embed-subs")
        return base_cmd

    def download_video(self):
        url = self.url_entry.get().strip()
        cfg = self.config_data[self.TAB_VID]
        real_path = os.path.expanduser(self.config_data["General"]["video_path"])
        
        if any(d in url for d in ["instagram.com", "tiktok.com", "kwai.com", "kw.ai", "twitter.com", "x.com", "facebook.com", "fb.watch", "reddit.com", "linkedin.com", "pinterest.com", "snapchat.com"]):
            out_tmpl = "%(uploader)s [%(id)s].%(ext)s"
        else:
            out_tmpl = "%(title)s.%(ext)s"
        
        base_cmd = self.build_base_cmd()
        vfmt = self.format_menu.get().lower()
        
        if cfg["thumb"] and (self.manual_selection_var.get() or vfmt != "webm"): 
            base_cmd.append("--embed-thumbnail")
        if cfg["meta"]: base_cmd.append("--embed-metadata")
        
        base_cmd = self.add_subtitle_args(base_cmd, cfg)
            
        if self.manual_selection_var.get():
            self.open_manual_selection(url, base_cmd, out_tmpl, ["MP4", "MKV", "WEBM"])
            return
            
        res_map = {"360p": "360", "480p": "480", "720p": "720", "1080p (H.264)": "1080", "1080p (AV1/VP9)": "1080", "1440p (QHD)": "1440", "2160p (4K)": "2160"}
        selected_quality = self.quality_menu.get()
        
        # ==============================================================
        # TRAVA DE COMPATIBILIDADE WEBM NO DOWNLOAD (AUTO-FIX)
        # ==============================================================
        if vfmt == "webm" and selected_quality == "1080p (H.264)":
            selected_quality = "1080p (AV1/VP9)"
            self.safe_ui(self.add_to_log, "[Auto-Fix] Forced VP9/Opus stream for WEBM download compatibility.")
        # ==============================================================
        
        res = res_map[selected_quality]
        
        if selected_quality == "1080p (H.264)": search_str = f"res:{res},vcodec:avc1,aext:m4a"
        elif vfmt == "mp4": search_str = f"res:{res},aext:m4a"
        elif vfmt == "webm": search_str = f"res:{res},vcodec:vp9,aext:opus"
        elif vfmt == "mkv": search_str = f"res:{res},aext:opus"
        else: search_str = f"res:{res}"

        cmd = base_cmd + ["-S", search_str, "--merge-output-format", vfmt, "--remux-video", vfmt, "-o", f"{real_path}/{out_tmpl}", "-o", f"subtitle:{real_path}/subtitles/{out_tmpl}", url]
        self.run_command(cmd, task_name=url)

    def download_music(self):
        url = self.url_entry.get().strip()
        cfg = self.config_data[self.TAB_AUD]
        real_path = os.path.expanduser(self.config_data["General"]["audio_path"])
        afmt, q = self.format_menu.get().lower(), self.quality_menu.get()
        
        base_cmd = self.build_base_cmd() + ["-x"]
        if not self.manual_selection_var.get(): base_cmd.extend(["--audio-format", afmt])
        
        if cfg["thumb"] and (self.manual_selection_var.get() or afmt != "wav"): base_cmd.append("--embed-thumbnail")
        if cfg["meta"] and (self.manual_selection_var.get() or afmt != "wav"): 
            base_cmd.extend(["--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s"])
            
        if self.manual_selection_var.get():
            self.open_manual_selection(url, base_cmd, "%(playlist_index&{}. |)s%(title)s.%(ext)s", ["M4A", "MP3", "FLAC", "WAV", "Opus"])
            return
            
        bitrate_map = {"Low (128 kbps)": "128k", "Medium (192 kbps)": "192k", "High (320 kbps)": "320k"}
        if q != "Auto": base_cmd.extend(["--audio-quality", bitrate_map.get(q)])
            
        cmd = base_cmd + ["-o", f"{real_path}/%(playlist_index&{{}}. |)s%(title)s.%(ext)s", url]
        self.run_command(cmd, task_name=url)

    def convert_media(self, media_type="video"):
        src = self.src_entry.get().strip()
        
        if not os.path.exists(src):
            self.status_error("ERROR: Source file does not exist.")
            return

        is_video = media_type == "video"
        base_name = os.path.splitext(os.path.basename(src))[0]
        ext_final = self.menu_conv_2.get().lower()
        
        if not is_video and self.extract_audio_var.get():
            suffix = "extracted"
        else:
            suffix = "converted"
        
        gen_cfg = self.config_data.get("General", {})
        save_dir = os.path.expanduser(gen_cfg.get("video_path") if is_video else gen_cfg.get("audio_path"))
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        dst = os.path.join(save_dir, f"{base_name}_{suffix}.{ext_final}").replace("\\", "/")
        if src == dst:
            dst = os.path.join(save_dir, f"{base_name}_new.{ext_final}").replace("\\", "/")
            
        # ===================================================
        # [LINUX/MAC FIX] FFMPEG SEM .EXE
        # ===================================================
        ffmpeg_exe = os.path.join("bin", f"ffmpeg{self.exe}").replace("\\", "/")
        if not os.path.exists(ffmpeg_exe):
            try:
                # Tenta rodar o FFmpeg do sistema silenciosamente para ver se ele existe
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                ffmpeg_exe = "ffmpeg"
            except Exception:
                # Se der erro, avisa na tela e cancela a conversão!
                self.safe_ui(self.status_error, "ERROR: FFmpeg is missing! Please check your 'bin' folder.")
                return
            
        cmd = [ffmpeg_exe, "-y", "-i", src]
        
        if is_video:
            vc_map = {"Original": "copy", "H.264": "libx264", "H.265": "libx265", "VP9": "libvpx-vp9"}
            ac_map = {"Original": "copy", "AAC": "aac", "MP3": "libmp3lame", "FLAC": "flac", "Opus": "libopus", "None (Video Only)": "none"}
            
            vc = vc_map.get(self.menu_conv_3.get(), "copy")
            ac = ac_map.get(self.menu_conv_4.get(), "copy")            
            
            # ==============================================================
            # NOVA LÓGICA DE RESOLUÇÃO (COM AUTO-FIX)
            # ==============================================================
            res_choice = self.menu_conv_1.get()
            scale_filter = None
            if res_choice != "Original" and vc != "none":
                h_map = {"2160p (4K)": "2160", "1440p (QHD)": "1440", "1080p": "1080", "720p": "720", "480p": "480", "360p": "360"}
                target_h = h_map.get(res_choice)
                
                if target_h:
                    # scale=-2 garante que a largura seja sempre par (exigência do H.264/H.265) preservando a proporção!
                    scale_filter = f"scale=-2:{target_h}" 
                    
                    # FFmpeg NÃO pode redimensionar sem recodificar. Força a recodificação se estiver no "Original":
                    if vc == "copy":
                        if ext_final == "webm":
                            vc = "libvpx-vp9"
                            self.safe_ui(self.add_to_log, f"[Auto-Fix] Forced VP9 codec to allow scaling to {target_h}p.")
                        else:
                            vc = "libx264"
                            self.safe_ui(self.add_to_log, f"[Auto-Fix] Forced H.264 codec to allow scaling to {target_h}p.")
            # ==============================================================
            
            # ==============================================================
            # TRAVAS DE COMPATIBILIDADE INTELIGENTES (AUTO-FIX)
            # ==============================================================
            if ext_final == "avi":
                if vc == "copy": 
                    vc = "libx264"
                    self.safe_ui(self.add_to_log, "[Auto-Fix] Forced H.264 codec for AVI compatibility.")
                if ac in ["copy", "aac", "flac", "libopus"]: 
                    ac = "libmp3lame"
                    self.safe_ui(self.add_to_log, "[Auto-Fix] Forced MP3 codec for AVI compatibility.")
                    
            elif ext_final == "webm":
                # WebM NÃO aceita H.264/H.265 nem AAC/MP3/FLAC.
                if vc in ["copy", "libx264", "libx265"]:
                    vc = "libvpx-vp9"
                    self.safe_ui(self.add_to_log, "[Auto-Fix] Forced VP9 codec for WEBM compatibility.")
                if ac in ["copy", "aac", "libmp3lame", "flac"]:
                    ac = "libopus"
                    self.safe_ui(self.add_to_log, "[Auto-Fix] Forced Opus codec for WEBM compatibility.")
            # ==============================================================
            
            if vc == "none": cmd.append("-vn")
            else:
                cmd.extend(["-c:v", vc])
                
                if scale_filter:
                    cmd.extend(["-vf", scale_filter])
                
                if vc == "libvpx-vp9":
                    cmd.extend(["-crf", "20", "-b:v", "0", "-row-mt", "1", "-cpu-used", "4"])
                
                elif vc == "libx264":
                    # Adicionado pix_fmt para máxima compatibilidade universal
                    cmd.extend(["-crf", "18", "-preset", "faster", "-pix_fmt", "yuv420p"])
                    
                elif vc == "libx265":
                    # Adicionado pix_fmt para máxima compatibilidade universal
                    cmd.extend(["-crf", "22", "-preset", "faster", "-tag:v", "hvc1"])
                
                elif vc != "copy": 
                    cmd.extend(["-crf", "18"])
                
            if ac == "none": cmd.append("-an")
            else:
                cmd.extend(["-c:a", ac])
                if ac != "copy" and ac != "flac": cmd.extend(["-b:a", "192k"])
        else:
            cmd.append("-vn")
            dst_fmt = self.menu_conv_2.get().lower()
            
            # --- LÓGICA DE EXTRAÇÃO E TRAVA DE COMPATIBILIDADE ---
            if self.extract_audio_var.get():
                if dst_fmt in ["mp3", "wav"]:
                    # Trava Inteligente: Impede cópia pura para MP3/WAV. Força recodificação na melhor qualidade possível.
                    ac_map = {"mp3": "libmp3lame", "wav": "pcm_s16le"}
                    ac = ac_map.get(dst_fmt)
                    cmd.extend(["-c:a", ac])
                    if dst_fmt == "mp3": cmd.extend(["-b:a", "320k"])
                    self.safe_ui(self.add_to_log, f"[Auto-Fix] Forced {ac} for {dst_fmt.upper()} compatibility during extraction.")
                else:
                    cmd.extend(["-c:a", "copy"])
                    
            # --- LÓGICA DE RECODIFICAÇÃO (Com bugs corrigidos!) ---
            else:
                ac_map = {"m4a": "aac", "mp3": "libmp3lame", "flac": "flac", "wav": "pcm_s16le", "opus": "libopus", "ogg": "libvorbis"}
                ac = ac_map.get(dst_fmt, "copy")
                cmd.extend(["-c:a", ac])
                
                bitrate = self.menu_conv_1.get()
                sample_rate = self.menu_conv_4.get()
                channels = self.menu_conv_3.get()
                
                if bitrate != "Auto" and ac != "copy" and ac != "flac":
                    # Fix: Substitui " kbps" por "k" para o formato exato do FFmpeg (ex: 320k)
                    cmd.extend(["-b:a", bitrate.replace(" kbps", "k")])
                    
                if sample_rate != "Original" and ac != "copy":
                    cmd.extend(["-ar", sample_rate.replace(" Hz", "")])
                    
                # Fix: Os canais de áudio agora são enviados para o FFmpeg!
                if channels != "Original" and ac != "copy":
                    cmd.extend(["-ac", "2" if "Stereo" in channels else "1"])
            
        cmd.append(dst)
        self.run_command(cmd, task_name=base_name)

    def open_manual_selection(self, url, base_cmd, output_template, container_options):
        self.is_busy = True
        manual_win = ctk.CTkToplevel(self)
        self.apply_window_icon(manual_win)
        manual_win.title("Manual Format Selection")
        self.center_window(manual_win, 750, 550)
        manual_win.resizable(False, False)
        manual_win.transient(self)
        manual_win.grab_set()
        self.apply_modal_fix(manual_win)
        manual_win.configure(fg_color="#181a1f")

        def on_close(): 
            self.is_busy = False
            self.reset_status()
            manual_win.destroy()
            self.manual_selection_var.set(False)
            self.evaluate_ui_state()
            
        manual_win.protocol("WM_DELETE_WINDOW", on_close)

        loading_frame = ctk.CTkFrame(manual_win, fg_color="transparent")
        loading_frame.pack(expand=True, fill="both")
        
        ctk.CTkLabel(loading_frame, text="Fetching formats and thumbnail...", font=("Segoe UI", 16)).pack(pady=(250, 15))
        spinner = ctk.CTkProgressBar(loading_frame, mode="indeterminate", width=300)
        spinner.pack()
        spinner.start()

        def fetch_data_task():
            try:
                cmd_json = self.build_base_cmd(is_json=True) + ["--no-playlist", url]
                output = subprocess.check_output(cmd_json, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
                
                video_data = json.loads(output)
                formats = video_data.get('formats', [])
                thumb_url = video_data.get('thumbnail', None)
                video_title = video_data.get('title', 'Unknown Video')

                self.safe_ui(build_ui_task, formats, thumb_url, video_title)
                
            except subprocess.CalledProcessError as e:
                self.safe_ui(handle_error, f"Failed to fetch formats:\n{e.output.strip() if e.output else 'Unknown error'}")
            
            except Exception as e:
                self.safe_ui(handle_error, f"Failed to parse data: {e}")

        def handle_error(error_msg):
            self.is_busy = False
            if manual_win.winfo_exists(): manual_win.destroy()
            self.manual_selection_var.set(False)
            self.evaluate_ui_state()
            self.status_error(error_msg)

        def build_ui_task(formats, thumb_url, video_title):
            if not manual_win.winfo_exists(): return
            spinner.stop()
            loading_frame.destroy()

            self.selected_vid = ctk.StringVar(value="")
            self.selected_aud = ctk.StringVar(value="")

            header_frame = ctk.CTkFrame(manual_win, fg_color="transparent")
            header_frame.pack(pady=10, padx=20, fill="x")

            if thumb_url:
                try:
                    r = requests.get(thumb_url, stream=True, timeout=5)
                    if r.status_code == 200:
                        img_data = Image.open(io.BytesIO(r.content))
                        ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(160, 90))
                        ctk.CTkLabel(header_frame, image=ctk_img, text="").pack(side="left", padx=(0, 15))
                except Exception as e: self.add_to_log(f"Warning: Could not load thumbnail: {e}")

            ctk.CTkLabel(header_frame, text=video_title, font=("Segoe UI", 16, "bold"), wraplength=500, justify="left").pack(side="left", anchor="w", fill="x", expand=True)

            lists_frame = ctk.CTkFrame(manual_win, fg_color="transparent")
            lists_frame.pack(padx=20, pady=5, fill="both", expand=True)

            video_frame = ctk.CTkFrame(lists_frame, fg_color="#21252b", corner_radius=10)
            video_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
            ctk.CTkLabel(video_frame, text="Select Video", font=("Segoe UI", 14, "bold")).pack(pady=10)
            scroll_video = ctk.CTkScrollableFrame(video_frame, fg_color="transparent")
            scroll_video.pack(fill="both", expand=True, padx=5, pady=5)

            audio_frame = ctk.CTkFrame(lists_frame, fg_color="#21252b", corner_radius=10)
            audio_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
            ctk.CTkLabel(audio_frame, text="Select Audio", font=("Segoe UI", 14, "bold")).pack(pady=10)
            scroll_audio = ctk.CTkScrollableFrame(audio_frame, fg_color="transparent")
            scroll_audio.pack(fill="both", expand=True, padx=5, pady=5)

            ctk.CTkRadioButton(scroll_video, text="None", variable=self.selected_vid, value="none").pack(anchor="w", pady=5, padx=5)
            ctk.CTkRadioButton(scroll_audio, text="None", variable=self.selected_aud, value="none").pack(anchor="w", pady=5, padx=5)

            for f in formats:
                fmt_id = f.get('format_id', 'N/A')
                ext = f.get('ext', 'N/A')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = f"{filesize / (1024 * 1024):.1f} MB" if filesize else "Unknown size"
                
                if 'mhtml' in ext or 'sb' in ext: continue

                if vcodec == 'none' and acodec != 'none':
                    ctk.CTkRadioButton(scroll_audio, text=f"ID: {fmt_id} | {ext.upper()} | {acodec} | {size_mb}", variable=self.selected_aud, value=fmt_id).pack(anchor="w", pady=5, padx=5)
                elif vcodec != 'none':
                    res = f.get('resolution', 'Unknown')
                    if res == 'Unknown': res = f"{f.get('width', '?')}x{f.get('height', '?')}"
                    type_note = "[Video+Audio]" if acodec != 'none' else "[Video Only]"
                    ctk.CTkRadioButton(scroll_video, text=f"ID: {fmt_id} | {res} | {ext.upper()} | {vcodec} {type_note} | {size_mb}", variable=self.selected_vid, value=fmt_id).pack(anchor="w", pady=5, padx=5)

            footer_frame = ctk.CTkFrame(manual_win, fg_color="transparent")
            footer_frame.pack(pady=15, padx=20, fill="x")

            ctk.CTkLabel(footer_frame, text="Output Format:").pack(side="left", padx=5)
            self.format_adv = ctk.CTkOptionMenu(footer_frame, values=container_options, fg_color="#21252b", button_color="#2c313a")
            self.format_adv.set(container_options[0])
            if len(container_options) == 1:
                self.format_adv.configure(state="disabled")
            self.format_adv.pack(side="left", padx=5)

            def start():
                vid, aud = self.selected_vid.get(), self.selected_aud.get()
                if not vid and not aud:
                    self.safe_ui(messagebox.showerror, "Error", "Please select at least one Video or Audio track.", parent=manual_win)
                    return
                    
                if vid != "none" and aud != "none" and vid and aud: fmt = f"{vid}+{aud}"
                elif vid != "none" and vid: fmt = vid            
                elif aud != "none" and aud: fmt = aud
                else:
                    self.safe_ui(messagebox.showerror, "Error", "Invalid selection.", parent=manual_win)
                    return

                ext_final = self.format_adv.get().lower()
                current_tab = self.current_category.get()
                
                gen_cfg = self.config_data.get("General", {})
                is_video = current_tab in [self.TAB_VID, self.TAB_C_VID]
                base_path = os.path.expanduser(gen_cfg.get("video_path") if is_video else gen_cfg.get("audio_path"))
                
                clean_cmd = base_cmd.copy()
                if ext_final in ["webm", "wav"]:
                    clean_cmd = [arg for arg in clean_cmd if arg not in ("--embed-thumbnail", "--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "--embed-subs")]

                if current_tab == self.TAB_AUD: cmd = clean_cmd + ["-f", fmt, "--audio-format", ext_final, "-o", f"{base_path}/{output_template}", url]
                else: cmd = clean_cmd + ["-f", fmt, "--merge-output-format", ext_final, "--remux-video", ext_final, "-o", f"{base_path}/{output_template}", "-o", f"subtitle:{base_path}/subtitles/{output_template}", url]
                    
                manual_win.destroy()
                self.manual_selection_var.set(False)
                self.evaluate_ui_state()
                self.run_command(cmd, task_name=url)

            ctk.CTkButton(footer_frame, text="Download selected", font=("Segoe UI", 12, "bold"), fg_color="#1f538d", command=start, height=35).pack(side="right", padx=5)

        threading.Thread(target=fetch_data_task, daemon=True).start()

    def handle_unified_download(self):
        tab = self.current_category.get()
        
        if tab == self.TAB_C_VID:
            self.convert_media(media_type="video")
            return
        elif tab == self.TAB_C_AUD:
            self.convert_media(media_type="audio")
            return
            
        url = self.url_entry.get().strip()
        if not self.is_valid_media_url(url):
            self.status_error("ERROR: Invalid URL.")
            return
        
        if not os.path.exists(self.ytdlp_path):
            self.status_error("ERROR: yt-dlp is missing! Please place it in the 'bin' folder.")
            return
        
        if tab == self.TAB_VID: self.download_video()
        elif tab == self.TAB_AUD: self.download_music()

    def download_progress(self, p):
        self.progress_bar.set(p/100)
        # Verifica se existe um item de playlist na memória, se não, fica vazio
        item_text = getattr(self, 'current_playlist_item', '')
        self.progress_label.configure(text=f"Downloading{item_text}... {int(p)}%", text_color="white")
        self.progress_bar.configure(progress_color="#1f538d")
        
    def open_folder(self):
        real_path = os.path.expanduser(self.last_folder)
        if not os.path.exists(real_path): os.makedirs(real_path)
        
        # ===================================================
        # [LINUX/MAC FIX] ABRIR GERENCIADOR DE ARQUIVOS
        # ===================================================
        if self.is_windows:
            os.startfile(os.path.realpath(real_path))
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(["open", real_path])
        else: # Linux
            subprocess.Popen(["xdg-open", real_path])

    # ==========================================
    # SISTEMA DE FILA E MOTOR FFMPEG
    # ==========================================
    def show_queue(self):
        if self.queue_window is None or not self.queue_window.winfo_exists():
            self.queue_window = ctk.CTkToplevel(self)
            self.apply_window_icon(self.queue_window)
            self.queue_window.title("Process Queue")
            self.center_window(self.queue_window, 550, 400)
            self.queue_window.transient(self)
            self.queue_window.resizable(False, False)
            self.queue_window.configure(fg_color="#181a1f")

            # =========================================================
            # O SEGREDO DA MEMÓRIA: Não destruir a janela, apenas ocultar
            # =========================================================
            self.queue_window.protocol("WM_DELETE_WINDOW", self.queue_window.withdraw)

            ctk.CTkLabel(self.queue_window, text="Process Queue", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

            self.queue_scroll = ctk.CTkScrollableFrame(self.queue_window, fg_color="#21252b")
            self.queue_scroll.pack(fill="both", expand=True, padx=15, pady=10)

            btn_frame = ctk.CTkFrame(self.queue_window, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))

            ctk.CTkButton(btn_frame, text="Clear Queue", width=100, height=30, font=("Segoe UI", 12, "bold"), fg_color="#2c313a", hover_color="#a94442", command=self.clear_entire_queue).pack(side="right")

            self.render_queue_list()
        else:
            # Se a janela já existe na memória, apenas trazemos ela de volta
            self.queue_window.deiconify()
            self.queue_window.lift() # Traz para frente da janela principal
            self.render_queue_list() # Força a atualização visual por segurança

    # --- NOVA FUNÇÃO PARA LIMPAR TUDO ---
    def clear_entire_queue(self):
        self.download_queue.clear()
        self.btn_queue.configure(text="📥 Queue (0)")
        self.render_queue_list()

    def render_queue_list(self):
        if not hasattr(self, 'queue_window') or self.queue_window is None or not self.queue_window.winfo_exists():
            return

        # 1. Cria a mensagem de "Fila Vazia" se ela não existir OU se foi morta
        if not hasattr(self, 'empty_label') or not self.empty_label.winfo_exists():
            self.empty_label = ctk.CTkLabel(self.queue_scroll, text="Queue is empty.", text_color="gray")
            
        # 2. Se a fila estiver vazia, esconde tudo e mostra a mensagem
        if not self.download_queue:
            for widget in self.queue_scroll.winfo_children():
                if widget != self.empty_label:
                    widget.pack_forget()
            self.empty_label.pack(pady=20)
            return
            
        # Esconde a mensagem de vazia se houver itens
        if self.empty_label.winfo_manager() == "pack":
            self.empty_label.pack_forget()

        # 3. Mapeia os frames (linhas) que já existem na tela
        existing_frames = [w for w in self.queue_scroll.winfo_children() if w != self.empty_label]

        # 4. Loop Inteligente: Atualiza os velhos ou cria os novos
        for index, task in enumerate(self.download_queue):
            name = task.get("name", "Media Task")
            if len(name) > 60: name = name[:57] + "..." # Reduzi um pouco para caber as setas

            if index < len(existing_frames):
                # ==========================================
                # A. RECICLA o frame existente (0% Flicker)
                # ==========================================
                f = existing_frames[index]
                if f.winfo_manager() != "pack":
                    f.pack(fill="x", pady=8, padx=5) 
                
                # Atualiza a Label (Índice 0)
                lbl = f.winfo_children()[0]
                lbl.configure(text=f"{index+1}. {name}")
                task["label_widget"] = lbl
                
                # Atualiza o Botão X (Índice 1)
                btn_remove = f.winfo_children()[1]
                btn_remove.configure(command=lambda i=index: self.remove_from_queue(i))

                # Atualiza o Botão Descer ▼ (Índice 2)
                btn_down = f.winfo_children()[2]
                btn_down.configure(state="normal" if index < len(self.download_queue)-1 else "disabled", command=lambda i=index: self.move_queue_item(i, 1))

                # Atualiza o Botão Subir ▲ (Índice 3)
                btn_up = f.winfo_children()[3]
                btn_up.configure(state="normal" if index > 0 else "disabled", command=lambda i=index: self.move_queue_item(i, -1))

            else:
                # ==========================================
                # B. CRIA um novo frame com os novos botões
                # ==========================================
                f = ctk.CTkFrame(self.queue_scroll, fg_color="#181a1f", corner_radius=8)
                f.pack(fill="x", pady=8, padx=5)
                
                # 1. CRIA OS WIDGETS PRIMEIRO (MANTÉM A ORDEM DA RECICLAGEM!)
                lbl = ctk.CTkLabel(f, text=f"{index+1}. {name}", font=("Segoe UI", 12), anchor="w")
                task["label_widget"] = lbl
                
                btn_remove = ctk.CTkButton(f, text="X", width=30, height=24, fg_color="#a94442", hover_color="#803331", command=lambda i=index: self.remove_from_queue(i))
                btn_down = ctk.CTkButton(f, text="▼", width=30, height=24, fg_color="#2c313a", state="normal" if index < len(self.download_queue)-1 else "disabled", command=lambda i=index: self.move_queue_item(i, 1))
                btn_up = ctk.CTkButton(f, text="▲", width=30, height=24, fg_color="#2c313a", state="normal" if index > 0 else "disabled", command=lambda i=index: self.move_queue_item(i, -1))

                # 2. EMPACOTA DA DIREITA PARA A ESQUERDA (Protege os botões!)
                btn_remove.pack(side="right", padx=10)
                btn_down.pack(side="right", padx=2)
                btn_up.pack(side="right", padx=2)
                
                # 3. EMPACOTA O TEXTO POR ÚLTIMO (Preenchendo o espaço que sobrar)
                lbl.pack(side="left", fill="x", expand=True, padx=10, pady=12)

        # 5. Esconde os frames que sobraram (se a fila diminuiu)
        for i in range(len(self.download_queue), len(existing_frames)):
            existing_frames[i].pack_forget()
    
    def animate_queue_button(self, count):
        # 1. Cancela a animação anterior se o usuário clicar várias vezes rápido
        if getattr(self, 'queue_anim_id', None):
            self.after_cancel(self.queue_anim_id)
            
        # 2. Muda para o estado de "Sucesso" (Verde)
        self.btn_queue.configure(text=f"✅ Added! ({count})", text_color="#3fb950")
        
        # 3. Função interna que reverte o botão ao normal
        def revert():
            current_count = len(self.download_queue)
            # Verifica se a janela ainda existe para evitar erros ao fechar o app
            if self.winfo_exists():
                self.btn_queue.configure(text=f"📥 Queue ({current_count})", text_color="#e0e0e0")
                
        # 4. Agenda a reversão para daqui a 2 segundos (2000 ms)
        self.queue_anim_id = self.after(2000, revert)
    
    def remove_from_queue(self, index):
        if 0 <= index < len(self.download_queue):
            self.download_queue.pop(index)
            count = len(self.download_queue)
            self.btn_queue.configure(text=f"📥 Queue ({count})")
            self.render_queue_list()
            
    def move_queue_item(self, index, direction):
        # direction: -1 para subir, 1 para descer
        new_index = index + direction
        
        # Verifica se o novo índice está dentro dos limites da fila
        if 0 <= new_index < len(self.download_queue):
            # Troca os itens de lugar na lista do Python
            self.download_queue[index], self.download_queue[new_index] = self.download_queue[new_index], self.download_queue[index]
            
            # Chama a renderização limpa que criamos
            self.render_queue_list()

    def run_command(self, cmd, task_name="Media Task"):
        is_convert = self.current_category.get() in [self.TAB_C_VID, self.TAB_C_AUD]
        
        # 1. Adiciona o comando na fila
        queue_item = {
            "cmd": cmd, 
            "name": task_name, 
            "is_convert": is_convert,
            "label_widget": None
        }
        self.download_queue.append(queue_item)
        
        # 2. Atualiza contador e dispara a animação
        count = len(self.download_queue)
        self.safe_ui(self.animate_queue_button, count)
        self.render_queue_list()
        
        # 3. Limpa a caixa de texto instantaneamente
        # self.url_entry.delete(0, 'end')
        # self.src_entry.delete(0, 'end')
        # self.evaluate_ui_state()

        # 4. --- BUSCA O TÍTULO EM SEGUNDO PLANO (MAGIA) ---
        # Se for um download de internet (não é conversão e começa com http)
        if not is_convert and task_name.startswith("http"):
            def fetch_title_task():
                try:
                    # Pede pro yt-dlp apenas ler o título de forma rápida, sem baixar nada
                    title_cmd = [
                        self.ytdlp_path, 
                        "--get-title", 
                        "--no-warnings", 
                        "--flat-playlist", 
                        "--no-playlist", 
                        task_name
                    ]
                    result = subprocess.run(title_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        new_name = result.stdout.strip()
                        queue_item["name"] = new_name
                        
                        # ATUALIZAÇÃO CIRÚRGICA: Sem piscar a tela, altera só o texto!
                        def update_label():
                            if queue_item.get("label_widget") and queue_item["label_widget"].winfo_exists():
                                try:
                                    # Calcula a posição caso o usuário tenha apagado algo
                                    idx = self.download_queue.index(queue_item)
                                    display_name = new_name if len(new_name) <= 80 else new_name[:77] + "..."
                                    queue_item["label_widget"].configure(text=f"{idx+1}. {display_name}")
                                except ValueError:
                                    pass # O item saiu da fila antes do nome carregar

                        self.safe_ui(update_label)
                except Exception:
                    pass # Se falhar (ex: link privado), ele continua mostrando o link normal
            
            # Dispara a busca num motor separado para não travar o programa
            threading.Thread(target=fetch_title_task, daemon=True).start()
        # ----------------------------------------------------

        # 5. Inicia a engrenagem principal de download se ela estiver parada
        if not self.is_queue_running:
            self.process_next_in_queue()
        
    def process_next_in_queue(self):
        # Se a fila esvaziou, termina e libera os botões de configuração
        if not self.download_queue:
            self.is_queue_running = False
            self.toggle_buttons("normal")
            return

        self.is_queue_running = True
        current_task = self.download_queue.pop(0) # Puxa o próximo da fila
        
        # Atualiza a interface
        count = len(self.download_queue)
        self.btn_queue.configure(text=f"📥 Queue ({count})")
        self.render_queue_list()

        cmd = current_task["cmd"]
        is_convert = current_task["is_convert"]
        
        if hasattr(self, 'status_id') and self.status_id: self.after_cancel(self.status_id)
        self.is_cancelling = False
        self.toggle_buttons("disabled")
        
        start_process_time = time.time()
        self.current_playlist_item = "" 
        
        if is_convert:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_label.configure(text="Starting conversion...", text_color="white")
            self.progress_bar.configure(progress_color="#1f538d")
            self.add_to_log("\n>>> Starting conversion...")
        else:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.progress_label.configure(text="Starting download...", text_color="white")
            self.progress_bar.configure(progress_color="#1f538d")
            self.add_to_log("\n>>> Starting download...")
        
        def task():
            error_detected = False
            try:
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
                for line in self.current_process.stdout:
                    clean = line.strip()
                    if clean:
                        if "ERROR:" in clean or "Invalid data found" in clean:
                            error_detected = True
                            self.safe_ui(self.add_to_log, clean)
                            continue
                        
                        if is_convert and "time=" in clean:
                            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2})", clean)
                            if time_match:
                                self.safe_ui(self.progress_label.configure, text=f"Converting... (Time processed: {time_match.group(1)})", text_color="white")
                                self.progress_bar.configure(progress_color="#1f538d")

                        if not is_convert and "Downloading item" in clean:
                            item_match = re.search(r"Downloading item (\d+ of \d+)", clean)
                            if item_match:
                                self.current_playlist_item = f" [Item {item_match.group(1)}]"

                        if "100%" in clean or "already been downloaded" in clean or "already is in target format" in clean:
                            self.safe_ui(self.add_to_log, clean)
                            if not is_convert: self.safe_ui(self.download_progress, 100.0)
                        elif "B/s" not in clean and "ETA" not in clean and "time=" not in clean:
                            self.safe_ui(self.add_to_log, clean)
                            
                        if not is_convert:
                            match = self.re_progress.search(clean)
                            if match and not error_detected and not self.is_cancelling:
                                self.safe_ui(self.download_progress, float(match.group(1))) 

                # ... (código acima continua igual, lendo as linhas do terminal) ...
                self.current_process.stdout.close()
                self.current_process.wait()
                
                if is_convert:
                    self.safe_ui(self.progress_bar.stop)
                    self.safe_ui(self.progress_bar.configure, mode="determinate")
                
                if self.is_cancelling:
                    self.safe_ui(self.status_canceled)
                    self.download_queue.clear()
                    self.safe_ui(lambda: self.btn_queue.configure(text="📥 Queue (0)"))
                    self.safe_ui(self.render_queue_list)
                    self.is_queue_running = False
                    self.safe_ui(self.toggle_buttons, "normal")

                elif self.current_process.returncode == 0 and not error_detected:
                    end_process_time = time.time()
                    duration = int(end_process_time - start_process_time)
                    duration_str = f"{duration//60}m {duration%60}s" if duration >= 60 else f"{duration}s"

                    msg = f"Conversion Complete! (Total time: {duration_str})" if is_convert else f"Download Complete! (Total time: {duration_str})"
                        
                    self.safe_ui(self.progress_label.configure, text=msg, text_color="#3fb950") # VERDE
                    self.safe_ui(self.progress_bar.configure, progress_color="#3fb950")
                    self.safe_ui(self.progress_bar.set, 1)
                    
                    self.safe_ui(self.add_to_log, f">>> {msg}\n")
                    self.safe_ui(self.process_next_in_queue)

                elif error_detected:
                    # --- NOVO: STATUS AMARELO (PLAYLIST INCOMPLETA / ERRO PARCIAL) ---
                    msg = "Conversion Incomplete (Check Logs)" if is_convert else "Download Incomplete (Check Logs)"
                    
                    self.safe_ui(self.progress_label.configure, text=msg, text_color="#d29922") # AMARELO/LARANJA
                    self.safe_ui(self.progress_bar.configure, progress_color="#d29922")
                    self.safe_ui(self.progress_bar.set, 1)
                    
                    self.safe_ui(self.add_to_log, f">>> {msg}\n")
                    
                    # Espera 3 segundos para o usuário ler o aviso e continua a fila guerreira!
                    self.safe_ui(self.after, 3000, self.process_next_in_queue)

                else:
                    self.safe_ui(self.status_error)
                    self.download_queue.clear()
                    self.safe_ui(lambda: self.btn_queue.configure(text="📥 Queue (0)"))
                    self.safe_ui(self.render_queue_list)
                    self.is_queue_running = False
                    self.safe_ui(self.toggle_buttons, "normal")

            except Exception as e:
                self.safe_ui(self.status_error, f"SYSTEM ERROR: {e}")
                self.is_queue_running = False
                self.safe_ui(self.toggle_buttons, "normal")
            finally:
                self.current_process = None
                self.safe_ui(self.btn_cancel.configure, text="Cancel")
                
        threading.Thread(target=task, daemon=True).start()

    def show_settings(self):
        lang_map = {"None": "none", "English": "en", "Portuguese": "pt", "Spanish": "es", "French": "fr", "German": "de", "Italian": "it", "Japanese": "ja", "Korean": "ko", "Russian": "ru"}
        reverse_lang_map = {v: k for k, v in lang_map.items()}

        settings_win = ctk.CTkToplevel(self)
        self.apply_window_icon(settings_win)
        settings_win.title("Global Settings")
        self.center_window(settings_win, 500, 620)
        settings_win.transient(self)
        settings_win.grab_set()
        self.apply_modal_fix(settings_win)
        settings_win.resizable(False, False)
        settings_win.configure(fg_color="#181a1f")
        
        ctk.CTkLabel(settings_win, text="Global Settings", font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

        scroll_frame = ctk.CTkScrollableFrame(settings_win, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(scroll_frame, text="Output Folders", font=("Segoe UI", 13, "bold")).pack(pady=(5, 5), anchor="w")
        
        ctk.CTkLabel(scroll_frame, text="Video output folder:", font=("Segoe UI", 12)).pack(anchor="w")
        vid_path_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        vid_path_frame.pack(pady=2, fill="x")
        vid_entry = ctk.CTkEntry(vid_path_frame, fg_color="#21252b", border_color="#3a3f4b")
        vid_entry.insert(0, self.config_data.get("General", {}).get("video_path", "~/Videos/CopynDown"))
        vid_entry.configure(state="readonly")
        vid_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def format_and_insert_path(p, entry_widget):
            if not p: return  # Se o usuário cancelar a janela, não faz nada
            
            p = p.replace("\\", "/")
            home = os.path.expanduser("~").replace("\\", "/")
            app_dir = os.path.abspath(".").replace("\\", "/")
            
            # Regra 1: Se estiver dentro da pasta do app (útil para o cookies.txt)
            if p.startswith(app_dir): 
                p = p[len(app_dir):].lstrip("/")
            # Regra 2: Se estiver na pasta do usuário (útil para salvar mídias)
            elif p.startswith(home): 
                p = "~" + p[len(home):]
                
            entry_widget.configure(state="normal")
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, p)
            entry_widget.configure(state="readonly")

        # --- APLICAÇÃO NAS PASTAS (VÍDEO/ÁUDIO) ---
        def change_path(entry_widget):
            p = filedialog.askdirectory(parent=settings_win)
            format_and_insert_path(p, entry_widget)
        
        ctk.CTkButton(vid_path_frame, text="Browse", width=60, fg_color="#21252b", hover_color="#2c313a", command=lambda: change_path(vid_entry)).pack(side="right")

        ctk.CTkLabel(scroll_frame, text="Audio output folder:", font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 0))
        aud_path_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        aud_path_frame.pack(pady=2, fill="x")
        aud_entry = ctk.CTkEntry(aud_path_frame, fg_color="#21252b", border_color="#3a3f4b")
        aud_entry.insert(0, self.config_data.get("General", {}).get("audio_path", "~/Music/CopynDown"))
        aud_entry.configure(state="readonly")
        aud_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(aud_path_frame, text="Browse", width=60, fg_color="#21252b", hover_color="#2c313a", command=lambda: change_path(aud_entry)).pack(side="right")

        ctk.CTkLabel(scroll_frame, text="General Options", font=("Segoe UI", 13, "bold")).pack(pady=(20, 5), anchor="w")
        
        ctk.CTkLabel(scroll_frame, text="Cookies txt path:", font=("Segoe UI", 12)).pack(anchor="w")
        cookie_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cookie_frame.pack(pady=2, fill="x")
        cookie_entry = ctk.CTkEntry(cookie_frame, fg_color="#21252b", border_color="#3a3f4b")
        cookie_entry.insert(0, self.config_data.get("General", {}).get("cookies_path", self.cookies_path_default))
        cookie_entry.configure(state="readonly")
        cookie_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def change_cookie_path():
            p = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")], parent=settings_win)
            format_and_insert_path(p, cookie_entry)
        ctk.CTkButton(cookie_frame, text="Browse", width=60, fg_color="#21252b", hover_color="#2c313a", command=change_cookie_path).pack(side="right")

        v_auto_paste = ctk.BooleanVar(value=self.config_data.get("General", {}).get("auto_paste", self.DEF_AUTO_PASTE))
        v_use_cookies = ctk.BooleanVar(value=self.config_data.get("General", {}).get("use_cookies", self.DEF_USE_COOKIES))
        v_hide_options = ctk.BooleanVar(value=self.config_data.get("General", {}).get("hide_options", self.DEF_HIDE_OPTS))
        ctk.CTkCheckBox(scroll_frame, text="Auto-paste URLs", variable=v_auto_paste).pack(pady=4, anchor="w")
        ctk.CTkCheckBox(scroll_frame, text="Use cookies file", variable=v_use_cookies).pack(pady=4, anchor="w")
        ctk.CTkCheckBox(scroll_frame, text="Hide UI options before pasting URL", variable=v_hide_options).pack(pady=4, anchor="w")
        
        ctk.CTkLabel(scroll_frame, text="Media Embedding (Video & Audio)", font=("Segoe UI", 13, "bold")).pack(pady=(20, 5), anchor="w")
        v_vid_thumb = ctk.BooleanVar(value=self.config_data.get(self.TAB_VID, {}).get("thumb", True))
        v_aud_meta = ctk.BooleanVar(value=self.config_data.get(self.TAB_AUD, {}).get("meta", True))
        ctk.CTkCheckBox(scroll_frame, text="Embed thumbnail (Cover art)", variable=v_vid_thumb).pack(pady=4, anchor="w")
        ctk.CTkCheckBox(scroll_frame, text="Embed metadata (Artist, Title, etc)", variable=v_aud_meta).pack(pady=4, anchor="w")

        ctk.CTkLabel(scroll_frame, text="Subtitles (Video only)", font=("Segoe UI", 13, "bold")).pack(pady=(20, 5), anchor="w")
        v_native_subs = ctk.BooleanVar(value=self.config_data.get(self.TAB_VID, {}).get("native_subs", False))
        v_auto_subs = ctk.BooleanVar(value=self.config_data.get(self.TAB_VID, {}).get("auto_subs", False))
        v_embed_subs = ctk.BooleanVar(value=self.config_data.get(self.TAB_VID, {}).get("embed_subs", False))
        
        def check_subtitle_state():
            if v_native_subs.get() or v_auto_subs.get(): chk_embed.configure(state="normal")
            else:
                chk_embed.configure(state="disabled")
                v_embed_subs.set(False)
                
        chk_native = ctk.CTkCheckBox(scroll_frame, text="Download standard subtitles", variable=v_native_subs, command=check_subtitle_state)
        chk_native.pack(pady=4, anchor="w")
        chk_auto = ctk.CTkCheckBox(scroll_frame, text="Download auto-generated subtitles", variable=v_auto_subs, command=check_subtitle_state)
        chk_auto.pack(pady=4, anchor="w")
        chk_embed = ctk.CTkCheckBox(scroll_frame, text="Embed subtitles into video", variable=v_embed_subs)
        chk_embed.pack(pady=4, anchor="w")
        check_subtitle_state()
        
        langs_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        langs_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(langs_frame, text="Original language:").grid(row=0, column=0, padx=(0, 10), pady=2, sticky="w")
        lang_selector = ctk.CTkOptionMenu(langs_frame, values=list(lang_map.keys())[1:], fg_color="#21252b", button_color="#2c313a") 
        lang_selector.set(reverse_lang_map.get(self.config_data.get(self.TAB_VID, {}).get("langs", "en"), "English"))
        lang_selector.grid(row=1, column=0, padx=(0, 10), pady=2, sticky="w")

        ctk.CTkLabel(langs_frame, text="Translate to:").grid(row=0, column=1, padx=(10, 0), pady=2, sticky="w")
        trans_selector = ctk.CTkOptionMenu(langs_frame, values=list(lang_map.keys()), fg_color="#21252b", button_color="#2c313a")
        trans_selector.set(reverse_lang_map.get(self.config_data.get(self.TAB_VID, {}).get("trans_langs", "none"), "None"))
        trans_selector.grid(row=1, column=1, padx=(10, 0), pady=2, sticky="w")

        def restore_defaults():
            vid_entry.configure(state="normal")
            vid_entry.delete(0, 'end')
            vid_entry.insert(0, "~/Videos/CopynDown")
            vid_entry.configure(state="readonly")
            
            aud_entry.configure(state="normal")
            aud_entry.delete(0, 'end')
            aud_entry.insert(0, "~/Music/CopynDown")
            aud_entry.configure(state="readonly")
            
            cookie_entry.configure(state="normal")
            cookie_entry.delete(0, 'end')
            cookie_entry.insert(0, self.cookies_path_default)
            cookie_entry.configure(state="readonly")

            v_auto_paste.set(self.DEF_AUTO_PASTE)
            v_use_cookies.set(self.DEF_USE_COOKIES)
            v_hide_options.set(self.DEF_HIDE_OPTS)
            
            v_vid_thumb.set(True)
            v_aud_meta.set(True)
            
            v_native_subs.set(False)
            v_auto_subs.set(False)
            v_embed_subs.set(False)
            lang_selector.set("English")
            trans_selector.set("None")
            check_subtitle_state()
            
        def save():
            self.config_data["General"].update({
                "video_path": vid_entry.get(),
                "audio_path": aud_entry.get(),
                "auto_paste": v_auto_paste.get(), 
                "use_cookies": v_use_cookies.get(), 
                "cookies_path": cookie_entry.get(), 
                "hide_options": v_hide_options.get()
            })
            
            self.config_data[self.TAB_VID].update({
                "thumb": v_vid_thumb.get(),
                "native_subs": v_native_subs.get(), 
                "auto_subs": v_auto_subs.get(), 
                "embed_subs": v_embed_subs.get(),
                "langs": lang_map.get(lang_selector.get(), "en"), 
                "trans_langs": lang_map.get(trans_selector.get(), "none")
            })
            
            self.config_data[self.TAB_AUD].update({
                "thumb": v_vid_thumb.get(), 
                "meta": v_aud_meta.get()
            })
            
            self.save_config()
            self.update_folder_context()
            self.evaluate_ui_state()
            settings_win.destroy()
            self.add_to_log(f">>> Global Settings saved successfully.")

        btn_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=10)
        ctk.CTkButton(btn_frame, text="Restore defaults", font=("Segoe UI", 12, "bold"), fg_color="#2c313a", hover_color="#a94442", command=restore_defaults).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Save settings", font=("Segoe UI", 12, "bold"), fg_color="#1f538d", hover_color="#14375e", command=save).pack(side="right", padx=10)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    l = json.load(f)
                    
                    if "General" not in self.config_data: self.config_data["General"] = {}
                    
                    # Migração das chaves antigas de vídeo para a nova Constante
                    legacy_vid_keys = ["YouTube", "Video", "Save Video"]
                    for key in legacy_vid_keys:
                        if key in l:
                            for k, v in l[key].items():
                                if k == "path": self.config_data["General"]["video_path"] = v
                                elif k in self.config_data[self.TAB_VID]: self.config_data[self.TAB_VID][k] = v
                    
                    # Migração das chaves antigas de áudio para a nova Constante
                    legacy_aud_keys = ["Music", "Audio", "Save Audio"]
                    for key in legacy_aud_keys:
                        if key in l:
                            for k, v in l[key].items():
                                if k == "path": self.config_data["General"]["audio_path"] = v
                                elif k in self.config_data[self.TAB_AUD]: self.config_data[self.TAB_AUD][k] = v
                    
                    if "General" in l:
                        self.config_data["General"].update(l["General"])
                        
            except Exception as e: self.add_to_log(f">>> Warning: Could not read config.txt: {e}")

    def save_config(self):
        try:
            if not os.path.exists("bin"): os.makedirs("bin")
            with open(self.config_file, "w") as f: json.dump(self.config_data, f, indent=4)
        except Exception as e: self.add_to_log(f">>> ERROR: Failed to save config.txt: {e}")

    def update_folder_context(self):
        is_video = self.current_category.get() in [self.TAB_VID, self.TAB_C_VID]
        self.last_folder = self.config_data["General"]["video_path"] if is_video else self.config_data["General"]["audio_path"]

    def toggle_buttons(self, state, is_downloading=True):
        self.is_busy = (state == "disabled")
        
        if state == "disabled" and is_downloading:
            self.btn_cancel.configure(state="normal")
        else:
            self.btn_cancel.configure(state="disabled")
            
        for btn in self.pills.values(): 
            btn.configure(state=state)

    def check_ytdlp_updates(self):
        if not os.path.exists(self.ytdlp_path):
            if self.winfo_exists():
                self.safe_ui(self.add_to_log, ">>> Warning: yt-dlp is missing! Update check skipped. Please check your 'bin' folder.")
            return
        try:
            self.safe_ui(self.toggle_buttons, "disabled", is_downloading=False)
            process = subprocess.Popen([self.ytdlp_path, "-U"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
            for line in process.stdout:
                if line.strip(): self.safe_ui(self.add_to_log, f"[yt-dlp update] {line.strip()}")
            process.stdout.close()
            process.wait()
        except Exception as e:
            if self.winfo_exists(): self.safe_ui(self.add_to_log, f"ERROR: {e}")
        finally:
            if self.winfo_exists():
                self.safe_ui(self.toggle_buttons, "normal") 
                self.safe_ui(self.reset_status)             

    def get_local_version(self):
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r", encoding='utf-8') as f: return f.read().strip()
            except Exception as e: self.add_to_log(f">>> Warning: Failed to read version.txt: {e}")
        return "Version file not found"

    def show_about(self):
        self.about_win = ctk.CTkToplevel(self)
        self.apply_window_icon(self.about_win)
        self.about_win.title("About CopynDown")
        self.center_window(self.about_win, 640, 500)
        
        self.about_win.resizable(False, False)
        self.about_win.transient(self)
        self.about_win.grab_set()
        self.apply_modal_fix(self.about_win)
        self.about_win.configure(fg_color="#181a1f")
        
        scroll_frame = ctk.CTkScrollableFrame(self.about_win, width=580, height=350, fg_color="transparent")
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(scroll_frame, text="CopynDown", font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(15, 0))
        ctk.CTkLabel(scroll_frame, text=f"Version {self.version}", text_color="gray", font=("Segoe UI", 13)).pack(anchor="w", pady=(0, 15))
        ctk.CTkLabel(scroll_frame, text="Developed by DanMixerBR", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 25))
        
        desc_text = (
            "A modern, fast, and cross-platform media downloader and converter.\n\n"
            "Supported platforms: YouTube, Vimeo, Dailymotion, Twitch, Instagram, TikTok, Kwai, Facebook, Twitter/X, Reddit, SoundCloud, LinkedIn, Pinterest, Snapchat, Bilibili, Rumble, Bandcamp, Mixcloud, Kick, and Odysee."
        )
        ctk.CTkLabel(scroll_frame, text=desc_text, font=("Segoe UI", 13), justify="left", wraplength=550).pack(anchor="w", pady=10)
        ctk.CTkLabel(scroll_frame, text="Credits & License", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(30, 10))
        
        credits_text = (
            "Built with:\n\n"
            "• Python\n"
            "• CustomTkinter\n"
            "• yt-dlp\n"
            "• FFmpeg\n"
            "• Deno\n\n"
            "This software is distributed under the MIT License."
        )
        ctk.CTkLabel(scroll_frame, text=credits_text, font=("Segoe UI", 13), justify="left").pack(anchor="w", pady=10)
            
        btn_frame = ctk.CTkFrame(self.about_win, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="GitHub", fg_color="#1f538d", hover_color="#14375e", width=120, command=lambda: webbrowser.open_new("https://github.com/DanMixerBR/CopynDown")).pack(side="left", padx=10)
        self.btn_update_app = ctk.CTkButton(btn_frame, text="Check for updates", width=120, command=self.start_github_update, fg_color="#21252b", hover_color="#2c313a")
        self.btn_update_app.pack(side="left", padx=10)

    def start_github_update(self):
        self.btn_update_app.configure(state="disabled", text="Checking...")
        self.is_updating = True 
        self.reset_status("Checking for updates...")
        threading.Thread(target=self.perform_github_update, daemon=True).start()

    def perform_github_update(self):
        api_url = "https://api.github.com/repos/DanMixerBR/CopynDown/releases/latest"
        download_url_windows = "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Windows.zip"
        download_url_linux = "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Linux.zip"
        
        # ===================================================
        # [LINUX/MAC FIX] DETECTAR QUAL SCRIPT BAIXAR
        # ===================================================
        script_ext = "bat" if self.is_windows else "sh"
        script_url = f"https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/update.{script_ext}"
        hash_url = "https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/hash_v2.txt"
        zip_platform = "CopynDown_Windows.zip" if self.is_windows else "CopynDown_Linux.zip"
        
        try:
            local_v = self.get_local_version()
            response = requests.get(api_url, timeout=10)
            remote_v = response.json()['tag_name']
            
            if remote_v not in local_v:
                msg = f"{local_v}\nLatest version: {remote_v}\n\nDo you want to update?"
                parent_win = self.about_win if (hasattr(self, 'about_win') and self.about_win.winfo_exists()) else self
                
                if not messagebox.askyesno("Update available", msg, parent=parent_win):
                    self.is_updating = False
                    self.safe_ui(self.reset_status)
                    return
                
                if hasattr(self, 'about_win') and self.about_win.winfo_exists(): 
                    self.safe_ui(self.about_win.destroy)
                    
                self.safe_ui(self.toggle_buttons, "disabled", is_downloading=False)

                dir_app = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
                script_path = os.path.join(dir_app, f"update.{script_ext}")
                zip_path = os.path.join(dir_app, zip_platform)
                
                if os.path.exists(zip_path): os.remove(zip_path)
                    
                self.safe_ui(self.progress_label.configure, text="Updating... 25%", text_color="white")
                self.safe_ui(self.progress_bar.set, 0.25)
                self.safe_ui(self.add_to_log, "\n>>> Downloading update file...")
                
                if self.is_windows: 
                    r = requests.get(download_url_windows, timeout=30)
                else:
                    r = requests.get(download_url_linux, timeout=30)
                with open(zip_path, 'wb') as f: f.write(r.content)
                
                self.safe_ui(self.progress_label.configure, text="Updating... 50%", text_color="white")
                self.safe_ui(self.progress_bar.set, 0.5)
                self.safe_ui(self.add_to_log, "Verifying update file...")
                
                # 1. Abre, testa e fecha o arquivo automaticamente
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    corrupt_file = zf.testzip()
                
                # 2. Agora, com o arquivo já fechado, podemos apagar se der erro!
                if corrupt_file is not None:
                    if os.path.exists(zip_path): os.remove(zip_path)
                    raise Exception("ERROR: File structure is corrupted.")
                
                self.safe_ui(self.add_to_log, "File structure verified (OK).")
                
                r_hash = requests.get(hash_url, timeout=10)
                if r_hash.status_code == 200:
                    expected_hashes = [
                        line.strip().lower().replace("sha256:", "") 
                        for line in r_hash.text.splitlines() 
                        if line.strip()
                    ]
                    
                    sha256_hash = hashlib.sha256()
                    with open(zip_path, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""): 
                            sha256_hash.update(byte_block)
                            
                    if sha256_hash.hexdigest().lower() not in expected_hashes:
                        if os.path.exists(zip_path): 
                            os.remove(zip_path)
                        raise Exception(f"ERROR: Hash mismatch!")
                    
                    self.safe_ui(self.add_to_log, "Hash verification (OK).")
                else:
                    self.safe_ui(self.add_to_log, "Warning: Could not download hash_v2.txt")
                    
                self.safe_ui(self.progress_label.configure, text="Updating... 75%", text_color="white")
                self.safe_ui(self.progress_bar.set, 0.75)
                self.safe_ui(self.add_to_log, "Downloading update script...")
                
                r_script = requests.get(script_url, timeout=10)
                if r_script.status_code == 200:
                    with open(script_path, 'wb') as f: f.write(r_script.content)
                else: 
                    raise Exception(f"Could not download update.{script_ext} from GitHub.")
                
                self.safe_ui(self.progress_label.configure, text="Update Ready! (100%)", text_color="#3fb950")
                self.safe_ui(self.progress_bar.configure, progress_color="#3fb950")
                self.safe_ui(self.progress_bar.set, 1)
                self.safe_ui(self.add_to_log, ">>> Update downloaded and verified successfully!")
                
                parent_win = self.about_win if (hasattr(self, 'about_win') and self.about_win.winfo_exists()) else self
                messagebox.showinfo("Success", "Update Ready! The app will close to complete the update.", parent=parent_win)
                
                # ===================================================
                # [LINUX/MAC FIX] RODAR BASH EM VEZ DE CMD
                # ===================================================
                if os.path.exists(script_path):
                    if self.is_windows:
                        subprocess.Popen(['cmd.exe', '/c', script_path], creationflags=0x00000010)
                    else:
                        os.chmod(script_path, 0o755) # Dá permissão de execução
                        
                        # 1. Limpa o ambiente para o terminal não herdar as bibliotecas pesadas do Nuitka
                        limpo_env = os.environ.copy()
                        limpo_env.pop("LD_LIBRARY_PATH", None)
                        limpo_env.pop("GTK_PATH", None)
                        
                        # Comando exato que o terminal vai executar
                        comando_bash = f'cd "{dir_app}" && bash update.sh'
                        
                        # 2. Lista dos terminais mais famosos do Linux (Garante compatibilidade universal)
                        terminais = [
                            ['x-terminal-emulator', '-e'], # Padrão Debian/Ubuntu/Mint
                            ['gnome-terminal', '--'],      # Ubuntu antigo
                            ['konsole', '-e'],             # Kubuntu/KDE
                            ['xfce4-terminal', '-x']       # Xubuntu/XFCE
                        ]
                        
                        abriu_terminal = False
                        for term in terminais:
                            try:
                                # 3. O start_new_session=True DESCOLA o terminal do app. O app pode morrer, o terminal vive!
                                subprocess.Popen(term + ['bash', '-c', comando_bash], env=limpo_env, start_new_session=True)
                                abriu_terminal = True
                                break
                            except Exception:
                                continue
                                
                        if not abriu_terminal:
                            # Fallback silencioso só em último caso extremo
                            subprocess.Popen(['bash', script_path], env=limpo_env, start_new_session=True)
                            
                    os._exit(0)
            else:
                self.is_updating = False
                parent_win = self.about_win if (hasattr(self, 'about_win') and self.about_win.winfo_exists()) else self
                self.safe_ui(messagebox.showinfo, "Up to date", "You are already using the latest version.", parent=parent_win)
                self.safe_ui(self.reset_status)
        except Exception as e:
            self.is_updating = False
            err_text = str(e)
            if "File structure" in err_text or "Hash mismatch" in err_text:
                self.safe_ui(self.status_update_error, zip_platform, None, custom_msg=err_text)
            else:
                self.safe_ui(self.set_terminal_state, "Update Failed!", f"ERROR: {err_text}")
                self.safe_ui(self.schedule_reset, 7000)
                
                parent_win = self.about_win if (hasattr(self, 'about_win') and self.about_win.winfo_exists()) else self
                self.safe_ui(messagebox.showerror, "Error", e, parent=parent_win)
        finally:
            if hasattr(self, 'about_win') and self.about_win.winfo_exists(): 
                self.safe_ui(self.btn_update_app.configure, state="normal", text="Check for updates")
            if not self.is_updating:
                self.safe_ui(self.toggle_buttons, "normal")

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
