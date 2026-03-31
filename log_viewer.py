import tkinter as tk
from tkinter import ttk, font
import json
import os
from datetime import datetime
from collections import Counter

LOG_FILE = "log.json"

# ── Farben ───────────────────────────────────
BG        = "#0d0f14"
SURFACE   = "#161820"
SURFACE2  = "#1e2028"
BORDER    = "#2a2d3a"
ACCENT    = "#7c6af7"
ACCENT2   = "#f7c26a"
GREEN     = "#5edc8a"
RED       = "#f76a6a"
TEXT      = "#e8eaf0"
MUTED     = "#6b7080"
# ─────────────────────────────────────────────


def lade_log():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


class LogViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📊 Vinted Log Viewer — python_tutorials_de")
        self.geometry("950x700")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._build_ui()
        self.aktualisieren()

    # ── UI aufbauen ──────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 0))

        tk.Label(
            header, text="VINTED LOG VIEWER",
            bg=BG, fg=ACCENT,
            font=("Courier", 18, "bold")
        ).pack(side="left")

        tk.Label(
            header, text="made by python_tutorials_de",
            bg=BG, fg=MUTED,
            font=("Courier", 9)
        ).pack(side="left", padx=(12, 0), pady=(6, 0))

        self.lbl_update = tk.Label(
            header, text="",
            bg=BG, fg=MUTED,
            font=("Courier", 9)
        )
        self.lbl_update.pack(side="right")

        # Aktualisieren Button
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=(12, 0))

        btn = tk.Button(
            btn_frame,
            text="🔄  AKTUALISIEREN",
            command=self.aktualisieren,
            bg=ACCENT, fg="white",
            font=("Courier", 10, "bold"),
            relief="flat",
            padx=20, pady=8,
            cursor="hand2",
            activebackground="#6255d4",
            activeforeground="white",
            bd=0
        )
        btn.pack(side="left")

        self.lbl_total = tk.Label(
            btn_frame, text="",
            bg=BG, fg=ACCENT2,
            font=("Courier", 10, "bold")
        )
        self.lbl_total.pack(side="left", padx=20)

        # Trennlinie
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)

        # Haupt Content — 2 Spalten
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=24, pady=(0, 10))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # ── Linke Seite: Top Suchbegriffe ────
        left = tk.Frame(content, bg=SURFACE, bd=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(
            left, text="🔥  TOP SUCHBEGRIFFE",
            bg=SURFACE, fg=TEXT,
            font=("Courier", 11, "bold"),
            anchor="w", padx=14, pady=10
        ).pack(fill="x")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x")

        # Scrollbarer Bereich für Top-Begriffe
        self.top_frame = tk.Frame(left, bg=SURFACE)
        self.top_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # ── Rechte Seite: Letzte Suchen ──────
        right = tk.Frame(content, bg=SURFACE, bd=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        tk.Label(
            right, text="🕐  LETZTE SUCHEN",
            bg=SURFACE, fg=TEXT,
            font=("Courier", 11, "bold"),
            anchor="w", padx=14, pady=10
        ).pack(fill="x")

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x")

        # Treeview für letzte Suchen
        tree_frame = tk.Frame(right, bg=SURFACE)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
            background=SURFACE2,
            foreground=TEXT,
            fieldbackground=SURFACE2,
            borderwidth=0,
            font=("Courier", 9),
            rowheight=28
        )
        style.configure("Custom.Treeview.Heading",
            background=SURFACE,
            foreground=ACCENT2,
            font=("Courier", 9, "bold"),
            borderwidth=0
        )
        style.map("Custom.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")]
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("zeit", "begriff"),
            show="headings",
            style="Custom.Treeview"
        )
        self.tree.heading("zeit", text="ZEIT")
        self.tree.heading("begriff", text="SUCHBEGRIFF")
        self.tree.column("zeit", width=140, anchor="w")
        self.tree.column("begriff", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Untere Leiste: Statistiken ───────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        stats_bar = tk.Frame(self, bg=SURFACE2)
        stats_bar.pack(fill="x", padx=24, pady=(0, 16))

        self.stat_labels = {}
        stats = [
            ("stat_heute", "📅 Heute: -"),
            ("stat_woche", "📆 Diese Woche: -"),
            ("stat_unique", "🔤 Unique Begriffe: -"),
            ("stat_top1", "🏆 #1 Begriff: -"),
        ]
        for i, (key, text) in enumerate(stats):
            lbl = tk.Label(
                stats_bar, text=text,
                bg=SURFACE2, fg=MUTED,
                font=("Courier", 9),
                padx=16, pady=10
            )
            lbl.pack(side="left", expand=True)
            self.stat_labels[key] = lbl

    # ── Daten laden & UI aktualisieren ───────
    def aktualisieren(self):
        daten = lade_log()

        # ── Treeview leeren & neu befüllen ───
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Neueste zuerst
        for eintrag in reversed(daten[-200:]):
            self.tree.insert("", "end", values=(
                eintrag.get("zeit", ""),
                eintrag.get("suchbegriff", "")
            ))

        # ── Top Suchbegriffe ─────────────────
        for widget in self.top_frame.winfo_children():
            widget.destroy()

        begriffe = [e.get("suchbegriff", "").lower() for e in daten]
        counter = Counter(begriffe)
        top10 = counter.most_common(15)

        if top10:
            max_count = top10[0][1]
            farben = [ACCENT, ACCENT2, GREEN, "#3b9eff", "#ff6b9d", "#ff6b35", "#b06bff", GREEN, ACCENT2, ACCENT]

            for i, (begriff, count) in enumerate(top10):
                row = tk.Frame(self.top_frame, bg=SURFACE)
                row.pack(fill="x", pady=3)

                # Rang
                tk.Label(
                    row, text=f"#{i+1:02d}",
                    bg=SURFACE, fg=MUTED,
                    font=("Courier", 9, "bold"),
                    width=4, anchor="w"
                ).pack(side="left", padx=(0, 8))

                # Begriff
                tk.Label(
                    row, text=begriff[:22],
                    bg=SURFACE, fg=TEXT,
                    font=("Courier", 10),
                    width=18, anchor="w"
                ).pack(side="left")

                # Balken
                bar_frame = tk.Frame(row, bg=SURFACE2, height=14)
                bar_frame.pack(side="left", fill="x", expand=True, padx=(8, 8))
                bar_frame.pack_propagate(False)

                bar_width = max(4, int((count / max_count) * 120))
                farbe = farben[i % len(farben)]

                bar_fill = tk.Frame(bar_frame, bg=farbe, height=14, width=bar_width)
                bar_fill.place(x=0, y=0)

                # Count
                tk.Label(
                    row, text=f"{count}x",
                    bg=SURFACE, fg=farbe,
                    font=("Courier", 9, "bold"),
                    width=5, anchor="e"
                ).pack(side="right", padx=(0, 4))
        else:
            tk.Label(
                self.top_frame,
                text="Noch keine Daten in log.json",
                bg=SURFACE, fg=MUTED,
                font=("Courier", 10)
            ).pack(pady=20)

        # ── Statistiken berechnen ─────────────
        heute = datetime.now().strftime("%Y-%m-%d")
        heute_count = sum(1 for e in daten if e.get("zeit", "").startswith(heute))

        # Diese Woche
        jetzt = datetime.now()
        woche_count = 0
        for e in daten:
            try:
                dt = datetime.strptime(e.get("zeit", ""), "%Y-%m-%d %H:%M:%S")
                if (jetzt - dt).days <= 7:
                    woche_count += 1
            except:
                pass

        unique = len(set(begriffe))
        top1 = top10[0][0] if top10 else "-"

        self.stat_labels["stat_heute"].config(text=f"📅 Heute: {heute_count}")
        self.stat_labels["stat_woche"].config(text=f"📆 Diese Woche: {woche_count}")
        self.stat_labels["stat_unique"].config(text=f"🔤 Unique: {unique}")
        self.stat_labels["stat_top1"].config(text=f"🏆 #1: {top1[:15]}")

        # Gesamt
        self.lbl_total.config(text=f"📊 Gesamt: {len(daten)} Suchen")

        # Timestamp
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_update.config(text=f"Zuletzt aktualisiert: {now}")


if __name__ == "__main__":
    app = LogViewer()
    app.mainloop()
