#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
# import python 3.14 files = off
# pr
"""
CAT CLIENT 0.1
Offline Minecraft launcher — dark/light/system theme.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
import subprocess
import zipfile
import ssl
import threading
import sys
import os
import platform
from pathlib import Path
import uuid
import io
import hashlib
import concurrent.futures
import urllib.parse

# Create an explicit unverified context to use directly in urlopen
ctx = ssl._create_unverified_context()

# Paths
if sys.platform == "win32":
    GAME_DIR = Path.home() / "AppData" / "Roaming" / ".minecraft"
elif sys.platform == "darwin":
    GAME_DIR = Path.home() / "Library" / "Application Support" / "minecraft"
else:
    GAME_DIR = Path.home() / ".minecraft"

SKIN_SERVER = "https://mc-heads.net"
VERSION_MANIFEST_URLS = [
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
]
ASSETS_URL = "https://resources.download.minecraft.net"
CLASSPATH_SEP = ";" if sys.platform == "win32" else ":"
USER_AGENT = "CatClient/0.1"
APP_NAME = "CAT CLIENT 0.1"
BRAND_COPY = "0.1"
OFFLINE_ACCOUNT = "Cat Client"
MICROSOFT_ACCOUNT = "Microsoft Account"
MOJANG_ACCOUNT = "Mojang Account (Legacy)"
DOWNLOAD_CHUNK = 1024 * 1024
LIB_WORKERS = 32
ASSET_WORKERS = 48
FABRIC_META = "https://meta.fabricmc.net/v2"
MODRINTH_API = "https://api.modrinth.com/v2"
MOD_WORKERS = 12
# ULTRAMAX FPS + Ping pack — fabric-api first; extras skip if unavailable on version
FPS_MODS = [
    ("fabric-api", "Fabric API"),
    ("fabric-language-kotlin", "Fabric Language Kotlin"),
    ("yacl", "YetAnotherConfigLib"),
    ("cloth-config", "Cloth Config API"),
    ("controlling", "Controlling"),
    ("searchables", "Searchables"),
    ("sodium", "Sodium"),
    ("lithium", "Lithium"),
    ("entityculling", "Entity Culling"),
    ("immediatelyfast", "ImmediatelyFast"),
    ("moreculling", "More Culling"),
    ("badoptimizations", "BadOptimizations"),
    ("dynamic-fps", "Dynamic FPS"),
    ("fps-reducer", "FPS Reducer"),
    ("sodium-extra", "Sodium Extra"),
    ("reeses-sodium-options", "Reese's Sodium Options"),
    ("clumps", "Clumps"),
    ("c2me-fabric", "C2ME Chunks"),
    ("vmp-fabric", "VMP Multiplayer"),
    ("servercore", "ServerCore"),
    ("alternate-current", "Alternate Current"),
    ("packet-fixer", "Packet Fixer"),
    ("modmenu", "Mod Menu"),
    ("fpsdisplay", "FPS Display"),
    ("ferrite-core", "FerriteCore"),
    ("modernfix", "ModernFix"),
    ("krypton", "Krypton Network"),
    ("noisium", "Noisium"),
    ("memoryleakfix", "Memory Leak Fix"),
    ("cull-less-leaves", "Cull Less Leaves"),
    ("threadtweak", "ThreadTweak"),
    ("fastquit", "FastQuit"),
    ("lazydfu", "LazyDFU"),
    ("spark", "Spark"),
]

# ============== CAT CLIENT THEMES (TLauncher dark style) ==============
THEMES = {
    "dark": {
        "bg_dark": "#1e1e1e",
        "bg_darker": "#141414",
        "bg_panel": "#2b2b2b",
        "bg_input": "#383838",
        "bg_header": "#0f0f0f",
        "sidebar_active": "#2f2f2f",
        "accent": "#5cb85c",
        "accent_hover": "#6fdc6f",
        "accent_green": "#5cb85c",
        "accent_green_hover": "#6fdc6f",
        "accent_orange": "#e67e22",
        "accent_blue": "#4a9eff",
        "text_primary": "#eeeeee",
        "text_secondary": "#aaaaaa",
        "text_muted": "#666666",
        "border": "#404040",
        "button_play": "#5cb85c",
        "button_play_hover": "#6fdc6f",
        "button_play_text": "#ffffff",
    },
    "light": {
        "bg_dark": "#f3f4f6",
        "bg_darker": "#e5e7eb",
        "bg_panel": "#ffffff",
        "bg_input": "#f9fafb",
        "bg_header": "#2b2b2b",
        "sidebar_active": "#e5e7eb",
        "accent": "#5cb85c",
        "accent_hover": "#6fdc6f",
        "accent_green": "#5cb85c",
        "accent_green_hover": "#6fdc6f",
        "accent_orange": "#d97706",
        "accent_blue": "#2563eb",
        "text_primary": "#111827",
        "text_secondary": "#4b5563",
        "text_muted": "#9ca3af",
        "border": "#d1d5db",
        "button_play": "#5cb85c",
        "button_play_hover": "#6fdc6f",
        "button_play_text": "#ffffff",
    }
}

# ============== UTILITY FUNCTIONS ==============
def get_system_theme():
    """Detect system dark/light mode"""
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        elif sys.platform == "darwin":
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            return "dark" if "Dark" in result.stdout else "light"
    except:
        pass
    return "dark"


def find_java():
    candidates = []
    java_home = os.environ.get("JAVA_HOME", "").strip()
    if sys.platform == "win32":
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java.exe")
        candidates.extend([
            Path("C:/Program Files/Java/jdk-17/bin/java.exe"),
            Path("C:/Program Files/Java/jdk-21/bin/java.exe"),
            Path("C:/Program Files/Eclipse Adoptium/jdk-17/bin/java.exe"),
            Path("C:/Program Files/Eclipse Adoptium/jdk-21/bin/java.exe"),
            Path("C:/Program Files/BellSoft/LibericaJDK-21/bin/java.exe"),
            Path("C:/Program Files/BellSoft/LibericaJDK-17/bin/java.exe"),
        ])
    elif sys.platform == "darwin":
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java")
        candidates.extend([
            Path("/opt/homebrew/opt/openjdk@17/bin/java"),
            Path("/opt/homebrew/opt/openjdk@21/bin/java"),
            Path("/opt/homebrew/opt/openjdk/bin/java"),
            Path("/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home/bin/java"),
            Path("/usr/bin/java"),
        ])
    else:
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java")
        candidates.extend([
            Path("/usr/lib/jvm/java-17-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-17-openjdk-amd64/bin/java"),
            Path("/usr/bin/java"),
        ])
    
    for path in candidates:
        if path.exists():
            return str(path)
    return "java"


def get_os_name():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "osx"
    return "linux"


def get_arch():
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x64"
    elif machine in ("aarch64", "arm64"):
        return "arm64"
    return "x86"


def check_rules(rules):
    if not rules:
        return True
    
    os_name = get_os_name()
    arch = get_arch()
    result = False
    
    for rule in rules:
        action = rule.get("action", "allow")
        matches = True
        
        if "os" in rule:
            os_rule = rule["os"]
            if "name" in os_rule and os_rule["name"] != os_name:
                matches = False
            if "arch" in os_rule and os_rule["arch"] != arch:
                matches = False
        
        if matches:
            result = (action == "allow")
    
    return result


def check_arg_rules(rules, features=None):
    """Evaluate Mojang argument rules (OS + feature flags)."""
    if not rules:
        return True
    features = features or {}
    result = False
    for rule in rules:
        action = rule.get("action", "allow")
        matches = True
        if "os" in rule:
            os_rule = rule["os"]
            if "name" in os_rule and os_rule["name"] != get_os_name():
                matches = False
            if "arch" in os_rule and os_rule["arch"] != get_arch():
                matches = False
        if "features" in rule:
            for feat, required in rule["features"].items():
                if features.get(feat, False) != required:
                    matches = False
                    break
        if matches:
            result = (action == "allow")
    return result


def substitute_vars(text, variables):
    if not isinstance(text, str):
        return text
    for key, value in variables.items():
        text = text.replace("${" + key + "}", str(value))
    return text


def expand_arguments(arg_list, variables, features=None):
    """Expand version.json JVM/game argument lists."""
    expanded = []
    for entry in arg_list:
        if isinstance(entry, str):
            expanded.append(substitute_vars(entry, variables))
        elif isinstance(entry, dict):
            if not check_arg_rules(entry.get("rules"), features):
                continue
            value = entry.get("value", "")
            if isinstance(value, list):
                for item in value:
                    expanded.append(substitute_vars(item, variables))
            elif value:
                expanded.append(substitute_vars(value, variables))
    return expanded


def generate_offline_uuid(username):
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}"))


def calculate_sha1(filepath):
    sha1 = hashlib.sha1()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                sha1.update(chunk)
        return sha1.hexdigest()
    except OSError:
        return None


def fetch_json(url, timeout=15):
    """Fetch JSON over HTTPS with explicit SSL context."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode())


def fetch_version_manifest(timeout=15):
    """Try current Mojang manifest endpoints in order."""
    last_err = None
    for url in VERSION_MANIFEST_URLS:
        try:
            return fetch_json(url, timeout=timeout)
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Could not fetch version manifest: {last_err}")


def get_latest_release_id():
    manifest = fetch_version_manifest(timeout=10)
    return manifest["latest"]["release"]


def maven_to_rel_path(name):
    parts = name.split(":")
    if len(parts) < 3:
        return name
    group, artifact, version = parts[0], parts[1], parts[2]
    group_path = group.replace(".", "/")
    return f"{group_path}/{artifact}/{version}/{artifact}-{version}.jar"


def merge_version_info(child, parent):
    merged = json.loads(json.dumps(parent))
    merged["id"] = child["id"]
    if child.get("mainClass"):
        merged["mainClass"] = child["mainClass"]
    merged["libraries"] = child.get("libraries", []) + parent.get("libraries", [])
    if "arguments" in child:
        merged.setdefault("arguments", {})
        parent_args = merged.get("arguments", {})
        for key in ("jvm", "game"):
            child_vals = child["arguments"].get(key, [])
            parent_vals = parent_args.get(key, [])
            merged["arguments"][key] = child_vals + parent_vals
    return merged


def resolve_version_info(version_info):
    if not version_info.get("inheritsFrom"):
        return version_info
    parent_id = version_info["inheritsFrom"]
    parent_path = GAME_DIR / "versions" / parent_id / f"{parent_id}.json"
    if not parent_path.exists():
        raise FileNotFoundError(f"Parent version missing: {parent_id}")
    with open(parent_path, encoding="utf-8") as f:
        parent = json.load(f)
    parent = resolve_version_info(parent)
    return merge_version_info(version_info, parent)


def library_download_task(lib, libs_dir):
    if "downloads" in lib and "artifact" in lib["downloads"]:
        artifact = lib["downloads"]["artifact"]
        return (
            artifact["url"],
            libs_dir / artifact["path"],
            artifact.get("sha1"),
            artifact.get("size"),
        )
    if "name" in lib:
        rel = maven_to_rel_path(lib["name"])
        base = lib.get("url", "https://libraries.minecraft.net/")
        if not base.endswith("/"):
            base += "/"
        return (base + rel, libs_dir / rel, lib.get("sha1"), lib.get("size"))
    return None


def fetch_modrinth_versions(slug, game_version):
    params = urllib.parse.urlencode([
        ("game_versions", json.dumps([game_version])),
        ("loaders", json.dumps(["fabric"])),
    ])
    url = f"{MODRINTH_API}/project/{slug}/version?{params}"
    return fetch_json(url, timeout=20)


def file_is_valid(dest_path, expected_hash=None, expected_size=None):
    """Fast local cache check — size first, SHA1 only when needed."""
    dest_path = Path(dest_path)
    if not dest_path.exists():
        return False
    try:
        actual_size = dest_path.stat().st_size
    except OSError:
        return False
    if expected_size is not None and actual_size != expected_size:
        return False
    if expected_hash:
        if dest_path.name == expected_hash and expected_size is not None:
            return True
        return calculate_sha1(dest_path) == expected_hash
    return True


def download_file_fast(url, dest_path, expected_hash=None, expected_size=None, timeout=60):
    """Stream download with cache skip and optional integrity check."""
    dest_path = Path(dest_path)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")
    if file_is_valid(dest_path, expected_hash, expected_size):
        return True
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(DOWNLOAD_CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
        if expected_hash and calculate_sha1(tmp_path) != expected_hash:
            tmp_path.unlink(missing_ok=True)
            return False
        if expected_size is not None and tmp_path.stat().st_size != expected_size:
            tmp_path.unlink(missing_ok=True)
            return False
        tmp_path.replace(dest_path)
        return True
    except Exception as exc:
        print(f"Download failed ({dest_path.name}): {exc}")
        tmp_path.unlink(missing_ok=True)
        return False


# ============== ASSET DOWNLOADER ==============
class AssetDownloader:
    def __init__(self, game_dir, progress_callback=None, status_callback=None):
        self.game_dir = Path(game_dir)
        self.assets_dir = self.game_dir / "assets"
        self.objects_dir = self.assets_dir / "objects"
        self.indexes_dir = self.assets_dir / "indexes"
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.downloaded = 0
        self.total = 0
        self.failed = []
        self._lock = threading.Lock()
    
    def download_file(self, url, dest_path, expected_hash=None, expected_size=None):
        return download_file_fast(url, dest_path, expected_hash, expected_size, timeout=30)
    
    def download_asset(self, asset_hash, asset_size=None):
        prefix = asset_hash[:2]
        asset_path = self.objects_dir / prefix / asset_hash
        url = f"{ASSETS_URL}/{prefix}/{asset_hash}"
        
        success = self.download_file(url, asset_path, asset_hash, asset_size)
        
        with self._lock:
            self.downloaded += 1
            progress = int((self.downloaded / self.total) * 100) if self.total else 0
        if self.progress_callback and self.total > 0:
            self.progress_callback(progress)
        
        if not success:
            self.failed.append(asset_hash)
        
        return success
    
    def download_all_assets(self, asset_index_id, asset_index_url=None):
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = self.indexes_dir / f"{asset_index_id}.json"
        if not index_path.exists() and asset_index_url:
            if self.status_callback:
                self.status_callback("Downloading asset index...")
            self.download_file(asset_index_url, index_path)
        
        if not index_path.exists():
            raise FileNotFoundError(f"Asset index not found: {index_path}")
        
        with open(index_path) as f:
            asset_index = json.load(f)
        
        objects = asset_index.get("objects", {})
        self.total = len(objects)
        self.downloaded = 0
        self.failed = []
        
        if self.status_callback:
            self.status_callback(f"Checking {self.total} assets...")
        
        assets_to_download = []
        for asset_name, asset_info in objects.items():
            asset_hash = asset_info["hash"]
            asset_size = asset_info.get("size")
            prefix = asset_hash[:2]
            asset_path = self.objects_dir / prefix / asset_hash
            
            if file_is_valid(asset_path, asset_hash, asset_size):
                self.downloaded += 1
                continue
            
            assets_to_download.append((asset_hash, asset_size))
        
        if self.status_callback:
            self.status_callback(f"Downloading {len(assets_to_download)} assets...")
        
        if assets_to_download:
            with concurrent.futures.ThreadPoolExecutor(max_workers=ASSET_WORKERS) as executor:
                list(executor.map(lambda item: self.download_asset(*item), assets_to_download))
        
        if self.status_callback:
            if self.failed:
                self.status_callback(f"Assets done ({len(self.failed)} failed)")
            else:
                self.status_callback("All assets downloaded!")
        
        return len(self.failed) == 0


# ============== THEME TOGGLE WIDGET ==============
class ThemeToggle(tk.Frame):
    def __init__(self, parent, callback, initial="system", **kwargs):
        super().__init__(parent, **kwargs)
        self.callback = callback
        self.current = initial
        self.options = ["dark", "light", "system"]
        self.labels = ["🌙", "☀️", "💻"]
        
        self.configure(bg=kwargs.get("bg", "#16213e"))
        
        self.buttons = []
        for i, (opt, lbl) in enumerate(zip(self.options, self.labels)):
            btn = tk.Label(
                self, text=lbl, font=("Segoe UI", 12),
                fg="#ffffff" if opt == initial else "#6b7280",
                bg=self["bg"], padx=8, pady=4, cursor="hand2"
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, o=opt: self.select(o))
            self.buttons.append(btn)
    
    def select(self, option):
        self.current = option
        for btn, opt in zip(self.buttons, self.options):
            if opt == option:
                btn.config(fg="#ffffff", font=("Segoe UI", 12, "bold"))
            else:
                btn.config(fg="#6b7280", font=("Segoe UI", 12))
        self.callback(option)
    
    def update_bg(self, bg):
        self.configure(bg=bg)
        for btn in self.buttons:
            btn.configure(bg=bg)


class AccountLoginDialog(tk.Toplevel):
    """Modal Microsoft / Mojang sign-in prompt."""

    def __init__(self, parent, theme, account_kind, initial_username=""):
        super().__init__(parent)
        self.theme = theme
        self.account_kind = account_kind
        self.result = None

        is_ms = account_kind == "microsoft"
        title = "Microsoft Sign In" if is_ms else "Mojang Sign In"
        self.title(f"{APP_NAME} — {title}")
        self.geometry("460x420" if is_ms else "460x450")
        self.resizable(False, False)
        self.configure(bg=theme["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() // 2) - 230
        py = parent.winfo_rooty() + (parent.winfo_height() // 2) - 210
        self.geometry(f"+{max(px, 0)}+{max(py, 0)}")

        card = tk.Frame(self, bg=theme["bg_panel"], padx=24, pady=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        icon = "🪟" if is_ms else "☁"
        tk.Label(
            card, text=icon, font=("Segoe UI", 28),
            fg=theme["accent_blue"] if is_ms else theme["accent_orange"],
            bg=theme["bg_panel"],
        ).pack(anchor="w")

        tk.Label(
            card, text=title, font=("Segoe UI", 16, "bold"),
            fg=theme["text_primary"], bg=theme["bg_panel"],
        ).pack(anchor="w", pady=(6, 4))

        subtitle = (
            "Sign in with the Microsoft account linked to Minecraft."
            if is_ms else
            "Legacy Mojang login. Most accounts have been migrated to Microsoft."
        )
        tk.Label(
            card, text=subtitle, font=("Segoe UI", 9),
            fg=theme["text_secondary"], bg=theme["bg_panel"],
            wraplength=390, justify="left",
        ).pack(anchor="w", pady=(0, 16))

        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.username_var = tk.StringVar(value=initial_username)

        self._field(card, "Email", self.email_var)
        self._field(card, "Password", self.password_var, show="*")
        self._field(card, "Minecraft Username", self.username_var)

        if not is_ms:
            tk.Label(
                card,
                text="Tip: Use a Microsoft account if login fails — Mojang accounts were merged.",
                font=("Segoe UI", 8), fg=theme["text_muted"], bg=theme["bg_panel"],
                wraplength=390, justify="left",
            ).pack(anchor="w", pady=(4, 0))

        btn_row = tk.Frame(card, bg=theme["bg_panel"])
        btn_row.pack(fill="x", pady=(18, 0))

        tk.Button(
            btn_row, text="Cancel", font=("Segoe UI", 10),
            fg=theme["text_secondary"], bg=theme["bg_input"],
            activeforeground=theme["text_primary"], activebackground=theme["bg_panel"],
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self._cancel,
        ).pack(side="right")

        sign_btn = tk.Button(
            btn_row, text="Sign In", font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=theme["accent_green"],
            activeforeground="#ffffff", activebackground=theme["accent_green_hover"],
            relief="flat", cursor="hand2", padx=20, pady=6,
            command=self._submit,
        )
        sign_btn.pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _field(self, parent, label, variable, show=None):
        t = self.theme
        tk.Label(
            parent, text=label, font=("Segoe UI", 9),
            fg=t["text_secondary"], bg=t["bg_panel"],
        ).pack(anchor="w", pady=(0, 4))
        entry = tk.Entry(
            parent, textvariable=variable, font=("Segoe UI", 11),
            fg=t["text_primary"], bg=t["bg_input"],
            insertbackground=t["text_primary"], relief="flat", show=show,
        )
        entry.pack(fill="x", ipady=7, pady=(0, 10))
        if label == "Email":
            entry.bind("<KeyRelease>", self._on_email_change)
            entry.focus_set()

    def _on_email_change(self, event=None):
        email = self.email_var.get().strip()
        if "@" in email and not self.username_var.get().strip():
            local = email.split("@", 1)[0]
            safe = "".join(c for c in local if c.isalnum() or c == "_")[:16]
            if len(safe) >= 3:
                self.username_var.set(safe)

    def _submit(self):
        email = self.email_var.get().strip()
        password = self.password_var.get()
        username = self.username_var.get().strip()

        if not email or "@" not in email:
            messagebox.showwarning(APP_NAME, "Enter a valid email address.", parent=self)
            return
        if len(password) < 4:
            messagebox.showwarning(APP_NAME, "Enter your account password.", parent=self)
            return
        if len(username) < 3 or len(username) > 16:
            messagebox.showwarning(APP_NAME, "Minecraft username must be 3-16 characters.", parent=self)
            return
        if not all(c.isalnum() or c == "_" for c in username):
            messagebox.showwarning(APP_NAME, "Username can only use letters, numbers, and underscores.", parent=self)
            return

        self.result = {
            "type": self.account_kind,
            "email": email,
            "display_name": username,
        }
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


# ============== CAT CLIENT UI ==============
class CatClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x620")
        self.root.resizable(False, False)
        
        self.theme_mode = "dark"
        self.current_theme = THEMES["dark"]
        
        self.username = tk.StringVar(value="Player")
        self.version = tk.StringVar(value="1.20.1")
        self.account_type = tk.StringVar(value=OFFLINE_ACCOUNT)
        self.ram = tk.IntVar(value=4)
        self.skin_photo = None
        self.status_text = tk.StringVar(value="Ready to play 🐱")
        self.java_bin = find_java()
        self.game_process = None
        self._log_handle = None
        self.active_tab = "PLAY"
        self.tab_buttons = {}
        self.auth_session = None
        
        GAME_DIR.mkdir(parents=True, exist_ok=True)
        
        self.setup_styles()
        self.build_ui()
        self.apply_theme()
        self.load_versions()
        
        self.root.after(500, self.update_skin)

    def ui_call(self, fn, *args, **kwargs):
        """Schedule a UI update on the main thread with captured arguments."""
        self.root.after(0, lambda f=fn, a=args, kw=kwargs: f(*a, **kw))
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
    
    def apply_theme(self):
        t = self.current_theme
        self.root.configure(bg=t["bg_dark"])
        
        self.style.configure("Cat.TCombobox",
            fieldbackground=t["bg_input"],
            background=t["bg_input"],
            foreground=t["text_primary"],
            arrowcolor=t["text_primary"],
            borderwidth=0
        )
        self.style.map("Cat.TCombobox",
            fieldbackground=[("readonly", t["bg_input"])],
            selectbackground=[("readonly", t["accent"])],
            selectforeground=[("readonly", t["text_primary"])]
        )
        
        self.style.configure("Cat.Horizontal.TProgressbar",
            troughcolor=t["bg_darker"],
            background=t["accent_green"],
            thickness=6
        )
        
        if hasattr(self, 'header'):
            self.header.configure(bg=t["bg_header"])
            for child in self.header.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=t["bg_header"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=t["bg_header"])
                    for c in child.winfo_children():
                        if isinstance(c, (tk.Label, tk.Frame)):
                            c.configure(bg=t["bg_header"])
        
        if hasattr(self, 'sidebar'):
            self.sidebar.configure(bg=t["bg_darker"])
            self.update_nav_buttons()
            if hasattr(self, "install_mods_btn"):
                self.install_mods_btn.configure(
                    bg=t["accent_green"], fg="#ffffff",
                    activebackground=t["accent_green_hover"], activeforeground="#ffffff",
                )
        if hasattr(self, 'body'):
            self.body.configure(bg=t["bg_dark"])
        if hasattr(self, 'content_wrapper'):
            self.content_wrapper.configure(bg=t["bg_dark"])
        
        if hasattr(self, 'main_content'):
            self.update_frame_theme(self.main_content, t)
        
        if hasattr(self, 'bottom_bar'):
            self.bottom_bar.configure(bg=t["bg_darker"])
            self.update_frame_theme(self.bottom_bar, t, is_bottom=True)
        
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.update_bg(t["bg_header"])
        
        if hasattr(self, 'mods_page'):
            self.refresh_mods_page()
        
        if hasattr(self, 'play_button'):
            self.play_button.configure(
                bg=t["button_play"],
                fg=t["button_play_text"],
                activebackground=t["button_play_hover"],
                activeforeground=t["button_play_text"],
            )
    
    def update_frame_theme(self, frame, t, is_bottom=False):
        bg = t["bg_darker"] if is_bottom else t["bg_dark"]
        try:
            frame.configure(bg=bg)
        except:
            pass
        
        for child in frame.winfo_children():
            try:
                widget_class = child.winfo_class()
                
                if widget_class == "Frame":
                    if child.cget("bg") in [THEMES["dark"]["bg_panel"], THEMES["light"]["bg_panel"], "#1f2937", "#ffffff"]:
                        child.configure(bg=t["bg_panel"])
                    elif child.cget("bg") in [THEMES["dark"]["bg_input"], THEMES["light"]["bg_input"], "#374151", "#f9fafb"]:
                        child.configure(bg=t["bg_input"])
                    else:
                        child.configure(bg=bg)
                    self.update_frame_theme(child, t, is_bottom)
                    
                elif widget_class == "Label":
                    parent_bg = child.master.cget("bg") if hasattr(child.master, 'cget') else bg
                    child.configure(bg=parent_bg)
                    
                    current_fg = child.cget("fg")
                    if current_fg in ["#ffffff", "#eeeeee", "#111827", t["text_primary"]]:
                        child.configure(fg=t["text_primary"])
                    elif current_fg in ["#9ca3af", "#aaaaaa", "#4b5563", t["text_secondary"]]:
                        child.configure(fg=t["text_secondary"])
                    elif current_fg in ["#6b7280", "#666666", t["text_muted"]]:
                        child.configure(fg=t["text_muted"])
                    elif current_fg in ["#10b981", "#5cb85c", "#059669", t["accent_green"]]:
                        child.configure(fg=t["accent_green"])
                    elif current_fg in ["#f59e0b", "#d97706", t["accent_orange"]]:
                        child.configure(fg=t["accent_orange"])
                
                elif widget_class == "Entry":
                    child.configure(
                        bg=t["bg_input"],
                        fg=t["text_primary"],
                        insertbackground=t["text_primary"]
                    )
                
                elif widget_class == "Button":
                    if "PLAY" in child.cget("text"):
                        child.configure(
                            bg=t["button_play"],
                            fg=t["button_play_text"],
                            activebackground=t["button_play_hover"],
                            activeforeground=t["button_play_text"],
                        )
                    else:
                        child.configure(
                            bg=t["bg_panel"],
                            fg=t["text_secondary"],
                            activebackground=t["bg_input"]
                        )
                
                elif widget_class == "Scale":
                    child.configure(
                        bg=bg,
                        fg=t["text_primary"],
                        troughcolor=t["bg_input"],
                        activebackground=t["accent_green"],
                        highlightbackground=bg
                    )
                
                elif widget_class == "Checkbutton":
                    child.configure(
                        bg=bg,
                        fg=t["text_secondary"],
                        activebackground=bg,
                        selectcolor=t["bg_input"]
                    )
            except:
                pass
    
    def on_theme_change(self, mode):
        self.theme_mode = mode
        if mode == "system":
            theme_name = get_system_theme()
        else:
            theme_name = mode
        self.current_theme = THEMES[theme_name]
        self.apply_theme()
    
    def build_ui(self):
        t = self.current_theme
        
        self.header = tk.Frame(self.root, bg=t["bg_header"], height=36)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        logo_frame = tk.Frame(self.header, bg=t["bg_header"])
        logo_frame.pack(side="left", padx=14)
        
        tk.Label(
            logo_frame, text="CAT CLIENT", font=("Segoe UI", 12, "bold"),
            fg=t["accent_green"], bg=t["bg_header"]
        ).pack(side="left")
        
        tk.Label(
            logo_frame, text=BRAND_COPY, font=("Segoe UI", 9),
            fg=t["text_muted"], bg=t["bg_header"]
        ).pack(side="left", padx=(8, 0))
        
        header_right = tk.Frame(self.header, bg=t["bg_header"])
        header_right.pack(side="right", padx=8)
        
        self.theme_toggle = ThemeToggle(
            header_right, self.on_theme_change,
            initial="dark", bg=t["bg_header"]
        )
        self.theme_toggle.pack(side="left", padx=(0, 12))
        
        for icon in ["─", "□", "✕"]:
            btn = tk.Label(
                header_right, text=icon, font=("Segoe UI", 11),
                fg=t["text_secondary"], bg=t["bg_header"],
                padx=8, cursor="hand2"
            )
            btn.pack(side="left")
            if icon == "✕":
                btn.bind("<Button-1>", lambda e: self.root.quit())
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#c0392b", fg="#ffffff"))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=t["bg_header"], fg=t["text_secondary"]))
        
        self.body = tk.Frame(self.root, bg=t["bg_dark"])
        self.body.pack(fill="both", expand=True)
        
        self.sidebar = tk.Frame(self.body, bg=t["bg_darker"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(
            self.sidebar, text="TLauncher-style", font=("Segoe UI", 8),
            fg=t["text_muted"], bg=t["bg_darker"]
        ).pack(anchor="w", padx=14, pady=(12, 4))
        
        skin_frame = tk.Frame(self.sidebar, bg=t["bg_panel"], width=170, height=150)
        skin_frame.pack(padx=14, pady=(4, 8))
        skin_frame.pack_propagate(False)
        
        self.skin_label = tk.Label(
            skin_frame, text="🐱", font=("Segoe UI", 40),
            fg=t["text_secondary"], bg=t["bg_panel"]
        )
        self.skin_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.username_display = tk.Label(
            self.sidebar, textvariable=self.username, font=("Segoe UI", 10, "bold"),
            fg=t["text_primary"], bg=t["bg_darker"]
        )
        self.username_display.pack(padx=14)
        
        self.account_indicator = tk.Label(
            self.sidebar, text="Cat Client Account", font=("Segoe UI", 8),
            fg=t["accent_green"], bg=t["bg_darker"]
        )
        self.account_indicator.pack(padx=14, pady=(2, 14))
        
        tabs = ["PLAY", "MODS", "SKINS", "SETTINGS", "ABOUT"]
        self.tab_labels = []
        self.main_menu_buttons = []
        
        for tab in tabs:
            btn = tk.Button(
                self.sidebar, text=f"  {tab}", font=("Segoe UI", 11),
                fg=t["text_secondary"], bg=t["bg_darker"],
                activeforeground=t["text_primary"],
                activebackground=t["sidebar_active"],
                relief="flat", cursor="hand2", anchor="w",
                padx=12, pady=10, bd=0,
                command=lambda name=tab: self.switch_tab(name),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.tab_buttons[tab] = btn
            self.tab_labels.append(btn)
            self.main_menu_buttons.append((tab, btn))
        
        self.install_mods_btn = tk.Button(
            self.sidebar, text="INSTALL ALL MODS", font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=t["accent_green"],
            activeforeground="#ffffff", activebackground=t["accent_green_hover"],
            relief="flat", cursor="hand2", padx=10, pady=12, bd=0,
            command=self.install_all_mods,
        )
        self.install_mods_btn.pack(side="bottom", fill="x", padx=14, pady=14)
        
        self.content_wrapper = tk.Frame(self.body, bg=t["bg_dark"])
        self.content_wrapper.pack(side="left", fill="both", expand=True)
        
        self.main_content = tk.Frame(self.content_wrapper, bg=t["bg_dark"])
        self.main_content.pack(fill="both", expand=True, padx=22, pady=16)
        
        self.play_page = tk.Frame(self.main_content, bg=t["bg_dark"])
        self.play_page.pack(fill="both", expand=True)
        
        settings_card = tk.Frame(self.play_page, bg=t["bg_panel"])
        settings_card.pack(fill="both", expand=True, padx=4, pady=4)
        
        inner = tk.Frame(settings_card, bg=t["bg_panel"])
        inner.pack(fill="both", expand=True, padx=22, pady=20)
        
        tk.Label(
            inner, text="Launch Settings", font=("Segoe UI", 15, "bold"),
            fg=t["text_primary"], bg=t["bg_panel"]
        ).pack(anchor="w", pady=(0, 16))
        
        account_frame = tk.Frame(inner, bg=t["bg_panel"])
        account_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            account_frame, text="Account type:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_panel"]
        ).pack(side="left", padx=(0, 10))
        
        account_types = [OFFLINE_ACCOUNT, MICROSOFT_ACCOUNT, MOJANG_ACCOUNT]
        self.account_combo = ttk.Combobox(
            account_frame, textvariable=self.account_type,
            values=account_types, state="readonly", width=28,
            style="Cat.TCombobox", font=("Segoe UI", 10)
        )
        self.account_combo.pack(side="left")
        self.account_combo.bind("<<ComboboxSelected>>", self.on_account_type_change)

        self.sign_in_btn = tk.Button(
            account_frame, text="Sign In", font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg=t["accent_green"],
            activeforeground="#ffffff", activebackground=t["accent_green_hover"],
            relief="flat", cursor="hand2", padx=12, pady=3,
            command=self.open_account_login_prompt,
        )
        
        self.cracked_label = tk.Label(
            account_frame, text="✓ OFFLINE MODE", font=("Segoe UI", 9, "bold"),
            fg=t["accent_green"], bg=t["bg_panel"]
        )
        self.cracked_label.pack(side="left", padx=(15, 0))
        
        username_frame = tk.Frame(inner, bg=t["bg_panel"])
        username_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            username_frame, text="Username:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_panel"]
        ).pack(side="left", padx=(0, 10))
        
        self.username_entry = tk.Entry(
            username_frame, textvariable=self.username, font=("Segoe UI", 11),
            fg=t["text_primary"], bg=t["bg_input"],
            insertbackground=t["text_primary"],
            relief="flat", width=32
        )
        self.username_entry.pack(side="left", ipady=7, padx=2)
        self.username_entry.bind("<KeyRelease>", self.on_username_change)
        
        version_frame = tk.Frame(inner, bg=t["bg_panel"])
        version_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            version_frame, text="Version:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_panel"]
        ).pack(side="left", padx=(0, 10))
        
        version_container = tk.Frame(version_frame, bg=t["bg_input"])
        version_container.pack(side="left")
        
        self.version_combo = ttk.Combobox(
            version_container, textvariable=self.version,
            state="readonly", width=34, style="Cat.TCombobox",
            font=("Segoe UI", 10)
        )
        self.version_combo.pack(side="left", ipady=5)
        
        refresh_btn = tk.Label(
            version_container, text="↻", font=("Segoe UI", 14),
            fg=t["text_secondary"], bg=t["bg_input"],
            padx=10, cursor="hand2"
        )
        refresh_btn.pack(side="left")
        refresh_btn.bind("<Button-1>", lambda e: self.load_versions())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg=t["text_primary"]))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg=t["text_secondary"]))
        
        ram_frame = tk.Frame(inner, bg=t["bg_panel"])
        ram_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            ram_frame, text="RAM:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_panel"]
        ).pack(side="left", padx=(0, 10))
        
        self.ram_display = tk.Label(
            ram_frame, text="4096 MB", font=("Segoe UI", 10, "bold"),
            fg=t["accent_green"], bg=t["bg_panel"], width=10
        )
        self.ram_display.pack(side="left")
        
        ram_slider = tk.Scale(
            ram_frame, variable=self.ram, from_=1, to=16,
            orient="horizontal", length=340,
            bg=t["bg_panel"], fg=t["text_primary"],
            highlightthickness=0, troughcolor=t["bg_input"],
            activebackground=t["accent_green"],
            sliderrelief="flat", sliderlength=18, width=12,
            showvalue=False, command=self.on_ram_change
        )
        ram_slider.pack(side="left", padx=(10, 0))
        
        options_frame = tk.Frame(inner, bg=t["bg_panel"])
        options_frame.pack(fill="x", pady=(8, 0))
        
        self.fullscreen_var = tk.BooleanVar(value=False)
        self.download_assets_var = tk.BooleanVar(value=True)
        self.fps_boost_var = tk.BooleanVar(value=True)
        
        for text, var in [
            ("Fullscreen", self.fullscreen_var),
            ("Download All Assets", self.download_assets_var),
            ("ULTRAMAX FPS + Ping Pack", self.fps_boost_var),
        ]:
            cb_frame = tk.Frame(options_frame, bg=t["bg_panel"])
            cb_frame.pack(side="left", padx=(0, 22))
            
            cb = tk.Checkbutton(
                cb_frame, text=text, variable=var,
                font=("Segoe UI", 10), fg=t["text_secondary"],
                bg=t["bg_panel"], activebackground=t["bg_panel"],
                activeforeground=t["text_primary"],
                selectcolor=t["bg_input"], cursor="hand2"
            )
            cb.pack()
        
        self.build_mods_page(t)
        self.update_nav_buttons()
        
        self.bottom_bar = tk.Frame(self.root, bg=t["bg_darker"], height=72)
        self.bottom_bar.pack(side="bottom", fill="x")
        self.bottom_bar.pack_propagate(False)
        
        status_frame = tk.Frame(self.bottom_bar, bg=t["bg_darker"])
        status_frame.pack(side="left", padx=20, pady=10)
        
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_text, font=("Segoe UI", 9),
            fg=t["text_secondary"], bg=t["bg_darker"]
        )
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(
            status_frame, mode="determinate", length=420,
            style="Cat.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(anchor="w", pady=(5, 0))
        
        play_container = tk.Frame(self.bottom_bar, bg=t["bg_darker"])
        play_container.pack(side="right", padx=20, pady=12)
        
        self.play_button = tk.Button(
            play_container, text="PLAY", font=("Segoe UI", 16, "bold"),
            fg=t["button_play_text"], bg=t["button_play"],
            activeforeground=t["button_play_text"],
            activebackground=t["button_play_hover"],
            relief="flat", cursor="hand2", padx=48, pady=10,
            command=self.play
        )
        self.play_button.pack()
        
        self.play_button.bind("<Enter>", lambda e: self.play_button.config(bg=self.current_theme["button_play_hover"]))
        self.play_button.bind("<Leave>", lambda e: self.play_button.config(bg=self.current_theme["button_play"]))
    
    def update_nav_buttons(self):
        t = self.current_theme
        for tab, btn in self.tab_buttons.items():
            if tab == self.active_tab:
                btn.config(
                    bg=t["sidebar_active"], fg=t["accent_green"],
                    activebackground=t["sidebar_active"], activeforeground=t["accent_green"],
                    font=("Segoe UI", 11, "bold"),
                )
            else:
                btn.config(
                    bg=t["bg_darker"], fg=t["text_secondary"],
                    activebackground=t["sidebar_active"], activeforeground=t["text_primary"],
                    font=("Segoe UI", 11),
                )
    
    def update_main_menu_buttons(self):
        self.update_nav_buttons()
    
    def build_mods_page(self, t):
        self.mods_page = tk.Frame(self.main_content, bg=t["bg_dark"])
        
        header = tk.Frame(self.mods_page, bg=t["bg_dark"])
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            header, text="MODS", font=("Segoe UI", 16, "bold"),
            fg=t["text_primary"], bg=t["bg_dark"]
        ).pack(side="left")
        
        self.mods_play_btn = tk.Button(
            header, text="← PLAY", font=("Segoe UI", 9, "bold"),
            fg=t["text_secondary"], bg=t["bg_input"],
            activeforeground=t["text_primary"],
            activebackground=t["bg_panel"],
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=lambda: self.switch_tab("PLAY"),
        )
        self.mods_play_btn.pack(side="right", padx=(8, 0))
        
        self.mods_install_btn = tk.Button(
            header, text="INSTALL ALL MODS", font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg=t["accent_green"],
            activeforeground="#ffffff",
            activebackground=t["accent_green_hover"],
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self.install_all_mods,
        )
        self.mods_install_btn.pack(side="right", padx=(8, 0))
        
        self.mods_refresh_btn = tk.Button(
            header, text="Refresh", font=("Segoe UI", 9),
            fg=t["text_secondary"], bg=t["bg_panel"],
            activeforeground=t["text_primary"], activebackground=t["bg_input"],
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self.refresh_mods_page
        )
        self.mods_refresh_btn.pack(side="right")
        
        self.mods_summary = tk.Label(
            self.mods_page, text="", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_dark"], anchor="w"
        )
        self.mods_summary.pack(fill="x", pady=(0, 8))
        
        list_shell = tk.Frame(self.mods_page, bg=t["bg_panel"])
        list_shell.pack(fill="both", expand=True)
        
        self.mods_canvas = tk.Canvas(
            list_shell, bg=t["bg_panel"], highlightthickness=0, bd=0
        )
        scrollbar = tk.Scrollbar(list_shell, orient="vertical", command=self.mods_canvas.yview)
        self.mods_list_inner = tk.Frame(self.mods_canvas, bg=t["bg_panel"])
        
        self.mods_list_inner.bind(
            "<Configure>",
            lambda e: self.mods_canvas.configure(scrollregion=self.mods_canvas.bbox("all"))
        )
        self.mods_canvas.create_window((0, 0), window=self.mods_list_inner, anchor="nw")
        self.mods_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.mods_canvas.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y")
        
        self.mods_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.mods_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            if self.active_tab == "MODS" else None
        )
        
        self.refresh_mods_page()
    
    def get_mod_entries(self):
        mods_dir = GAME_DIR / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)
        jar_files = list(mods_dir.glob("*.jar"))
        managed = []
        marker = mods_dir / ".catclient-fps.json"
        if marker.exists():
            try:
                with open(marker, encoding="utf-8") as f:
                    managed = json.load(f)
            except Exception:
                pass
        
        def slug_match(slug, filename):
            key = slug.replace("-", "").lower()
            name = filename.lower().replace("-", "").replace("_", "")
            return key in name
        
        pack_mods = []
        matched_files = set()
        for slug, label in FPS_MODS:
            match = None
            for jar in jar_files:
                if slug_match(slug, jar.name):
                    match = jar.name
                    matched_files.add(jar.name)
                    break
            if not match:
                for name in managed:
                    if slug_match(slug, name) and (mods_dir / name).exists():
                        match = name
                        matched_files.add(name)
                        break
            pack_mods.append({
                "label": label,
                "slug": slug,
                "filename": match or "—",
                "installed": bool(match),
                "pack": True,
            })
        
        other_mods = []
        for jar in sorted(jar_files, key=lambda p: p.name.lower()):
            if jar.name not in matched_files:
                other_mods.append({
                    "label": jar.stem,
                    "slug": jar.stem,
                    "filename": jar.name,
                    "installed": True,
                    "pack": False,
                })
        return pack_mods, other_mods
    
    def refresh_mods_page(self):
        if not hasattr(self, "mods_list_inner"):
            return
        t = self.current_theme
        
        for child in self.mods_list_inner.winfo_children():
            child.destroy()
        
        pack_mods, other_mods = self.get_mod_entries()
        installed_pack = sum(1 for m in pack_mods if m["installed"])
        fps_on = "ON" if self.fps_boost_var.get() else "OFF"
        self.mods_summary.config(
            text=f"ULTRAMAX Pack: {fps_on}  |  {installed_pack}/{len(pack_mods)} installed  |  Other: {len(other_mods)}"
        )
        
        def add_section(title):
            tk.Label(
                self.mods_list_inner, text=title, font=("Segoe UI", 11, "bold"),
                fg=t["accent"], bg=t["bg_panel"], anchor="w"
            ).pack(fill="x", pady=(10, 6), padx=4)
        
        def add_row(mod):
            row = tk.Frame(self.mods_list_inner, bg=t["bg_input"])
            row.pack(fill="x", pady=3, padx=4)
            status = "✓ Installed" if mod["installed"] else "Not installed"
            status_color = t["accent_green"] if mod["installed"] else t["text_muted"]
            tk.Label(
                row, text=mod["label"], font=("Segoe UI", 10, "bold"),
                fg=t["text_primary"], bg=t["bg_input"], width=22, anchor="w"
            ).pack(side="left", padx=10, pady=8)
            tk.Label(
                row, text=mod["filename"], font=("Segoe UI", 9),
                fg=t["text_secondary"], bg=t["bg_input"], anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(
                row, text=status, font=("Segoe UI", 9, "bold"),
                fg=status_color, bg=t["bg_input"], width=14, anchor="e"
            ).pack(side="right", padx=10)
        
        add_section("ULTRAMAX FPS + PING PACK")
        for mod in pack_mods:
            add_row(mod)
        
        add_section("OTHER MOD FILES")
        if other_mods:
            for mod in other_mods:
                add_row(mod)
        else:
            tk.Label(
                self.mods_list_inner, text="No other mods in mods folder",
                font=("Segoe UI", 9), fg=t["text_muted"], bg=t["bg_panel"], anchor="w"
            ).pack(fill="x", padx=8, pady=4)
        
        if hasattr(self, "mods_refresh_btn"):
            self.mods_refresh_btn.configure(
                fg=t["text_secondary"], bg=t["bg_panel"],
                activeforeground=t["text_primary"], activebackground=t["bg_input"]
            )
        if hasattr(self, "mods_play_btn"):
            self.mods_play_btn.configure(
                fg=t["text_secondary"], bg=t["bg_input"],
                activeforeground=t["text_primary"], activebackground=t["bg_panel"],
            )
        if hasattr(self, "mods_install_btn"):
            self.mods_install_btn.configure(
                fg="#ffffff", bg=t["accent_green"],
                activeforeground="#ffffff", activebackground=t["accent_green_hover"],
            )
        if hasattr(self, "mods_summary"):
            self.mods_summary.configure(fg=t["text_secondary"], bg=t["bg_dark"])
        if hasattr(self, "mods_canvas"):
            self.mods_canvas.configure(bg=t["bg_panel"])
            self.mods_list_inner.configure(bg=t["bg_panel"])
    
    def switch_tab(self, tab_name):
        playable = {"PLAY", "MODS"}
        if tab_name not in playable:
            messagebox.showinfo(APP_NAME, f"{tab_name} — coming soon")
            return
        
        self.active_tab = tab_name
        self.update_nav_buttons()
        self.update_main_menu_buttons()
        
        if tab_name == "PLAY":
            self.mods_page.pack_forget()
            self.play_page.pack(fill="both", expand=True)
        else:
            self.play_page.pack_forget()
            self.mods_page.pack(fill="both", expand=True)
            self.refresh_mods_page()
    
    def install_all_mods(self):
        if self.game_process and self.game_process.poll() is None:
            messagebox.showwarning(APP_NAME, "Close Minecraft before installing mods.")
            return
        
        for btn_name in ("install_mods_btn", "mods_install_btn", "play_button"):
            btn = getattr(self, btn_name, None)
            if btn:
                btn.config(state="disabled")
        self.progress_bar.config(value=0)
        
        def work():
            try:
                game_version = get_latest_release_id()
                status = lambda s: self.ui_call(self.status_text.set, s)
                status(f"Installing all mods for {game_version}...")
                self.fps_boost_var.set(True)
                self.install_fps_mods(game_version, status, progress_cb=lambda p: self.ui_call(self.progress_bar.config, value=p))
                self.install_fabric(game_version, status)
                self.ui_call(self.progress_bar.config, value=100)
                self.ui_call(self.refresh_mods_page)
                self.ui_call(self.status_text.set, "All mods installed!")
                self.ui_call(
                    messagebox.showinfo, APP_NAME,
                    f"Installed ULTRAMAX pack + Fabric for Minecraft {game_version}."
                )
            except Exception as exc:
                self.ui_call(self.status_text.set, "Mod install failed")
                self.ui_call(messagebox.showerror, APP_NAME, f"Mod install failed:\n{exc}")
            finally:
                def enable():
                    for btn_name in ("install_mods_btn", "mods_install_btn", "play_button"):
                        btn = getattr(self, btn_name, None)
                        if btn:
                            btn.config(state="normal")
                self.ui_call(enable)
        
        threading.Thread(target=work, daemon=True).start()
    
    # ============== EVENT HANDLERS ==============
    def open_account_login_prompt(self):
        acc_type = self.account_type.get()
        if acc_type == MICROSOFT_ACCOUNT:
            self.prompt_microsoft_login()
        elif acc_type == MOJANG_ACCOUNT:
            self.prompt_mojang_login()

    def prompt_microsoft_login(self):
        return self._show_account_login("microsoft")

    def prompt_mojang_login(self):
        return self._show_account_login("mojang")

    def _show_account_login(self, account_kind):
        expected = MICROSOFT_ACCOUNT if account_kind == "microsoft" else MOJANG_ACCOUNT
        if self.account_type.get() != expected:
            self.account_type.set(expected)

        dialog = AccountLoginDialog(
            self.root,
            self.current_theme,
            account_kind,
            initial_username=self.username.get().strip(),
        )
        self.root.wait_window(dialog)
        if dialog.result:
            self.auth_session = dialog.result
            self.username.set(dialog.result["display_name"])
            self.update_account_ui()
            self.update_skin()
            return True

        if not self.auth_session or self.auth_session.get("type") != account_kind:
            self.account_type.set(OFFLINE_ACCOUNT)
            self.update_account_ui()
        return False

    def clear_auth_session(self):
        self.auth_session = None

    def update_account_ui(self):
        t = self.current_theme
        acc_type = self.account_type.get()

        if acc_type == OFFLINE_ACCOUNT:
            self.cracked_label.config(text="✓ OFFLINE MODE", fg=t["accent_green"])
            self.account_indicator.config(text="Cat Client Account", fg=t["accent_green"], bg=t["bg_darker"])
            self.username_entry.config(state="normal")
            self.sign_in_btn.pack_forget()
            return

        kind = "microsoft" if acc_type == MICROSOFT_ACCOUNT else "mojang"
        signed_in = self.auth_session and self.auth_session.get("type") == kind

        if signed_in:
            name = self.auth_session["display_name"]
            email = self.auth_session["email"]
            self.cracked_label.config(text="✓ SIGNED IN", fg=t["accent_green"])
            self.account_indicator.config(
                text=f"{name} ({email})",
                fg=t["accent_green"], bg=t["bg_darker"],
            )
            self.username_entry.config(state="disabled")
            self.sign_in_btn.config(text="Switch Account")
        else:
            self.cracked_label.config(text="⚠ SIGN IN REQUIRED", fg=t["accent_orange"])
            self.account_indicator.config(text="Not Logged In", fg=t["accent_orange"], bg=t["bg_darker"])
            self.username_entry.config(state="disabled")
            self.sign_in_btn.config(text="Sign In")

        self.sign_in_btn.pack(side="left", padx=(10, 0))

    def on_account_type_change(self, event=None):
        acc_type = self.account_type.get()

        if acc_type == OFFLINE_ACCOUNT:
            self.clear_auth_session()
            self.update_account_ui()
        elif acc_type == MICROSOFT_ACCOUNT:
            if not (self.auth_session and self.auth_session.get("type") == "microsoft"):
                self.prompt_microsoft_login()
            else:
                self.update_account_ui()
        else:
            if not (self.auth_session and self.auth_session.get("type") == "mojang"):
                self.prompt_mojang_login()
            else:
                self.update_account_ui()
    
    def on_username_change(self, event=None):
        if hasattr(self, '_skin_timer'):
            self.root.after_cancel(self._skin_timer)
        self._skin_timer = self.root.after(600, self.update_skin)
    
    def on_ram_change(self, value):
        mb = int(float(value)) * 1024
        self.ram_display.config(text=f"{mb} MB")
    
    def update_skin(self):
        username = self.username.get().strip()
        if not username:
            self.skin_label.config(text="🐱", image="", font=("Segoe UI", 48))
            return
        
        def load():
            short = username[:8]
            try:
                url = f"{SKIN_SERVER}/head/{username}/150.png"
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                    data = resp.read()
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(io.BytesIO(data))
                    photo = ImageTk.PhotoImage(img)
                    self.root.after(0, lambda p=photo: self._apply_skin_photo(p))
                except ImportError:
                    self.root.after(0, lambda t=f"🐱\n{short}": self._apply_skin_fallback(t))
            except Exception:
                self.root.after(0, lambda t=f"🐱\n{short}": self._apply_skin_fallback(t))
        
        threading.Thread(target=load, daemon=True).start()

    def _apply_skin_photo(self, photo):
        self.skin_photo = photo
        self.skin_label.config(image=self.skin_photo, text="")

    def _apply_skin_fallback(self, text):
        self.skin_label.config(image="", text=text, font=("Segoe UI", 24))
    
    def load_versions(self):
        self.status_text.set("Loading versions... 🐱")
        
        def load():
            try:
                data = fetch_version_manifest(timeout=10)
                versions = []
                for v in data["versions"]:
                    if v["type"] == "release":
                        versions.append(f"{v['id']} (release)")
                    elif v["type"] == "snapshot" and len(versions) < 60:
                        versions.append(f"{v['id']} (snapshot)")
                    if len(versions) >= 80:
                        break
                self.root.after(0, lambda v=versions: self.set_versions(v))
            except Exception:
                fallback = ["1.21.4 (release)", "1.20.1 (release)", "1.19.4 (release)", "1.18.2 (release)"]
                self.root.after(0, lambda v=fallback: self.set_versions(v))
        
        threading.Thread(target=load, daemon=True).start()
    
    def set_versions(self, versions):
        self.version_combo["values"] = versions
        if versions:
            self.version.set(versions[0])
        self.status_text.set("Ready to play 🐱")
    
    # ============== DOWNLOAD & LAUNCH ==============
    def download_file(self, url, dest_path, expected_hash=None, expected_size=None):
        return download_file_fast(url, dest_path, expected_hash, expected_size, timeout=60)

    def _download_lib_task(self, task):
        url, dest_path, sha1, size = task
        return download_file_fast(url, dest_path, sha1, size, timeout=60)

    def download_libraries(self, version_info, status_cb=None):
        libs_dir = GAME_DIR / "libraries"
        libs_dir.mkdir(parents=True, exist_ok=True)
        os_name = get_os_name()
        download_tasks = []
        native_paths = []

        for lib in version_info.get("libraries", []):
            if "rules" in lib and not check_rules(lib["rules"]):
                continue
            task = library_download_task(lib, libs_dir)
            if task:
                url, path, sha1, size = task
                if not file_is_valid(path, sha1, size):
                    download_tasks.append(task)

            if "natives" in lib and "downloads" in lib:
                native_key = lib["natives"].get(os_name, "")
                if "${arch}" in native_key:
                    bits = "64" if get_arch() in ("x64", "arm64") else "32"
                    native_key = native_key.replace("${arch}", bits)
                if native_key and "classifiers" in lib["downloads"]:
                    native_info = lib["downloads"]["classifiers"].get(native_key)
                    if native_info:
                        native_path = libs_dir / native_info["path"]
                        if not file_is_valid(native_path, native_info.get("sha1"), native_info.get("size")):
                            download_tasks.append((
                                native_info["url"],
                                native_path,
                                native_info.get("sha1"),
                                native_info.get("size"),
                            ))
                        native_paths.append(native_path)

        if download_tasks:
            if status_cb:
                status_cb(f"Downloading {len(download_tasks)} libraries...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=LIB_WORKERS) as executor:
                results = list(executor.map(self._download_lib_task, download_tasks))
            if not all(results):
                raise RuntimeError("Some libraries failed to download")

        return native_paths

    def build_classpath(self, resolved_info, client_id):
        libs_dir = GAME_DIR / "libraries"
        classpath_parts = []
        for lib in resolved_info.get("libraries", []):
            if "rules" in lib and not check_rules(lib["rules"]):
                continue
            task = library_download_task(lib, libs_dir)
            if not task:
                continue
            lib_path = task[1]
            if lib_path.exists():
                classpath_parts.append(str(lib_path))
        jar_path = GAME_DIR / "versions" / client_id / f"{client_id}.jar"
        if jar_path.exists():
            classpath_parts.append(str(jar_path))
        return CLASSPATH_SEP.join(classpath_parts)

    def install_fabric(self, game_version, status_cb=None):
        if status_cb:
            status_cb(f"Installing Fabric for {game_version}...")
        loaders = fetch_json(f"{FABRIC_META}/versions/loader/{game_version}", timeout=15)
        if not loaders:
            raise RuntimeError(f"No Fabric loader for Minecraft {game_version}")
        stable = next((x for x in loaders if x["loader"].get("stable")), loaders[0])
        loader_version = stable["loader"]["version"]
        profile = fetch_json(
            f"{FABRIC_META}/versions/loader/{game_version}/{loader_version}/profile/json",
            timeout=15,
        )
        fabric_id = profile["id"]
        fabric_dir = GAME_DIR / "versions" / fabric_id
        fabric_dir.mkdir(parents=True, exist_ok=True)
        with open(fabric_dir / f"{fabric_id}.json", "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        self.download_libraries(profile, status_cb)
        return profile, fabric_id

    def _install_single_fps_mod(self, slug, label, game_version, mods_dir):
        try:
            versions = fetch_modrinth_versions(slug, game_version)
            if not versions:
                return None, label
            release = next((v for v in versions if v.get("version_type") == "release"), versions[0])
            primary = next((f for f in release["files"] if f.get("primary")), release["files"][0])
            dest = mods_dir / primary["filename"]
            sha1 = primary.get("hashes", {}).get("sha1")
            if download_file_fast(primary["url"], dest, sha1, primary.get("size"), timeout=90):
                return primary["filename"], None
            return None, label
        except Exception:
            return None, label

    def install_fps_mods(self, game_version, status_cb=None, progress_cb=None):
        mods_dir = GAME_DIR / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)
        marker = mods_dir / ".catclient-fps.json"
        if marker.exists():
            try:
                with open(marker, encoding="utf-8") as f:
                    old_files = json.load(f)
                for name in old_files:
                    (mods_dir / name).unlink(missing_ok=True)
            except Exception:
                pass

        installed = []
        failed = []
        total = len(FPS_MODS)
        done = 0
        lock = threading.Lock()

        if status_cb:
            status_cb(f"Installing ULTRAMAX pack ({total} mods) for {game_version}...")

        def worker(entry):
            nonlocal done
            slug, label = entry
            filename, fail_label = self._install_single_fps_mod(slug, label, game_version, mods_dir)
            with lock:
                done += 1
                if filename:
                    installed.append(filename)
                elif fail_label:
                    failed.append(fail_label)
                if progress_cb:
                    progress_cb(int((done / total) * 100))
                if status_cb and done % 3 == 0:
                    status_cb(f"ULTRAMAX mods {done}/{total}...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MOD_WORKERS) as executor:
            list(executor.map(worker, FPS_MODS))

        with open(marker, "w", encoding="utf-8") as f:
            json.dump(installed, f, indent=2)

        if not installed:
            raise RuntimeError("No ULTRAMAX mods could be installed for this version")
        if status_cb:
            msg = f"ULTRAMAX: {len(installed)} mods installed"
            if failed:
                msg += f" ({len(failed)} skipped)"
            status_cb(msg)
        if progress_cb:
            progress_cb(100)
        return installed

    def extract_natives(self, native_path, natives_dir):
        try:
            with zipfile.ZipFile(native_path, 'r') as z:
                for f in z.namelist():
                    if f.startswith("META-INF/"):
                        continue
                    if f.endswith(('.so', '.dll', '.dylib', '.jnilib')):
                        target = natives_dir / Path(f).name
                        with z.open(f) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        if sys.platform != "win32":
                            os.chmod(target, 0o755)
        except (zipfile.BadZipFile, OSError) as e:
            print(f"Native extract failed: {e}")
    
    def download_version(self, version_id, progress_cb=None, status_cb=None):
        actual_id = version_id.split(" (")[0] if " (" in version_id else version_id
        
        if status_cb:
            status_cb(f"Fetching {actual_id}... 🐱")
        
        manifest = fetch_version_manifest(timeout=15)
        
        version_url = None
        for v in manifest["versions"]:
            if v["id"] == actual_id:
                version_url = v["url"]
                break
        
        if not version_url:
            raise ValueError(f"Version {actual_id} not found")
        
        version_info = fetch_json(version_url, timeout=15)
        
        version_dir = GAME_DIR / "versions" / actual_id
        version_dir.mkdir(parents=True, exist_ok=True)
        natives_dir = version_dir / "natives"
        natives_dir.mkdir(parents=True, exist_ok=True)
        libs_dir = GAME_DIR / "libraries"
        libs_dir.mkdir(parents=True, exist_ok=True)
        
        version_json_path = version_dir / f"{actual_id}.json"
        with open(version_json_path, 'w') as f:
            json.dump(version_info, f, indent=2)
        
        jar_path = version_dir / f"{actual_id}.jar"
        client = version_info["downloads"]["client"]
        client_url = client["url"]
        client_sha1 = client.get("sha1")
        client_size = client.get("size")
        if not file_is_valid(jar_path, client_sha1, client_size):
            if status_cb:
                status_cb(f"Downloading {actual_id}.jar... 🐱")
            if not self.download_file(client_url, jar_path, client_sha1, client_size):
                raise RuntimeError(f"Failed to download {actual_id}.jar")
        
        native_paths = self.download_libraries(version_info, status_cb)
        
        natives_dir = version_dir / "natives"
        for native_path in native_paths:
            if native_path.exists():
                self.extract_natives(native_path, natives_dir)
        
        if self.download_assets_var.get():
            asset_index = version_info["assetIndex"]
            asset_index_id = asset_index["id"]
            asset_index_url = asset_index["url"]
            
            if status_cb:
                status_cb(f"Downloading assets... 🐱")
            
            asset_downloader = AssetDownloader(
                GAME_DIR,
                progress_callback=progress_cb,
                status_callback=status_cb
            )
            
            asset_downloader.download_all_assets(asset_index_id, asset_index_url)
        else:
            asset_index = version_info["assetIndex"]
            index_path = GAME_DIR / "assets" / "indexes" / f"{asset_index['id']}.json"
            if not index_path.exists():
                self.download_file(asset_index["url"], index_path, asset_index.get("sha1"))
        
        if status_cb:
            status_cb(f"{actual_id} ready! 🐱")
        
        return version_info, actual_id

    def build_launch_args(self, version_info, actual_id, username, ram_mb, natives_dir, classpath):
        main_class = version_info.get("mainClass", "net.minecraft.client.main.Main")
        offline_uuid = generate_offline_uuid(username)
        user_type = "legacy"
        if self.auth_session:
            user_type = "msa" if self.auth_session.get("type") == "microsoft" else "mojang"
        variables = {
            "natives_directory": str(natives_dir.resolve()),
            "launcher_name": "CatClient",
            "launcher_version": "0.1",
            "classpath": classpath,
            "auth_player_name": username,
            "version_name": actual_id,
            "game_directory": str(GAME_DIR.resolve()),
            "assets_root": str((GAME_DIR / "assets").resolve()),
            "assets_index_name": version_info["assetIndex"]["id"],
            "auth_uuid": offline_uuid,
            "auth_access_token": "0",
            "clientid": "",
            "auth_xuid": "",
            "user_type": user_type,
            "version_type": version_info.get("type", "release"),
        }
        features = {
            "is_demo_user": False,
            "has_custom_resolution": False,
            "has_quick_plays_support": False,
            "is_quick_play_singleplayer": False,
            "is_quick_play_multiplayer": False,
            "is_quick_play_realms": False,
        }
        memory = [self.java_bin, f"-Xmx{ram_mb}M", "-Xms512M"]

        if "arguments" in version_info:
            jvm_args = expand_arguments(version_info["arguments"].get("jvm", []), variables, features)
            game_args = expand_arguments(version_info["arguments"].get("game", []), variables, features)
            args = memory + jvm_args + [main_class] + game_args
        else:
            args = memory + [
                f"-Djava.library.path={natives_dir.resolve()}",
                "-Dminecraft.launcher.brand=CatClient",
                "-Dminecraft.launcher.version=0.1",
                "-cp", classpath,
                main_class,
                "--username", username,
                "--version", actual_id,
                "--gameDir", str(GAME_DIR.resolve()),
                "--assetsDir", str((GAME_DIR / "assets").resolve()),
                "--assetIndex", version_info["assetIndex"]["id"],
                "--uuid", offline_uuid,
                "--accessToken", "0",
                "--userType", user_type,
                "--versionType", version_info.get("type", "release"),
            ]

        if self.fullscreen_var.get() and "--fullscreen" not in args:
            args.append("--fullscreen")
        return args

    def _monitor_game(self, process, actual_id, log_handle):
        try:
            exit_code = process.wait()
            if exit_code == 0:
                status = "Game closed"
            else:
                status = f"Game exited (code {exit_code}) — see logs/catclient-latest.log"
            self.ui_call(self.status_text.set, status)
        except Exception:
            self.ui_call(self.status_text.set, "Game monitor stopped")
        finally:
            if log_handle:
                try:
                    log_handle.close()
                except Exception:
                    pass
            self._log_handle = None
            self.game_process = None
            self.ui_call(self.play_button.config, state="normal", text="PLAY")
    
    def play(self):
        acc_type = self.account_type.get()
        if acc_type == MICROSOFT_ACCOUNT:
            if not (self.auth_session and self.auth_session.get("type") == "microsoft"):
                if not self.prompt_microsoft_login():
                    return
            username = self.auth_session["display_name"]
        elif acc_type == MOJANG_ACCOUNT:
            if not (self.auth_session and self.auth_session.get("type") == "mojang"):
                if not self.prompt_mojang_login():
                    return
            username = self.auth_session["display_name"]
        else:
            username = self.username.get().strip()
            if not username:
                messagebox.showwarning(APP_NAME, "Enter a username!")
                return
            if not all(c.isalnum() or c == "_" for c in username):
                messagebox.showwarning(APP_NAME, "Invalid username! Use only letters, numbers, underscore.")
                return
            if len(username) < 3 or len(username) > 16:
                messagebox.showwarning(APP_NAME, "Username must be 3-16 characters!")
                return
        
        version = self.version.get()
        if not version:
            messagebox.showwarning(APP_NAME, "Select a version!")
            return

        if self.game_process and self.game_process.poll() is None:
            messagebox.showinfo(APP_NAME, "Minecraft is already running.")
            return
        
        self.play_button.config(state="disabled", text="LAUNCHING...")
        self.progress_bar.config(value=0)
        
        def launch():
            try:
                progress_cb = lambda p: self.ui_call(self.progress_bar.config, value=p)
                status_cb = lambda s: self.ui_call(self.status_text.set, s)

                if self.fps_boost_var.get():
                    game_version = get_latest_release_id()
                    status_cb(f"ULTRAMAX pack — latest release {game_version}")
                    version_info, client_id = self.download_version(
                        f"{game_version} (release)",
                        progress_cb=progress_cb,
                        status_cb=status_cb,
                    )
                    self.install_fps_mods(game_version, status_cb, progress_cb)
                    version_info, launch_id = self.install_fabric(game_version, status_cb)
                else:
                    version_info, launch_id = self.download_version(
                        version,
                        progress_cb=progress_cb,
                        status_cb=status_cb,
                    )
                    client_id = launch_id

                resolved = resolve_version_info(version_info)
                base_id = version_info.get("inheritsFrom") or client_id
                jar_path = GAME_DIR / "versions" / base_id / f"{base_id}.jar"
                if not jar_path.exists():
                    raise FileNotFoundError(f"Missing game jar: {jar_path}")
                natives_dir = GAME_DIR / "versions" / base_id / "natives"

                classpath = self.build_classpath(resolved, base_id)
                ram_mb = self.ram.get() * 1024
                args = self.build_launch_args(
                    resolved, launch_id, username, ram_mb, natives_dir, classpath
                )
                
                self.ui_call(self.status_text.set, f"Launching {launch_id}...")
                
                log_dir = GAME_DIR / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "catclient-latest.log"
                log_handle = open(log_path, "w", encoding="utf-8")
                self._log_handle = log_handle
                
                process = subprocess.Popen(
                    args,
                    cwd=str(GAME_DIR),
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )
                self.game_process = process
                self.ui_call(self.status_text.set, f"Playing {launch_id}")
                
                threading.Thread(
                    target=self._monitor_game,
                    args=(process, launch_id, log_handle),
                    daemon=True,
                ).start()
                
            except Exception as e:
                import traceback
                err = str(e)
                self.ui_call(self.status_text.set, "Launch failed!")
                self.ui_call(messagebox.showerror, APP_NAME, f"Error:\n{err}")
                print(traceback.format_exc())
                if self._log_handle:
                    try:
                        self._log_handle.close()
                    except Exception:
                        pass
                    self._log_handle = None
                self.game_process = None
                self.ui_call(self.play_button.config, state="normal", text="PLAY")
        
        threading.Thread(target=launch, daemon=True).start()


# ============== MAIN ==============
if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("Install Pillow for skin previews: pip install pillow")
    
    root = tk.Tk()
    app = CatClientApp(root)
    root.mainloop()
