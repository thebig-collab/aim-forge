import csv
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
 QListWidget,QStackedWidget,QFrame,QGridLayout,QComboBox,QSlider,QColorDialog,QSpinBox,
 QLineEdit,QMessageBox,QFileDialog,QTableWidget,QTableWidgetItem,QHeaderView,QCheckBox)
from .monitor import PerformanceMonitor
from .overlay import CrosshairOverlay
from . import storage
from .i18n import LANGUAGES, RTL, LABELS

STYLE = """
QWidget { background:#0b1020; color:#e7edf7; font-family:'Segoe UI'; font-size:10pt; }
QLabel#muted { color:#8c9ab2; }
QFrame#panel { background:#131c30; border:1px solid #263550; border-radius:12px; }
QPushButton { background:#1d2b45; border:1px solid #344968; border-radius:8px; padding:9px 13px; }
QPushButton:hover { background:#293d60; }
QPushButton#accent { background:#00b884; color:#04140f; font-weight:700; border:0; }
QListWidget { background:#10182a; border:0; padding:8px; }
QListWidget::item { padding:12px; border-radius:7px; }
QListWidget::item:selected { background:#1b3e45; color:#5fffc5; }
QLineEdit,QSpinBox,QComboBox { background:#0e1728; border:1px solid #344968; border-radius:7px; padding:7px; }
QTableWidget { background:#10182a; gridline-color:#263550; }
QHeaderView::section { background:#1a2942; padding:7px; border:0; }
"""

def make_card(title, note):
    f=QFrame(); f.setObjectName("panel"); lay=QVBoxLayout(f)
    t=QLabel(title); t.setObjectName("muted"); v=QLabel("—")
    v.setStyleSheet("font-size:22pt;font-weight:700;color:#5fffc5")
    n=QLabel(note); n.setObjectName("muted"); lay.addWidget(t); lay.addWidget(v); lay.addWidget(n)
    return f,v

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AimForge | Gaming Command Center"); self.resize(1180,760)
        self.setStyleSheet(STYLE); self.monitor=PerformanceMonitor(); self.overlay=CrosshairOverlay()
        self.color="#00ff88"; self.language="English"; self._history_tick=0; self._build()
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1000)
        self.shortcut=QShortcut(QKeySequence("Ctrl+Shift+X"),self); self.shortcut.activated.connect(self.toggle_overlay)

    def _build(self):
        center=QWidget(); self.setCentralWidget(center); root=QHBoxLayout(center); root.setContentsMargins(0,0,0,0)
        side=QFrame(); side.setFixedWidth(220); side.setStyleSheet("background:#080d19;border:0")
        sl=QVBoxLayout(side); brand=QLabel("AIMFORGE"); brand.setStyleSheet("font-size:21pt;font-weight:900;color:#5fffc5;padding:16px")
        sl.addWidget(brand); self.nav=QListWidget(); self.pages=["Dashboard","Crosshair Studio","Live Monitor","Game Profiles","Benchmarks","Upgrade Advisor","Settings"]
        self.nav.addItems(self.pages); sl.addWidget(self.nav); sl.addStretch()
        sl.addWidget(QLabel("CTRL + SHIFT + X\\nToggle crosshair")); root.addWidget(side)
        body=QVBoxLayout(); body.setContentsMargins(24,20,24,20); self.title=QLabel("Dashboard"); self.title.setStyleSheet("font-size:20pt;font-weight:700")
        body.addWidget(self.title); self.stack=QStackedWidget()
        for fn in [self.dashboard,self.crosshair,self.monitor_page,self.profiles_page,self.benchmarks_page,self.advisor_page,self.settings_page]:
            self.stack.addWidget(fn())
        body.addWidget(self.stack); self.nav.currentRowChanged.connect(self.change_page); self.nav.setCurrentRow(0); root.addLayout(body,1)

    def change_page(self,i):
        self.stack.setCurrentIndex(i); self.title.setText(self.pages[i])

    def dashboard(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel("Your gaming command center"))
        sub=QLabel("Local-first tools for crosshairs, PC telemetry and performance data."); sub.setObjectName("muted"); l.addWidget(sub)
        grid=QGridLayout(); self.dash={}
        for i,(k,note) in enumerate([("Live FPS","PresentMon CSV required"),("CPU usage","Live system utilization"),("RAM used","Used memory"),("GPU temperature","Sensor provider required")]):
            f,v=make_card(k,note); self.dash[k]=v; grid.addWidget(f,0,i)
        l.addLayout(grid)
        quick=QFrame(); quick.setObjectName("panel"); q=QVBoxLayout(quick); q.addWidget(QLabel("Quick actions"))
        for label,index in [("Open Crosshair Studio",1),("Open Live Monitor",2),("Game Profiles",3)]:
            b=QPushButton(label); b.clicked.connect(lambda checked=False,n=index:self.nav.setCurrentRow(n)); q.addWidget(b)
        l.addWidget(quick); l.addStretch(); return w

    def crosshair(self):
        w=QWidget(); l=QVBoxLayout(w); info=QLabel("Desktop overlay only. Check each game's and anti-cheat's overlay policy before enabling.")
        info.setObjectName("muted"); l.addWidget(info); panel=QFrame(); panel.setObjectName("panel"); g=QGridLayout(panel)
        self.style_box=QComboBox(); self.style_box.addItems(["Classic","Dot","Circle"])
        self.size=QSpinBox(); self.size.setRange(2,100); self.size.setValue(18)
        self.gap=QSpinBox(); self.gap.setRange(0,50); self.gap.setValue(5)
        self.thick=QSpinBox(); self.thick.setRange(1,12); self.thick.setValue(2)
        self.opacity=QSlider(Qt.Horizontal); self.opacity.setRange(10,100); self.opacity.setValue(100)
        color=QPushButton("Choose color"); color.clicked.connect(self.choose_color)
        for i,(name,widget) in enumerate([("Style",self.style_box),("Size",self.size),("Gap",self.gap),("Thickness",self.thick),("Opacity",self.opacity),("Color",color)]):
            g.addWidget(QLabel(name),i,0); g.addWidget(widget,i,1)
        l.addWidget(panel); row=QHBoxLayout(); show=QPushButton("Apply & show overlay"); show.setObjectName("accent"); show.clicked.connect(self.apply_overlay)
        hide=QPushButton("Hide overlay"); hide.clicked.connect(self.overlay.hide); row.addWidget(show); row.addWidget(hide); l.addLayout(row); l.addStretch(); return w

    def monitor_page(self):
        w=QWidget(); l=QVBoxLayout(w); n=QLabel("CPU/RAM are read locally. FPS requires PresentMon CSV. Unsupported GPU sensor fields stay unavailable.")
        n.setObjectName("muted"); l.addWidget(n); grid=QGridLayout(); self.metrics={}
        for i,k in enumerate(["fps","avg_fps","one_percent_low","cpu_usage","ram_used_gb","gpu_temp","gpu_usage","vram_used","cpu_clock","gpu_clock","gpu_power"]):
            f,v=make_card(k.replace("_"," ").title(),"—"); self.metrics[k]=v; grid.addWidget(f,i//3,i%3)
        l.addLayout(grid); b=QPushButton("Select PresentMon CSV"); b.clicked.connect(self.select_csv); l.addWidget(b); self.csv_note=QLabel("No telemetry file selected"); self.csv_note.setObjectName("muted"); l.addWidget(self.csv_note); l.addStretch(); return w

    def profiles_page(self):
        w=QWidget(); l=QVBoxLayout(w); row=QHBoxLayout(); self.game=QLineEdit(); self.game.setPlaceholderText("Game name")
        save=QPushButton("Save crosshair profile"); save.setObjectName("accent"); save.clicked.connect(self.save_profile); row.addWidget(self.game); row.addWidget(save); l.addLayout(row)
        self.profile_table=QTableWidget(0,3); self.profile_table.setHorizontalHeaderLabels(["Game","Style","Updated"]); self.profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); l.addWidget(self.profile_table); self.load_profiles(); return w

    def benchmarks_page(self):
        w=QWidget(); l=QVBoxLayout(w); n=QLabel("No benchmark values are bundled. Import sourced records; measured and estimated entries are labeled separately.")
        n.setObjectName("muted"); l.addWidget(n); b=QPushButton("Import benchmark CSV"); b.clicked.connect(self.import_benchmarks); l.addWidget(b)
        self.bench_count=QLabel(); l.addWidget(self.bench_count); self.bench_table=QTableWidget(0,7)
        self.bench_table.setHorizontalHeaderLabels(["Game","CPU","GPU","Resolution","Preset","Avg FPS","Kind"]); self.bench_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); l.addWidget(self.bench_table); self.load_benchmarks(); return w

    def advisor_page(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel("Compare sourced benchmark scores and real upgrade prices. This does not claim guaranteed FPS uplift."))
        self.score_a=QLineEdit(); self.score_a.setPlaceholderText("Current benchmark score")
        self.score_b=QLineEdit(); self.score_b.setPlaceholderText("Candidate benchmark score")
        self.price=QLineEdit(); self.price.setPlaceholderText("Upgrade price")
        for x in (self.score_a,self.score_b,self.price): l.addWidget(x)
        b=QPushButton("Compare scenario"); b.setObjectName("accent"); b.clicked.connect(self.compare); l.addWidget(b)
        self.advice=QLabel("Enter scores and price."); self.advice.setWordWrap(True); l.addWidget(self.advice); l.addStretch(); return w

    def settings_page(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel("Local settings and data management"))
        lang=QComboBox(); lang.addItems(LANGUAGES); lang.currentTextChanged.connect(self.set_language); l.addWidget(QLabel("Language")); l.addWidget(lang)
        l.addWidget(QLabel("Hebrew and Arabic switch the interface direction to RTL."))
        b=QPushButton("Export local backup"); b.clicked.connect(self.backup); l.addWidget(b)
        r=QPushButton("Restore local backup"); r.clicked.connect(self.restore); l.addWidget(r)
        l.addWidget(QLabel("Shortcut Ctrl+Shift+X works while AimForge is active. Startup, tray, auto-update and system-wide hotkeys are not included yet."))
        l.addStretch(); return w

    def set_language(self,lang):
        self.language=lang; self.setLayoutDirection(Qt.RightToLeft if lang in RTL else Qt.LeftToRight)
        for i,label in enumerate(LABELS.get(lang,LABELS["English"])): self.nav.item(i).setText(label)

    def choose_color(self):
        c=QColorDialog.getColor(QColor(self.color),self)
        if c.isValid(): self.color=c.name()

    def apply_overlay(self):
        self.overlay.configure(self.size.value(),self.gap.value(),self.thick.value(),self.color,self.opacity.value()/100,self.style_box.currentText())
        screen=self.screen()
        if screen: self.overlay.setGeometry(screen.geometry())
        self.overlay.show()

    def toggle_overlay(self):
        if self.overlay.isVisible(): self.overlay.hide()
        else: self.apply_overlay()

    def select_csv(self):
        p,_=QFileDialog.getOpenFileName(self,"Select PresentMon CSV","","CSV (*.csv)")
        if p: self.monitor.set_csv(p); self.csv_note.setText(Path(p).name)

    def refresh(self):
        s=self.monitor.snapshot()
        def f(v,suffix="",d=0): return "—" if v is None else f"{v:.{d}f}{suffix}"
        vals={"fps":f(s["fps"]),"avg_fps":f(s["avg_fps"]),"one_percent_low":f(s["one_percent_low"]),
              "cpu_usage":f(s["cpu_usage"],"%"),"ram_used_gb":f(s["ram_used_gb"]," GB",1)}
        for k,v in self.metrics.items(): v.setText(vals.get(k,"—"))
        for k,v in self.dash.items():
            v.setText({"Live FPS":vals["fps"],"CPU usage":vals["cpu_usage"],"RAM used":vals["ram_used_gb"],"GPU temperature":"—"}[k])
        self._history_tick += 1
        if self._history_tick % 15 == 0:
            storage.add_session({"time":datetime.now().isoformat(timespec="seconds"),"fps":s["fps"],"cpu_usage":s["cpu_usage"],"ram_used_gb":s["ram_used_gb"]})

    def save_profile(self):
        name=self.game.text().strip()
        if not name: QMessageBox.warning(self,"Game missing","Enter a game name."); return
        storage.save_profile(name,{"crosshair":{"style":self.style_box.currentText(),"size":self.size.value(),"gap":self.gap.value(),"thickness":self.thick.value(),"color":self.color,"opacity":self.opacity.value()/100}})
        self.load_profiles()

    def load_profiles(self):
        if not hasattr(self,"profile_table"): return
        data=storage.profiles(); self.profile_table.setRowCount(len(data))
        for i,(name,p) in enumerate(data.items()):
            for j,val in enumerate([name,p.get("crosshair",{}).get("style","Classic"),p.get("updated_at","")]):
                self.profile_table.setItem(i,j,QTableWidgetItem(str(val)))

    def import_benchmarks(self):
        path,_=QFileDialog.getOpenFileName(self,"Import benchmark CSV","","CSV (*.csv)")
        if not path: return
        required={"game","cpu","gpu","resolution","preset","avg_fps","one_percent_low","source","benchmark_date","kind"}
        try:
            with open(path,encoding="utf-8-sig",newline="") as f:
                reader=csv.DictReader(f)
                if not required.issubset(set(reader.fieldnames or [])): raise ValueError("Missing required columns; see benchmark_template.csv.")
                rows=[]
                for r in reader:
                    if r["kind"] not in ("measured","estimated"): raise ValueError("kind must be measured or estimated")
                    a=float(r["avg_fps"]); low=float(r["one_percent_low"])
                    if a<=0 or low<0: raise ValueError("Invalid FPS values")
                    rows.append({**r,"avg_fps":a,"one_percent_low":low})
            storage.add_benchmarks(rows); self.load_benchmarks(); QMessageBox.information(self,"Imported",f"{len(rows)} records imported.")
        except Exception as e: QMessageBox.critical(self,"Import failed",str(e))

    def load_benchmarks(self):
        if not hasattr(self,"bench_table"): return
        rows=storage.benchmarks(); self.bench_count.setText(f"Records stored locally: {len(rows)}"); self.bench_table.setRowCount(min(500,len(rows)))
        for i,r in enumerate(rows[-500:]):
            for j,v in enumerate([r.get("game"),r.get("cpu"),r.get("gpu"),r.get("resolution"),r.get("preset"),r.get("avg_fps"),r.get("kind")]):
                self.bench_table.setItem(i,j,QTableWidgetItem(str(v)))

    def compare(self):
        try:
            a,b,p=map(float,(self.score_a.text(),self.score_b.text(),self.price.text()))
            if min(a,b,p)<=0: raise ValueError()
            gain=b-a
            self.advice.setText(f"Score change: {gain:+.1f} ({gain/a*100:+.1f}%). Score gain per currency unit: {gain/p:.4f}. Based only on values you entered; not an FPS guarantee.")
        except ValueError: QMessageBox.warning(self,"Invalid input","Enter positive numeric scores and price.")

    def backup(self):
        p,_=QFileDialog.getSaveFileName(self,"Export backup","aimforge-backup.json","JSON (*.json)")
        if p: storage.backup(p); QMessageBox.information(self,"Backup","Export complete.")

    def restore(self):
        p,_=QFileDialog.getOpenFileName(self,"Restore backup","","JSON (*.json)")
        if p:
            try: storage.restore(p); self.load_profiles(); self.load_benchmarks()
            except Exception as e: QMessageBox.critical(self,"Restore failed",str(e))
