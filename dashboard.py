################################################################################
#                                                                              #
#  📊 VINTED SCRAPER DASHBOARD v2 (Ersetzt log_viewer.py + log_viewer1.py)   #
#                                                                              #
#  Features:                                                                  #
#  • Vollständig scrollbares Fenster                                         #
#  • Live CPU/RAM Auslastung mit Charts                                      #
#  • Top Suchbegriffe mit Balkendiagramm                                     #
#  • Top 20 Städte/Länder mit Scrollbar (NEU)                                #
#  • Vollständige Statistiken                                                #
#  • Automatische Aktualisierung                                             #
#                                                                              #
################################################################################

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
from collections import Counter
import psutil
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')

# ═══ KONFIGURATION ═════════════════════════════════════════════════════════
LOG_FILE = "log.json"
SEEN_FILE = "seen.json"
CITIES_FILE = "cities.json"
COUNTRIES_FILE = "countries.json"
LOCATION_ERRORS_FILE = "location_errors.json"

# ── Farben (Dark Mode) ──────────────────────────────────────────────────────
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

# ── Farben pro Land für Dashboard ───────────────────────────────────────────
COUNTRY_COLORS = {
    "Deutschland": "#1a1a1a",      # Schwarz (Flagge)
    "Frankreich": "#003399",       # Blau
    "Österreich": "#ff0000",       # Rot
    "Schweiz": "#ff0000",          # Rot
    "Niederlande": "#ff6b35",      # Orange
    "Belgien": "#ffcc00",          # Gelb
    "Polen": "#ff0000",            # Rot
    "Spanien": "#ffc400",          # Gold
    "Italien": "#00cc33",          # Grün
    "Schweden": "#0066cc",         # Blau
    "Dänemark": "#c8102e",         # Rot
    "Norwegen": "#ba0c2f",         # Rot
    "Griechenland": "#0066cc",     # Blau
    "Portugal": "#009900",         # Grün
    "Rumänien": "#0066cc",         # Blau
    "Tschechien": "#ff0000",       # Rot
    "Ungarn": "#ff0000",           # Rot
    "Irland": "#169b62",           # Grün
    "England": "#003399",          # Blau
    "Großbritannien": "#003399",   # Blau
    "UK": "#003399",               # Blau
    "Vereinigtes Königreich": "#003399", # Blau
    "Kroatien": "#ff0000",         # Rot
    "Slowakei": "#0066cc",         # Blau
    "Slowenien": "#ff0066",        # Rot
    "Litauen": "#ffc400",          # Gelb
    "Lettland": "#a63846",         # Rot
    "Estland": "#0066cc",          # Blau
    "Zypern": "#ffcc00",           # Gelb
    "Malta": "#ff0000",            # Rot
    "Luxemburg": "#0066cc",        # Blau
    "Bulgarien": "#ff0000",        # Rot
    "Serbien": "#0066ff",          # Blau
    "Bosnien": "#0066cc",          # Blau
    "Mazedonien": "#ff0000",       # Rot
    "Albanien": "#ff0000",         # Rot
    "Moldau": "#0066cc",           # Blau
    "Ukraine": "#ffcc00",          # Gelb
    "Russland": "#0066cc",         # Blau
    "Finnland": "#0066cc",         # Blau
}

# ── Land-Flaggen ────────────────────────────────────────────────────────────
COUNTRY_EMOJI = {
    "Deutschland": "🇩🇪",
    "Frankreich": "🇫🇷",
    "Österreich": "🇦🇹",
    "Schweiz": "🇨🇭",
    "Niederlande": "🇳🇱",
    "Belgien": "🇧🇪",
    "Polen": "🇵🇱",
    "Spanien": "🇪🇸",
    "Italien": "🇮🇹",
    "Schweden": "🇸🇪",
    "Dänemark": "🇩🇰",
    "Norwegen": "🇳🇴",
    "Griechenland": "🇬🇷",
    "Portugal": "🇵🇹",
    "Rumänien": "🇷🇴",
    "Tschechien": "🇨🇿",
    "Ungarn": "🇭🇺",
    "Irland": "🇮🇪",
    "England": "🇬🇧",
    "Großbritannien": "🇬🇧",
    "UK": "🇬🇧",
    "Vereinigtes Königreich": "🇬🇧",
    "Kroatien": "🇭🇷",
    "Slowakei": "🇸🇰",
    "Slowenien": "🇸🇮",
    "Litauen": "🇱🇹",
    "Lettland": "🇱🇻",
    "Estland": "🇪🇪",
    "Zypern": "🇨🇾",
    "Malta": "🇲🇹",
    "Luxemburg": "🇱🇺",
    "Bulgarien": "🇧🇬",
    "Serbien": "🇷🇸",
    "Bosnien": "🇧🇦",
    "Mazedonien": "🇲🇰",
    "Albanien": "🇦🇱",
    "Moldau": "🇲🇩",
    "Ukraine": "🇺🇦",
    "Russland": "🇷🇺",
}

# ═══ DATEN-LOADER FUNKTIONEN ═══════════════════════════════════════════════
def lade_log():
    """Lade log.json"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def lade_gesehene_artikel():
    """Lade seen.json"""
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def lade_stadte():
    """Lade cities.json"""
    try:
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def lade_laender():
    """Lade countries.json"""
    try:
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def lade_location_errors():
    """Lade location_errors.json"""
    try:
        with open(LOCATION_ERRORS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def speichere_stadte(cities):
    """Speichere cities.json"""
    with open(CITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=2, ensure_ascii=False)


# ═══ SYSTEM MONITOR ════════════════════════════════════════════════════════
class SystemMonitor:
    """Überwache CPU, RAM, etc."""
    def __init__(self):
        self.cpu_history = []
        self.ram_history = []
        self.max_history = 60
    
    def get_stats(self):
        """Hole aktuelle System-Statistiken"""
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        
        if len(self.cpu_history) > self.max_history:
            self.cpu_history.pop(0)
        if len(self.ram_history) > self.max_history:
            self.ram_history.pop(0)
        
        return {
            "cpu": cpu,
            "ram": ram,
            "cpu_avg": sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
            "ram_avg": sum(self.ram_history) / len(self.ram_history) if self.ram_history else 0,
            "cpu_max": max(self.cpu_history) if self.cpu_history else 0,
            "ram_max": max(self.ram_history) if self.ram_history else 0,
        }


# ═══ MAIN DASHBOARD CLASS ══════════════════════════════════════════════════
class VintedDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VINTED SCRAPER DASHBOARD")
        self.geometry("1600x1000")
        self.configure(bg=BG)
        self.resizable(True, True)
        
        # Leere JSON-Dateien beim Dashboard-Start
        for file in ["countries.json", "cities.json", "location_errors.json"]:
            try:
                with open(file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except:
                pass
        
        self.monitor = SystemMonitor()
        self.running = True
        self.session_start_errors_count = 0  # Starte bei 0 (Dateien sind leer)
        self.session_start_articles_count = 0  # Starte bei 0 (Dateien sind leer)
        
        self._build_ui()
        self._start_updates()
        
        # Schließen Handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _build_ui(self):
        """Baue die komplette scrollbare UI"""
        
        # ═══ HEADER ════════════════════════════════════════════════════
        header = tk.Frame(self, bg=SURFACE, relief="flat", bd=1, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        tk.Label(
            header, text="VINTED SCRAPER DASHBOARD",
            bg=SURFACE, fg=ACCENT,
            font=("Courier", 20, "bold")
        ).pack(side="left", padx=20, pady=10)
        
        self.lbl_time = tk.Label(
            header, text="",
            bg=SURFACE, fg=MUTED,
            font=("Courier", 10)
        )
        self.lbl_time.pack(side="right", padx=20, pady=10)
        
        # Trennlinie
        tk.Frame(self, bg=BORDER, height=2).pack(fill="x")
        
        # ═══ SCROLLBARES HAUPT-FENSTER ════════════════════════════════
        main_frame = tk.Frame(self, bg=BG)
        main_frame.pack(fill="both", expand=True)
        
        # Canvas mit Scrollbar
        self.canvas = tk.Canvas(main_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mit Mausrad scrollen
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ═══ INHALT ════════════════════════════════════════════════════
        
        # ─── SECTION 1: System Monitoring ────────────────────────────
        self._add_section_title(scrollable_frame, "SYSTEM MONITORING")
        
        monitor_frame = tk.Frame(scrollable_frame, bg=BG)
        monitor_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        left_mon = tk.Frame(monitor_frame, bg=BG)
        left_mon.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_mon = tk.Frame(monitor_frame, bg=BG)
        right_mon.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # CPU Panel
        self.panel_cpu = self._create_panel_pack(left_mon, "CPU Auslastung")
        self.fig_cpu = Figure(figsize=(6, 3), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_cpu = self.fig_cpu.add_subplot(111, facecolor=SURFACE2)
        self.canvas_cpu = FigureCanvasTkAgg(self.fig_cpu, master=self.panel_cpu)
        self.canvas_cpu.draw()
        self.canvas_cpu.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # RAM Panel
        self.panel_ram = self._create_panel_pack(right_mon, "RAM Auslastung")
        self.fig_ram = Figure(figsize=(6, 3), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_ram = self.fig_ram.add_subplot(111, facecolor=SURFACE2)
        self.canvas_ram = FigureCanvasTkAgg(self.fig_ram, master=self.panel_ram)
        self.canvas_ram.draw()
        self.canvas_ram.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info Panel mit 3 Charts
        self.panel_info = self._create_panel_pack(scrollable_frame, "System Info Panel")
        info_subframe = tk.Frame(self.panel_info, bg=SURFACE2)
        info_subframe.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 3 Mini-Charts nebeneinander
        info_col1 = tk.Frame(info_subframe, bg=SURFACE2)
        info_col1.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        info_col2 = tk.Frame(info_subframe, bg=SURFACE2)
        info_col2.pack(side="left", fill="both", expand=True, padx=(5, 5))
        
        info_col3 = tk.Frame(info_subframe, bg=SURFACE2)
        info_col3.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Info Chart 1: CPU Stats
        self.fig_info1 = Figure(figsize=(3, 2.5), dpi=80, facecolor=SURFACE2, edgecolor="none")
        self.ax_info1 = self.fig_info1.add_subplot(111, facecolor=SURFACE2)
        self.canvas_info1 = FigureCanvasTkAgg(self.fig_info1, master=info_col1)
        self.canvas_info1.draw()
        self.canvas_info1.get_tk_widget().pack(fill="both", expand=True)
        
        # Info Chart 2: RAM Stats
        self.fig_info2 = Figure(figsize=(3, 2.5), dpi=80, facecolor=SURFACE2, edgecolor="none")
        self.ax_info2 = self.fig_info2.add_subplot(111, facecolor=SURFACE2)
        self.canvas_info2 = FigureCanvasTkAgg(self.fig_info2, master=info_col2)
        self.canvas_info2.draw()
        self.canvas_info2.get_tk_widget().pack(fill="both", expand=True)
        
        # Info Chart 3: Location Errors & System Info
        self.fig_info3 = Figure(figsize=(3, 2.5), dpi=80, facecolor=SURFACE2, edgecolor="none")
        self.ax_info3 = self.fig_info3.add_subplot(111, facecolor=SURFACE2)
        self.canvas_info3 = FigureCanvasTkAgg(self.fig_info3, master=info_col3)
        self.canvas_info3.draw()
        self.canvas_info3.get_tk_widget().pack(fill="both", expand=True)
        
        # ─── SECTION 2: Location Error Statistiken ──────────────────
        self._add_section_title(scrollable_frame, "LOCATION EXTRACTION STATISTIKEN")
        
        # Error Percentage Chart
        self.panel_error_pct = self._create_panel_pack(scrollable_frame, "Fehlerquote & Anzahl")
        self.fig_error_pct = Figure(figsize=(12, 3), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_error_pct = self.fig_error_pct.add_subplot(111, facecolor=SURFACE2)
        self.canvas_error_pct = FigureCanvasTkAgg(self.fig_error_pct, master=self.panel_error_pct)
        self.canvas_error_pct.draw()
        self.canvas_error_pct.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # ─── SECTION 2.5: Suchbegriffe ────────────────────────────
        self._add_section_title(scrollable_frame, "SUCHBEGRIFFE STATISTIK")
        
        self.panel_searches = self._create_panel_pack(scrollable_frame, "Top Suchbegriffe")
        self.fig_searches = Figure(figsize=(12, 4), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_searches = self.fig_searches.add_subplot(111, facecolor=SURFACE2)
        self.canvas_searches = FigureCanvasTkAgg(self.fig_searches, master=self.panel_searches)
        self.canvas_searches.draw()
        self.canvas_searches.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # ─── SECTION 3: Städte (NEU) ────────────────────────────────
        self._add_section_title(scrollable_frame, "TOP 20 STADTE")
        
        self.panel_cities = self._create_panel_pack(scrollable_frame, "Top Städte & Länder (gefunden in Artikeln)")
        self.fig_cities = Figure(figsize=(12, 5), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_cities = self.fig_cities.add_subplot(111, facecolor=SURFACE2)
        self.canvas_cities = FigureCanvasTkAgg(self.fig_cities, master=self.panel_cities)
        self.canvas_cities.draw()
        self.canvas_cities.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # ─── SECTION 4: Länder (NEU) ────────────────────────────────
        self._add_section_title(scrollable_frame, "TOP 15 LAENDER")
        
        self.panel_countries = self._create_panel_pack(scrollable_frame, "Top Länder (gefunden in Artikeln)")
        self.fig_countries = Figure(figsize=(12, 4), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_countries = self.fig_countries.add_subplot(111, facecolor=SURFACE2)
        self.canvas_countries = FigureCanvasTkAgg(self.fig_countries, master=self.panel_countries)
        self.canvas_countries.draw()
        self.canvas_countries.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # ─── SECTION 5: Statistiken ────────────────────────────────
        self._add_section_title(scrollable_frame, "ALLGEMEINE STATISTIKEN")
        
        self.panel_stats = self._create_panel_pack(scrollable_frame, "Statistiken & Übersicht")
        self.fig_stats = Figure(figsize=(12, 3), dpi=80, facecolor=SURFACE, edgecolor="none")
        self.ax_stats = self.fig_stats.add_subplot(111, facecolor=SURFACE)
        self.canvas_stats = FigureCanvasTkAgg(self.fig_stats, master=self.panel_stats)
        self.canvas_stats.draw()
        self.canvas_stats.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def _add_section_title(self, parent, title):
        """Füge Section Überschrift hinzu"""
        section = tk.Frame(parent, bg=BG)
        section.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(
            section, text=title,
            bg=BG, fg=ACCENT2,
            font=("Courier", 14, "bold")
        ).pack(anchor="w")
    
    def _create_panel_pack(self, parent, title):
        """Erstelle einen Panel mit pack()"""
        panel = tk.Frame(parent, bg=SURFACE, relief="flat", bd=1)
        panel.pack(fill="x", padx=0, pady=(0, 8))
        
        # Header
        header = tk.Frame(panel, bg=SURFACE2)
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(
            header, text=title,
            bg=SURFACE2, fg=ACCENT,
            font=("Courier", 11, "bold")
        ).pack(side="left")
        
        return panel
    
    def _plot_cpu_ram(self):
        """Zeichne CPU und RAM Charts mit Farbgradient"""
        stats = self.monitor.get_stats()
        
        # CPU Chart
        self.ax_cpu.clear()
        
        # Farbcodierung basierend auf Wert (grün niedrig, rot hoch)
        colors_cpu = []
        for val in self.monitor.cpu_history:
            if val < 30:
                colors_cpu.append(GREEN)
            elif val < 60:
                colors_cpu.append(ACCENT2)
            else:
                colors_cpu.append(RED)
        
        self.ax_cpu.bar(range(len(self.monitor.cpu_history)), self.monitor.cpu_history, 
                        color=colors_cpu, edgecolor=BORDER, linewidth=0.2)
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_ylabel("CPU %", color=TEXT, fontsize=10, fontweight="bold")
        self.ax_cpu.tick_params(colors=MUTED, labelsize=8)
        self.ax_cpu.set_facecolor(SURFACE2)
        self.fig_cpu.patch.set_facecolor(SURFACE)
        self.ax_cpu.grid(True, alpha=0.1, color=BORDER, axis="y")
        self.ax_cpu.set_title(f"CPU: {stats['cpu']:.1f}% | Ø: {stats['cpu_avg']:.1f}% | Max: {stats['cpu_max']:.1f}%", 
                              color=TEXT, fontsize=9, fontweight="bold")
        self.canvas_cpu.draw_idle()
        
        # RAM Chart
        self.ax_ram.clear()
        
        colors_ram = []
        for val in self.monitor.ram_history:
            if val < 30:
                colors_ram.append(GREEN)
            elif val < 60:
                colors_ram.append(ACCENT2)
            else:
                colors_ram.append(RED)
        
        self.ax_ram.bar(range(len(self.monitor.ram_history)), self.monitor.ram_history, 
                        color=colors_ram, edgecolor=BORDER, linewidth=0.2)
        self.ax_ram.set_ylim(0, 100)
        self.ax_ram.set_ylabel("RAM %", color=TEXT, fontsize=10, fontweight="bold")
        self.ax_ram.tick_params(colors=MUTED, labelsize=8)
        self.ax_ram.set_facecolor(SURFACE2)
        self.fig_ram.patch.set_facecolor(SURFACE)
        self.ax_ram.grid(True, alpha=0.1, color=BORDER, axis="y")
        self.ax_ram.set_title(f"RAM: {stats['ram']:.1f}% | Ø: {stats['ram_avg']:.1f}% | Max: {stats['ram_max']:.1f}%", 
                              color=TEXT, fontsize=9, fontweight="bold")
        self.canvas_ram.draw_idle()
        
        # Info Panel 1: CPU Stats
        self.ax_info1.clear()
        cpu_stats_labels = ["Aktuell", "Ø", "Max"]
        cpu_stats_values = [stats['cpu'], stats['cpu_avg'], stats['cpu_max']]
        colors_info = [GREEN if v < 40 else ACCENT2 if v < 70 else RED for v in cpu_stats_values]
        self.ax_info1.barh(cpu_stats_labels, cpu_stats_values, color=colors_info, edgecolor=BORDER, linewidth=1)
        self.ax_info1.set_xlim(0, 100)
        self.ax_info1.tick_params(colors=MUTED, labelsize=8)
        self.ax_info1.set_xlabel("%", color=MUTED, fontsize=8)
        self.ax_info1.set_facecolor(SURFACE2)
        self.fig_info1.patch.set_facecolor(SURFACE2)
        self.ax_info1.grid(True, alpha=0.2, axis="x", color=BORDER)
        self.ax_info1.set_title("CPU Statistics", color=ACCENT, fontsize=9, fontweight="bold")
        for i, v in enumerate(cpu_stats_values):
            self.ax_info1.text(v + 2, i, f"{v:.1f}%", va="center", color=TEXT, fontsize=8)
        self.canvas_info1.draw_idle()
        
        # Info Panel 2: RAM Stats
        self.ax_info2.clear()
        ram_stats_labels = ["Aktuell", "Ø", "Max"]
        ram_stats_values = [stats['ram'], stats['ram_avg'], stats['ram_max']]
        colors_info = [GREEN if v < 40 else ACCENT2 if v < 70 else RED for v in ram_stats_values]
        self.ax_info2.barh(ram_stats_labels, ram_stats_values, color=colors_info, edgecolor=BORDER, linewidth=1)
        self.ax_info2.set_xlim(0, 100)
        self.ax_info2.tick_params(colors=MUTED, labelsize=8)
        self.ax_info2.set_xlabel("%", color=MUTED, fontsize=8)
        self.ax_info2.set_facecolor(SURFACE2)
        self.fig_info2.patch.set_facecolor(SURFACE2)
        self.ax_info2.grid(True, alpha=0.2, axis="x", color=BORDER)
        self.ax_info2.set_title("RAM Statistics", color=ACCENT, fontsize=9, fontweight="bold")
        for i, v in enumerate(ram_stats_values):
            self.ax_info2.text(v + 2, i, f"{v:.1f}%", va="center", color=TEXT, fontsize=8)
        self.canvas_info2.draw_idle()
        
        # Info Panel 3: System Info + Location Errors
        self.ax_info3.clear()
        self.ax_info3.axis("off")
        
        # Location Error Zähler
        location_errors = lade_location_errors()
        total_errors = len(location_errors)
        
        sys_info = f"""Prozesse:    {len(psutil.pids())}
Kerne:       {psutil.cpu_count()}
RAM Total:   {psutil.virtual_memory().total // (1024**3)} GB
RAM verfuegbar:   {psutil.virtual_memory().available // (1024**3)} GB
Loc-Fehler:   {total_errors}"""
        self.ax_info3.text(0.1, 0.9, sys_info, transform=self.ax_info3.transAxes, 
                          fontsize=9, verticalalignment="top", color=TEXT,
                          bbox=dict(boxstyle="round", facecolor=SURFACE, alpha=0.3))
        self.fig_info3.patch.set_facecolor(SURFACE2)
        self.canvas_info3.draw_idle()
    
    def _plot_searches(self):
        """Zeichne Suchbegriffe Chart"""
        log_data = lade_log()
        
        if not log_data:
            self.ax_searches.clear()
            self.ax_searches.text(0.5, 0.5, "Keine Daten", 
                                  ha="center", va="center", color=MUTED)
            self.canvas_searches.draw_idle()
            return
        
        searches = [item.get("suchbegriff", "") for item in log_data if item.get("suchbegriff")]
        search_counts = Counter(searches)
        top_searches = dict(search_counts.most_common(15))
        
        if not top_searches:
            return
        
        self.ax_searches.clear()
        labels = list(top_searches.keys())[::-1]
        values = list(top_searches.values())[::-1]
        
        colors = [ACCENT if v < 5 else ACCENT2 if v < 10 else GREEN for v in values]
        
        self.ax_searches.barh(labels, values, color=colors, edgecolor=BORDER, linewidth=0.5)
        self.ax_searches.set_xlabel("Anzahl", color=MUTED, fontsize=9)
        self.ax_searches.tick_params(colors=MUTED, labelsize=8)
        self.ax_searches.set_facecolor(SURFACE2)
        self.fig_searches.patch.set_facecolor(SURFACE)
        self.ax_searches.grid(True, alpha=0.1, axis="x", color=BORDER)
        
        self.canvas_searches.draw_idle()
    
    def _plot_cities(self):
        """Zeichne Städte Chart - Balkenfarben pro Land"""
        cities_data = lade_stadte()
        
        if not cities_data:
            self.ax_cities.clear()
            self.ax_cities.text(0.5, 0.5, "Keine Städte gefunden - Warte auf Artikel-Daten", 
                                ha="center", va="center", color=MUTED, fontsize=10)
            self.canvas_cities.draw_idle()
            return
        
        # Zähle Städte + Länder
        city_counts = {}
        for city_entry in cities_data:
            key = f"{city_entry.get('stadt', 'Unbekannt')} ({city_entry.get('land', 'Unbekannt')})"
            city_counts[key] = city_counts.get(key, 0) + 1
        
        # Top 20 (schöner aussehend)
        top_cities = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        
        if not top_cities:
            return
        
        self.ax_cities.clear()
        labels = list(top_cities.keys())[::-1]  # Umkehren für Horizontal
        values = list(top_cities.values())[::-1]
        
        # Farben pro Land extrahieren
        colors = []
        for label in labels:
            # Extrahiere Land aus Label: "Stadt (Land)"
            if "(" in label and ")" in label:
                land = label[label.rfind("(")+1:label.rfind(")")].strip()
            else:
                land = "Unbekannt"
            
            # Hole Farbe aus COUNTRY_COLORS, fallback zu ACCENT
            color = COUNTRY_COLORS.get(land, ACCENT)
            colors.append(color)
        
        bars = self.ax_cities.barh(range(len(labels)), values, color=colors, 
                                    edgecolor=BORDER, linewidth=1.5, height=0.7)
        
        # Beschriftung
        for i, (bar, v) in enumerate(zip(bars, values)):
            self.ax_cities.text(v + 0.3, bar.get_y() + bar.get_height()/2, 
                               f" {v}", va="center", color=TEXT, fontsize=9, fontweight="bold")
        
        self.ax_cities.set_yticks(range(len(labels)))
        self.ax_cities.set_yticklabels(labels, fontsize=9, color=TEXT)
        self.ax_cities.set_xlabel("Anzahl gefunden", color=TEXT, fontsize=10, fontweight="bold")
        self.ax_cities.tick_params(colors=MUTED, labelsize=8, axis="x")
        self.ax_cities.set_facecolor(SURFACE2)
        self.fig_cities.patch.set_facecolor(SURFACE)
        self.ax_cities.grid(True, alpha=0.2, axis="x", color=BORDER)
        self.ax_cities.set_title("Top 20 Staedte & Länder (farbig nach Land)", color=ACCENT, fontsize=11, fontweight="bold", pad=10)
        
        self.fig_cities.tight_layout()
        self.canvas_cities.draw_idle()
    
    def _plot_countries(self):
        """Zeichne Länder Chart - Horizontal und schöner"""
        countries_data = lade_laender()
        
        if not countries_data:
            self.ax_countries.clear()
            self.ax_countries.text(0.5, 0.5, "Keine Länder gefunden - Warte auf Artikel-Daten", 
                                   ha="center", va="center", color=MUTED, fontsize=10)
            self.canvas_countries.draw_idle()
            return
        
        # Zähle Länder
        country_counts = {}
        for country_entry in countries_data:
            land = country_entry.get('land', 'Unbekannt')
            if land != 'Unbekannt':
                country_counts[land] = country_counts.get(land, 0) + 1
        
        # Top 15
        top_countries = dict(sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:15])
        
        if not top_countries:
            return
        
        self.ax_countries.clear()
        labels = list(top_countries.keys())[::-1]  # Umkehren für Horizontal
        values = list(top_countries.values())[::-1]
        
        # Farben basierend auf Häufigkeit mit Gradient
        colors = []
        max_val = max(values) if values else 1
        for v in values:
            ratio = v / max_val
            if ratio > 0.7:
                colors.append(RED)
            elif ratio > 0.5:
                colors.append(ACCENT2)
            elif ratio > 0.3:
                colors.append(ACCENT)
            else:
                colors.append(GREEN)
        
        bars = self.ax_countries.barh(range(len(labels)), values, color=colors, 
                                       edgecolor=BORDER, linewidth=1.5, height=0.7)
        
        # Beschriftung
        for i, (bar, v) in enumerate(zip(bars, values)):
            self.ax_countries.text(v + 0.3, bar.get_y() + bar.get_height()/2, 
                                  f" {v}", va="center", color=TEXT, fontsize=9, fontweight="bold")
        
        self.ax_countries.set_yticks(range(len(labels)))
        self.ax_countries.set_yticklabels(labels, fontsize=9, color=TEXT)
        self.ax_countries.set_xlabel("Anzahl gefunden", color=TEXT, fontsize=10, fontweight="bold")
        self.ax_countries.tick_params(colors=MUTED, labelsize=8, axis="x")
        self.ax_countries.set_facecolor(SURFACE2)
        self.fig_countries.patch.set_facecolor(SURFACE)
        self.ax_countries.grid(True, alpha=0.2, axis="x", color=BORDER)
        self.ax_countries.set_title("Top 15 Länder", color=ACCENT, fontsize=11, fontweight="bold", pad=10)
        
        self.fig_countries.tight_layout()
        self.canvas_countries.draw_idle()
    
    def _plot_error_percentage(self):
        """Zeichne Fehlerquote - ALLE Fehler/Artikel seit session Start"""
        location_errors = lade_location_errors()
        
        self.ax_error_pct.clear()
        
        if not location_errors:
            self.ax_error_pct.text(0.5, 0.5, "Warte auf neue Artikel...", 
                                  ha="center", va="center", color=MUTED, fontsize=11)
            self.canvas_error_pct.draw_idle()
            return
        
        # Zähle Fehler vs Erfolg aus location_errors.json
        total_errors = len([e for e in location_errors if e.get('error_type') != 'success'])
        total_success = len([e for e in location_errors if e.get('error_type') == 'success'])
        total_articles = total_errors + total_success
        
        error_percentage = (total_errors / total_articles * 100) if total_articles > 0 else 0
        successful_articles = total_success
        
        # Bar Chart: Fehler vs Success
        categories = ['Fehler', 'Erfolgreich']
        values = [total_errors, successful_articles]
        colors = [RED, GREEN]
        
        bars = self.ax_error_pct.bar(categories, values, color=colors, 
                                     edgecolor=BORDER, linewidth=2, width=0.5, alpha=0.8)
        
        # Beschriftungen auf Balken
        for bar, val in zip(bars, values):
            height = bar.get_height()
            self.ax_error_pct.text(bar.get_x() + bar.get_width()/2., height,
                                  f'{val}\n({val/total_articles*100:.1f}%)' if total_articles > 0 else f'{val}',
                                  ha='center', va='bottom', color=TEXT, fontsize=10, fontweight='bold')
        
        # Fehlerquote Text
        error_msg = f"Fehlerquote: {error_percentage:.1f}%"
        self.ax_error_pct.text(0.5, -0.25, error_msg, 
                              transform=self.ax_error_pct.transAxes,
                              ha='center', va='top', color=RED if error_percentage > 5 else GREEN,
                              fontsize=11, fontweight='bold')
        
        self.ax_error_pct.set_ylabel('Anzahl Artikel', color=TEXT, fontsize=10, fontweight='bold')
        self.ax_error_pct.set_ylim(0, max(values) * 1.3 if values else 10)
        self.ax_error_pct.tick_params(colors=MUTED, labelsize=9, axis='y')
        self.ax_error_pct.set_xticks([0, 1])
        self.ax_error_pct.set_xticklabels(categories, fontsize=10, color=TEXT, fontweight='bold')
        self.ax_error_pct.grid(axis='y', alpha=0.2, color=MUTED, linestyle='--')
        self.ax_error_pct.set_facecolor(SURFACE2)
        self.fig_error_pct.patch.set_facecolor(SURFACE)
        self.canvas_error_pct.draw_idle()
    
    def _plot_stats(self):
        """Zeichne allgemeine Statistiken - schöner"""
        seen = lade_gesehene_artikel()
        log_data = lade_log()
        cities_data = lade_stadte()
        
        unique_searches = len(set(item.get("suchbegriff", "") for item in log_data))
        unique_cities = len(set(f"{c.get('stadt', '')}-{c.get('land', '')}" for c in cities_data))
        today_count = len([e for e in log_data if e.get('zeit', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
        
        # Erstelle eine schönere Visualisierung
        self.ax_stats.clear()
        self.ax_stats.axis("off")
        
        stats_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    VINTED SCRAPER STATISTIKEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Artikel gefunden:        {len(seen):>6}
  Suchvorgänge gesamt:     {len(log_data):>6}
  Suchkategorien (unique): {unique_searches:>6}
  
  Staedte gefunden:        {unique_cities:>6}
  Eintraege heute:         {today_count:>6}
  
  Zuletzt aktualisiert:    {datetime.now().strftime('%H:%M:%S')}
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        self.ax_stats.text(0.05, 0.95, stats_text, transform=self.ax_stats.transAxes,
                          fontsize=10, verticalalignment="top", color=TEXT,
                          bbox=dict(boxstyle="round,pad=1", facecolor=SURFACE2, 
                                   edgecolor=BORDER, linewidth=2, alpha=0.8))
        
        self.fig_stats.patch.set_facecolor(SURFACE)
        self.canvas_stats.draw_idle()
    
    def _start_updates(self):
        """Starte regelmäßige Updates"""
        def update_loop():
            while self.running:
                try:
                    self._plot_cpu_ram()
                    self._plot_searches()
                    self._plot_cities()
                    self._plot_countries()
                    self._plot_error_percentage()
                    self._plot_stats()
                    
                    self.lbl_time.config(text=f"{datetime.now().strftime('%H:%M:%S')}")
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"Update Error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def on_closing(self):
        """Schließe sauber"""
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = VintedDashboard()
    app.mainloop()
