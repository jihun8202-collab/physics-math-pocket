"""Pocket Glass drawing primitives. Native Tk controls remain accessible."""
from __future__ import annotations

import tkinter as tk


PALETTES = {
    "light": {
        "bg": "#EDF1F9", "rail": "#F6F8FD", "surface": "#FBFCFF",
        "surface2": "#F1F4FA", "surface3": "#E7ECF6", "glass": "#F7F9FD",
        "line": "#DCE4F1", "text": "#1C2943", "muted": "#596A83",
        "accent": "#5366DB", "accent2": "#3949AD", "accent_soft": "#E8EDFF",
        "blue": "#3568C9", "cyan": "#168299", "green": "#267A67",
        "orange": "#A76428", "pink": "#A94C79", "yellow": "#FFF3CD",
        "danger": "#BF394C", "shadow": "#DCE3F0", "hero_a": "#5368D8",
        "hero_b": "#7562C7", "shine": "#FFFFFF",
    },
    "dark": {
        "bg": "#101725", "rail": "#151E30", "surface": "#1C273B",
        "surface2": "#243148", "surface3": "#2D3C56", "glass": "#192338",
        "line": "#384760", "text": "#EFF4FF", "muted": "#B4C1D8",
        "accent": "#A5B4FF", "accent2": "#CAD3FF", "accent_soft": "#303D64",
        "blue": "#9CBFFF", "cyan": "#7FD8E8", "green": "#88DCBD",
        "orange": "#F4BA83", "pink": "#F1AFCE", "yellow": "#514731",
        "danger": "#FFAFB8", "shadow": "#0B111E", "hero_a": "#344783",
        "hero_b": "#514174", "shine": "#53647D",
    },
}
ACCENTS = {
    "indigo": ("#5366DB", "#3949AD", "#E8EDFF", "#A5B4FF", "#CAD3FF", "#303D64"),
    "teal": ("#227F80", "#176165", "#DFF3F0", "#7FD8D2", "#B2EAE6", "#22484E"),
    "rose": ("#A24D78", "#7E365D", "#F8E7F0", "#F0ACCF", "#FFD2E7", "#503047"),
}
CONTENT_TARGETS = {
    "수학": 10000, "물리": 15000, "화학": 20000, "생명과학": 9000,
    "지구과학": 9500, "천문학": 9000, "국어": 50000,
}


def make_theme(name: str, accent: str = "indigo", effects: bool = True) -> dict:
    theme = dict(PALETTES.get(name, PALETTES["light"]))
    values = ACCENTS.get(accent, ACCENTS["indigo"])
    theme.update(zip(("accent", "accent2", "accent_soft"), values[3:] if name == "dark" else values[:3]))
    theme["effects"] = bool(effects)
    return theme


def mix(a: str, b: str, fraction: float) -> str:
    return "#" + "".join(
        f"{round(int(a[i:i+2],16)*(1-fraction)+int(b[i:i+2],16)*fraction):02x}"
        for i in (1, 3, 5)
    )


def rounded(canvas: tk.Canvas, x1, y1, x2, y2, radius=18, **kw):
    radius = min(radius, max(0, (x2-x1)/2), max(0, (y2-y1)/2))
    points = [x1+radius,y1,x2-radius,y1,x2,y1,x2,y1+radius,
              x2,y2-radius,x2,y2,x2-radius,y2,x1+radius,y2,
              x1,y2,x1,y2-radius,x1,y1+radius,x1,y1]
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kw)


class GlassCard(tk.Frame):
    """Rounded solid reading surface with frosted border and soft depth.

    Tk child widgets do not support per-widget alpha. Text is always rendered
    on an opaque surface; Windows backdrop support is applied separately.
    """
    def __init__(self, master, theme, fill=None, padx=20, pady=18):
        try:
            background = master.cget("bg")
        except tk.TclError:
            background = theme["bg"]
        super().__init__(master, bg=background, bd=0)
        self._theme, self._fill = theme, fill or theme["surface"]
        self._canvas = tk.Canvas(self, bg=background, bd=0, highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.content = tk.Frame(self, bg=self._fill, bd=0)
        self.content.pack(fill="both", expand=True, padx=max(14,padx), pady=max(12,pady))
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        c, t = self._canvas, self._theme
        w, h = self.winfo_width(), self.winfo_height()
        c.delete("all")
        if w < 4 or h < 4:
            return
        if t.get("effects", True):
            rounded(c, 1, 3, w-1, h-1, fill=t["shadow"], outline="")
        rounded(c, 1, 1, w-2, h-3, fill=self._fill, outline=t["line"], width=1)
        if t.get("effects", True):
            c.create_line(20, 2, max(21,w-22), 2, fill=t["shine"])


def responsive_label(master, *, inset=0, **kwargs):
    """Wrap to available width rather than a fixed screen pixel assumption."""
    label = tk.Label(master, **kwargs)
    def fit(event):
        width = max(80, event.width-inset)
        if int(label.cget("wraplength") or 0) != width:
            label.configure(wraplength=width)
    label.bind("<Configure>", fit, add="+")
    return label


def bind_hover(button, theme, enabled=True):
    if not enabled:
        return button
    original = button.cget("bg")
    current = [None]
    def cancel():
        if current[0]:
            try:
                button.after_cancel(current[0])
            except tk.TclError:
                pass
            current[0] = None
    def transition(target):
        cancel()
        start = button.cget("bg")
        def tick(step=1):
            if not button.winfo_exists():
                return
            button.configure(bg=mix(start, target, step/5))
            current[0] = button.after(18, tick, step+1) if step < 5 else None
        tick()
    button.bind("<Enter>", lambda _e: transition(theme["surface3"]), add="+")
    button.bind("<Leave>", lambda _e: transition(original), add="+")
    button.bind("<Destroy>", lambda _e: cancel(), add="+")
    return button
