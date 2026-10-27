"""RandomikME - randomly pick photos from a folder and copy them somewhere else.

Optionally filters by orientation (landscape / portrait) and can move the used
originals aside so they never come up in the next draw.

Needs Python 3 with Tkinter and Pillow (see requirements.txt).
Keep favicon2.ico and created.png next to this script.
"""

import json
import os
import queue
import random
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from PIL import Image, ImageDraw, ImageTk

APP_NAME = "RandomikME"
GITHUB_URL = "https://github.com/nyorbee"
BTN = "#A9A9A9"  # classic grey used for the buttons

EXTENSIONS = {
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff", ".psd", ".ai", ".svg",
    ".eps", ".raw", ".pdf", ".ico", ".wmf", ".emf", ".exr", ".tga", ".webp",
    ".nef", ".cr2",
}

EXIF_ORIENTATION_TAG = 0x0112
EXIF_ROTATED_90 = {5, 6, 7, 8}  # EXIF values meaning width/height are swapped

TEXTS = {
    "en": {
        "num_files": "Number of photos to pick:",
        "source": "Source folder:",
        "destination": "Destination folder:",
        "browse": "Browse...",
        "clear_dest": "Clear destination folder",
        "subfolders": "Include files from subfolders",
        "orientation": "Photo orientation",
        "any": "Any",
        "horizontal": "Landscape",
        "vertical": "Portrait",
        "move": "Cut the copied photos",
        "move_to": "And move them to:",
        "open_when_done": "Open destination folder when done",
        "open_folder_tip": "Open the destination folder now",
        "remember": "Remember folders for next time",
        "start": "Start",
        "ready": "Ready.",
        "scanning": "Scanning source folder...",
        "checking": "Checking orientation... ({found}/{count} found)",
        "copying": "Copying {i}/{n}...",
        "moving": "Moving originals {i}/{n}...",
        "err_title": "Error :(",
        "done_title": "Done :)",
        "done_problems_title": "Done (with problems)",
        "e_num": "Number of photos must be a positive whole number.",
        "e_source": "The source folder doesn't exist.",
        "e_dest_empty": "Please choose a destination folder.",
        "e_move_empty": "Please choose a folder to move the originals to.",
        "e_mkdir": "Couldn't create the folder:\n{error}",
        "e_perm": "No write permission for:\n{path}",
        "e_same": "Source and target folders must be different.",
        "e_none_found": "No supported image files were found in the source folder.",
        "e_not_enough": "Not enough photos match your settings.\nFound: {found}, requested: {count}.\n\nNothing was copied or moved.",
        "e_unexpected": "Unexpected error: {error}",
        "done_msg": "{n} photo(s) copied to:\n{dest}",
        "done_moved": "{n} original(s) moved.",
        "problems": "{n} problem(s):\n{list}",
        "clear_title": "Clear destination folder",
        "clear_not_dir": "The destination folder doesn't exist.",
        "clear_unsafe": "For safety this folder can't be cleared:\n{path}\n\n"
                        "(It's a drive root, or it is/contains your source or move-to folder.)",
        "clear_empty": "The destination folder has no files to delete.",
        "clear_confirm": "Permanently delete {n} file(s) from:\n{path}\n\nThis cannot be undone!",
        "clear_done": "Deleted {n} file(s).",
        "clear_failed": "{n} file(s) couldn't be deleted.",
    },
    "pl": {
        "num_files": "Liczba zdjęć do wylosowania:",
        "source": "Folder źródłowy:",
        "destination": "Folder docelowy:",
        "browse": "Wybierz",
        "clear_dest": "Wyczyść folder docelowy",
        "subfolders": "Uwzględniaj pliki w podfolderach",
        "orientation": "Orientacja zdjęcia",
        "any": "Bez różnicy",
        "horizontal": "Poziome",
        "vertical": "Pionowe",
        "move": "Wytnij skopiowane zdjęcia",
        "move_to": "I przenieś je do:",
        "open_when_done": "Otwórz folder docelowy po zakończeniu",
        "open_folder_tip": "Otwórz folder docelowy teraz",
        "remember": "Zapamiętaj ścieżki",
        "start": "Start",
        "ready": "Gotowe.",
        "scanning": "Skanowanie folderu źródłowego...",
        "checking": "Sprawdzanie orientacji... (znaleziono {found}/{count})",
        "copying": "Kopiowanie {i}/{n}...",
        "moving": "Przenoszenie oryginałów {i}/{n}...",
        "err_title": "Błąd :(",
        "done_title": "Done :)",
        "done_problems_title": "Gotowe (z problemami)",
        "e_num": "Liczba zdjęć musi być dodatnią liczbą całkowitą.",
        "e_source": "Folder źródłowy nie istnieje.",
        "e_dest_empty": "Wybierz folder docelowy.",
        "e_move_empty": "Wybierz folder, do którego mają trafić oryginały.",
        "e_mkdir": "Nie udało się utworzyć folderu:\n{error}",
        "e_perm": "Brak uprawnień do zapisu w:\n{path}",
        "e_same": "Folder źródłowy i docelowy muszą być różne.",
        "e_none_found": "Nie znaleziono prawidłowych plików w folderze źródłowym.",
        "e_not_enough": "Za mało zdjęć spełniających wybrane kryteria.\nZnaleziono: {found}, a wybrano: {count}.\n\nNic nie zostało skopiowane ani przeniesione.",
        "e_unexpected": "Nieoczekiwany błąd: {error}",
        "done_msg": "Skopiowano zdjęć: {n}\nDo folderu:\n{dest}",
        "done_moved": "Przeniesiono oryginałów: {n}.",
        "problems": "Liczba problemów: {n}\n{list}",
        "clear_title": "Wyczyść folder docelowy",
        "clear_not_dir": "Folder docelowy nie istnieje.",
        "clear_unsafe": "Ze względów bezpieczeństwa nie można wyczyścić tego folderu:\n{path}\n\n"
                        "(To katalog główny dysku albo folder zawiera/jest Twoim folderem źródłowym lub docelowym przeniesienia.)",
        "clear_empty": "W folderze docelowym nie ma plików do usunięcia.",
        "clear_confirm": "Trwale usunąć plików: {n}\nz folderu:\n{path}\n\nTej operacji nie można cofnąć!",
        "clear_done": "Usunięto plików: {n}.",
        "clear_failed": "Nie udało się usunąć plików: {n}.",
    },
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def resource_path(name):
    """Locate bundled files: works from source and from PyInstaller / Nuitka builds."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def settings_file():
    base = os.environ.get("APPDATA") or os.path.join(Path.home(), ".config")
    return Path(base) / APP_NAME / "settings.json"


def load_settings():
    try:
        return json.loads(settings_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        path = settings_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def open_folder(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except OSError:
        pass


def is_inside(child, parent):
    """True if `child` is `parent` itself or lies somewhere below it."""
    try:
        parent = os.path.abspath(parent)
        return os.path.commonpath([os.path.abspath(child), parent]) == parent
    except ValueError:  # e.g. different drives on Windows
        return False


def unique_path(folder, filename):
    """A path in `folder` that doesn't exist yet (adds ' (1)', ' (2)'...)."""
    target = Path(folder) / filename
    stem, suffix, n = target.stem, target.suffix, 1
    while target.exists():
        target = Path(folder) / f"{stem} ({n}){suffix}"
        n += 1
    return target


def scan_images(source, include_subfolders, excluded_dirs):
    """Collect image paths; never descend into the destination / move-to folders."""
    found = []
    for root, dirs, names in os.walk(source):
        if include_subfolders:
            dirs[:] = [
                d for d in dirs
                if not any(is_inside(os.path.join(root, d), ex) for ex in excluded_dirs)
            ]
        else:
            dirs[:] = []
        for name in names:
            if os.path.splitext(name)[1].lower() in EXTENSIONS:
                found.append(os.path.join(root, name))
    return found


def get_orientation(path):
    """'horizontal' (square counts as horizontal), 'vertical', or None if unreadable."""
    try:
        with Image.open(path) as img:  # lazy: only reads the header
            width, height = img.size
            try:
                if img.getexif().get(EXIF_ORIENTATION_TAG) in EXIF_ROTATED_90:
                    width, height = height, width
            except Exception:
                pass
    except Exception:
        return None
    return "horizontal" if width >= height else "vertical"


# --------------------------------------------------------------------------
# Core job (runs in a worker thread, no GUI calls in here)
# --------------------------------------------------------------------------
class PickError(Exception):
    def __init__(self, key, **kw):
        super().__init__(key)
        self.key, self.kw = key, kw


def pick_photos(p, report):
    report("scanning", 0, 0)
    excluded = [p["destination"]] + ([p["move_to"]] if p["move"] else [])
    files = scan_images(p["source"], p["include_subfolders"], excluded)
    if not files:
        raise PickError("e_none_found")

    count, orientation = p["count"], p["orientation"]
    random.shuffle(files)

    # Shuffle first, then stop as soon as enough matching files are found.
    if orientation == "any":
        picked = files[:count]
    else:
        picked = []
        for i, path in enumerate(files, 1):
            if get_orientation(path) == orientation:
                picked.append(path)
                if len(picked) == count:
                    break
            if i % 10 == 0:
                report("checking", len(picked), count, found=len(picked), count=count)

    if len(picked) < count:
        raise PickError("e_not_enough", found=len(picked), count=count)

    copied, failed = [], []
    for i, src in enumerate(picked, 1):
        report("copying", i, count, i=i, n=count)
        try:
            shutil.copy2(src, unique_path(p["destination"], os.path.basename(src)))
            copied.append(src)
        except (OSError, shutil.Error) as exc:
            failed.append((src, str(exc)))

    moved = 0
    if p["move"]:
        for i, src in enumerate(copied, 1):
            report("moving", i, len(copied), i=i, n=len(copied))
            try:
                shutil.move(src, str(unique_path(p["move_to"], os.path.basename(src))))
                moved += 1
            except (OSError, shutil.Error) as exc:
                failed.append((src, str(exc)))

    return {"copied": len(copied), "moved": moved, "failed": failed}


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
def _photo_icon(w, h):
    """Tiny pixel-art 'photo' (sky, hill, grass, sun) in classic Windows colours."""
    img = Image.new("RGB", (w, h), "#000000")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, w - 2, h - 2], fill="#FFFFFF")      # white print edge
    d.rectangle([2, 2, w - 3, h - 3], fill="#99CCFF")      # sky
    d.rectangle([2, h - 5, w - 3, h - 3], fill="#008000")  # grass
    d.polygon([(2, h - 5), (w // 3, h // 2), (w // 2 + 1, h - 5)], fill="#808080")  # hill
    d.rectangle([w - 6, 3, w - 4, 5], fill="#FFFF00")      # sun
    return img


def _folder_icon():
    img = Image.new("RGBA", (16, 13), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1, 6, 4], fill="#FFFF00", outline="#000000")    # tab
    d.rectangle([0, 3, 15, 12], fill="#FFFF00", outline="#000000")  # body
    d.line([(1, 4), (14, 4)], fill="#FFFFC0")                        # highlight
    d.line([(1, 11), (14, 11)], fill="#C0A000")                      # shade
    return img


def _trash_icon():
    img = Image.new("RGBA", (12, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 0, 7, 2], outline="#000000")                     # handle
    d.rectangle([1, 2, 10, 4], fill="#C0C0C0", outline="#000000")    # lid
    d.rectangle([2, 4, 9, 13], fill="#DCDCDC", outline="#000000")    # can
    for x in (4, 7):
        d.line([(x, 6), (x, 11)], fill="#808080")                    # ribs
    return img


def add_tooltip(widget, text):
    """Classic yellow Windows tooltip."""
    state = {"win": None}

    def show(_e):
        if state["win"]:
            return
        win = tk.Toplevel(widget)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{widget.winfo_rootx() + 10}+{widget.winfo_rooty() + widget.winfo_height() + 4}")
        tk.Label(win, text=text, bg="#FFFFE1", relief="solid", bd=1,
                 font=("Arial", 9), padx=4, pady=1).pack()
        state["win"] = win

    def hide(_e=None):
        if state["win"]:
            state["win"].destroy()
            state["win"] = None

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)
    widget.bind("<ButtonPress>", hide)


def make_icons():
    """Create after the Tk root exists. Drawn small, then enlarged without smoothing = chunky pixels."""
    both = Image.new("RGBA", (26, 22), (0, 0, 0, 0))
    both.paste(_photo_icon(12, 17), (0, 0))
    both.paste(_photo_icon(17, 12), (9, 10))
    icons = {"any": both, "horizontal": _photo_icon(20, 14), "vertical": _photo_icon(14, 20),
             "folder": _folder_icon(), "trash": _trash_icon()}
    return {k: ImageTk.PhotoImage(im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST))
            for k, im in icons.items()}


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_settings()
        self.queue = queue.Queue()
        self.running = False
        self.main = None
        self.lang = self.cfg.get("language", "en") if self.cfg.get("language") in TEXTS else "en"

        if sys.platform.startswith("win"):
            try:  # makes the taskbar show our icon instead of python's
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nyorbee.randomikme")
            except Exception:
                pass

        root.title(APP_NAME)
        root.resizable(False, False)
        try:
            root.iconbitmap(resource_path("favicon2.ico"))
        except tk.TclError:
            print(f"Icon not loaded - is favicon2.ico next to the script? ({resource_path('favicon2.ico')})")

        self.f_normal = tkfont.Font(family="Arial", size=10)
        self.f_bold = tkfont.Font(family="Arial", size=10, weight="bold")
        self.f_italic = tkfont.Font(family="Arial", size=10, weight="bold", slant="italic")
        self.f_black = tkfont.Font(family="Arial Black", size=10, weight="bold")
        self.f_big = tkfont.Font(family="Arial", size=18, weight="bold")
        self.f_path = tkfont.Font(family="Arial", size=11, weight="bold")  # entries: bigger + bold
        self.icons = make_icons()  # keep references!

        style = ttk.Style()
        style.theme_use("classic")
        style.configure("Win98.Horizontal.TProgressbar", background="#000080",
                        troughcolor="white", borderwidth=2, relief="sunken")

        # Variables live here so they survive a language switch (UI rebuild).
        cfg = self.cfg
        self.num_var = tk.StringVar(value="1")  # always starts at 1
        self.source_var = tk.StringVar(value=cfg.get("source", ""))
        self.dest_var = tk.StringVar(value=cfg.get("destination", ""))
        self.subfolders_var = tk.BooleanVar(value=cfg.get("include_subfolders", False))
        self.orient_var = tk.StringVar(value=cfg.get("orientation", "any"))
        self.move_var = tk.BooleanVar(value=cfg.get("move", False))
        self.move_to_var = tk.StringVar(value=cfg.get("move_to", ""))
        self.open_var = tk.BooleanVar(value=cfg.get("open_when_done", False))
        self.remember_var = tk.BooleanVar(value=cfg.get("remember_paths", False))
        self.status = tk.StringVar(value=self.t("ready"))

        self.build_ui()
        self.center()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_queue()

    def t(self, key, **kw):
        text = TEXTS[self.lang][key]
        return text.format(**kw) if kw else text

    # ---- widget factories ---------------------------------------------------
    def label(self, parent, text, font=None, **kw):
        return tk.Label(parent, text=text, font=font or self.f_bold, **kw)

    def button(self, parent, text, command, font=None, **kw):
        return tk.Button(parent, text=text, command=command, bg=BTN,
                         font=font or self.f_bold, **kw)

    def check(self, parent, text, var, command=None, font=None):
        return tk.Checkbutton(parent, text=text, variable=var, command=command,
                              font=font or self.f_bold)

    def path_entry(self, parent, var, **kw):
        # bigger, bold, dark-blue text so a typed path stands out clearly
        return tk.Entry(parent, textvariable=var, font=self.f_path, fg="#000080",
                        disabledforeground="#808080", bd=2, relief="sunken", **kw)

    def add_path_row(self, parent, var, bottom=8):
        """Entry and Browse button side by side."""
        row = tk.Frame(parent)
        row.pack(fill="x", pady=(2, bottom))
        entry = self.path_entry(row, var, width=44)
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        button = self.button(row, self.t("browse"), lambda: self.browse(var))
        button.pack(side="left", padx=(6, 0))
        return entry, button

    # ---- UI construction -------------------------------------------------
    def build_ui(self):
        if self.main is not None:
            self.main.destroy()
        self.main = main = tk.Frame(self.root, padx=16, pady=8)
        main.pack(fill="both", expand=True)

        top = tk.Frame(main)
        top.pack(fill="x", pady=(0, 8))
        self.label(top, self.t("num_files")).pack(side="left")
        self.path_entry(top, self.num_var, width=5, justify="center").pack(side="left", padx=8)
        for code in ("EN", "PL"):  # language switch, top right
            active = self.lang == code.lower()
            tk.Button(top, text=code, command=lambda c=code.lower(): self.set_language(c),
                      bg=BTN, font=self.f_bold, width=3,
                      relief="sunken" if active else "raised").pack(side="right", padx=(2, 0))

        self.label(main, self.t("source")).pack(anchor="w")
        self.add_path_row(main, self.source_var)
        self.check(main, self.t("subfolders"), self.subfolders_var,
                   font=self.f_italic).pack(anchor="w", pady=(0, 8))

        self.label(main, self.t("destination")).pack(anchor="w")
        self.add_path_row(main, self.dest_var, bottom=3)
        self.button(main, self.t("clear_dest"), self.on_clear_destination,
                    image=self.icons["trash"], compound="left", padx=6).pack(anchor="w", pady=(0, 8))

        box = tk.LabelFrame(main, text=self.t("orientation"), font=self.f_italic, padx=10, pady=4)
        box.pack(fill="x", pady=(0, 8))
        for key in ("any", "horizontal", "vertical"):
            tk.Radiobutton(box, text=self.t(key), image=self.icons[key], compound="left",
                           value=key, variable=self.orient_var, font=self.f_bold,
                           padx=4).pack(side="left", padx=(0, 12))

        self.check(main, self.t("move"), self.move_var, command=self.update_move_state,
                   font=self.f_black).pack(anchor="w")
        self.label(main, self.t("move_to")).pack(anchor="w")
        self.move_entry, self.move_btn = self.add_path_row(main, self.move_to_var)
        self.update_move_state()

        open_row = tk.Frame(main)
        open_row.pack(anchor="w")
        self.check(open_row, self.t("open_when_done"), self.open_var).pack(side="left")
        open_btn = tk.Button(open_row, image=self.icons["folder"], command=self.open_destination_now,
                             bg=BTN, bd=2)
        open_btn.pack(side="left", padx=6)
        add_tooltip(open_btn, self.t("open_folder_tip"))
        self.check(main, self.t("remember"), self.remember_var).pack(anchor="w", pady=(0, 8))

        self.progress = ttk.Progressbar(main, mode="determinate",
                                        style="Win98.Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        tk.Label(main, textvariable=self.status, font=self.f_normal).pack(anchor="w", pady=(2, 4))

        self.start_btn = self.button(main, self.t("start"), self.on_start, font=self.f_big, bd=3)
        self.start_btn.pack(fill="x", pady=(4, 6), ipady=6)
        if self.running:
            self.start_btn.config(state="disabled")

        try:
            img = Image.open(resource_path("created.png"))
            img.thumbnail((200, 200))
            self.badge_img = ImageTk.PhotoImage(img)  # keep a reference!
            badge = tk.Label(main, image=self.badge_img, borderwidth=4, highlightthickness=4,
                             cursor="hand2")
            badge.pack(pady=(8, 0))
            badge.bind("<Button-1>", lambda _e: webbrowser.open(GITHUB_URL))
        except (OSError, tk.TclError):
            pass

    def center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.minsize(w, h)

    def set_language(self, code):
        if code == self.lang:
            return
        self.lang = code
        save_settings(self.collect_settings())
        if not self.running:
            self.status.set(self.t("ready"))
        self.build_ui()
        self.root.minsize(1, 1)
        self.root.geometry("")  # let the window re-fit to the new texts

    # ---- small UI actions ------------------------------------------------
    def browse(self, var):
        options = {"initialdir": var.get()} if os.path.isdir(var.get()) else {}
        chosen = filedialog.askdirectory(**options)
        if chosen:  # cancelling the dialog doesn't wipe the field
            var.set(os.path.normpath(chosen))

    def open_destination_now(self):
        dest = self.dest_var.get().strip()
        if dest and os.path.isdir(dest):
            open_folder(dest)
        else:
            self.error("clear_not_dir")

    def update_move_state(self):
        state = "normal" if self.move_var.get() else "disabled"
        self.move_entry.config(state=state)
        self.move_btn.config(state=state)

    def collect_settings(self):
        data = {
            "language": self.lang,
            "remember_paths": self.remember_var.get(),
            "orientation": self.orient_var.get(),
            "include_subfolders": self.subfolders_var.get(),
            "move": self.move_var.get(),          # the checkbox is always remembered...
            "open_when_done": self.open_var.get(),
        }
        if self.remember_var.get():               # ...the paths only if "Remember" is ticked
            data.update(source=self.source_var.get(),
                        destination=self.dest_var.get(),
                        move_to=self.move_to_var.get())
        return data

    def on_close(self):
        save_settings(self.collect_settings())
        self.root.destroy()

    def error(self, key, **kw):
        messagebox.showerror(self.t("err_title"), self.t(key, **kw))

    # ---- clear destination ----------------------------------------------
    def on_clear_destination(self):
        if self.running:
            return
        title = self.t("clear_title")
        dest = self.dest_var.get().strip()
        if not dest or not os.path.isdir(dest):
            messagebox.showerror(title, self.t("clear_not_dir"))
            return

        abs_dest = os.path.abspath(dest)
        protected = [self.source_var.get().strip()]
        if self.move_var.get():
            protected.append(self.move_to_var.get().strip())
        is_drive_root = os.path.dirname(abs_dest) == abs_dest
        if is_drive_root or any(p and is_inside(p, abs_dest) for p in protected):
            messagebox.showerror(title, self.t("clear_unsafe", path=abs_dest))
            return

        files = [e.path for e in os.scandir(abs_dest) if e.is_file()]  # subfolders are left alone
        if not files:
            messagebox.showinfo(title, self.t("clear_empty"))
            return
        if not messagebox.askyesno(title, self.t("clear_confirm", n=len(files), path=abs_dest),
                                   icon="warning", default="no"):
            return

        deleted = failed = 0
        for path in files:
            try:
                os.remove(path)
                deleted += 1
            except OSError:
                failed += 1
        msg = self.t("clear_done", n=deleted)
        if failed:
            msg += "\n" + self.t("clear_failed", n=failed)
        messagebox.showinfo(title, msg)

    # ---- validation + start ---------------------------------------------
    def on_start(self):
        if self.running:
            return
        try:
            count = int(self.num_var.get())
            if count < 1:
                raise ValueError
        except ValueError:
            self.error("e_num")
            return

        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()
        move = self.move_var.get()
        move_to = self.move_to_var.get().strip()

        if not os.path.isdir(source):
            self.error("e_source")
            return
        if not dest:
            self.error("e_dest_empty")
            return
        if move and not move_to:
            self.error("e_move_empty")
            return

        # Validate everything BEFORE copying anything.
        try:
            os.makedirs(dest, exist_ok=True)
            if move:
                os.makedirs(move_to, exist_ok=True)
        except OSError as exc:
            self.error("e_mkdir", error=exc)
            return
        for folder in [dest] + ([move_to] if move else []):
            if not os.access(folder, os.W_OK):
                self.error("e_perm", path=folder)
                return
            if os.path.samefile(folder, source):
                self.error("e_same")
                return

        save_settings(self.collect_settings())
        params = {
            "source": source, "destination": dest, "move": move, "move_to": move_to,
            "count": count, "orientation": self.orient_var.get(),
            "include_subfolders": self.subfolders_var.get(),
        }
        self.running = True
        self.start_btn.config(state="disabled")

        def report(key, value, maximum, **kw):
            self.queue.put(("progress", key, kw, value, maximum))

        threading.Thread(target=self.worker, args=(params, report), daemon=True).start()

    def worker(self, params, report):
        try:
            self.queue.put(("done", pick_photos(params, report)))
        except PickError as exc:
            self.queue.put(("error", exc.key, exc.kw))
        except Exception as exc:  # noqa: BLE001
            self.queue.put(("error", "e_unexpected", {"error": exc}))

    # ---- worker -> GUI messages -----------------------------------------
    def poll_queue(self):
        try:
            while True:
                kind, *payload = self.queue.get_nowait()
                if kind == "progress":
                    self.on_progress(*payload)
                elif kind == "done":
                    self.on_done(payload[0])
                elif kind == "error":
                    self.finish()
                    self.error(payload[0], **payload[1])
        except queue.Empty:
            pass
        self.root.after(80, self.poll_queue)

    def on_progress(self, key, kw, value, maximum):
        self.status.set(self.t(key, **kw))
        if maximum:
            self.progress.stop()
            self.progress.configure(mode="determinate", maximum=maximum, value=value)
        elif str(self.progress.cget("mode")) != "indeterminate":
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)

    def finish(self):
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status.set(self.t("ready"))
        self.start_btn.config(state="normal")
        self.running = False

    def on_done(self, result):
        self.finish()
        msg = self.t("done_msg", n=result["copied"], dest=self.dest_var.get())
        if self.move_var.get():
            msg += "\n\n" + self.t("done_moved", n=result["moved"])
        if result["failed"]:
            shown = "\n".join(f"- {os.path.basename(f)}: {e}" for f, e in result["failed"][:5])
            msg += "\n\n" + self.t("problems", n=len(result["failed"]), list=shown)
            messagebox.showwarning(self.t("done_problems_title"), msg)
        else:
            messagebox.showinfo(self.t("done_title"), msg)
        if self.open_var.get():
            open_folder(self.dest_var.get())


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
