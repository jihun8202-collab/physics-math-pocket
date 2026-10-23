from __future__ import annotations

import ctypes
import datetime as _dt
import html
import logging
import math
import os
import random
import subprocess
import sys
import threading
import tkinter as tk
import urllib.parse
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, font as tkfont
from typing import Callable, Dict, List, Optional

from core import (
    APP_NAME,
    APP_VERSION,
    APP_BUILD,
    APP_CHANNEL,
    APP_COPYRIGHT,
    JsonDictStore,
    JsonListStore,
    JsonSetStore,
    UNIT_FAMILIES,
    convert_unit,
    format_number,
    load_constants,
    load_sources,
    load_terms,
    resource_path,
    search_terms,
    unit_names,
    user_data_dir,
)
from knowledge_db import KnowledgeDatabase, bytes_to_human
from settings_store import DEFAULT_SETTINGS, SettingsStore
from simulations import SIM_TITLES as LEGACY_SIM_TITLES, SIM_SUBJECTS as LEGACY_SIM_SUBJECTS
from enhanced_simulations import ENHANCED_TITLES, ENHANCED_SUBJECTS, BIOLOGY_TITLES, BIOLOGY_SUBJECTS, build_simulator, simulator_for_term
from scientific_catalog import MODELS as SCIENCE_MODELS, SCENARIOS as SCIENCE_SCENARIOS
from korean_study import build_korean_page
from pocket_glass import GlassCard, bind_hover, make_theme
from mini_simulation import build_mini_simulator
SIM_TITLES = {**BIOLOGY_TITLES, **ENHANCED_TITLES, **LEGACY_SIM_TITLES}
SIM_SUBJECTS = {**LEGACY_SIM_SUBJECTS, **ENHANCED_SUBJECTS, **BIOLOGY_SUBJECTS}
from formula_catalog import build_formula_catalog, search_formulas
from calculator_specs import CALCULATOR_SPECS, CALCULATOR_CATEGORIES
from metadata_store import InstallMetadataStore
from updater import (
    ReleaseInfo, UpdateCheckResult, check_for_updates, default_local_update_dir,
    download_installer, launch_installer, launch_seamless_update, release_is_newer,
    list_github_releases
)

THEMES = {
    "light": {
        "bg": "#F6F7FB",
        "rail": "#F0F2F8",
        "surface": "#FFFFFF",
        "surface2": "#F7F8FC",
        "surface3": "#EEF1F7",
        "glass": "#F9FAFE",
        "line": "#E2E6EF",
        "text": "#17191F",
        "muted": "#737987",
        "accent": "#5B54F6",
        "accent2": "#3F45C8",
        "accent_soft": "#ECEBFF",
        "blue": "#356EE8",
        "cyan": "#2AA9C8",
        "green": "#248A64",
        "orange": "#C97728",
        "pink": "#C85C88",
        "yellow": "#FFF3CC",
        "danger": "#D94B54",
        "shadow": "#D8DDE8",
        "hero_a": "#455BF5",
        "hero_b": "#8A4DF3",
    },
    "dark": {
        "bg": "#0C0E13",
        "rail": "#11141C",
        "surface": "#171A22",
        "surface2": "#1D212B",
        "surface3": "#262B37",
        "glass": "#151922",
        "line": "#303644",
        "text": "#F7F8FC",
        "muted": "#A4A9B6",
        "accent": "#8F8BFF",
        "accent2": "#B8B6FF",
        "accent_soft": "#292751",
        "blue": "#7CA7FF",
        "cyan": "#67D4E8",
        "green": "#6AD0A6",
        "orange": "#F0AC67",
        "pink": "#ED91B8",
        "yellow": "#4D4327",
        "danger": "#FF8B93",
        "shadow": "#05070B",
        "hero_a": "#3443C8",
        "hero_b": "#6E3AB2",
    },
}

CATEGORY_ICONS = {
    "측정·기초": "▦",
    "운동학": "➜",
    "힘·에너지": "◆",
    "회전·평형": "◉",
    "유체": "≈",
    "진동·파동·소리": "∿",
    "열·열역학": "♨",
    "전기·자기": "ϟ",
    "빛·광학": "✦",
    "상대성이론": "∞",
    "양자·원자": "ψ",
    "핵·입자": "⚛",
    "천체·우주": "★",
    "수와 연산": "123",
    "대수": "x",
    "함수": "ƒ",
    "집합·논리": "∈",
    "삼각함수": "△",
    "수열": "Σ",
    "기하": "◇",
    "확률·통계": "%",
    "미적분": "∫",
    "다변수미적분": "∂",
    "벡터해석": "∇",
    "선형대수": "▦",
    "미분방정식": "dy",
    "해석학": "ε",
    "복소해석": "i",
    "이산수학": "G",
    "추상대수": "≅",
    "수치해석": "≈",
    "위상수학": "∞",
    "원자·주기율": "⚗",
    "화학결합": "⌬",
    "화학반응·양론": "⇄",
    "기체·열화학": "♨",
    "용액·산염기": "pH",
    "평형·반응속도": "⇌",
    "전기화학": "⚡",
    "유기화학": "C",
    "세포": "◎",
    "분자생물학·유전": "DNA",
    "생화학·대사": "ATP",
    "생리·항상성": "♡",
    "면역·미생물": "✚",
    "생태·진화": "♣",
    "지질·지구내부": "◒",
    "암석·광물": "◆",
    "대기·기상": "☁",
    "해양": "≈",
    "지구환경": "♻",
    "태양계": "☉",
    "항성": "★",
    "은하·우주론": "✦",
    "관측천문": "⌖",
    "조합론": "C",
    "사용자 추가": "+",
}


def configure_logging() -> None:
    log_path = user_data_dir() / "physics_math_pocket.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def enable_windows_high_dpi() -> None:
    if hasattr(ctypes, "windll"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def apply_windows_chrome(root: tk.Tk, dark: bool = False) -> None:
    """Best-effort Windows 11 chrome: dark title bar, rounded corners and Mica backdrop.

    The app remains fully functional when DWM attributes are unavailable.
    """
    if os.name != "nt" or not hasattr(ctypes, "windll"):
        return
    try:
        root.update_idletasks()
        hwnd = int(root.winfo_id())
        dwm = ctypes.windll.dwmapi
        def set_int(attr: int, value: int) -> None:
            data = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(data), ctypes.sizeof(data))
        set_int(20, 1 if dark else 0)   # DWMWA_USE_IMMERSIVE_DARK_MODE
        set_int(33, 2)                  # DWMWA_WINDOW_CORNER_PREFERENCE / round
        set_int(38, 2)                  # DWMWA_SYSTEMBACKDROP_TYPE / main-window backdrop
    except Exception:
        pass


def detect_system_theme() -> str:
    """Best-effort Windows light/dark detection; safe fallback elsewhere."""
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if int(value) else "dark"
        except Exception:
            pass
    return "light"


class ScrollableFrame(tk.Frame):
    def __init__(self, master: tk.Misc, bg: str, **kwargs) -> None:
        super().__init__(master, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_inner)
        self.canvas.bind("<Enter>", lambda _e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda _e: self._unbind_mousewheel())

    def _update_scrollregion(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_inner(self, event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event) -> None:
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = int(-event.delta / 120)
        self.canvas.yview_scroll(delta, "units")

    def to_top(self) -> None:
        self.canvas.yview_moveto(0)


class Splash(tk.Toplevel):
    """Compact splash with a modern layered loading surface."""
    def __init__(self, master: tk.Tk, theme: dict) -> None:
        super().__init__(master)
        self.theme = theme
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        width, height = 610, 380
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")
        self.canvas = tk.Canvas(self, width=width, height=height, bg="#10131C", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        # layered backdrop
        for y in range(height):
            q = y / max(1, height - 1)
            a = (18, 24, 52); b = (42, 22, 70)
            col = '#%02x%02x%02x' % tuple(int(a[i]*(1-q)+b[i]*q) for i in range(3))
            self.canvas.create_line(0, y, width, y, fill=col)
        self.canvas.create_oval(-80, -160, 350, 270, fill="#243A88", outline="")
        self.canvas.create_oval(370, 90, 760, 480, fill="#44245F", outline="")
        self.canvas.create_rectangle(34, 34, width-34, height-34, fill="#151925", outline="#363C50", width=1)
        try:
            raw = tk.PhotoImage(file=str(resource_path("assets/physics_pocket.png")))
            self._logo = raw.subsample(max(1, raw.width()//86), max(1, raw.height()//86))
            self.canvas.create_image(width//2, 115, image=self._logo)
        except Exception:
            self._logo = None
            self.canvas.create_text(width//2, 112, text="⚛∑", fill="#FFFFFF", font=("Segoe UI Symbol", 42, "bold"))
        self.canvas.create_text(width//2, 196, text="Physics + Math Pocket", fill="#FFFFFF", font=("Segoe UI Variable Display", 24, "bold"))
        self.canvas.create_text(width//2, 229, text=f"{APP_VERSION} · Build {APP_BUILD}", fill="#C7C9FF", font=("Segoe UI Variable Text", 11, "bold"))
        self.canvas.create_text(width//2, 258, text="지식베이스와 학습 도구를 준비하는 중", fill="#C2C6D4", font=("Malgun Gothic", 9))
        self.canvas.create_rectangle(92, 307, width-92, 313, fill="#2A2F3B", outline="")
        self.progress = self.canvas.create_rectangle(92, 307, 92, 313, fill="#9692FF", outline="")
        self.status = self.canvas.create_text(width//2, 338, text="검색 인덱스 · 시뮬레이션 · 업데이트 엔진 초기화", fill="#8F96A8", font=("Malgun Gothic", 8))
        self.step = 0
        self.after(16, self.animate)

    def animate(self) -> None:
        self.step += 1
        ratio = min(1.0, self.step / 74.0)
        eased = 1 - (1-ratio)**3
        self.canvas.coords(self.progress, 92, 307, 92 + 426*eased, 313)
        if self.step < 74:
            self.after(16, self.animate)


class PhysicsPocketApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.withdraw()
        self.title("Physics + Math Pocket {}{}".format(APP_VERSION, " Beta" if APP_CHANNEL == "beta" else ""))
        self.geometry("1500x930")
        self.minsize(1180, 740)

        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.install_meta = InstallMetadataStore(APP_VERSION, APP_BUILD, APP_CHANNEL)
        self.latest_release: Optional[ReleaseInfo] = None
        self.update_check_result: Optional[UpdateCheckResult] = None
        self.update_check_running = False
        requested_theme = self.settings.get("theme", "system")
        self.theme_name = detect_system_theme() if requested_theme == "system" else requested_theme
        self.theme = make_theme(
            self.theme_name,
            str(self.settings.get("accent_color", "indigo")),
            bool(self.settings.get("glass_effects", True)),
        )
        self.font_scale = float(self.settings.get("font_scale", 1.0))
        self.current_page = "home"
        self.current_term: Optional[dict] = None
        # Browser-like navigation history for the visible back button / Alt+Left.
        self.nav_history: List[dict] = []
        self._restoring_navigation = False
        self.current_category = "전체"
        self.current_subject = "전체"
        self.filter_mode = "전체"
        self.result_limit = int(self.settings.get("search_result_limit", 100))
        self.suggestion_popup: Optional[tk.Toplevel] = None
        self._search_after_id = None
        self._active_simulators = []

        self.db = KnowledgeDatabase(limit_gb=int(self.settings.get("storage_limit_gb", 5)))

        try:
            self.iconbitmap(str(resource_path("assets/physics_pocket.ico")))
        except Exception:
            try:
                self._icon_image = tk.PhotoImage(file=str(resource_path("assets/physics_pocket.png")))
                self.iconphoto(True, self._icon_image)
            except Exception:
                self._icon_image = None

        self.builtin_terms = load_terms()
        self.terms = self.builtin_terms + self.db.all_user_terms()
        self.sources = {s["id"]: s for s in load_sources()}
        self.constants = load_constants()
        self.formulas = build_formula_catalog(self.builtin_terms)
        self._reindex_terms()

        self.favorite_store = JsonSetStore("favorites.json")
        self.favorite_ids = self.favorite_store.load()
        self.history_store = JsonListStore("recent_searches.json", maximum=12)
        self.recent_searches = self.history_store.load()
        self.note_store = JsonDictStore("term_notes.json")
        self.term_notes = self.note_store.load()

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="준비됨")
        self.favorites_only_var = tk.BooleanVar(value=False)
        self.level_var = tk.StringVar(value="전체 수준")
        self.subject_var = tk.StringVar(value="전체")

        self._configure_ttk()
        self._build_shell()
        self._bind_shortcuts()

        splash = Splash(self, self.theme)
        self.update_idletasks()
        self.after(1200, lambda: self._finish_startup(splash))

    def _reindex_terms(self) -> None:
        self.term_by_id = {t["id"]: t for t in self.terms}
        self.term_by_name = {t["name_ko"]: t for t in self.terms}
        self.categories = sorted({t.get("category", "기타") for t in self.terms})
        self.category_counts = {c: sum(1 for t in self.terms if t.get("category") == c) for c in self.categories}
        science_subjects = {"물리", "화학", "생명과학", "지구과학", "천문학"}
        self.subject_counts = {name: sum(1 for t in self.terms if t.get("subject", "물리") == name and not t.get("user_added"))
                               for name in science_subjects | {"수학", "국어"}}
        self.subject_counts["과학"] = sum(self.subject_counts.get(name, 0) for name in science_subjects)
        self.subject_counts["사용자"] = sum(1 for t in self.terms if t.get("user_added"))

    def reload_user_terms(self) -> None:
        self.terms = self.builtin_terms + self.db.all_user_terms()
        self._reindex_terms()
        self._build_left_sidebar()
        self._build_right_sidebar()

    # ---------- Shell and theme ----------
    def _configure_ttk(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        t = self.theme
        style.configure("Vertical.TScrollbar", background=t["surface3"], troughcolor=t["bg"], bordercolor=t["bg"], arrowcolor=t["muted"], relief="flat")
        style.configure("TCombobox", fieldbackground=t["surface2"], background=t["surface2"], foreground=t["text"], arrowcolor=t["accent"], bordercolor=t["line"], lightcolor=t["line"], darkcolor=t["line"], padding=8)
        style.configure("Update.Horizontal.TProgressbar", troughcolor=t["surface3"], background=t["accent"], bordercolor=t["surface3"], lightcolor=t["accent"], darkcolor=t["accent"], thickness=8)
        style.configure("Soft.Horizontal.TProgressbar", troughcolor=t["surface3"], background=t["blue"], bordercolor=t["surface3"], thickness=6)

    def _finish_startup(self, splash: Splash) -> None:
        splash.destroy()
        self.deiconify()
        apply_windows_chrome(self, self.theme_name == "dark")
        self.lift()
        self.show_home()
        self.search_entry.focus_set()
        if bool(self.settings.get("check_updates_on_startup", True)):
            self.after(1800, self.check_updates_background)

    def _build_shell(self) -> None:
        for child in self.winfo_children():
            if isinstance(child, Splash):
                continue
            child.destroy()
        t = self.theme
        self.configure(bg=t["bg"])
        self._configure_ttk()

        self.shell = tk.Frame(self, bg=t["bg"])
        self.shell.pack(fill="both", expand=True)
        self.nav_rail = tk.Frame(self.shell, bg=t["rail"], width=218, highlightthickness=1, highlightbackground=t["line"])
        self.nav_rail.pack(side="left", fill="y")
        self.nav_rail.pack_propagate(False)
        self.main_stack = tk.Frame(self.shell, bg=t["bg"])
        self.main_stack.pack(side="right", fill="both", expand=True)

        self._build_navigation()
        self._build_top_header()
        self._build_statusbar()
        self._build_body()
        self._refresh_nav_state()

    def _build_top_header(self) -> None:
        t = self.theme
        header = tk.Frame(self.main_stack, bg=t["glass"], height=76, highlightthickness=1, highlightbackground=t["line"])
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=t["glass"])
        left.pack(side="left", padx=(22, 12), pady=14)
        self.back_button = self._button(left, "←", self.go_back, kind="ghost", padx=11, pady=8)
        self.back_button.pack(side="left", padx=(0, 9))
        self.header_context_var = getattr(self, "header_context_var", tk.StringVar(value="홈"))
        tk.Label(left, textvariable=self.header_context_var, bg=t["glass"], fg=t["text"], font=("Malgun Gothic", self._font(11), "bold")).pack(side="left")
        self._update_back_button()

        search_wrap = tk.Frame(header, bg=t["glass"])
        search_wrap.pack(side="left", fill="x", expand=True, padx=18, pady=13)
        search_box = tk.Frame(search_wrap, bg=t["surface"], highlightthickness=1, highlightbackground=t["line"])
        search_box.pack(fill="both", expand=True)
        tk.Label(search_box, text="⌕", bg=t["surface"], fg=t["muted"], font=("Segoe UI Symbol", 18)).pack(side="left", padx=(14, 8))
        self.search_entry = tk.Entry(search_box, textvariable=self.search_var, relief="flat", bd=0, bg=t["surface"], fg=t["text"], insertbackground=t["text"], font=("Malgun Gothic", self._font(11)))
        self.search_entry.pack(side="left", fill="both", expand=True, ipady=10)
        self.search_entry.bind("<Return>", lambda _e: self.perform_search())
        self.search_entry.bind("<KeyRelease>", self._schedule_suggestions)
        self.search_entry.bind("<Escape>", lambda _e: self._hide_suggestions())
        tk.Label(search_box, text="Ctrl+L", bg=t["surface2"], fg=t["muted"], font=("Segoe UI", self._font(7), "bold"), padx=7, pady=3).pack(side="right", padx=(4, 9))

        tools = tk.Frame(header, bg=t["glass"])
        tools.pack(side="right", padx=(8, 18), pady=13)
        self.update_button = self._button(tools, "↻", lambda: self.navigate("updates"), kind="ghost", padx=11, pady=8)
        self.update_button.pack(side="left", padx=3)
        self._refresh_update_indicator()
        self._button(tools, "☾" if self.theme_name == "light" else "☀", self.toggle_theme, kind="ghost", padx=11, pady=8).pack(side="left", padx=3)
        self._button(tools, "⚙", self.show_settings, kind="ghost", padx=11, pady=8).pack(side="left", padx=3)

    def _build_navigation(self) -> None:
        t = self.theme
        for child in self.nav_rail.winfo_children():
            child.destroy()

        brand = tk.Frame(self.nav_rail, bg=t["rail"])
        brand.pack(fill="x", padx=16, pady=(18, 15))
        try:
            raw = tk.PhotoImage(file=str(resource_path("assets/physics_pocket.png")))
            factor = max(1, raw.width() // 42)
            self._nav_logo = raw.subsample(factor, factor)
            tk.Label(brand, image=self._nav_logo, bg=t["rail"]).pack(side="left", padx=(0, 9))
        except Exception:
            tk.Label(brand, text="⚛", bg=t["accent"], fg="#FFFFFF", font=("Segoe UI Symbol", 15, "bold"), padx=7, pady=5).pack(side="left", padx=(0, 9))
        text = tk.Frame(brand, bg=t["rail"]); text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text="물리사전", bg=t["rail"], fg=t["text"], font=("Malgun Gothic", self._font(10), "bold")).pack(anchor="w")
        tk.Label(text, text=f"Pocket · {APP_VERSION}", bg=t["rail"], fg=t["muted"], font=("Segoe UI", self._font(7))).pack(anchor="w")

        tk.Label(self.nav_rail, text="탐색", bg=t["rail"], fg=t["muted"], font=("Malgun Gothic", self._font(7), "bold"), anchor="w").pack(fill="x", padx=20, pady=(2, 5))
        self.nav_buttons = {}
        items = [
            ("home", "⌂", "홈"), ("dictionary", "⌕", "개념 탐색"), ("formulas", "∑", "공식"),
            ("calculators", "▦", "계산기"), ("simulations", "◉", "시뮬레이션"), ("constants", "⊙", "물리상수"),
            ("korean", "가", "국어 학습"), ("converter", "⇄", "단위 변환"), ("data", "▣", "내 데이터"),
        ]
        for key, icon, label in items:
            btn = tk.Button(self.nav_rail, text=f"{icon}    {label}", command=lambda k=key: self.navigate(k), relief="flat", bd=0,
                bg=t["rail"], fg=t["muted"], activebackground=t["surface3"], activeforeground=t["text"],
                font=("Malgun Gothic", self._font(8), "bold"), anchor="w", padx=18, pady=7, cursor="hand2")
            btn.pack(fill="x", padx=9, pady=1)
            self.nav_buttons[key] = btn

        tk.Label(self.nav_rail, text="시스템", bg=t["rail"], fg=t["muted"], font=("Malgun Gothic", self._font(7), "bold"), anchor="w").pack(fill="x", padx=20, pady=(16, 5))
        for key, icon, label in [("updates","↻","업데이트"),("help","?","도움말"),("about","ⓘ","앱 정보")]:
            btn = tk.Button(self.nav_rail, text=f"{icon}    {label}", command=lambda k=key: self.navigate(k), relief="flat", bd=0,
                bg=t["rail"], fg=t["muted"], activebackground=t["surface3"], activeforeground=t["text"],
                font=("Malgun Gothic", self._font(8), "bold"), anchor="w", padx=18, pady=7, cursor="hand2")
            btn.pack(fill="x", padx=9, pady=1)
            self.nav_buttons[key] = btn
        tk.Button(self.nav_rail, text="⚙    설정", command=self.show_settings, relief="flat", bd=0, bg=t["rail"], fg=t["muted"], activebackground=t["surface3"], activeforeground=t["text"], font=("Malgun Gothic", self._font(8), "bold"), anchor="w", padx=18, pady=7, cursor="hand2").pack(fill="x", padx=9, pady=1)

        footer = tk.Frame(self.nav_rail, bg=t["rail"])
        footer.pack(side="bottom", fill="x", padx=15, pady=16)
        tk.Label(footer, text=f"Build {APP_BUILD} · {APP_CHANNEL.capitalize()}", bg=t["rail"], fg=t["muted"], font=("Segoe UI", self._font(7))).pack(anchor="w")
        tk.Label(footer, text=f"개념·색인 {len(self.terms):,}개", bg=t["rail"], fg=t["muted"], font=("Segoe UI", self._font(7))).pack(anchor="w", pady=(2,0))

    def _build_body(self) -> None:
        t = self.theme
        body = tk.Frame(self.main_stack, bg=t["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)
        self.center_panel = tk.Frame(body, bg=t["bg"])
        self.center_panel.pack(fill="both", expand=True)
        # Compatibility containers retained for existing data/navigation helpers, but no longer occupy layout space.
        self.left_panel = tk.Frame(body, bg=t["bg"])
        self.right_panel = tk.Frame(body, bg=t["bg"])

    def _build_statusbar(self) -> None:
        t = self.theme
        bar = tk.Frame(self.main_stack, bg=t["glass"], height=27, highlightthickness=1, highlightbackground=t["line"])
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var, bg=t["glass"], fg=t["muted"], font=("Malgun Gothic", self._font(7)), anchor="w", padx=16).pack(side="left", fill="x", expand=True)
        tk.Label(bar, text="Ctrl+L 검색  ·  Alt+← 뒤로  ·  F1 도움말", bg=t["glass"], fg=t["muted"], font=("Malgun Gothic", self._font(7)), padx=16).pack(side="right")

    def _build_left_sidebar(self) -> None:
        # 3.1.5 Beta 2: legacy permanent category sidebar was removed.
        # Subject/category controls now live contextually in Home and Search views.
        return

    def _build_right_sidebar(self) -> None:
        # 3.1.5 Beta 2: legacy permanent right sidebar was removed to free content width.
        return

    def _font(self, size: int) -> int:
        return max(8, int(round(size * self.font_scale)))

    def _button(self, master: tk.Misc, text: str, command: Callable, kind: str = "normal", padx: int = 14, pady: int = 8) -> tk.Button:
        t = self.theme
        styles = {
            "accent": (t["accent"], "#FFFFFF", t["accent2"], "#FFFFFF"),
            "normal": (t["surface2"], t["text"], t["surface3"], t["text"]),
            "ghost": (t["surface"], t["muted"], t["surface3"], t["text"]),
            "subtle": (t["accent_soft"], t["accent2"], t["surface3"], t["accent2"]),
            "danger": (t["surface2"], t["danger"], t["surface3"], t["danger"]),
        }
        bg, fg, active_bg, active_fg = styles.get(kind, styles["normal"])
        return tk.Button(
            master,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            font=("Malgun Gothic", self._font(9), "bold"),
            padx=padx,
            pady=pady,
            cursor="hand2",
        )

    def _side_button(self, master: tk.Misc, label: str, category: str, count: int) -> tk.Button:
        t = self.theme
        selected = self.current_category == category
        bg = t["accent_soft"] if selected else t["surface"]
        fg = t["accent2"] if selected else t["text"]
        return tk.Button(
            master,
            text="{}     {}".format(label, count),
            command=lambda c=category: self.select_category(c),
            relief="flat",
            bd=0,
            bg=bg,
            fg=fg,
            activebackground=t["surface3"],
            activeforeground=t["accent2"],
            font=("Malgun Gothic", self._font(9), "bold" if selected else "normal"),
            anchor="w",
            padx=10,
            pady=9,
            cursor="hand2",
        )

    def _link_button(self, master: tk.Misc, text: str, command: Callable) -> tk.Button:
        t = self.theme
        return tk.Button(
            master,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            bg=t["surface"],
            fg=t["blue"],
            activebackground=t["surface3"],
            activeforeground=t["accent2"],
            font=("Malgun Gothic", self._font(9)),
            anchor="w",
            padx=4,
            pady=5,
            cursor="hand2",
        )

    def _chip(self, master: tk.Misc, text: str, command: Optional[Callable] = None, accent: bool = False) -> tk.Widget:
        t = self.theme
        bg = t["accent_soft"] if accent else t["surface3"]
        fg = t["accent2"] if accent else t["muted"]
        if command:
            return tk.Button(master, text=text, command=command, relief="flat", bd=0, bg=bg, fg=fg, activebackground=t["accent_soft"], activeforeground=t["accent2"], font=("Malgun Gothic", self._font(8), "bold"), padx=9, pady=4, cursor="hand2")
        return tk.Label(master, text=text, bg=bg, fg=fg, font=("Malgun Gothic", self._font(8), "bold"), padx=9, pady=4)

    def _sidebar_title(self, master: tk.Misc, text: str) -> None:
        t = self.theme
        row = tk.Frame(master, bg=t["surface"])
        row.pack(fill="x", padx=14, pady=(18, 8))
        tk.Label(row, text=text, bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(10), "bold")).pack(side="left")
        tk.Frame(row, bg=t["line"], height=1).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _clear_center(self) -> tk.Frame:
        self._active_simulators = []
        for child in self.center_panel.winfo_children(): child.destroy()
        frame = tk.Frame(self.center_panel, bg=self.theme["bg"]); frame.pack(fill="both", expand=True)
        return frame

    def _page_title(self, master: tk.Misc, title: str, subtitle: str = "") -> tk.Frame:
        t = self.theme
        row = tk.Frame(master, bg=t["bg"])
        row.pack(fill="x", pady=(0, 16))
        text_box = tk.Frame(row, bg=t["bg"])
        text_box.pack(side="left", fill="x", expand=True)
        tk.Label(text_box, text=title, bg=t["bg"], fg=t["text"], font=("Malgun Gothic", self._font(20), "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(text_box, text=subtitle, bg=t["bg"], fg=t["muted"], font=("Malgun Gothic", self._font(9)), wraplength=850, justify="left").pack(anchor="w", pady=(5, 0))
        return row

    def _card(self, master: tk.Misc, bg: Optional[str] = None, padx: int = 20, pady: int = 18) -> tk.Frame:
        # GlassCard keeps the same outer/content contract used by every page,
        # while giving cards a readable opaque surface and a soft rounded edge.
        return GlassCard(master, self.theme, fill=bg or self.theme["surface"], padx=padx, pady=pady)

    def _put_card_content(self, outer: tk.Frame) -> tk.Frame:
        if hasattr(outer, "content"):
            return outer.content  # type: ignore[attr-defined]
        inner = outer.winfo_children()[0]
        padx, pady = getattr(inner, "_content_padding", (20, 18))
        content = tk.Frame(inner, bg=inner.cget("bg"))
        content.pack(fill="both", expand=True, padx=padx, pady=pady)
        return content

    def _soft_subject_color(self, subject: str) -> str:
        return {
            "수학": self.theme["blue"], "물리": self.theme["accent"], "화학": self.theme["orange"],
            "생명과학": self.theme["green"], "지구과학": self.theme["cyan"], "천문학": self.theme["pink"],
        }.get(subject, self.theme["accent"])

    def _home_subject_card(self, master: tk.Misc, subject: str, icon: str, count: int) -> tk.Frame:
        t = self.theme
        tone = self._soft_subject_color(subject)
        outer = self._card(master, padx=16, pady=16)
        c = self._put_card_content(outer)
        stripe = tk.Frame(c, bg=tone, height=5); stripe.pack(fill="x", pady=(0,12)); stripe.pack_propagate(False)
        top = tk.Frame(c, bg=t["surface"]); top.pack(fill="x")
        badge = tk.Label(top, text=icon, bg=t["accent_soft"], fg=tone, font=("Segoe UI Symbol", self._font(16), "bold"), padx=10, pady=7)
        badge.pack(side="left")
        meta = tk.Frame(top, bg=t["surface"]); meta.pack(side="left", fill="x", expand=True, padx=(12,0))
        tk.Label(meta, text=subject, bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(12), "bold"), anchor="w").pack(fill="x")
        tk.Label(meta, text="개념 · 공식 · 실험", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(7)), anchor="w").pack(fill="x", pady=(3,0))
        tk.Label(c, text=f"{count:,}", bg=t["surface"], fg=tone, font=("Segoe UI", self._font(21), "bold"), anchor="w").pack(fill="x", pady=(15,0))
        tk.Label(c, text="검증된 학습 항목", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), anchor="w").pack(fill="x")
        tk.Button(c, text="탐색 시작   →", command=lambda s=subject:self.select_subject(s), relief="flat", bd=0, bg=t["accent_soft"], fg=t["accent2"], activebackground=t["surface3"], activeforeground=t["text"], font=("Malgun Gothic", self._font(8), "bold"), anchor="w", cursor="hand2", padx=10, pady=8).pack(fill="x", pady=(14,0))
        return outer

    def _simple_list_row(self, master: tk.Misc, title: str, subtitle: str, command: Callable, icon: str = "•") -> None:
        t = self.theme
        row = tk.Frame(master, bg=t["surface2"]); row.pack(fill="x", pady=3)
        tk.Label(row, text=icon, bg=t["surface2"], fg=t["accent2"], font=("Segoe UI Symbol", self._font(10), "bold"), width=3).pack(side="left", padx=(8,0), pady=8)
        txt = tk.Frame(row, bg=t["surface2"]); txt.pack(side="left", fill="x", expand=True, padx=5, pady=7)
        tk.Button(txt, text=title, command=command, relief="flat", bd=0, bg=t["surface2"], fg=t["text"], activebackground=t["surface2"], activeforeground=t["accent2"], font=("Malgun Gothic", self._font(9), "bold"), anchor="w", cursor="hand2").pack(fill="x")
        tk.Label(txt, text=subtitle, bg=t["surface2"], fg=t["muted"], font=("Malgun Gothic", self._font(7)), anchor="w").pack(fill="x")
        tk.Label(row, text="›", bg=t["surface2"], fg=t["muted"], font=("Segoe UI Symbol", self._font(14))).pack(side="right", padx=10)

    # ---------- Navigation ----------
    def _capture_nav_state(self) -> dict:
        return {
            "page": self.current_page,
            "term_id": self.current_term.get("id") if self.current_term else None,
            "query": self.search_var.get(),
            "category": self.current_category,
            "subject": self.current_subject,
            "filter_mode": self.filter_mode,
            "level": self.level_var.get(),
            "favorites_only": bool(self.favorites_only_var.get()),
            "result_limit": self.result_limit,
        }

    def _remember_location(self) -> None:
        if self._restoring_navigation:
            return
        state = self._capture_nav_state()
        if self.nav_history and self.nav_history[-1] == state:
            return
        self.nav_history.append(state)
        if len(self.nav_history) > 60:
            self.nav_history = self.nav_history[-60:]
        self._update_back_button()

    def _update_back_button(self) -> None:
        button = getattr(self, "back_button", None)
        if button is None:
            return
        try:
            button.configure(state="normal" if self.nav_history else "disabled")
        except tk.TclError:
            pass

    def go_back(self, _event=None) -> None:
        self._hide_suggestions()
        if not self.nav_history:
            self._update_back_button()
            return
        state = self.nav_history.pop()
        self._restoring_navigation = True
        try:
            self.search_var.set(state.get("query", ""))
            self.current_category = state.get("category", "전체")
            self.current_subject = state.get("subject", "전체")
            self.subject_var.set(self.current_subject)
            self.filter_mode = state.get("filter_mode", "전체")
            self.level_var.set(state.get("level", "전체 수준"))
            self.favorites_only_var.set(bool(state.get("favorites_only", False)))
            self.result_limit = int(state.get("result_limit", self.settings.get("search_result_limit", 100)))
            self._build_left_sidebar()
            page = state.get("page", "home")
            term = self.term_by_id.get(state.get("term_id")) if state.get("term_id") else None
            if page == "term" and term:
                self.show_term(term, record_navigation=False)
            elif page in ("results", "dictionary"):
                self.perform_search(add_history=False, record_navigation=False)
            else:
                self.navigate(page, record_navigation=False)
        finally:
            self._restoring_navigation = False
            self._update_back_button()

    def navigate(self, page: str, record_navigation: bool = True) -> None:
        self._hide_suggestions()
        if record_navigation and page != self.current_page:
            self._remember_location()
        if page == "home": self.show_home()
        elif page == "dictionary":
            self.current_page = "dictionary"; self.perform_search(add_history=False, record_navigation=False)
        elif page == "formulas": self.show_formulas()
        elif page == "simulations": self.show_simulations()
        elif page == "korean": self.show_korean()
        elif page == "constants": self.show_constants()
        elif page == "converter": self.show_converter()
        elif page == "calculators": self.show_calculators()
        elif page == "data": self.show_data_manager()
        elif page == "updates": self.show_updates()
        elif page == "help": self.show_help()
        elif page == "about": self.show_about()

    def _refresh_nav_state(self) -> None:
        t = self.theme
        page_labels = {"home":"홈","dictionary":"개념 탐색","results":"검색 결과","term":"개념 상세","formulas":"공식","simulations":"시뮬레이션","calculators":"계산기","constants":"물리상수","converter":"단위 변환","data":"내 데이터","updates":"업데이트 센터","help":"도움말","about":"앱 정보"}
        if hasattr(self, "header_context_var"):
            self.header_context_var.set("국어 학습" if self.current_page == "korean" else page_labels.get(self.current_page, "Physics + Math Pocket"))
        for key, button in getattr(self, "nav_buttons", {}).items():
            selected = (self.current_page == key) or (self.current_page == "term" and key == "dictionary") or (self.current_page == "results" and key == "dictionary")
            try:
                button.configure(bg=t["accent_soft"] if selected else t["rail"], fg=t["accent2"] if selected else t["muted"])
            except tk.TclError:
                pass

    def select_category(self, category: str) -> None:
        self._remember_location()
        self.current_category = category
        self.search_var.set("")
        self.filter_mode = "전체"
        self.current_page = "results"
        self._build_left_sidebar()
        self.perform_search(add_history=False)

    def select_subject(self, subject: str) -> None:
        self._remember_location()
        self.current_subject = subject
        self.subject_var.set(subject)
        self.current_category = "전체"
        self.search_var.set("")
        self.filter_mode = "전체"
        self.current_page = "results"
        self._build_left_sidebar()
        self.perform_search(add_history=False)

    def show_home(self) -> None:
        self.current_page = "home"; self.current_term = None; self._refresh_nav_state()
        frame = self._clear_center(); t = self.theme
        scroll = ScrollableFrame(frame, t["bg"]); scroll.pack(fill="both", expand=True); inner = scroll.inner

        # Hero: task-focused search first, with large touch-friendly controls inspired by modern system UIs.
        hero = tk.Canvas(inner, height=246, bg=t["accent"], highlightthickness=0)
        hero.pack(fill="x", pady=(0,18))
        search_host = tk.Frame(hero, bg="#FFFFFF")
        tk.Label(search_host, text="⌕", bg="#FFFFFF", fg="#697080", font=("Segoe UI Symbol", 18)).pack(side="left", padx=(14,8))
        home_entry = tk.Entry(search_host, textvariable=self.search_var, relief="flat", bd=0, bg="#FFFFFF", fg="#17191F", insertbackground="#17191F", font=("Malgun Gothic", self._font(11)))
        home_entry.pack(side="left", fill="both", expand=True, ipady=10)
        home_entry.bind("<Return>", lambda _e: self.perform_search())
        self._button(search_host, "검색", self.perform_search, kind="accent", padx=18, pady=9).pack(side="right", padx=5, pady=5)
        search_host.place(x=38, y=146, width=690, height=54)
        hero_title = "오늘도 새로운 지식을 탐험해보세요"
        title_font = tkfont.Font(self, family="Malgun Gothic", size=self._font(22), weight="bold")
        caption_font = tkfont.Font(self, family="Malgun Gothic", size=self._font(9))
        def paint_hero(event=None):
            w=max(hero.winfo_width(),600)
            title_lines=max(1, math.ceil(title_font.measure(hero_title)/max(1,w-76)))
            title_height=title_font.metrics("linespace")*title_lines
            line_height=caption_font.metrics("linespace")
            subtitle_y=35+title_height+10
            note_y=subtitle_y+line_height+8
            search_y=note_y+line_height+14
            h=search_y+54+24
            if int(float(hero.cget("height"))) != h:
                hero.configure(height=h)
            hero.delete("hero_bg")
            a=(69,91,245); b=(138,77,243)
            for x in range(0,w,10):
                q=x/max(1,w-1); col='#%02x%02x%02x'%tuple(int(a[i]*(1-q)+b[i]*q) for i in range(3))
                hero.create_rectangle(x,0,x+11,h,fill=col,outline='',tags='hero_bg')
            hero.create_oval(w-300,-100,w+70,270,fill="#8E70F7",outline="",tags='hero_bg')
            hero.create_oval(w-155,80,w+80,315,fill="#5575F7",outline="",tags='hero_bg')
            hero.create_text(38,35,text=hero_title,width=w-76,fill="#FFFFFF",font=title_font,anchor="nw",tags='hero_bg')
            hero.create_text(40,subtitle_y,text=f"자세한 설명 {sum(t.get('tier') != '확장 인덱스' for t in self.terms):,}개 · 공식 {len(self.formulas):,}개 · 시뮬레이션 {len(SIM_TITLES)}종",fill="#E8E8FF",font=caption_font,anchor="nw",tags="hero_bg")
            hero.create_text(40,note_y,text="물리 실험으로 원리를 살펴보고, 국어 개념과 확인 문제로 학습을 이어가세요.",fill="#F2F1FF",font=caption_font,anchor="nw",tags="hero_bg")
            hero.tag_lower('hero_bg')
            search_host.place_configure(y=search_y,width=min(730,max(420,w-76)))
        hero.bind("<Configure>", paint_hero); self.after(1, paint_hero)

        self._page_title(inner, "빠른 탐색", "과목을 먼저 고르거나 위 검색창에서 바로 시작하세요.")
        subjects = [("수학","∑"),("물리","⚛"),("화학","⚗"),("생명과학","DNA"),("지구과학","◎"),("천문학","✦"),("국어","가")]
        grid = tk.Frame(inner, bg=t["bg"]); grid.pack(fill="x", pady=(0,18))
        columns = 4
        for i in range(columns): grid.grid_columnconfigure(i, weight=1, uniform="subjects")
        for i,(subject,icon) in enumerate(subjects):
            row, col = divmod(i, columns)
            card=self._home_subject_card(grid,subject,icon,self.subject_counts.get(subject,0)); card.grid(row=row,column=col,sticky="nsew",padx=(0 if col==0 else 6,0 if col==columns-1 else 6),pady=(0 if row==0 else 10,0))

        cols=tk.Frame(inner,bg=t["bg"]); cols.pack(fill="x",pady=(0,18)); cols.grid_columnconfigure(0,weight=1); cols.grid_columnconfigure(1,weight=1)
        left=self._card(cols,padx=20,pady=18); left.grid(row=0,column=0,sticky="nsew",padx=(0,8)); lc=self._put_card_content(left)
        head=tk.Frame(lc,bg=t["surface"]); head.pack(fill="x",pady=(0,8)); tk.Label(head,text="최근 검색",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(side="left")
        if self.recent_searches:
            for q in self.recent_searches[:5]: self._simple_list_row(lc,q,"다시 검색",lambda x=q:self.search_for(x),"⌕")
        else:
            tk.Label(lc,text="아직 검색 기록이 없어요. 위 검색창에서 첫 개념을 찾아보세요.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9)),wraplength=430,justify="left").pack(anchor="w",pady=10)

        right=self._card(cols,padx=20,pady=18); right.grid(row=0,column=1,sticky="nsew",padx=(8,0)); rc=self._put_card_content(right)
        head=tk.Frame(rc,bg=t["surface"]); head.pack(fill="x",pady=(0,8)); tk.Label(head,text="즐겨찾기",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(side="left")
        favs=[self.term_by_id[x] for x in list(self.favorite_ids) if x in self.term_by_id][:5]
        if favs:
            for term in favs: self._simple_list_row(rc,term["name_ko"],f"{term.get('subject','')} · {term.get('category','')}",lambda x=term:self.show_term(x),"☆")
        else:
            for term in self._daily_featured(3): self._simple_list_row(rc,term["name_ko"],f"추천 · {term.get('subject','')}",lambda x=term:self.show_term(x),"✦")

        self._page_title(inner,"학습 도구","필요한 기능으로 바로 이동합니다.")
        tools=tk.Frame(inner,bg=t["bg"]); tools.pack(fill="x",pady=(0,12))
        tool_specs=[("∑","공식 라이브러리",f"{len(self.formulas):,}개 공식",lambda:self.navigate('formulas')),("▦","계산기",f"{len(CALCULATOR_SPECS)}개 계산기",lambda:self.navigate('calculators')),("◉","시뮬레이션",f"{len(SIM_TITLES)}개 실험 항목",lambda:self.navigate('simulations')),("↻","업데이트 센터",f"Build {APP_BUILD}",lambda:self.navigate('updates'))]
        for i,(icon,title,sub,cmd) in enumerate(tool_specs):
            tools.grid_columnconfigure(i,weight=1,uniform='tools'); outer=self._card(tools,padx=16,pady=15); outer.grid(row=0,column=i,sticky='nsew',padx=(0 if i==0 else 5,0 if i==3 else 5)); c=self._put_card_content(outer)
            tk.Label(c,text=icon,bg=t["surface"],fg=t["accent2"],font=("Segoe UI Symbol",self._font(17),"bold")).pack(anchor='w')
            tk.Button(c,text=title,command=cmd,relief='flat',bd=0,bg=t["surface"],fg=t["text"],activebackground=t["surface"],activeforeground=t["accent2"],font=("Malgun Gothic",self._font(10),"bold"),anchor='w',cursor='hand2').pack(fill='x',pady=(8,2))
            tk.Label(c,text=sub,bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(8)),anchor='w').pack(fill='x')
        scroll.to_top(); self.status_var.set(f"홈 · {len(self.terms):,}개 개념")

    def perform_search(self, add_history: bool = True, record_navigation: Optional[bool] = None) -> None:
        if record_navigation is None: record_navigation = add_history
        if record_navigation: self._remember_location()
        self._hide_suggestions(); query=self.search_var.get().strip()
        if query and add_history:
            self.recent_searches=[query]+[x for x in self.recent_searches if x!=query]; self.recent_searches=self.recent_searches[:12]; self.history_store.save(self.recent_searches)
        self.current_page="results"; self.current_term=None; self._refresh_nav_state(); frame=self._clear_center(); t=self.theme
        scope="전체 수학·과학 개념" if self.current_subject=="전체" else f"{self.current_subject} 개념"
        title=f"‘{query}’ 검색 결과" if query else (f"{self.current_category} 분야" if self.current_category!="전체" else scope)
        results=search_terms(self.terms,query=query,category=self.current_category,favorite_ids=self.favorite_ids,favorites_only=self.favorites_only_var.get(),limit=None)
        results=self._apply_level_and_mode_filters(results)
        header=self._page_title(frame,title,f"{len(results):,}개 결과 · 한국어·영어·설명·공식·관련어를 한 번에 검색합니다.")
        self._button(header,"초기화",self.reset_search,kind="ghost",padx=12,pady=7).pack(side="right")

        subject_strip=tk.Frame(frame,bg=t["bg"]); subject_strip.pack(fill="x",pady=(0,8))
        for subject in ["전체","수학","물리","화학","생명과학","지구과학","천문학","국어"]:
            selected=self.current_subject==subject
            tk.Button(subject_strip,text=subject,command=lambda s=subject:self.select_subject(s),relief="flat",bd=0,bg=t["accent_soft"] if selected else t["surface"],fg=t["accent2"] if selected else t["muted"],activebackground=t["accent_soft"],activeforeground=t["accent2"],font=("Malgun Gothic",self._font(8),"bold"),padx=12,pady=7,cursor="hand2").pack(side="left",padx=(0,5))

        tabs=tk.Frame(frame,bg=t["bg"]); tabs.pack(fill="x",pady=(0,12))
        for mode in ["전체","공식 있음","중등","고등·일반","대학","시뮬레이션","즐겨찾기"]:
            selected=mode==self.filter_mode
            tk.Button(tabs,text=mode,command=lambda m=mode:self.set_filter_mode(m),relief="flat",bd=0,bg=t["surface3"] if not selected else t["accent"],fg=t["muted"] if not selected else "#FFFFFF",activebackground=t["accent_soft"],activeforeground=t["accent2"],font=("Malgun Gothic",self._font(8),"bold"),padx=11,pady=6,cursor="hand2").pack(side="left",padx=(0,5))
        scroll=ScrollableFrame(frame,t["bg"]); scroll.pack(fill="both",expand=True)
        if not results:
            outer=self._card(scroll.inner,padx=30,pady=36); outer.pack(fill="x",pady=10); c=self._put_card_content(outer)
            tk.Label(c,text="검색 결과가 없습니다",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(16),"bold")).pack(); tk.Label(c,text="검색어를 줄이거나 영어·공식·관련어로 다시 찾아보세요.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9))).pack(pady=(8,0))
        else:
            shown=results[:self.result_limit]
            for term in shown:self._result_card(scroll.inner,term)
            if len(results)>len(shown): self._button(scroll.inner,f"다음 {min(80,len(results)-len(shown))}개 더 보기",self._show_more_results,kind="normal",padx=20,pady=10).pack(pady=15)
        scroll.to_top(); self.status_var.set(f"검색 결과 {len(results):,}개")

    def _apply_level_and_mode_filters(self, terms: List[dict]) -> List[dict]:
        if self.current_subject == "과학": terms=[t for t in terms if t.get("subject","물리") in {"물리","화학","생명과학","지구과학","천문학"} and not t.get("user_added")]
        elif self.current_subject not in {"전체", "사용자"}: terms=[t for t in terms if t.get("subject","물리")==self.current_subject and not t.get("user_added")]
        elif self.current_subject == "사용자": terms=[t for t in terms if t.get("user_added")]
        level=self.level_var.get()
        if level!="전체 수준": terms=[t for t in terms if level in t.get("level","")]
        mode=self.filter_mode
        if mode=="공식 있음": terms=[t for t in terms if t.get("formula","").strip()]
        elif mode=="중등": terms=[t for t in terms if "중등" in t.get("level","")]
        elif mode=="고등·일반": terms=[t for t in terms if any(x in t.get("level","") for x in ("고등","일반","심화"))]
        elif mode=="대학": terms=[t for t in terms if "대학" in t.get("level","") or (t.get("subject")=="수학" and "심화" in t.get("level",""))]
        elif mode=="시뮬레이션": terms=[t for t in terms if simulator_for_term(t)]
        elif mode=="즐겨찾기": terms=[t for t in terms if t.get("id") in self.favorite_ids]
        return terms

    def _result_card(self, master: tk.Misc, term: dict) -> None:
        t=self.theme; outer=self._card(master,padx=18,pady=15); outer.pack(fill="x",pady=6); content=self._put_card_content(outer)
        head=tk.Frame(content,bg=t["surface"]); head.pack(fill="x")
        tk.Button(head,text=term["name_ko"],command=lambda x=term:self.show_term(x),relief="flat",bd=0,bg=t["surface"],fg=t["blue"],activebackground=t["surface"],activeforeground=t["accent2"],font=("Malgun Gothic",self._font(14),"bold"),anchor="w",cursor="hand2").pack(side="left")
        tk.Button(head,text="★" if term["id"] in self.favorite_ids else "☆",command=lambda x=term:self.toggle_favorite(x),relief="flat",bd=0,bg=t["surface"],fg=t["accent2"],activebackground=t["surface"],activeforeground=t["accent"],font=("Segoe UI Symbol",self._font(14)),cursor="hand2").pack(side="right")
        tk.Label(content,text=term.get("name_en",""),bg=t["surface"],fg=t["muted"],font=("Segoe UI",self._font(9),"italic"),anchor="w").pack(fill="x",pady=(2,8))
        chips=tk.Frame(content,bg=t["surface"]); chips.pack(fill="x",pady=(0,9))
        self._chip(chips,term.get("subject","물리"),accent=True).pack(side="left",padx=(0,5)); self._chip(chips,term.get("category","기타"),lambda c=term.get("category","전체"):self.select_category(c)).pack(side="left",padx=(0,5)); self._chip(chips,term.get("level","수준 미정")).pack(side="left",padx=(0,5))
        if term.get("formula"): self._chip(chips,"공식").pack(side="left",padx=(0,5))
        if simulator_for_term(term): self._chip(chips,"▸ 시뮬레이션").pack(side="left",padx=(0,5))
        if term.get("user_added"): self._chip(chips,"내 데이터").pack(side="left",padx=(0,5))
        if term.get("tier")=="확장 인덱스": self._chip(chips,"확장 색인 · 요약").pack(side="left",padx=(0,5))
        tk.Label(content,text=term.get("summary",""),bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(10)),wraplength=760,justify="left",anchor="w").pack(fill="x")
        related=term.get("related",[])[:4]
        if related:
            rr=tk.Frame(content,bg=t["surface"]); rr.pack(fill="x",pady=(10,0)); tk.Label(rr,text="관련",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(8),"bold")).pack(side="left",padx=(0,7))
            for name in related:self._chip(rr,name,lambda n=name:self.open_related(n)).pack(side="left",padx=(0,4))

    def _show_more_results(self) -> None:
        self.result_limit += 80
        self.perform_search(add_history=False)

    def set_filter_mode(self, mode: str) -> None:
        self.filter_mode = mode
        self.result_limit = 80
        self.perform_search(add_history=False)

    def _refresh_current_results(self) -> None:
        if self.current_page in ("results", "dictionary"):
            self.perform_search(add_history=False)
        else:
            self._build_left_sidebar()

    def reset_search(self) -> None:
        self.search_var.set(""); self.current_category="전체"; self.current_subject="전체"; self.subject_var.set("전체"); self.filter_mode="전체"; self.favorites_only_var.set(False); self.level_var.set("전체 수준"); self.result_limit=int(self.settings.get("search_result_limit",100)); self._build_left_sidebar(); self.show_home()

    def search_for(self, query: str) -> None:
        self.search_var.set(query)
        self.current_category = "전체"
        self.filter_mode = "전체"
        self._build_left_sidebar()
        self.perform_search()

    def _schedule_suggestions(self, _event=None) -> None:
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(120, self._show_suggestions)

    def _show_suggestions(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            self._hide_suggestions()
            return
        suggestions = search_terms(self.terms, query=query, limit=7)
        if not suggestions:
            self._hide_suggestions()
            return
        self._hide_suggestions()
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        self.suggestion_popup = popup
        t = self.theme
        popup.configure(bg=t["line"])
        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height() + 8
        width = max(420, self.search_entry.winfo_width())
        popup.geometry("{}x{}+{}+{}".format(width, 44 * len(suggestions) + 8, x, y))
        box = tk.Frame(popup, bg=t["surface"], highlightthickness=1, highlightbackground=t["line"])
        box.pack(fill="both", expand=True)
        for term in suggestions:
            row = tk.Button(
                box,
                text="{}    {}".format(term["name_ko"], term.get("name_en", "")),
                command=lambda x=term: self._choose_suggestion(x),
                relief="flat",
                bd=0,
                bg=t["surface"],
                fg=t["text"],
                activebackground=t["accent_soft"],
                activeforeground=t["accent2"],
                anchor="w",
                font=("Malgun Gothic", self._font(9)),
                padx=14,
                pady=9,
                cursor="hand2",
            )
            row.pack(fill="x")

    def _choose_suggestion(self, term: dict) -> None:
        self.search_var.set(term["name_ko"])
        self._hide_suggestions()
        self.show_term(term, add_history=True)

    def _hide_suggestions(self) -> None:
        if self.suggestion_popup is not None:
            try:
                self.suggestion_popup.destroy()
            except Exception:
                pass
            self.suggestion_popup = None

    # ---------- Term detail ----------
    def show_term(self, term: dict, add_history: bool = False, record_navigation: bool = True) -> None:
        if record_navigation and not (self.current_page == "term" and self.current_term and self.current_term.get("id") == term.get("id")):
            self._remember_location()
        self._hide_suggestions()
        self.current_page = "term"
        self.current_term = term
        self._refresh_nav_state()
        if add_history:
            query = term["name_ko"]
            self.recent_searches = [query] + [x for x in self.recent_searches if x != query]
            self.recent_searches = self.recent_searches[:12]
            self.history_store.save(self.recent_searches)
            self._build_right_sidebar()
        frame = self._clear_center()
        t = self.theme
        scroll = ScrollableFrame(frame, t["bg"])
        scroll.pack(fill="both", expand=True)
        inner = scroll.inner

        breadcrumb = tk.Frame(inner, bg=t["bg"])
        breadcrumb.pack(fill="x", pady=(0, 8))
        self._link_button(breadcrumb, "홈", lambda: self.navigate("home")).pack(side="left")
        tk.Label(breadcrumb, text="  ›  ", bg=t["bg"], fg=t["muted"], font=("Malgun Gothic", self._font(9))).pack(side="left")
        self._link_button(breadcrumb, term.get("category", "분야"), lambda c=term.get("category", "전체"): self.select_category(c)).pack(side="left")
        tk.Label(breadcrumb, text="  ›  {}".format(term["name_ko"]), bg=t["bg"], fg=t["muted"], font=("Malgun Gothic", self._font(9))).pack(side="left")

        hero = self._card(inner, padx=26, pady=24)
        hero.pack(fill="x", pady=(0, 12))
        content = self._put_card_content(hero)
        head = tk.Frame(content, bg=t["surface"])
        head.pack(fill="x")
        title_box = tk.Frame(head, bg=t["surface"])
        title_box.pack(side="left", fill="x", expand=True)
        tk.Label(title_box, text=term["name_ko"], bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(24), "bold")).pack(anchor="w")
        tk.Label(title_box, text=term.get("name_en", ""), bg=t["surface"], fg=t["muted"], font=("Segoe UI", self._font(11), "italic")).pack(anchor="w", pady=(3, 0))
        fav_text = "★ 즐겨찾기됨" if term["id"] in self.favorite_ids else "☆ 즐겨찾기"
        self._button(head, fav_text, lambda: self.toggle_favorite(term), kind="subtle", padx=13, pady=8).pack(side="right", anchor="n")

        actions = tk.Frame(content, bg=t["surface"])
        actions.pack(fill="x", pady=(14, 2))
        self._button(actions, "내용 복사", lambda: self.copy_term_text(term), kind="ghost", padx=12, pady=7).pack(side="left", padx=(0, 6))
        self._button(actions, "HTML 저장·인쇄", lambda: self.export_term_html(term), kind="ghost", padx=12, pady=7).pack(side="left", padx=(0, 6))
        self._button(actions, "웹에서 더 보기", lambda: self.open_web_reference_menu(term), kind="ghost", padx=12, pady=7).pack(side="left")
        if term.get("user_added"):
            self._button(actions, "수정", lambda: self.show_add_term_dialog(term), kind="subtle", padx=12, pady=7).pack(side="left", padx=(6, 0))
            self._button(actions, "삭제", lambda: self.delete_user_term(term), kind="danger", padx=12, pady=7).pack(side="left", padx=(6, 0))

        chips = tk.Frame(content, bg=t["surface"])
        chips.pack(fill="x", pady=(14, 16))
        self._chip(chips, term.get("subject", "물리"), accent=True).pack(side="left", padx=(0, 5))
        self._chip(chips, term.get("category", "기타"), lambda c=term.get("category", "전체"): self.select_category(c)).pack(side="left", padx=(0, 5))
        self._chip(chips, term.get("level", "수준 미정")).pack(side="left", padx=(0, 5))
        if term.get("user_added"):
            self._chip(chips, "내 데이터").pack(side="left", padx=(0, 5))
        aliases = term.get("aliases", [])
        for alias in aliases[:3]:
            self._chip(chips, "별칭 · " + alias).pack(side="left", padx=(0, 5))
        summary_box = tk.Frame(content, bg=t["accent_soft"])
        summary_box.pack(fill="x")
        tk.Label(summary_box, text="한눈에 보기", bg=t["accent_soft"], fg=t["accent2"], font=("Malgun Gothic", self._font(9), "bold")).pack(anchor="w", padx=16, pady=(13, 4))
        tk.Label(summary_box, text=term.get("summary", ""), bg=t["accent_soft"], fg=t["text"], font=("Malgun Gothic", self._font(11)), wraplength=780, justify="left", anchor="w").pack(fill="x", padx=16, pady=(0, 14))

        self._detail_section(inner, "자세한 설명", term.get("detail", "설명이 아직 준비되지 않았습니다."), "≡")
        if term.get("formula"):
            self._detail_section(inner, "대표 공식", term["formula"], "ƒ", formula=True)
        if term.get("unit"):
            self._detail_section(inner, "단위와 기호", term["unit"], "▦")
        if term.get("example"):
            self._detail_section(inner, "예시", term["example"], "◎")
        if term.get("caution"):
            self._detail_section(inner, "헷갈리기 쉬운 점", term["caution"], "!")

        sim_id = simulator_for_term(term)
        if sim_id and bool(self.settings.get("show_simulations", True)):
            outer = self._card(inner, padx=22, pady=18)
            outer.pack(fill="x", pady=6)
            c = self._put_card_content(outer)
            tk.Label(c, text="직접 움직여 보기", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(anchor="w")
            tk.Label(c, text="변수를 조절하면 계산·그래프·운동이 즉시 바뀝니다. 실제 법칙을 바탕으로 한 학습용 모델이며 단위와 가정을 함께 표시합니다.", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), wraplength=790, justify="left").pack(anchor="w", pady=(4, 10))
            sim = build_mini_simulator(c, term, self.theme, fps=int(self.settings.get("simulation_fps", 30)))
            if sim is None:
                sim = build_simulator(c, term, self.theme, fps=int(self.settings.get("simulation_fps", 30)))
            if sim is not None:
                if not bool(self.settings.get("animations", True)):
                    sim.play_btn.configure(state="disabled", text="정적 모드")
                sim.pack(fill="x")
                self._active_simulators.append(sim)

        related = term.get("related", [])
        if related:
            outer = self._card(inner, padx=22, pady=18)
            outer.pack(fill="x", pady=6)
            c = self._put_card_content(outer)
            tk.Label(c, text="관련 개념", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(anchor="w", pady=(0, 10))
            wrap = tk.Frame(c, bg=t["surface"])
            wrap.pack(fill="x")
            for i, name in enumerate(related):
                self._chip(wrap, name, lambda n=name: self.open_related(n), accent=(i < 2)).pack(side="left", padx=(0, 6), pady=4)

        note_outer = self._card(inner, padx=22, pady=18)
        note_outer.pack(fill="x", pady=6)
        note_content = self._put_card_content(note_outer)
        tk.Label(note_content, text="내 학습 메모", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(anchor="w")
        tk.Label(note_content, text="이 메모는 이 컴퓨터에만 저장되며 인터넷으로 전송되지 않습니다.", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8))).pack(anchor="w", pady=(4, 8))
        note_text = tk.Text(
            note_content,
            height=5,
            wrap="word",
            bg=t["surface2"],
            fg=t["text"],
            insertbackground=t["text"],
            relief="flat",
            font=("Malgun Gothic", self._font(9)),
            padx=12,
            pady=10,
        )
        note_text.pack(fill="x")
        note_text.insert("1.0", self.term_notes.get(term["id"], ""))
        self._button(
            note_content,
            "메모 저장",
            lambda box=note_text, x=term: self.save_term_note(x, box.get("1.0", "end-1c")),
            kind="subtle",
            padx=14,
            pady=7,
        ).pack(anchor="e", pady=(8, 0))

        source_ids = term.get("sources", [])
        if source_ids:
            outer = self._card(inner, padx=22, pady=18)
            outer.pack(fill="x", pady=6)
            c = self._put_card_content(outer)
            tk.Label(c, text="참고 출처", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(anchor="w")
            imported_source = any(str(self.sources.get(source_id, {}).get("id", "")).startswith(("nlm_", "pubchem_")) for source_id in source_ids)
            source_note = ("공식 자료의 영어 원문·구조 속성을 보존한 수록 항목입니다. 한국어 번역이나 교과 해설로 검증된 내용과 구분해 표시합니다." if imported_source else "본문은 아래 자료를 대조해 새로 풀어쓴 설명이며, 원문을 그대로 복사하지 않았습니다.")
            tk.Label(c, text=source_note, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), wraplength=760, justify="left").pack(anchor="w", pady=(5, 10))
            for source_id in source_ids:
                source = self.sources.get(source_id)
                if not source:
                    continue
                row = tk.Frame(c, bg=t["surface2"])
                row.pack(fill="x", pady=3)
                tk.Label(row, text="•", bg=t["surface2"], fg=t["accent"], font=("Malgun Gothic", self._font(10), "bold")).pack(side="left", padx=(10, 4))
                tk.Button(row, text=(source.get("title") or source.get("name") or source_id), command=lambda u=source.get("url", ""): self.open_url(u), relief="flat", bd=0, bg=t["surface2"], fg=t["blue"], activebackground=t["surface2"], activeforeground=t["accent2"], font=("Malgun Gothic", self._font(9)), anchor="w", cursor="hand2").pack(side="left", fill="x", expand=True, padx=(0, 10), pady=7)

        scroll.to_top()
        self.status_var.set("{} · {}".format(term["name_ko"], term.get("category", "")))

    def _detail_section(self, master: tk.Misc, title: str, text: str, icon: str, formula: bool = False) -> None:
        t = self.theme
        outer = self._card(master, padx=22, pady=18)
        outer.pack(fill="x", pady=6)
        c = self._put_card_content(outer)
        head = tk.Frame(c, bg=t["surface"])
        head.pack(fill="x", pady=(0, 10))
        tk.Label(head, text=icon, bg=t["accent_soft"], fg=t["accent2"], font=("Segoe UI Symbol", self._font(12), "bold"), padx=8, pady=4).pack(side="left", padx=(0, 8))
        tk.Label(head, text=title, bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(side="left")
        if formula:
            box = tk.Frame(c, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
            box.pack(fill="x")
            tk.Label(box, text=text, bg=t["surface2"], fg=t["accent2"], font=("Consolas", self._font(14), "bold"), wraplength=760, justify="left", anchor="w").pack(fill="x", padx=18, pady=16)
        else:
            tk.Label(c, text=text, bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(10)), wraplength=790, justify="left", anchor="w").pack(fill="x")

    def open_related(self, name: str) -> None:
        term = self.term_by_name.get(name)
        if term:
            self.show_term(term)
        else:
            self.search_for(name)

    def _term_plain_text(self, term: dict) -> str:
        lines = [
            term.get("name_ko", ""),
            term.get("name_en", ""),
            "",
            "정의: " + term.get("summary", ""),
            "",
            "설명: " + term.get("detail", ""),
        ]
        for label, key in (("공식", "formula"), ("단위", "unit"), ("예시", "example"), ("주의", "caution")):
            value = term.get(key, "").strip()
            if value:
                lines.extend(["", "{}: {}".format(label, value)])
        related = term.get("related", [])
        if related:
            lines.extend(["", "관련 개념: " + ", ".join(related)])
        lines.extend(["", "Physics + Math Pocket {}".format(APP_VERSION)])
        return "\n".join(lines)

    def copy_term_text(self, term: dict) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(self._term_plain_text(term))
            self.update_idletasks()
            self.status_var.set("{} 내용을 클립보드에 복사했습니다.".format(term["name_ko"]))
        except Exception as exc:
            messagebox.showerror("복사 실패", str(exc), parent=self)

    def export_term_html(self, term: dict) -> None:
        default_name = "{}_PhysicsMathPocket.html".format(term.get("name_ko", "term"))
        path = filedialog.asksaveasfilename(
            parent=self,
            title="용어 문서 저장",
            defaultextension=".html",
            initialfile=default_name,
            filetypes=[("HTML 문서", "*.html"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        esc = html.escape
        sections = []
        for title, key in (("자세한 설명", "detail"), ("대표 공식", "formula"), ("단위와 기호", "unit"), ("예시", "example"), ("헷갈리기 쉬운 점", "caution")):
            value = term.get(key, "").strip()
            if value:
                cls = "formula" if key == "formula" else "section"
                sections.append('<section class="{}"><h2>{}</h2><p>{}</p></section>'.format(cls, esc(title), esc(value).replace("\n", "<br>")))
        related = term.get("related", [])
        if related:
            sections.append('<section class="section"><h2>관련 개념</h2><p>{}</p></section>'.format(esc(" · ".join(related))))
        source_names = []
        for source_id in term.get("sources", []):
            source = self.sources.get(source_id)
            if source:
                source_names.append(source.get("title") or source.get("name") or source_id)
        if source_names:
            sections.append('<section class="section"><h2>참고 자료</h2><p>{}</p></section>'.format(esc(" · ".join(source_names))))
        document = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} - Physics Pocket</title>
<style>
body{{margin:0;background:#f3f6f8;color:#172126;font-family:'Malgun Gothic','Noto Sans KR',sans-serif;line-height:1.75}}
main{{max-width:920px;margin:40px auto;padding:0 24px}}
header,section{{background:white;border:1px solid #dde5e9;border-radius:16px;padding:24px 28px;margin:14px 0}}
h1{{margin:0;font-size:2rem}} .en{{color:#65757d;font-style:italic}} .summary{{background:#dff7f0;border-radius:12px;padding:16px}}
h2{{font-size:1.15rem;margin:0 0 10px}} .formula p{{font-family:Consolas,monospace;font-size:1.15rem;color:#007a67;background:#f8fafb;padding:16px;border-radius:10px}}
footer{{color:#65757d;text-align:center;padding:20px}} @media print{{body{{background:white}} header,section{{box-shadow:none;break-inside:avoid}}}}
</style></head><body><main>
<header><h1>{title}</h1><div class="en">{english}</div><p class="summary">{summary}</p></header>
{sections}
<footer>Physics Pocket {version} · 이 문서는 앱에서 내보냈습니다.</footer>
</main></body></html>""".format(
            title=esc(term.get("name_ko", "")),
            english=esc(term.get("name_en", "")),
            summary=esc(term.get("summary", "")),
            sections="\n".join(sections),
            version=esc(APP_VERSION),
        )
        try:
            Path(path).write_text(document, encoding="utf-8")
            self.status_var.set("HTML 문서를 저장했습니다: {}".format(Path(path).name))
            if messagebox.askyesno("저장 완료", "문서를 저장했습니다. 지금 브라우저에서 열까요?", parent=self):
                webbrowser.open(Path(path).resolve().as_uri())
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc), parent=self)

    def open_web_reference_menu(self, term: dict) -> None:
        query = urllib.parse.quote_plus(term.get("name_ko", ""))
        query_physics = urllib.parse.quote_plus(term.get("name_ko", "") + " 물리")
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="네이버 지식백과에서 검색", command=lambda: self.open_url("https://terms.naver.com/search.naver?query=" + query))
        menu.add_command(label="네이버 국어사전에서 검색", command=lambda: self.open_url("https://ko.dict.naver.com/#/search?query=" + query))
        menu.add_command(label="네이버 통합검색에서 확인", command=lambda: self.open_url("https://search.naver.com/search.naver?query=" + query_physics))
        menu.add_separator()
        for source_id in term.get("sources", []):
            source = self.sources.get(source_id)
            if source and source.get("url"):
                label = source.get("organization") or source.get("name") or source_id
                menu.add_command(label="출처 열기 · " + label, command=lambda u=source["url"]: self.open_url(u))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def save_term_note(self, term: dict, note: str) -> None:
        note = note.strip()
        if note:
            self.term_notes[term["id"]] = note
        else:
            self.term_notes.pop(term["id"], None)
        self.note_store.save(self.term_notes)
        self.status_var.set("{} 학습 메모를 저장했습니다.".format(term["name_ko"]))

    def toggle_favorite(self, term: Optional[dict] = None) -> None:
        term = term or self.current_term
        if not term:
            return
        term_id = term["id"]
        if term_id in self.favorite_ids:
            self.favorite_ids.remove(term_id)
            self.status_var.set("즐겨찾기에서 제거: {}".format(term["name_ko"]))
        else:
            self.favorite_ids.add(term_id)
            self.status_var.set("즐겨찾기에 추가: {}".format(term["name_ko"]))
        self.favorite_store.save(self.favorite_ids)
        self._build_right_sidebar()
        if self.current_page == "term":
            self.show_term(term)
        elif self.current_page == "results":
            self.perform_search(add_history=False)

    # ---------- Constants ----------
    def show_constants(self) -> None:
        self.current_page = "constants"
        self.current_term = None
        self._refresh_nav_state()
        frame = self._clear_center()
        t = self.theme
        self._page_title(frame, "물리상수", "NIST CODATA와 SI 정의를 기준으로 정리한 기본 상수입니다.")
        scroll = ScrollableFrame(frame, t["bg"])
        scroll.pack(fill="both", expand=True)
        for item in self.constants:
            outer = self._card(scroll.inner, padx=20, pady=16)
            outer.pack(fill="x", pady=6)
            c = self._put_card_content(outer)
            head = tk.Frame(c, bg=t["surface"])
            head.pack(fill="x")
            tk.Label(head, text=item.get("name_ko", item.get("name", "상수")), bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(side="left")
            tk.Label(head, text=item.get("symbol", ""), bg=t["accent_soft"], fg=t["accent2"], font=("Cambria Math", self._font(12), "bold"), padx=10, pady=4).pack(side="right")
            tk.Label(c, text=item.get("name_en", ""), bg=t["surface"], fg=t["muted"], font=("Segoe UI", self._font(9), "italic")).pack(anchor="w", pady=(2, 9))
            value = "{} {}".format(item.get("value", ""), item.get("unit", "")).strip()
            tk.Label(c, text=value, bg=t["surface2"], fg=t["accent2"], font=("Consolas", self._font(12), "bold"), anchor="w", padx=14, pady=12).pack(fill="x")
            if item.get("note"):
                tk.Label(c, text=item["note"], bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), wraplength=760, justify="left").pack(anchor="w", pady=(8, 0))
        scroll.to_top()
        self.status_var.set("물리상수 {}개".format(len(self.constants)))

    # ---------- Converter ----------
    def show_converter(self) -> None:
        self.current_page = "converter"
        self.current_term = None
        self._refresh_nav_state()
        frame = self._clear_center()
        t = self.theme
        self._page_title(frame, "단위 변환", "값과 단위를 고르면 즉시 변환합니다. 계산은 완전히 오프라인에서 처리됩니다.")
        outer = self._card(frame, padx=28, pady=26)
        outer.pack(fill="x")
        c = self._put_card_content(outer)
        form = tk.Frame(c, bg=t["surface"])
        form.pack(fill="x")
        for col in range(4):
            form.grid_columnconfigure(col, weight=1)

        self.conv_family = tk.StringVar(value="길이")
        self.conv_value = tk.StringVar(value="1")
        self.conv_from = tk.StringVar(value="m")
        self.conv_to = tk.StringVar(value="km")
        self.conv_result = tk.StringVar(value="0.001 km")

        labels = ["종류", "값", "출발 단위", "도착 단위"]
        for i, label in enumerate(labels):
            tk.Label(form, text=label, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8), "bold")).grid(row=0, column=i, sticky="w", padx=(0 if i == 0 else 8, 0), pady=(0, 6))
        families = list(UNIT_FAMILIES.keys()) + ["온도"]
        family_combo = ttk.Combobox(form, textvariable=self.conv_family, values=families, state="readonly")
        family_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=4)
        value_entry = tk.Entry(form, textvariable=self.conv_value, bg=t["surface2"], fg=t["text"], insertbackground=t["text"], relief="flat", font=("Consolas", self._font(11)))
        value_entry.grid(row=1, column=1, sticky="ew", padx=8, ipady=10)
        self.from_combo = ttk.Combobox(form, textvariable=self.conv_from, state="readonly")
        self.from_combo.grid(row=1, column=2, sticky="ew", padx=8, ipady=4)
        self.to_combo = ttk.Combobox(form, textvariable=self.conv_to, state="readonly")
        self.to_combo.grid(row=1, column=3, sticky="ew", padx=(8, 0), ipady=4)
        family_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_unit_choices())
        value_entry.bind("<KeyRelease>", lambda _e: self.calculate_conversion(silent=True))
        self.from_combo.bind("<<ComboboxSelected>>", lambda _e: self.calculate_conversion(silent=True))
        self.to_combo.bind("<<ComboboxSelected>>", lambda _e: self.calculate_conversion(silent=True))
        self._update_unit_choices(initial=True)

        result_box = tk.Frame(c, bg=t["accent_soft"])
        result_box.pack(fill="x", pady=(24, 0))
        tk.Label(result_box, text="변환 결과", bg=t["accent_soft"], fg=t["accent2"], font=("Malgun Gothic", self._font(9), "bold")).pack(anchor="w", padx=18, pady=(14, 5))
        tk.Label(result_box, textvariable=self.conv_result, bg=t["accent_soft"], fg=t["text"], font=("Consolas", self._font(18), "bold"), anchor="w").pack(fill="x", padx=18, pady=(0, 16))
        buttons = tk.Frame(c, bg=t["surface"])
        buttons.pack(fill="x", pady=(14, 0))
        self._button(buttons, "변환", self.calculate_conversion, kind="accent", padx=22, pady=10).pack(side="left")
        self._button(buttons, "단위 서로 바꾸기", self.swap_units, kind="normal", padx=16, pady=10).pack(side="left", padx=8)

        guide = self._card(frame, padx=22, pady=18)
        guide.pack(fill="x", pady=14)
        gc = self._put_card_content(guide)
        tk.Label(gc, text="사용 예", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(12), "bold")).pack(anchor="w")
        tk.Label(gc, text="72 km/h → 20 m/s · 1 eV → 1.602176634 × 10^-19 J · 25 °C → 298.15 K", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(9)), wraplength=780, justify="left").pack(anchor="w", pady=(7, 0))
        self.status_var.set("단위 변환기")

    def _update_unit_choices(self, initial: bool = False) -> None:
        units = unit_names(self.conv_family.get())
        self.from_combo.configure(values=units)
        self.to_combo.configure(values=units)
        if not initial or self.conv_from.get() not in units:
            self.conv_from.set(units[0] if units else "")
        if not initial or self.conv_to.get() not in units:
            self.conv_to.set(units[1] if len(units) > 1 else (units[0] if units else ""))
        self.calculate_conversion(silent=True)

    def calculate_conversion(self, silent: bool = False) -> None:
        try:
            value = float(self.conv_value.get().replace(",", "").strip())
            result = convert_unit(value, self.conv_family.get(), self.conv_from.get(), self.conv_to.get())
            self.conv_result.set("{} {}".format(format_number(result), self.conv_to.get()))
            self.status_var.set("{} {} = {} {}".format(format_number(value), self.conv_from.get(), format_number(result), self.conv_to.get()))
        except Exception as exc:
            self.conv_result.set("값을 확인하세요")
            if not silent:
                messagebox.showerror("변환 오류", str(exc), parent=self)

    def swap_units(self) -> None:
        a, b = self.conv_from.get(), self.conv_to.get()
        self.conv_from.set(b)
        self.conv_to.set(a)
        self.calculate_conversion(silent=True)

    # ---------- Formula library ----------
    def show_formulas(self) -> None:
        self.current_page = "formulas"
        self.current_term = None
        self._refresh_nav_state()
        frame = self._clear_center()
        t = self.theme
        title_row = self._page_title(frame, "공식집", f"{len(self.formulas):,}개 공식·관계식 · 수학·물리·화학을 한곳에서 검색합니다.")
        self._button(title_row, "공식 계산기 열기", self.show_calculators, kind="accent", padx=14, pady=7).pack(side="right")

        toolbar = self._card(frame, padx=16, pady=13)
        toolbar.pack(fill="x", pady=(0, 10))
        c = self._put_card_content(toolbar)
        query_var = tk.StringVar()
        subject_var = tk.StringVar(value="전체")
        category_var = tk.StringVar(value="전체")
        count_var = tk.StringVar(value="")
        search_box = tk.Frame(c, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        search_box.pack(side="left", fill="x", expand=True)
        tk.Label(search_box, text="⌕", bg=t["surface2"], fg=t["accent"], font=("Segoe UI Symbol", 16, "bold")).pack(side="left", padx=(10, 4))
        ent = tk.Entry(search_box, textvariable=query_var, relief="flat", bd=0, bg=t["surface2"], fg=t["text"], insertbackground=t["text"], font=("Malgun Gothic", self._font(10)))
        ent.pack(side="left", fill="x", expand=True, ipady=8)
        subjects = ["전체"] + sorted({x.get("subject", "기타") for x in self.formulas})
        categories = ["전체"] + sorted({x.get("category", "기타") for x in self.formulas})
        ttk.Combobox(c, textvariable=subject_var, values=subjects, state="readonly", width=10).pack(side="left", padx=(10, 4))
        category_combo = ttk.Combobox(c, textvariable=category_var, values=categories, state="readonly", width=14)
        category_combo.pack(side="left", padx=4)
        tk.Label(c, textvariable=count_var, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), width=12, anchor="e").pack(side="right", padx=(8,0))

        holder = ScrollableFrame(frame, t["bg"])
        holder.pack(fill="both", expand=True)

        def render(*_args) -> None:
            for w in holder.inner.winfo_children():
                w.destroy()
            rows = search_formulas(self.formulas, query_var.get(), subject_var.get(), category_var.get())
            count_var.set(f"{len(rows):,}개")
            grid = tk.Frame(holder.inner, bg=t["bg"])
            grid.pack(fill="both", expand=True)
            for col in range(2):
                grid.grid_columnconfigure(col, weight=1, uniform="formula")
            shown = rows[:160]
            for i, row in enumerate(shown):
                outer = self._card(grid, padx=16, pady=14)
                outer.grid(row=i//2, column=i%2, sticky="nsew", padx=(0 if i%2==0 else 6, 6 if i%2==0 else 0), pady=6)
                x = self._put_card_content(outer)
                head = tk.Frame(x, bg=t["surface"]); head.pack(fill="x")
                tk.Label(head, text=row.get("title", "공식"), bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(11), "bold"), anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(head, text=f"{row.get('subject','')} · {row.get('category','')}", bg=t["surface3"], fg=t["muted"], font=("Malgun Gothic", self._font(7), "bold"), padx=7, pady=3).pack(side="right")
                tk.Label(x, text=row.get("formula", ""), bg=t["accent_soft"], fg=t["accent2"], font=("Cambria Math", self._font(12), "bold"), anchor="w", justify="left", padx=10, pady=9, wraplength=430).pack(fill="x", pady=(9,7))
                if row.get("note"):
                    tk.Label(x, text=row.get("note", ""), bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), anchor="w", justify="left", wraplength=430).pack(fill="x")
                actions = tk.Frame(x, bg=t["surface"]); actions.pack(fill="x", pady=(9,0))
                self._button(actions, "공식 복사", lambda f=row.get("formula",""): self._copy_to_clipboard(f), kind="ghost", padx=9, pady=5).pack(side="left")
                term = self.term_by_id.get(row.get("term_id", ""))
                if term:
                    self._button(actions, "개념 보기", lambda z=term:self.show_term(z), kind="subtle", padx=9, pady=5).pack(side="left", padx=4)
                source = self.sources.get(row.get("source", ""))
                if source:
                    tk.Label(actions, text=source.get("organization", source.get("name", "")), bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(7))).pack(side="right")
            if len(rows) > len(shown):
                tk.Label(holder.inner, text=f"성능을 위해 앞의 {len(shown)}개를 표시했습니다. 검색어나 분야 필터를 사용해 좁혀 보세요.", bg=t["bg"], fg=t["muted"], font=("Malgun Gothic", self._font(8))).pack(pady=14)
            if not rows:
                empty = self._card(holder.inner, padx=24, pady=26); empty.pack(fill="x", pady=8); ex=self._put_card_content(empty)
                tk.Label(ex, text="일치하는 공식이 없습니다.", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(12), "bold")).pack(anchor="w")
                tk.Label(ex, text="공식 기호, 개념 이름 또는 분야 이름으로 다시 검색해 보세요.", bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8))).pack(anchor="w", pady=(5,0))
            holder.to_top()
            self.status_var.set(f"공식집 · {len(rows):,}개 결과 / 전체 {len(self.formulas):,}개")

        query_var.trace_add("write", render)
        subject_var.trace_add("write", render)
        category_var.trace_add("write", render)
        render()
        ent.focus_set()

    # ---------- Formula calculators ----------
    def show_calculators(self) -> None:
        self.current_page = "calculators"
        self.current_term = None
        self._refresh_nav_state()
        frame = self._clear_center()
        t = self.theme
        title_row = self._page_title(frame, "공식 계산기", f"{len(CALCULATOR_SPECS)}개 계산기 · 역학·전자기·광학·현대물리·화학·수학을 빠르게 계산합니다.")
        self._button(title_row, "공식집 열기", self.show_formulas, kind="ghost", padx=12, pady=7).pack(side="right")

        chooser = self._card(frame, padx=16, pady=13)
        chooser.pack(fill="x", pady=(0,10))
        c = self._put_card_content(chooser)
        query_var = tk.StringVar()
        category_var = tk.StringVar(value="전체")
        count_var = tk.StringVar()
        search = tk.Entry(c, textvariable=query_var, bg=t["surface2"], fg=t["text"], insertbackground=t["text"], relief="flat", font=("Malgun Gothic", self._font(10)))
        search.pack(side="left", fill="x", expand=True, ipady=9, padx=(0,8))
        ttk.Combobox(c, textvariable=category_var, values=CALCULATOR_CATEGORIES, state="readonly", width=14).pack(side="left", padx=4)
        tk.Label(c, textvariable=count_var, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), width=10, anchor="e").pack(side="right")

        holder = ScrollableFrame(frame, t["bg"])
        holder.pack(fill="both", expand=True)

        def render(*_args) -> None:
            for w in holder.inner.winfo_children(): w.destroy()
            q=query_var.get().strip().casefold(); cat=category_var.get()
            specs=[]
            for spec in CALCULATOR_SPECS:
                title, category, formula, fields, calculator, note = spec
                if cat != "전체" and category != cat: continue
                hay=(title+" "+category+" "+formula+" "+note).casefold()
                if q and q not in hay: continue
                specs.append((title, formula, fields, calculator, note, category))
            count_var.set(f"{len(specs)}개")
            grid=tk.Frame(holder.inner,bg=t["bg"]); grid.pack(fill="both",expand=True)
            for col in range(2): grid.grid_columnconfigure(col,weight=1,uniform="calc")
            for index,(title,formula,fields,calculator,note,category) in enumerate(specs):
                card=self._formula_card(grid,title,formula,fields,calculator,note)
                card.grid(row=index//2,column=index%2,sticky="nsew",padx=(0 if index%2==0 else 7,7 if index%2==0 else 0),pady=7)
                inner=card.winfo_children()[0]
                tk.Label(inner,text=category,bg=t["surface3"],fg=t["muted"],font=("Malgun Gothic",self._font(7),"bold"),padx=6,pady=2).place(relx=0.98,rely=0.04,anchor="ne")
            if not specs:
                empty=self._card(holder.inner,padx=22,pady=24); empty.pack(fill="x",pady=8); x=self._put_card_content(empty)
                tk.Label(x,text="일치하는 계산기가 없습니다.",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w")
            holder.to_top(); self.status_var.set(f"공식 계산기 {len(specs)}개 / 전체 {len(CALCULATOR_SPECS)}개")

        query_var.trace_add("write",render); category_var.trace_add("write",render); render(); search.focus_set()

    def _formula_card(self, master: tk.Misc, title: str, formula: str, fields: List[tuple], calculator: Callable, note: str) -> tk.Frame:
        t = self.theme
        outer = self._card(master, padx=20, pady=18)
        c = self._put_card_content(outer)
        tk.Label(c, text=title, bg=t["surface"], fg=t["text"], font=("Malgun Gothic", self._font(13), "bold")).pack(anchor="w")
        tk.Label(c, text=formula, bg=t["accent_soft"], fg=t["accent2"], font=("Cambria Math", self._font(13), "bold"), padx=12, pady=8).pack(fill="x", pady=(8, 12))

        variables = []
        for label, unit, default in fields:
            row = tk.Frame(c, bg=t["surface"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(9), "bold"), width=15, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            entry = tk.Entry(row, textvariable=var, bg=t["surface2"], fg=t["text"], insertbackground=t["text"], relief="flat", font=("Consolas", self._font(10)))
            entry.pack(side="left", fill="x", expand=True, ipady=7)
            tk.Label(row, text=unit, bg=t["surface"], fg=t["muted"], font=("Consolas", self._font(9)), width=8, anchor="e").pack(side="right", padx=(8, 0))
            variables.append(var)

        result_var = tk.StringVar(value="계산 전")
        result_box = tk.Frame(c, bg=t["surface2"], highlightthickness=1, highlightbackground=t["line"])
        result_box.pack(fill="x", pady=(12, 8))
        tk.Label(result_box, textvariable=result_var, bg=t["surface2"], fg=t["accent2"], font=("Consolas", self._font(12), "bold"), anchor="w", padx=12, pady=10).pack(fill="x")

        def calculate() -> None:
            try:
                values = [float(v.get().replace(",", "").strip()) for v in variables]
                if "구심력" in title and values[-1] == 0:
                    raise ValueError("반지름은 0일 수 없습니다.")
                result, unit = calculator(values)
                if not math.isfinite(result):
                    raise ValueError("유한한 값을 입력하세요.")
                result_var.set("{} {}".format(format_number(result), unit))
                self.status_var.set("{} 계산 완료".format(title))
            except Exception as exc:
                result_var.set("입력값을 확인하세요")
                messagebox.showerror("계산 오류", str(exc), parent=self)

        for var in variables:
            var.trace_add("write", lambda *_args: None)
        self._button(c, "계산", calculate, kind="accent", padx=18, pady=8).pack(anchor="w", pady=(2, 8))
        tk.Label(c, text=note, bg=t["surface"], fg=t["muted"], font=("Malgun Gothic", self._font(8)), wraplength=360, justify="left", anchor="w").pack(fill="x")
        return outer

    # ---------- Help / user guide ----------
    def show_help(self) -> None:
        self.current_page = "help"
        self.current_term = None
        self._refresh_nav_state()
        frame = self._clear_center()
        t = self.theme
        row = self._page_title(frame, "도움말 · 사용 설명서", "F1로 언제든 열 수 있습니다. 검색부터 시뮬레이션·공식·내 데이터까지 앱 안에서 바로 안내합니다.")
        self._button(row, "README 열기", self.open_user_guide_file, kind="ghost", padx=12, pady=7).pack(side="right")

        scroll = ScrollableFrame(frame, t["bg"]); scroll.pack(fill="both", expand=True); inner=scroll.inner
        hero=self._card(inner,padx=24,pady=22); hero.pack(fill="x",pady=(0,12)); c=self._put_card_content(hero)
        tk.Label(c,text="처음이라면 이 4개만 기억하세요",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(15),"bold")).pack(anchor="w")
        tk.Label(c,text="① 위 검색창에서 개념 검색  →  ② 결과의 표제어 열기  →  ③ 개념 아래 시뮬레이터 조작  →  ④ 공식집·계산기로 값 확인",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9)),wraplength=850,justify="left").pack(anchor="w",pady=(7,12))
        quick=tk.Frame(c,bg=t["surface"]); quick.pack(anchor="w")
        for label,cmd in [("통합사전",lambda:self.navigate("dictionary")),("공식집",self.show_formulas),("시뮬레이터",self.show_simulations),("계산기",self.show_calculators)]:
            self._button(quick,label,cmd,kind="accent" if label=="통합사전" else "normal",padx=12,pady=7).pack(side="left",padx=(0,6))

        def guide(title: str, body: str, bullets: Optional[List[str]] = None) -> None:
            outer=self._card(inner,padx=22,pady=18); outer.pack(fill="x",pady=6); x=self._put_card_content(outer)
            tk.Label(x,text=title,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w")
            if body:
                tk.Label(x,text=body,bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9)),wraplength=850,justify="left",anchor="w").pack(fill="x",pady=(6,4))
            for item in bullets or []:
                tk.Label(x,text="• "+item,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(8)),wraplength=840,justify="left",anchor="w").pack(fill="x",pady=2)

        guide("1. 검색과 통합사전", "검색창은 한국어·영어·별칭·설명·공식·관련어와 한글 초성을 함께 찾습니다.", [
            "Ctrl+L 또는 Ctrl+K: 어디서든 검색창으로 이동",
            "왼쪽에서 과목/분야/수준을 좁힐 수 있고, 검색 결과 탭에서 공식·시뮬레이션·즐겨찾기만 볼 수 있습니다.",
            "개념 페이지의 관련 용어를 누르면 사전처럼 계속 이어서 탐색할 수 있습니다.",
        ])
        guide("2. 개념 시뮬레이터", "50개 계산 모델의 5,000개 조건 실험과 몸 전체 감염·면역 실험실을 제공합니다. 기존 학습 도구 105개도 사용할 수 있습니다.", [
            "슬라이더를 움직이면 그래프/그림이 즉시 갱신됩니다.",
            "재생 버튼이 있는 시뮬레이터는 시간 변화를 볼 수 있습니다.",
            "설정에서 시뮬레이션 표시, 애니메이션, 30/60 FPS를 바꿀 수 있습니다.",
            "시뮬레이션은 개념 이해용 모델이며 실제 실험의 모든 조건을 대신하지 않습니다.",
        ])
        guide("3. 공식집과 계산기", f"공식집에는 현재 {len(self.formulas):,}개의 공식·관계식 카드가 있고, 계산기는 {len(CALCULATOR_SPECS)}개입니다.", [
            "공식집에서 개념명·기호·분야로 검색하고 공식 복사 버튼을 사용할 수 있습니다.",
            "사전 표제어에서 온 공식은 ‘개념 보기’로 원래 설명으로 이동할 수 있습니다.",
            "계산기는 입력 단위가 카드에 표시됩니다. 단위가 다르면 먼저 ‘단위 변환’을 사용하세요.",
            "공식의 적용 조건과 부호 규약은 개념 설명/주의 문구를 함께 확인하세요.",
        ])
        guide("4. 내 데이터", "기본 지식과 별도로 SQLite 사용자 DB에 나만의 개념을 추가할 수 있습니다.", [
            "+ 새 개념: 표제어·설명·공식·관련어·연결 시뮬레이터를 직접 저장",
            "JSON/CSV 가져오기·내보내기로 확장팩과 백업을 관리",
            f"저장 한도는 현재 {self.db.limit_gb}GB이며, 빈 공간을 미리 차지하지 않고 실제 데이터만큼만 커집니다.",
            "사용자 DB는 기본 데이터와 분리되어 앱 업데이트 시에도 유지되도록 설계했습니다.",
        ])
        guide("5. 설정", "오른쪽 위 ‘⚙ 설정’에서 장시간 읽기와 시뮬레이션 환경을 조정할 수 있습니다.", [
            "Windows 시스템 테마 / 밝게 / 어둡게",
            "글자 크기, 검색 결과 개수, 시뮬레이터 표시와 FPS",
            "사용자 DB 소프트 한도 1~5GB",
            "외부 링크를 열기 전에 확인창을 표시할지 선택",
            "업데이트 자동 확인, Stable/Beta 채널, GitHub Releases 또는 HTTPS manifest 소스를 설정",
        ])
        guide("6. 키보드 단축키", "마우스 없이도 주요 작업을 빠르게 할 수 있습니다.", [
            "F1  도움말", "Ctrl+L / Ctrl+K  검색창", "Alt+←  이전 화면으로 뒤로가기", "Ctrl+D  현재 개념 즐겨찾기", "Esc  자동완성 닫기 또는 이전 화면으로 돌아가기",
        ])
        guide("7. 설치·문제 해결", "소스 실행과 설치형 빌드는 서로 다른 단계입니다.", [
            "소스 실행: RUN_APP.cmd",
            "Windows 설치형 빌드: BUILD_SETUP_GUI.pyw → 앱 EXE 빌드 → Setup.exe 빌드",
            "Setup.exe 생성에는 PyInstaller와 Inno Setup 6/7이 사용됩니다.",
            "3.1.2부터 같은 AppId를 유지하므로 기존 설치 위치에 새 Setup.exe를 실행하면 업그레이드로 적용됩니다.",
            "앱의 ‘업데이트’ 화면에서 새 버전을 확인하고, SHA-256이 제공된 릴리스는 다운로드 후 설치까지 진행할 수 있습니다.",
            "Windows가 출처를 알 수 없는 실행 파일을 경고하면 보안 기능을 무작정 끄지 말고, 직접 빌드한 파일인지와 출처를 먼저 확인하세요.",
            "오류 기록은 사용자 데이터 폴더의 physics_math_pocket.log에서 확인할 수 있습니다.",
        ])
        guide("8. 자료와 정확도", "교과 범위와 공식 검토에는 교육부, OpenStax, BIPM, NIST/DLMF, NASA, CERN 등 공개·공식 자료를 참고했습니다.", [
            "외부 사전의 문장이나 UI를 그대로 복사하지 않고, 앱 설명과 화면은 독자적으로 작성·구성했습니다.",
            "간결한 데이터 항목은 학습 출발점입니다. 중요한 계산이나 과제에는 교과서·공식 자료와 함께 확인하세요.",
        ])
        scroll.to_top(); self.status_var.set("도움말 · 사용 설명서")

    def open_user_guide_file(self) -> None:
        candidates=[resource_path("README_KO.md"), Path(__file__).resolve().parent / "README_KO.md"]
        for path in candidates:
            if path.exists():
                try:
                    if os.name=="nt": os.startfile(str(path))
                    elif sys.platform=="darwin": subprocess.Popen(["open",str(path)])
                    else: subprocess.Popen(["xdg-open",str(path)])
                    return
                except Exception as exc:
                    messagebox.showerror("설명서 열기 실패",str(exc),parent=self); return
        messagebox.showinfo("설명서", "README_KO.md를 찾지 못했습니다. 앱 안의 도움말은 그대로 사용할 수 있습니다.", parent=self)

    # ---------- Updates / About ----------
    def _refresh_update_indicator(self) -> None:
        button = getattr(self, "update_button", None)
        if button is None:
            return
        text = "↻ 업데이트"
        if self.update_check_running:
            text = "↻ 확인 중…"
        elif self.update_check_result and self.update_check_result.status == "update_available" and self.update_check_result.release:
            rel = self.update_check_result.release
            text = "● {}{}".format(rel.version, " Beta" if rel.is_beta else "")
        elif self.update_check_result and self.update_check_result.status == "current":
            text = "✓ 최신"
        try:
            button.configure(text=text)
        except tk.TclError:
            pass

    def check_updates_background(self, interactive: bool = False) -> None:
        if self.update_check_running:
            return
        self.update_check_running = True
        self._refresh_update_indicator()
        channel = self.settings.get("update_channel", "stable")
        repository = self.settings.get("update_repository") or DEFAULT_SETTINGS["update_repository"]
        manifest_url = self.settings.get("update_manifest_url", "")
        local_dir = self.settings.get("update_local_dir", "")
        source_mode = self.settings.get("update_source_mode") or DEFAULT_SETTINGS["update_source_mode"]

        def worker() -> None:
            result = check_for_updates(
                APP_VERSION, APP_BUILD, channel=channel, repository=repository,
                manifest_url=manifest_url, local_dir=local_dir, source_mode=source_mode
            )
            self.after(0, lambda: self._finish_update_check(result, interactive))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_update_check(self, result: UpdateCheckResult, interactive: bool) -> None:
        self.update_check_running = False
        self.update_check_result = result
        self.latest_release = result.release
        latest_payload = result.release.as_dict() if result.release else None
        self.install_meta.mark_check(latest_payload)
        self._refresh_update_indicator()
        if self.current_page == "updates":
            self.show_updates()
        if result.status == "update_available" and result.release:
            rel = result.release
            beta_note = "\n\n⚠ 베타 버전은 기능이 완성되지 않았거나 오류가 있을 수 있습니다." if rel.is_beta else ""
            prompt = "새 업데이트가 있습니다.\n\n{}\n{}{}\n\n업데이트하시겠습니까?".format(rel.name, rel.display_version, beta_note)
            if messagebox.askyesno("업데이트 사용 가능", prompt, parent=self):
                self.install_release(rel)
        elif interactive:
            if result.status == "current":
                messagebox.showinfo("업데이트", "현재 최신 버전을 사용 중입니다.\n\n{} · Build {}".format(APP_VERSION, APP_BUILD), parent=self)
            elif result.status == "unconfigured":
                local_folder = self.settings.get("update_local_dir", "") or str(default_local_update_dir())
                messagebox.showinfo(
                    "업데이트 소스 미설정",
                    "새 업데이트를 찾지 못했습니다.\n\n"
                    "개인 테스트 단계에서는 아래 로컬 폴더에 다음 버전 Setup.exe를 넣으면 GitHub 없이도 업데이트 탐지 기능을 시험할 수 있습니다.\n\n"
                    f"{local_folder}\n\n"
                    "설정 → 업데이트에서 로컬/GitHub/manifest 소스를 선택할 수도 있습니다.",
                    parent=self,
                )
            else:
                messagebox.showwarning("업데이트 확인", result.message, parent=self)

    def choose_rollback(self) -> None:
        repository = str(self.settings.get("update_repository", "") or "").strip()
        if not repository:
            messagebox.showwarning("롤백", "GitHub 업데이트 저장소가 설정되지 않았습니다.", parent=self)
            return
        self.status_var.set("롤백 가능한 릴리스 목록을 불러오는 중…")
        def worker() -> None:
            try:
                # Rollback uses the signed payload ZIP so stale files, assets and
                # layout resources are removed by the transactional updater.
                releases = list_github_releases(repository, str(self.settings.get("update_channel", "beta")), asset_contains="PhysicsMathPocket_Update_")
                self.after(0, lambda: self._show_rollback_choices(releases))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("롤백 목록 오류", str(exc), parent=self))
        threading.Thread(target=worker, daemon=True).start()

    def _show_rollback_choices(self, releases: List[ReleaseInfo]) -> None:
        if not releases:
            messagebox.showinfo("롤백", "선택할 수 있는 공개 릴리스를 찾지 못했습니다.", parent=self); return
        dialog = tk.Toplevel(self); dialog.title("버전 롤백"); dialog.transient(self); dialog.grab_set(); dialog.geometry("620x430")
        t = self.theme
        tk.Label(dialog, text="돌아갈 버전을 선택하세요", bg=t["surface"], fg=t["text"], font=("Malgun Gothic", 14, "bold")).pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(dialog, text="롤백하면 최근 검색 기록과 업데이트 기록이 삭제되고 선택한 버전의 파일만 남습니다.", bg=t["surface"], fg=t["danger"], wraplength=560, justify="left").pack(fill="x", padx=20, pady=(0, 10))
        dialog.configure(bg=t["surface"])
        box = tk.Listbox(dialog, height=12, font=("Segoe UI", 10), bg=t["surface2"], fg=t["text"], relief="flat")
        box.pack(fill="both", expand=True, padx=20, pady=8)
        for rel in releases: box.insert("end", f"{rel.display_version} · {rel.name}")
        box.selection_set(0)
        def apply_choice() -> None:
            index = box.curselection()
            if not index: return
            rel = releases[index[0]]
            if not messagebox.askyesno("롤백 확인", f"{rel.display_version}(으)로 롤백할까요?\n\n검색 기록과 업데이트 기록이 모두 삭제됩니다.", parent=dialog): return
            dialog.destroy(); self.install_release(rel, rollback=True)
        self._button(dialog, "선택한 버전으로 롤백", apply_choice, kind="accent", padx=14, pady=8).pack(side="right", padx=20, pady=14)
        self._button(dialog, "취소", dialog.destroy, kind="ghost", padx=14, pady=8).pack(side="right", pady=14)

    def install_release(self, release: ReleaseInfo, rollback: bool = False) -> None:
        if not release.download_url:
            if release.page_url:
                self.open_url(release.page_url)
            else:
                messagebox.showinfo("다운로드 없음", "이 릴리스에는 업데이트 파일 URL이 없습니다.", parent=self)
            return
        if not release.sha256:
            if release.page_url:
                messagebox.showwarning("자동 설치 보류", "릴리스에 SHA-256 검증값이 없어 앱이 자동 설치하지 않습니다.\n릴리스 페이지를 열어 직접 확인해 주세요.", parent=self)
                self.open_url(release.page_url)
            else:
                messagebox.showwarning("자동 설치 보류", "SHA-256 검증값이 없어 자동 설치하지 않습니다.", parent=self)
            return
        self.status_var.set("업데이트 다운로드 중…")

        def worker() -> None:
            try:
                path = download_installer(release)
                self.after(0, lambda: self._launch_downloaded_update(path, release, rollback))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("업데이트 실패", str(exc), parent=self))

        threading.Thread(target=worker, daemon=True).start()

    def _launch_downloaded_update(self, path: Path, release: ReleaseInfo, rollback: bool = False) -> None:
        seamless = path.suffix.lower() == ".zip" or release.asset_kind == "package"
        method = "앱을 다시 설치하지 않고 현재 프로그램 파일만 교체합니다." if seamless else "설치 프로그램 방식으로 업데이트합니다."
        if not messagebox.askyesno(
            "롤백 적용" if rollback else "업데이트 적용",
            "{}\n\nSHA-256 검증을 통과했습니다.\n{}\n\n{}".format(release.display_version, method, "검색 기록과 업데이트 기록을 삭제하고 진행합니다. 계속할까요?" if rollback else "사용자 데이터와 설정은 유지됩니다. 계속할까요?"),
            parent=self,
        ):
            return
        try:
            if not rollback:
                self.install_meta.record_update_started(release.as_dict(), kind="update")
                self.install_meta.data["pending_update"]["notes"] = release.notes or "릴리스 노트가 제공되지 않았습니다."
                self.install_meta._write()
            if seamless:
                launch_seamless_update(path, restart=True, rollback=rollback)
            else:
                launch_installer(path, silent=True)
            self.status_var.set("업데이트 준비 완료 · 앱을 다시 시작합니다…")
            self.after(500, self.on_close)
        except Exception as exc:
            messagebox.showerror("업데이트 실행 실패", str(exc), parent=self)

    def install_local_update(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Physics + Math Pocket 업데이트 설치 파일 선택", filetypes=[("Windows 설치 파일", "*.exe"), ("모든 파일", "*.*")])
        if not path:
            return
        if not messagebox.askyesno("로컬 업데이트", "선택한 설치 파일을 실행해 기존 Physics + Math Pocket을 업데이트할까요?\n\n{}\n\n직접 받은 신뢰할 수 있는 파일인지 확인하세요.".format(path), parent=self):
            return
        try:
            launch_installer(Path(path), silent=False)
            self.after(250, self.on_close)
        except Exception as exc:
            messagebox.showerror("설치 실행 실패", str(exc), parent=self)

    def _configured_local_update_dir(self) -> Path:
        value = str(self.settings.get("update_local_dir", "") or "").strip()
        path = Path(value).expanduser() if value else default_local_update_dir()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def open_local_update_folder(self) -> None:
        path = self._configured_local_update_dir()
        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("폴더 열기 실패", str(exc), parent=self)

    def choose_local_update_folder(self) -> None:
        initial = str(self._configured_local_update_dir())
        chosen = filedialog.askdirectory(parent=self, title="로컬 업데이트 폴더 선택", initialdir=initial)
        if not chosen:
            return
        self.settings["update_local_dir"] = chosen
        self.settings_store.save(self.settings)
        self.status_var.set("로컬 업데이트 폴더를 저장했습니다.")
        if self.current_page == "updates":
            self.show_updates()

    def test_update_prompt(self) -> None:
        # UI/버전 비교 로직을 실제 설치 없이 확인하는 안전한 진단용 가상 릴리스입니다.
        parts = APP_VERSION.split(".")
        next_version = ".".join(parts[:-1] + [str(int(parts[-1]) + 1)])
        fake = ReleaseInfo(next_version, APP_BUILD + 101, "beta", next_version + " Beta 기능 확인용 가상 빌드", notes="실제 설치 파일을 실행하지 않는 알림 테스트입니다.")
        newer = release_is_newer(fake, APP_VERSION, APP_BUILD)
        if not newer:
            messagebox.showerror("업데이트 테스트", "버전 비교 테스트가 실패했습니다.", parent=self)
            return
        prompt = (
            "[테스트 모드] 새 업데이트가 있습니다.\n\n"
            f"{fake.name}\n{fake.display_version}\n\n"
            "⚠ 베타 버전은 기능이 완성되지 않았거나 오류가 있을 수 있습니다.\n\n"
            "업데이트하시겠습니까?"
        )
        accepted = messagebox.askyesno("업데이트 사용 가능 · 테스트", prompt, parent=self)
        messagebox.showinfo(
            "업데이트 테스트 완료",
            ("[업데이트]를 선택했습니다." if accepted else "[나중에]에 해당하는 선택을 했습니다.")
            + "\n\n테스트 모드이므로 Setup.exe는 실행하지 않았습니다. 알림·버전/빌드 표시·선택 흐름은 정상입니다.",
            parent=self,
        )

    def run_update_diagnostics(self) -> None:
        folder = self._configured_local_update_dir()
        checks = []
        try:
            folder.mkdir(parents=True, exist_ok=True)
            checks.append(("로컬 UpdateInbox 접근", folder.exists() and folder.is_dir(), str(folder)))
        except Exception as exc:
            checks.append(("로컬 UpdateInbox 접근", False, str(exc)))
        parts = APP_VERSION.split(".")
        next_version = ".".join(parts[:-1] + [str(int(parts[-1]) + 1)])
        fake_stable = ReleaseInfo(next_version, APP_BUILD + 100, "stable", "진단")
        fake_beta = ReleaseInfo(next_version, APP_BUILD + 101, "beta", "진단")
        checks.append(("Stable 버전 비교", release_is_newer(fake_stable, APP_VERSION, APP_BUILD), fake_stable.display_version))
        checks.append(("Beta 버전 비교", release_is_newer(fake_beta, APP_VERSION, APP_BUILD), fake_beta.display_version))
        mode = str(self.settings.get("update_source_mode", "auto"))
        checks.append(("업데이트 소스 모드", mode in {"auto", "local", "github", "manifest"}, mode))
        lines = ["업데이트 기능 진단"]
        for name, ok, detail in checks:
            lines.append(("✓ " if ok else "✗ ") + f"{name}: {detail}")
        lines.append("\n실제 설치 테스트는 다음 버전의 Setup.exe를 로컬 업데이트 폴더에 넣은 뒤 [업데이트 확인]을 사용하세요.")
        messagebox.showinfo("업데이트 기능 진단", "\n".join(lines), parent=self)

    def show_updates(self) -> None:
        self.current_page="updates"; self.current_term=None; self._refresh_nav_state(); frame=self._clear_center(); t=self.theme
        header=self._page_title(frame,"업데이트 센터","새 빌드를 확인하고, 사용자 데이터는 그대로 둔 채 프로그램 파일만 안전하게 교체합니다.")
        self._button(header,"지금 확인",lambda:self.check_updates_background(interactive=True),kind="accent",padx=16,pady=8).pack(side="right")
        scroll=ScrollableFrame(frame,t["bg"]); scroll.pack(fill="both",expand=True); root=scroll.inner

        # Hero update card
        outer=self._card(root,padx=24,pady=22); outer.pack(fill="x",pady=(0,12)); c=self._put_card_content(outer)
        top=tk.Frame(c,bg=t["surface"]); top.pack(fill="x")
        icon_box=tk.Frame(top,bg=t["accent_soft"],width=86,height=86); icon_box.pack(side="left",padx=(0,18)); icon_box.pack_propagate(False)
        tk.Label(icon_box,text="↓",bg=t["accent_soft"],fg=t["accent2"],font=("Segoe UI Symbol",28,"bold")).pack(expand=True)
        meta=tk.Frame(top,bg=t["surface"]); meta.pack(side="left",fill="both",expand=True)
        if self.update_check_running:
            status_title="업데이트를 확인하는 중…"; status_sub="GitHub Releases / 로컬 업데이트 소스를 확인하고 있습니다."
        elif self.update_check_result and self.update_check_result.status=="update_available" and self.update_check_result.release:
            rel=self.update_check_result.release; status_title="새 업데이트를 사용할 수 있습니다"; status_sub=f"{rel.display_version} · {rel.name}"
        elif self.update_check_result and self.update_check_result.status=="current":
            status_title="최신 상태입니다"; status_sub=f"{APP_VERSION} · Build {APP_BUILD}"
        else:
            status_title="업데이트 상태를 확인하세요"; status_sub=f"현재 {APP_VERSION} · Build {APP_BUILD}"
        tk.Label(meta,text=status_title,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(16),"bold"),anchor="w").pack(fill="x")
        tk.Label(meta,text=status_sub,bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9)),anchor="w").pack(fill="x",pady=(5,10))
        progress=ttk.Progressbar(meta,style="Update.Horizontal.TProgressbar",mode="indeterminate" if self.update_check_running else "determinate",maximum=100,value=100 if self.update_check_result and self.update_check_result.status=="current" else 0)
        progress.pack(fill="x",pady=(0,8))
        if self.update_check_running: progress.start(12)
        tk.Label(meta,text="무중단 패키지 업데이트 · SHA-256 검증 · 사용자 DB/설정 유지",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(8)),anchor="w").pack(fill="x")
        actions=tk.Frame(top,bg=t["surface"]); actions.pack(side="right",padx=(18,0))
        if self.update_check_result and self.update_check_result.status=="update_available" and self.update_check_result.release:
            self._button(actions,"다운로드 및 업데이트",lambda r=self.update_check_result.release:self.install_release(r),kind="accent",padx=15,pady=9).pack()
        else:
            self._button(actions,"업데이트 확인",lambda:self.check_updates_background(interactive=True),kind="accent",padx=15,pady=9).pack()

        cols=tk.Frame(root,bg=t["bg"]); cols.pack(fill="x",pady=(0,12)); cols.grid_columnconfigure(0,weight=1); cols.grid_columnconfigure(1,weight=1)
        left=self._card(cols,padx=20,pady=18); left.grid(row=0,column=0,sticky="nsew",padx=(0,7)); lc=self._put_card_content(left)
        tk.Label(lc,text="현재 설치",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w",pady=(0,10))
        rows=[("버전",f"{APP_VERSION}"),("빌드",str(APP_BUILD)),("채널",str(self.settings.get('update_channel','stable'))),("업데이트 횟수",str(self.install_meta.data.get('update_count',0))),("마지막 업데이트",self.install_meta.format_timestamp(self.install_meta.data.get('last_updated_at')))]
        for key,value in rows:
            row=tk.Frame(lc,bg=t["surface2"]); row.pack(fill="x",pady=2); tk.Label(row,text=key,bg=t["surface2"],fg=t["muted"],font=("Malgun Gothic",self._font(8)),padx=10,pady=7).pack(side="left"); tk.Label(row,text=value,bg=t["surface2"],fg=t["text"],font=("Malgun Gothic",self._font(8),"bold"),padx=10).pack(side="right")

        right=self._card(cols,padx=20,pady=18); right.grid(row=0,column=1,sticky="nsew",padx=(7,0)); rc=self._put_card_content(right)
        tk.Label(rc,text="업데이트 설정",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w",pady=(0,10))
        settings_rows=[("업데이트 소스",str(self.settings.get('update_source_mode','auto'))),("저장소",str(self.settings.get('update_repository','') or '미설정')),("자동 확인","켜짐" if self.settings.get('check_updates_on_startup',True) else '꺼짐'),("로컬 폴더",str(self._configured_local_update_dir()))]
        for key,value in settings_rows:
            row=tk.Frame(rc,bg=t["surface2"]); row.pack(fill="x",pady=2); tk.Label(row,text=key,bg=t["surface2"],fg=t["muted"],font=("Malgun Gothic",self._font(8)),padx=10,pady=7).pack(side="left"); tk.Label(row,text=value,bg=t["surface2"],fg=t["text"],font=("Malgun Gothic",self._font(8),"bold"),padx=10,wraplength=330,justify="right").pack(side="right")
        btns=tk.Frame(rc,bg=t["surface"]); btns.pack(anchor="w",pady=(10,0)); self._button(btns,"설정 열기",self.show_settings,kind="normal",padx=12,pady=7).pack(side="left",padx=(0,5)); self._button(btns,"진단",self.run_update_diagnostics,kind="ghost",padx=12,pady=7).pack(side="left")

        outer=self._card(root,padx=20,pady=18); outer.pack(fill="x",pady=(0,12)); c=self._put_card_content(outer)
        tk.Label(c,text="업데이트 기록",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w")
        history = list(reversed(self.install_meta.history()))
        if history:
            for item in history[:12]:
                title = f"{item.get('to_version','?')} · Build {item.get('to_build','?')} · {item.get('kind','update')}"
                detail = f"{self.install_meta.format_timestamp(item.get('timestamp'))} · {item.get('from_version','?')} → {item.get('to_version','?')}\n{item.get('notes') or '추가/수정 내용이 기록되지 않았습니다.'}"
                tk.Label(c,text=title,bg=t["surface2"],fg=t["accent2"],font=("Malgun Gothic",self._font(9),"bold"),anchor="w",justify="left").pack(fill="x",pady=(6,0),ipadx=10,ipady=5)
                tk.Label(c,text=detail,bg=t["surface2"],fg=t["muted"],font=("Malgun Gothic",self._font(8)),wraplength=900,justify="left",anchor="w").pack(fill="x",ipadx=10,ipady=5)
        else:
            tk.Label(c,text="아직 설치된 업데이트 기록이 없습니다.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9))).pack(anchor="w",pady=(8,0))
        self._button(c,"버전 롤백…",self.choose_rollback,kind="ghost",padx=12,pady=7).pack(anchor="w",pady=(12,0))

        outer=self._card(root,padx=20,pady=18); outer.pack(fill="x",pady=(0,12)); c=self._put_card_content(outer)
        tk.Label(c,text="새로운 기능 / 릴리스 노트",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w")
        if self.update_check_result and self.update_check_result.release:
            rel=self.update_check_result.release; notes=(rel.notes or "릴리스 노트가 없습니다.")[:1400]; subtitle=f"{rel.display_version} · {rel.name}"
        elif self.update_check_result:
            notes=self.update_check_result.message; subtitle="최근 확인 결과"
        else:
            notes="아직 업데이트를 확인하지 않았습니다. [지금 확인]을 누르면 GitHub Releases, manifest 또는 로컬 UpdateInbox를 확인합니다."; subtitle="확인 전"
        tk.Label(c,text=subtitle,bg=t["surface"],fg=t["accent2"],font=("Malgun Gothic",self._font(9),"bold"),anchor="w").pack(fill="x",pady=(6,4))
        tk.Label(c,text=notes,bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9)),wraplength=900,justify="left",anchor="w").pack(fill="x")

        outer=self._card(root,padx=20,pady=18); outer.pack(fill="x",pady=(0,12)); c=self._put_card_content(outer)
        tk.Label(c,text="고급 / 테스트",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(12),"bold")).pack(anchor="w",pady=(0,10))
        bar=tk.Frame(c,bg=t["surface"]); bar.pack(anchor="w")
        self._button(bar,"업데이트 기능 테스트",self.test_update_prompt,kind="normal",padx=12,pady=7).pack(side="left",padx=(0,5)); self._button(bar,"로컬 업데이트 폴더",self.open_local_update_folder,kind="normal",padx=12,pady=7).pack(side="left",padx=5); self._button(bar,"Setup.exe 직접 선택",self.install_local_update,kind="ghost",padx=12,pady=7).pack(side="left",padx=5)
        scroll.to_top(); self.status_var.set(f"업데이트 센터 · {APP_VERSION} · Build {APP_BUILD}")

    def show_about(self) -> None:
        self.current_page="about"; self.current_term=None; self._refresh_nav_state(); frame=self._clear_center(); t=self.theme
        self._page_title(frame,"앱 정보","버전·빌드·설치 기록·저작권·자료 출처를 확인합니다.")
        scroll=ScrollableFrame(frame,t["bg"]); scroll.pack(fill="both",expand=True)
        latest = self.install_meta.latest_known() or {}
        latest_text = "{} · Build {}".format(latest.get("version", "확인 전"), latest.get("build", "-")) if latest else "확인 전"
        info_rows = [
            ("제품", "Physics + Math Pocket"),
            ("현재 버전", "{} {}".format(APP_VERSION, "Beta" if APP_CHANNEL == "beta" else "Stable")),
            ("현재 빌드 번호", str(APP_BUILD)),
            ("최초 설치일", self.install_meta.format_timestamp(self.install_meta.data.get("first_installed_at"))),
            ("최신 업데이트 설치일", self.install_meta.format_timestamp(self.install_meta.data.get("last_updated_at"))),
            ("최초 설치 버전", "{} · Build {}".format(self.install_meta.data.get("first_version", APP_VERSION), self.install_meta.data.get("first_build", APP_BUILD))),
            ("최신 빌드 정보", latest_text),
            ("업데이트 소스 모드", str(self.settings.get("update_source_mode", "auto"))),
            ("로컬 UpdateInbox", str(self._configured_local_update_dir())),
        ]
        outer=self._card(scroll.inner,padx=22,pady=19); outer.pack(fill="x",pady=6); c=self._put_card_content(outer)
        tk.Label(c,text="Physics + Math Pocket",bg=t["surface"],fg=t["text"],font=("Segoe UI",self._font(18),"bold")).pack(anchor="w")
        tk.Label(c,text=APP_COPYRIGHT,bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",self._font(9))).pack(anchor="w",pady=(4,12))
        for key,value in info_rows:
            row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=3)
            tk.Label(row,text=key,bg=t["surface"],fg=t["muted"],width=22,anchor="w",font=("Malgun Gothic",self._font(9))).pack(side="left")
            tk.Label(row,text=value,bg=t["surface"],fg=t["text"],anchor="w",font=("Malgun Gothic",self._font(9),"bold")).pack(side="left",fill="x",expand=True)
        actions=tk.Frame(c,bg=t["surface"]); actions.pack(anchor="w",pady=(14,0))
        self._button(actions,"업데이트 확인",lambda:self.check_updates_background(interactive=True),kind="accent",padx=14,pady=8).pack(side="left",padx=(0,6))
        self._button(actions,"업데이트 화면",lambda:self.navigate("updates"),kind="normal",padx=14,pady=8).pack(side="left",padx=6)

        sections=[
            ("라이선스","프로그램 소스 코드는 MIT License를 사용합니다. 앱에 포함된 자체 작성 사전 설명의 이용 조건과 제3자 자료의 개별 조건은 LICENSE.md와 SOURCES.md에서 확인할 수 있습니다."),
            ("내용 규모",f"과학 {self.subject_counts['과학']:,}개 + 수학 {self.subject_counts['수학']:,}개 기본 개념, {len(self.formulas):,}개 공식·관계식, {len(CALCULATOR_SPECS)}개 계산기, {len(SIM_TITLES)}개 실험 항목를 갖춘 Windows 우선 오프라인 전자사전입니다."),
            ("UI 설계 원칙","웹 사전의 큰 검색창·표제어 카드·관련 개념·백과형 상세 보기처럼 빠르게 훑을 수 있는 구조를 참고했지만, 특정 서비스의 로고·문장·이미지·코드·고유 디자인을 복제하지 않은 독자 UI입니다."),
            ("내용 작성 원칙","BIPM·NIST·OpenStax·NASA·CERN과 교육과정·대학 공개강의 등 신뢰 가능한 자료를 대조해 설명을 새로 작성합니다. 외부 사전의 설명을 대량 복사하거나 내장하지 않습니다."),
            ("사용자 데이터와 1~5GB","기본 지식은 앱에 포함된 읽기 전용 데이터이고, 사용자가 추가·가져오기한 항목은 별도 SQLite DB에 저장됩니다. 5GB를 미리 빈 파일로 잡지 않고 필요할 때만 커지며 설정에서 1~5GB 소프트 한도를 정합니다."),
            ("Windows 업데이트","3.1.5부터 GitHub ZIP + 외부 업데이트 에이전트 방식이 기본입니다. 최초 설치/복구용 Setup.exe도 유지하며 LOCALAPPDATA의 사용자 데이터는 어느 방식에서도 보존됩니다."),
        ]
        for title,text in sections:
            outer=self._card(scroll.inner,padx=22,pady=19); outer.pack(fill="x",pady=6); c=self._put_card_content(outer); tk.Label(c,text=title,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(13),"bold")).pack(anchor="w"); tk.Label(c,text=text,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(9)),wraplength=800,justify="left",anchor="w").pack(fill="x",pady=(8,0))
        outer=self._card(scroll.inner,padx=22,pady=19); outer.pack(fill="x",pady=6); c=self._put_card_content(outer); tk.Label(c,text="주요 데이터 출처",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",self._font(13),"bold")).pack(anchor="w",pady=(0,8))
        for source in self.sources.values():
            row=tk.Frame(c,bg=t["surface2"]); row.pack(fill="x",pady=3); tk.Button(row,text=(source.get("title") or source.get("name") or source.get("id","출처")),command=lambda u=source.get("url",""):self.open_url(u),relief="flat",bd=0,bg=t["surface2"],fg=t["blue"],activebackground=t["surface2"],activeforeground=t["accent2"],font=("Malgun Gothic",self._font(9)),anchor="w",cursor="hand2").pack(side="left",fill="x",expand=True,padx=12,pady=8)
        scroll.to_top(); self.status_var.set("앱 정보 · {} · Build {}".format(APP_VERSION, APP_BUILD))

    def toggle_theme(self) -> None:
        self.theme_name="dark" if self.theme_name=="light" else "light"
        self.theme=make_theme(self.theme_name, str(self.settings.get("accent_color", "indigo")), bool(self.settings.get("glass_effects", True)))
        self.settings["theme"]=self.theme_name
        self.settings_store.save(self.settings)
        self._rebuild_current_page()
        apply_windows_chrome(self, self.theme_name == "dark")

    def change_font(self, amount: float) -> None:
        new_scale=min(1.4,max(0.8,round(self.font_scale+amount,2)))
        if new_scale==self.font_scale:return
        self.font_scale=new_scale; self.settings["font_scale"]=new_scale; self.settings_store.save(self.settings); self._rebuild_current_page()

    def _rebuild_current_page(self) -> None:
        page=self.current_page; term=self.current_term; self._build_shell()
        if page=="home": self.show_home()
        elif page in ("results","dictionary"): self.perform_search(add_history=False, record_navigation=False)
        elif page=="term" and term: self.show_term(term, record_navigation=False)
        elif page=="formulas": self.show_formulas()
        elif page=="simulations": self.show_simulations()
        elif page=="korean": self.show_korean()
        elif page=="constants": self.show_constants()
        elif page=="converter": self.show_converter()
        elif page=="calculators": self.show_calculators()
        elif page=="data": self.show_data_manager()
        elif page=="updates": self.show_updates()
        elif page=="help": self.show_help()
        else: self.show_about()

    def show_settings(self) -> None:
        t = self.theme
        win = tk.Toplevel(self)
        win.title("Physics + Math Pocket 설정")
        win.geometry("820x800")
        win.minsize(720, 680)
        win.configure(bg=t["bg"])
        win.transient(self)
        win.grab_set()
        wrap=ScrollableFrame(win,t["bg"]); wrap.pack(fill="both",expand=True,padx=18,pady=18); root=wrap.inner
        hero=tk.Frame(root,bg=t["accent_soft"],highlightthickness=1,highlightbackground=t["line"]); hero.pack(fill="x",pady=(0,14))
        tk.Label(hero,text="설정",bg=t["accent_soft"],fg=t["text"],font=("Malgun Gothic",20,"bold")).pack(anchor="w",padx=20,pady=(18,3))
        tk.Label(hero,text="모양 · 검색 · 시뮬레이션 · 업데이트 · 사용자 데이터",bg=t["accent_soft"],fg=t["muted"],font=("Malgun Gothic",9)).pack(anchor="w",padx=20,pady=(0,18))

        theme_var=tk.StringVar(value=self.settings.get("theme","system"))
        accent_var=tk.StringVar(value=self.settings.get("accent_color","indigo"))
        effects_var=tk.BooleanVar(value=bool(self.settings.get("glass_effects",True)))
        density_var=tk.StringVar(value=self.settings.get("density","comfortable"))
        font_var=tk.DoubleVar(value=self.font_scale)
        fps_var=tk.IntVar(value=int(self.settings.get("simulation_fps",30)))
        show_var=tk.BooleanVar(value=bool(self.settings.get("show_simulations",True)))
        anim_var=tk.BooleanVar(value=bool(self.settings.get("animations",True)))
        quota_var=tk.IntVar(value=int(self.settings.get("storage_limit_gb",5)))
        limit_var=tk.IntVar(value=int(self.settings.get("search_result_limit",100)))
        confirm_links_var=tk.BooleanVar(value=bool(self.settings.get("confirm_external_links",False)))
        update_startup_var=tk.BooleanVar(value=bool(self.settings.get("check_updates_on_startup",True)))
        update_channel_var=tk.StringVar(value=self.settings.get("update_channel","stable"))
        update_repo_var=tk.StringVar(value=self.settings.get("update_repository") or DEFAULT_SETTINGS["update_repository"])
        update_manifest_var=tk.StringVar(value=self.settings.get("update_manifest_url",""))
        update_source_var=tk.StringVar(value=self.settings.get("update_source_mode") or DEFAULT_SETTINGS["update_source_mode"])
        update_local_var=tk.StringVar(value=self.settings.get("update_local_dir","") or str(default_local_update_dir()))

        def section(title: str):
            outer=self._card(root,padx=18,pady=16); outer.pack(fill="x",pady=6); c=self._put_card_content(outer)
            tk.Label(c,text=title,bg=t["surface"],fg=t["text"],font=("Malgun Gothic",11,"bold")).pack(anchor="w",pady=(0,10)); return c

        c=section("화면")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=4)
        tk.Label(row,text="테마",bg=t["surface"],fg=t["muted"],width=18,anchor="w").pack(side="left")
        ttk.Combobox(row,textvariable=theme_var,values=["system","light","dark"],state="readonly",width=18).pack(side="right")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=4)
        tk.Label(row,text="강조 색상",bg=t["surface"],fg=t["muted"],width=18,anchor="w").pack(side="left")
        ttk.Combobox(row,textvariable=accent_var,values=["indigo","teal","rose"],state="readonly",width=18).pack(side="right")
        tk.Checkbutton(c,text="글래스 깊이·광택 효과 사용",variable=effects_var,bg=t["surface"],fg=t["text"],activebackground=t["surface"],selectcolor=t["surface2"]).pack(anchor="w",pady=(3,0))
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=4)
        tk.Label(row,text="화면 밀도",bg=t["surface"],fg=t["muted"],width=18,anchor="w").pack(side="left")
        ttk.Combobox(row,textvariable=density_var,values=["comfortable","compact"],state="readonly",width=18).pack(side="right")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=4)
        tk.Label(row,text="글자 배율",bg=t["surface"],fg=t["muted"],width=18,anchor="w").pack(side="left")
        ttk.Scale(row,from_=0.8,to=1.4,variable=font_var,orient="horizontal").pack(side="left",fill="x",expand=True,padx=8)
        tk.Label(row,textvariable=font_var,bg=t["surface"],fg=t["text"],width=5).pack(side="right")

        c=section("개념 시뮬레이션")
        tk.Checkbutton(c,text="개념 아래 미니 시뮬레이션 표시",variable=show_var,bg=t["surface"],fg=t["text"],activebackground=t["surface"],selectcolor=t["surface2"]).pack(anchor="w")
        tk.Checkbutton(c,text="애니메이션 사용",variable=anim_var,bg=t["surface"],fg=t["text"],activebackground=t["surface"],selectcolor=t["surface2"]).pack(anchor="w")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=(8,0))
        tk.Label(row,text="시뮬레이션 FPS",bg=t["surface"],fg=t["muted"]).pack(side="left")
        ttk.Combobox(row,textvariable=fps_var,values=[30,60],state="readonly",width=8).pack(side="right")

        c=section("검색·링크")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x")
        tk.Label(row,text="한 번에 표시할 결과",bg=t["surface"],fg=t["muted"]).pack(side="left")
        ttk.Combobox(row,textvariable=limit_var,values=[50,80,100,150,200,300],state="readonly",width=8).pack(side="right")
        tk.Checkbutton(c,text="외부 웹 링크를 열기 전에 확인",variable=confirm_links_var,bg=t["surface"],fg=t["text"],activebackground=t["surface"],selectcolor=t["surface2"]).pack(anchor="w",pady=(10,0))

        c=section("업데이트")
        tk.Checkbutton(c,text="앱 시작 후 업데이트 자동 확인",variable=update_startup_var,bg=t["surface"],fg=t["text"],activebackground=t["surface"],selectcolor=t["surface2"]).pack(anchor="w")
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=(8,4))
        tk.Label(row,text="업데이트 채널",bg=t["surface"],fg=t["muted"]).pack(side="left")
        ttk.Combobox(row,textvariable=update_channel_var,values=["stable","beta"],state="readonly",width=12).pack(side="right")
        tk.Label(c,text="beta 채널은 정식판과 베타판을 모두 확인합니다. 베타판은 설치 전에 별도 확인창을 표시합니다.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8),wraplength=530,justify="left").pack(anchor="w",pady=(2,8))
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x",pady=(2,6))
        tk.Label(row,text="업데이트 소스",bg=t["surface"],fg=t["muted"]).pack(side="left")
        ttk.Combobox(row,textvariable=update_source_var,values=["github","auto","local","manifest"],state="readonly",width=12).pack(side="right")
        tk.Label(c,text="github: 공개 GitHub Releases를 바로 확인 · auto: 로컬 폴더 → manifest → GitHub · local: 배포 전 기능 시험용",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8),wraplength=530,justify="left").pack(anchor="w",pady=(0,8))
        tk.Label(c,text="로컬 업데이트 폴더",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8)).pack(anchor="w")
        local_row=tk.Frame(c,bg=t["surface"]); local_row.pack(fill="x",pady=(3,6))
        local_entry=tk.Entry(local_row,textvariable=update_local_var,bg=t["surface2"],fg=t["text"],insertbackground=t["text"],relief="flat",font=("Consolas",9))
        local_entry.pack(side="left",fill="x",expand=True,ipady=7)
        def browse_update_folder():
            chosen=filedialog.askdirectory(parent=win,title="로컬 업데이트 폴더 선택",initialdir=update_local_var.get() or str(default_local_update_dir()))
            if chosen: update_local_var.set(chosen)
        self._button(local_row,"찾기",browse_update_folder,kind="ghost",padx=10,pady=7).pack(side="left",padx=(6,0))
        tk.Label(c,text="GitHub Releases 저장소",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8)).pack(anchor="w")
        repo_entry=tk.Entry(c,textvariable=update_repo_var,bg=t["surface2"],fg=t["text"],insertbackground=t["text"],relief="flat",font=("Consolas",9))
        repo_entry.pack(fill="x",ipady=7,pady=(3,6))
        tk.Label(c,text="예: owner/repository · 공개 저장소면 별도 업데이트 웹사이트 없이 GitHub Releases를 업데이트 피드로 사용할 수 있습니다.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8),wraplength=530,justify="left").pack(anchor="w")
        tk.Label(c,text="고급: HTTPS manifest URL (선택, GitHub보다 우선)",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8)).pack(anchor="w",pady=(8,0))
        manifest_entry=tk.Entry(c,textvariable=update_manifest_var,bg=t["surface2"],fg=t["text"],insertbackground=t["text"],relief="flat",font=("Consolas",9))
        manifest_entry.pack(fill="x",ipady=7,pady=(3,0))

        c=section("사용자 데이터베이스")
        tk.Label(c,text=f"현재 사용량: {bytes_to_human(self.db.size_bytes())}  ·  위치: {self.db.path}",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8),wraplength=530,justify="left").pack(anchor="w",pady=(0,8))
        row=tk.Frame(c,bg=t["surface"]); row.pack(fill="x")
        tk.Label(row,text="확장 데이터 한도",bg=t["surface"],fg=t["muted"]).pack(side="left")
        ttk.Combobox(row,textvariable=quota_var,values=[1,2,3,4,5],state="readonly",width=8).pack(side="right")
        tk.Label(c,text="빈 5GB 파일을 만들지 않습니다. SQLite 파일은 실제로 항목을 넣은 만큼만 커지고, 이 값은 안전을 위한 소프트 한도입니다.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8),wraplength=530,justify="left").pack(anchor="w",pady=(8,0))

        buttons=tk.Frame(root,bg=t["bg"]); buttons.pack(fill="x",pady=12)
        def save():
            self.settings.update({
                "theme":theme_var.get(), "accent_color":accent_var.get(), "glass_effects":bool(effects_var.get()),
                "density":density_var.get(), "font_scale":round(float(font_var.get()),2),
                "simulation_fps":int(fps_var.get()), "show_simulations":bool(show_var.get()), "animations":bool(anim_var.get()),
                "storage_limit_gb":int(quota_var.get()), "search_result_limit":int(limit_var.get()),
                "confirm_external_links":bool(confirm_links_var.get()),
                "check_updates_on_startup":bool(update_startup_var.get()),
                "update_channel":update_channel_var.get(),
                "update_repository":update_repo_var.get().strip(),
                "update_manifest_url":update_manifest_var.get().strip(),
                "update_source_mode":update_source_var.get(),
                "update_local_dir":update_local_var.get().strip(),
            })
            self.settings_store.save(self.settings)
            self.db.set_limit_gb(int(quota_var.get()))
            self.font_scale=float(self.settings["font_scale"])
            self.theme_name=detect_system_theme() if self.settings["theme"]=="system" else self.settings["theme"]
            self.theme=make_theme(self.theme_name, str(self.settings.get("accent_color","indigo")), bool(self.settings.get("glass_effects",True)))
            self.result_limit=int(self.settings["search_result_limit"])
            win.destroy(); self._rebuild_current_page()
        self._button(buttons,"저장",save,kind="accent",padx=20,pady=9).pack(side="right")
        self._button(buttons,"취소",win.destroy,kind="ghost",padx=16,pady=9).pack(side="right",padx=6)

    def show_korean(self) -> None:
        self.current_page = "korean"
        self.current_term = None
        self._refresh_nav_state()
        build_korean_page(self)

    def show_simulations(self) -> None:
        from simulation_browser import build_simulation_browser
        build_simulation_browser(self, ScrollableFrame)

    def show_data_manager(self) -> None:
        self.current_page="data"; self.current_term=None; self._refresh_nav_state(); frame=self._clear_center(); t=self.theme; self._page_title(frame,"내 데이터", "내가 직접 추가한 개념과 외부 JSON/CSV 확장팩을 관리합니다.")
        scroll=ScrollableFrame(frame,t["bg"]); scroll.pack(fill="both",expand=True); inner=scroll.inner
        outer=self._card(inner,padx=22,pady=18); outer.pack(fill="x",pady=6); c=self._put_card_content(outer); tk.Label(c,text="확장형 SQLite 지식베이스",bg=t["surface"],fg=t["text"],font=("Malgun Gothic",13,"bold")).pack(anchor="w"); tk.Label(c,text=f"사용 {bytes_to_human(self.db.size_bytes())} / 한도 {self.db.limit_gb} GB  ·  {self.db.count():,}개 사용자 항목",bg=t["surface"],fg=t["accent2"],font=("Malgun Gothic",10,"bold")).pack(anchor="w",pady=(6,2)); tk.Label(c,text="기본 데이터와 분리되어 앱을 업데이트해도 내 항목은 유지됩니다. 5GB를 선점하지 않고 실제 데이터가 늘어날 때만 파일이 커집니다.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",9),wraplength=780,justify="left").pack(anchor="w")
        actions=tk.Frame(c,bg=t["surface"]); actions.pack(fill="x",pady=(12,0)); self._button(actions,"+ 새 개념",lambda:self.show_add_term_dialog(),kind="accent").pack(side="left",padx=(0,6)); self._button(actions,"JSON/CSV 가져오기",self.import_user_data,kind="normal").pack(side="left",padx=3); self._button(actions,"내보내기",self.export_user_data,kind="normal").pack(side="left",padx=3); self._button(actions,"DB 최적화",self.optimize_database,kind="ghost").pack(side="left",padx=3); self._button(actions,"폴더 열기",self.open_data_folder,kind="ghost").pack(side="left",padx=3)
        terms=self.db.all_user_terms(); self._page_title(inner,"내가 추가한 개념",f"{len(terms):,}개")
        if not terms:
            outer=self._card(inner,padx=22,pady=20); outer.pack(fill="x",pady=6); x=self._put_card_content(outer); tk.Label(x,text="아직 직접 추가한 개념이 없습니다. 위의 ‘+ 새 개념’ 또는 가져오기로 확장할 수 있어요.",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",9)).pack(anchor="w")
        for term in terms[:120]:
            outer=self._card(inner,padx=15,pady=12); outer.pack(fill="x",pady=4); x=self._put_card_content(outer); tk.Button(x,text=term["name_ko"],command=lambda z=term:self.show_term(z),relief="flat",bd=0,bg=t["surface"],fg=t["blue"],font=("Malgun Gothic",11,"bold"),cursor="hand2").pack(side="left"); tk.Label(x,text=f"{term.get('subject','사용자')} · {term.get('category','사용자 추가')}",bg=t["surface"],fg=t["muted"],font=("Malgun Gothic",8)).pack(side="left",padx=10); self._button(x,"삭제",lambda z=term:self.delete_user_term(z),kind="danger",padx=9,pady=5).pack(side="right"); self._button(x,"수정",lambda z=term:self.show_add_term_dialog(z),kind="ghost",padx=9,pady=5).pack(side="right",padx=4)
        self.status_var.set(f"내 데이터 · {self.db.count():,}개")

    def show_add_term_dialog(self, term: Optional[dict] = None) -> None:
        t=self.theme; win=tk.Toplevel(self); win.title("개념 수정" if term else "새 개념 추가"); win.geometry("720x760"); win.configure(bg=t["bg"]); win.transient(self); win.grab_set(); wrap=ScrollableFrame(win,t["bg"]); wrap.pack(fill="both",expand=True,padx=16,pady=16); root=wrap.inner; data=term or {}
        tk.Label(root,text="내 개념 편집기",bg=t["bg"],fg=t["text"],font=("Malgun Gothic",16,"bold")).pack(anchor="w",pady=(0,10)); fields={}
        specs=[("표제어 *","name_ko"),("영문명","name_en"),("교과 (수학/물리/화학/생명과학/지구과학/천문학/국어/사용자)","subject"),("분야","category"),("수준","level"),("한줄 정의","summary"),("공식","formula"),("단위","unit"),("예시","example"),("주의","caution"),("별칭 - 쉼표 구분","aliases"),("관련 개념 - 쉼표 구분","related")]
        for label,key in specs:
            tk.Label(root,text=label,bg=t["bg"],fg=t["muted"],font=("Malgun Gothic",8,"bold")).pack(anchor="w",pady=(7,3)); var=tk.StringVar(value=(", ".join(data.get(key,[])) if key in ("aliases","related") else str(data.get(key,"")))); ent=tk.Entry(root,textvariable=var,bg=t["surface"],fg=t["text"],insertbackground=t["text"],relief="flat",font=("Malgun Gothic",10)); ent.pack(fill="x",ipady=7); fields[key]=var
        tk.Label(root,text="자세한 설명",bg=t["bg"],fg=t["muted"],font=("Malgun Gothic",8,"bold")).pack(anchor="w",pady=(7,3)); detail=tk.Text(root,height=8,wrap="word",bg=t["surface"],fg=t["text"],insertbackground=t["text"],relief="flat",font=("Malgun Gothic",10),padx=10,pady=8); detail.pack(fill="x"); detail.insert("1.0",data.get("detail",""))
        sim_var=tk.StringVar(value=data.get("simulator","")); tk.Label(root,text="연결할 미니 시뮬레이터",bg=t["bg"],fg=t["muted"],font=("Malgun Gothic",8,"bold")).pack(anchor="w",pady=(7,3)); ttk.Combobox(root,textvariable=sim_var,values=[""]+list(SIM_TITLES.keys()),state="readonly").pack(fill="x")
        def save():
            try:
                payload={k:v.get().strip() for k,v in fields.items()}; payload["detail"]=detail.get("1.0","end-1c").strip(); payload["aliases"]=[x.strip() for x in payload.pop("aliases","").split(",") if x.strip()]; payload["related"]=[x.strip() for x in payload.pop("related","").split(",") if x.strip()]; payload["sources"]=[]; payload["simulator"]=sim_var.get(); payload["subject"]=payload.get("subject") or "사용자"; payload["category"]=payload.get("category") or "사용자 추가"; payload["level"]=payload.get("level") or "사용자"
                if term and term.get("user_added"): payload["id"]=term["id"]
                self.db.upsert_term(payload); self.reload_user_terms(); win.destroy(); self.show_data_manager(); self.status_var.set("내 개념을 저장했습니다.")
            except Exception as exc: messagebox.showerror("저장 실패",str(exc),parent=win)
        buttons=tk.Frame(root,bg=t["bg"]); buttons.pack(fill="x",pady=14); self._button(buttons,"저장",save,kind="accent",padx=20,pady=9).pack(side="right"); self._button(buttons,"취소",win.destroy,kind="ghost",padx=16,pady=9).pack(side="right",padx=6)

    def import_user_data(self) -> None:
        path=filedialog.askopenfilename(parent=self,title="지식 확장팩 가져오기",filetypes=[("JSON/CSV","*.json *.csv"),("JSON","*.json"),("CSV","*.csv")]);
        if not path:return
        try:
            p=Path(path); ok,bad=self.db.import_json(p) if p.suffix.lower()==".json" else self.db.import_csv(p); self.reload_user_terms(); self.show_data_manager(); messagebox.showinfo("가져오기 완료",f"성공 {ok}개 · 건너뜀 {bad}개",parent=self)
        except Exception as exc: messagebox.showerror("가져오기 실패",str(exc),parent=self)

    def export_user_data(self) -> None:
        path=filedialog.asksaveasfilename(parent=self,title="내 데이터 내보내기",defaultextension=".json",filetypes=[("JSON","*.json"),("CSV","*.csv")]);
        if not path:return
        try:
            p=Path(path); self.db.export_csv(p) if p.suffix.lower()==".csv" else self.db.export_json(p); messagebox.showinfo("내보내기 완료",str(p),parent=self)
        except Exception as exc: messagebox.showerror("내보내기 실패",str(exc),parent=self)

    def delete_user_term(self, term: dict) -> None:
        if not term.get("user_added"):return
        if messagebox.askyesno("개념 삭제",f"‘{term.get('name_ko','')}’을(를) 내 데이터에서 삭제할까요?",parent=self): self.db.delete_term(term["id"]); self.reload_user_terms(); self.show_data_manager()

    def optimize_database(self) -> None:
        try: self.db.optimize(); self.show_data_manager(); self.status_var.set("사용자 데이터베이스를 최적화했습니다.")
        except Exception as exc: messagebox.showerror("DB 최적화 실패",str(exc),parent=self)

    def open_data_folder(self) -> None:
        folder=str(self.db.path.parent)
        try:
            if os.name=="nt": os.startfile(folder)
            elif sys.platform=="darwin": subprocess.Popen(["open",folder])
            else: subprocess.Popen(["xdg-open",folder])
        except Exception as exc: messagebox.showerror("폴더 열기 실패",str(exc),parent=self)

    def clear_recent_searches(self) -> None:
        self.recent_searches = []
        self.history_store.save([])
        self._build_right_sidebar()
        self.status_var.set("최근 검색 기록을 지웠습니다.")

    def _copy_to_clipboard(self, text: str) -> None:
        try:
            self.clipboard_clear(); self.clipboard_append(text); self.update_idletasks(); self.status_var.set("클립보드에 복사했습니다.")
        except Exception as exc:
            messagebox.showerror("복사 실패", str(exc), parent=self)

    def open_url(self, url: str) -> None:
        if not url:
            return
        if bool(self.settings.get("confirm_external_links", False)):
            host=urllib.parse.urlparse(url).netloc or url
            if not messagebox.askyesno("외부 링크 열기", f"웹 브라우저에서 다음 사이트를 열까요?\n\n{host}", parent=self):
                return
        try:
            webbrowser.open(url)
        except Exception as exc:
            messagebox.showerror("링크 열기 실패", str(exc), parent=self)

    def _daily_featured(self, count: int) -> List[dict]:
        seed = int(_dt.date.today().strftime("%Y%m%d"))
        rng = random.Random(seed)
        pool = list(self.terms)
        rng.shuffle(pool)
        return pool[:count]

    def _bind_shortcuts(self) -> None:
        self.bind_all("<Control-l>", lambda _e: self._focus_search())
        self.bind_all("<Control-k>", lambda _e: self._focus_search())
        self.bind_all("<Control-d>", lambda _e: self.toggle_favorite())
        self.bind_all("<F1>", lambda _e: self.navigate("help"))
        self.bind_all("<Alt-Left>", self.go_back)
        self.bind_all("<Escape>", self._escape_action)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self) -> None:
        try: self.db.close()
        except Exception: pass
        self.destroy()

    def _focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")

    def _escape_action(self, _event=None) -> None:
        if self.suggestion_popup is not None:
            self._hide_suggestions()
        elif self.nav_history:
            self.go_back()
        elif self.current_page != "home":
            self.show_home()


def run() -> None:
    enable_windows_high_dpi()
    configure_logging()
    try:
        app = PhysicsPocketApp()
        app.mainloop()
    except Exception as exc:
        logging.exception("앱 시작 실패")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Physics + Math Pocket 오류",
                "앱을 시작하지 못했습니다.\n\n{}\n\n로그: {}".format(exc, user_data_dir() / "physics_math_pocket.log"),
            )
            root.destroy()
        except Exception:
            raise
