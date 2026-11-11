import csv
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QPainter, QPen
from PySide6.QtWidgets import (QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,
 QListWidget,QStackedWidget,QFrame,QGridLayout,QComboBox,QSlider,QColorDialog,QSpinBox,
 QLineEdit,QMessageBox,QFileDialog,QTableWidget,QTableWidgetItem,QHeaderView,QCheckBox)
from .monitor import PerformanceMonitor
from .overlay import CrosshairOverlay
from . import storage
from .i18n import LANGUAGES, RTL, LABELS

STYLE = """
QWidget { background:#0b0d16; color:#eef0fa; font-family:'Segoe UI'; font-size:10pt; }
QLabel#muted { color:#858ba3; }
QFrame#panel { background:#141725; border:1px solid #292d42; border-radius:13px; }
QPushButton { background:#1b2032; border:1px solid #30364e; border-radius:9px; padding:10px 14px; }
QPushButton:hover { background:#282e45; border-color:#6655c9; }
QPushButton#accent { background:#7657f6; color:white; font-weight:700; border:0; }
QPushButton#accent:hover { background:#896eff; }
QListWidget { background:#090b12; border:0; padding:10px; outline:0; }
QListWidget::item { padding:13px 12px; border-radius:8px; color:#a6abc0; }
QListWidget::item:selected { background:#24203c; color:#b9aaff; border-left:3px solid #8b70ff; }
QLineEdit,QSpinBox,QComboBox { background:#101321; border:1px solid #30364e; border-radius:8px; padding:8px; selection-background-color:#7657f6; }
QSlider::groove:horizontal { height:5px; background:#30364e; border-radius:2px; }
QSlider::handle:horizontal { background:#9b83ff; width:14px; margin:-5px 0; border-radius:7px; }
QCheckBox { spacing:8px; }
QCheckBox::indicator { width:16px; height:16px; }
QTableWidget { background:#101321; gridline-color:#292d42; border:1px solid #292d42; border-radius:8px; }
QHeaderView::section { background:#1b2032; color:#aeb4ca; padding:8px; border:0; }
"""

def make_card(title, note):
    f=QFrame(); f.setObjectName("panel"); lay=QVBoxLayout(f)
    t=QLabel(title); t.setObjectName("muted"); v=QLabel("—")
    v.setStyleSheet("font-size:22pt;font-weight:700;color:#5fffc5")
    n=QLabel(note); n.setObjectName("muted"); lay.addWidget(t); lay.addWidget(v); lay.addWidget(n)
    return f,v


class CrosshairPreview(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setMinimumSize(250,180)
        self.config={"style":"Classic","size":18,"gap":5,"thickness":2,"color":"#00ff88","opacity":100,"dot":False,"outline":False,"outline_color":"#000000"}
    def set_config(self,cfg):
        self.config=dict(cfg); self.update()
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(),QColor("#080d19"))
        c=QColor(self.config.get("color","#00ff88")); c.setAlphaF(max(.1,min(1,float(self.config.get("opacity",100))/100)))
        s=int(self.config.get("size",18)); g=int(self.config.get("gap",5)); t=int(self.config.get("thickness",2))
        x,y=self.width()//2,self.height()//2
        outlined=bool(self.config.get("outline",False)); outline_color=QColor(self.config.get("outline_color","#000000")); outline_color.setAlpha(c.alpha())
        def stroke(pen_color,width):
            p.setPen(QPen(pen_color,width,Qt.SolidLine,Qt.RoundCap)); p.setBrush(Qt.NoBrush)
            if self.config.get("style")=="Circle": p.drawEllipse(x-s//2,y-s//2,s,s)
            else:
                p.drawLine(x-s,y,x-g,y); p.drawLine(x+g,y,x+s,y)
                p.drawLine(x,y-s,x,y-g); p.drawLine(x,y+g,x,y+s)
        if self.config.get("style")=="Dot":
            d=max(2,t*2)
            if outlined:
                p.setPen(Qt.NoPen); p.setBrush(outline_color); p.drawEllipse(x-d//2-2,y-d//2-2,d+4,d+4)
            p.setPen(Qt.NoPen); p.setBrush(c); p.drawEllipse(x-d//2,y-d//2,d,d)
        else:
            if outlined: stroke(outline_color,t+4)
            stroke(c,t)
            if self.config.get("dot"):
                d=max(2,t*2)
                if outlined:
                    p.setPen(Qt.NoPen); p.setBrush(QColor(0,0,0,c.alpha())); p.drawEllipse(x-d//2-2,y-d//2-2,d+4,d+4)
                p.setPen(Qt.NoPen); p.setBrush(c); p.drawEllipse(x-d//2,y-d//2,d,d)

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
        sl.addWidget(brand)
        tagline=QLabel("PRECISION • CONTROL • PLAY"); tagline.setStyleSheet("font-size:8pt;color:#777d96;padding:0 16px 14px")
        sl.addWidget(tagline); self.nav=QListWidget()
        self.pages=["Home","Browse Crosshairs","Designer","Saved Profiles","PC Monitor","Benchmarks","Gaming Tweaks","Settings"]
        self.nav.addItems(self.pages); sl.addWidget(self.nav); sl.addStretch()
        self.overlay_status=QLabel("●  OVERLAY OFF"); self.overlay_status.setStyleSheet("color:#858ba3;padding:12px")
        sl.addWidget(self.overlay_status)
        sl.addWidget(QLabel("CTRL + SHIFT + X  •  Toggle")); root.addWidget(side)
        body=QVBoxLayout(); body.setContentsMargins(28,22,28,22)
        header=QHBoxLayout(); self.title=QLabel("Home"); self.title.setStyleSheet("font-size:22pt;font-weight:750")
        self.quick_toggle=QPushButton("Show Crosshair"); self.quick_toggle.setObjectName("accent"); self.quick_toggle.clicked.connect(self.toggle_overlay)
        header.addWidget(self.title); header.addStretch(); header.addWidget(self.quick_toggle); body.addLayout(header)
        self.stack=QStackedWidget()
        for fn in [self.dashboard,self.browse_page,self.crosshair,self.profiles_page,self.monitor_page,self.benchmarks_page,self.tweaks_page,self.settings_page]:
            self.stack.addWidget(fn())
        body.addWidget(self.stack); self.nav.currentRowChanged.connect(self.change_page); self.nav.setCurrentRow(0); root.addLayout(body,1)

    def change_page(self,i):
        self.stack.setCurrentIndex(i); self.title.setText(self.pages[i])

    def dashboard(self):
        w=QWidget(); l=QVBoxLayout(w)
        hero=QFrame(); hero.setObjectName("panel"); hl=QVBoxLayout(hero)
        h=QLabel("Your aim. Your style."); h.setStyleSheet("font-size:25pt;font-weight:800;color:#c7bbff")
        sub=QLabel("Build a crosshair that feels right. Save it, switch it, and take it into your games."); sub.setObjectName("muted")
        hl.addWidget(h); hl.addWidget(sub); l.addWidget(hero)
        grid=QGridLayout(); self.dash={}
        for i,(k,note) in enumerate([("Live FPS","PresentMon CSV required"),("CPU usage","Live system utilization"),("RAM used","Used memory"),("GPU temperature","Sensor provider required")]):
            f,v=make_card(k,note); self.dash[k]=v; grid.addWidget(f,0,i)
        l.addLayout(grid)
        quick=QFrame(); quick.setObjectName("panel"); q=QVBoxLayout(quick); q.addWidget(QLabel("Quick actions"))
        for label,index in [("Browse Crosshairs",1),("Open Designer",2),("Saved Profiles",3)]:
            b=QPushButton(label); b.clicked.connect(lambda checked=False,n=index:self.nav.setCurrentRow(n)); q.addWidget(b)
        l.addWidget(quick); l.addStretch(); return w

    def browse_page(self):
        w=QWidget(); l=QVBoxLayout(w)
        intro=QLabel("Pick a starting point. Every preset is editable in the Designer."); intro.setObjectName("muted"); l.addWidget(intro)
        self.preset_search=QLineEdit(); self.preset_search.setPlaceholderText("Search presets…"); self.preset_search.textChanged.connect(self.filter_presets); l.addWidget(self.preset_search)
        self.preset_grid=QGridLayout(); l.addLayout(self.preset_grid); l.addStretch()
        self.preset_cards=[]
        presets=[
            ("Neon Classic","Classic",22,5,2,"#00ff88",100,False,True),
            ("Clean White","Classic",18,6,2,"#ffffff",100,False,False),
            ("Tiny Cyan","Classic",10,3,1,"#00e5ff",100,True,False),
            ("Violet Dot","Dot",8,0,3,"#a78bfa",100,False,True),
            ("Minimal Red","Classic",14,4,1,"#ff4655",95,False,False),
            ("Precision Circle","Circle",24,0,2,"#f8fafc",90,False,True),
            ("Toxic Green","Classic",20,2,3,"#7CFC00",100,True,True),
            ("Gold Compact","Classic",12,3,2,"#ffc857",100,False,True),
            ("Ice Blue","Classic",26,7,2,"#60a5fa",85,False,True),
            ("Pink Dot","Dot",6,0,2,"#ff70c8",100,False,False),
            ("Stealth Gray","Classic",16,5,2,"#d1d5db",75,False,True),
            ("Wide Tactical","Classic",30,9,2,"#facc15",100,False,True)]
        self.presets=[]
        for name,style,size,gap,thick,color,opacity,dot,outline in presets:
            cfg={"style":style,"size":size,"gap":gap,"thickness":thick,"color":color,"opacity":opacity,"dot":dot,"outline":outline}
            card=QFrame(); card.setObjectName("panel"); cl=QVBoxLayout(card)
            sample=QLabel("✛" if style=="Classic" else ("●" if style=="Dot" else "◎")); sample.setAlignment(Qt.AlignCenter)
            sample.setStyleSheet(f"font-size:32pt;font-weight:300;color:{color};padding:12px")
            title=QLabel(name); title.setStyleSheet("font-weight:700")
            btn=QPushButton("Use preset"); btn.setObjectName("accent"); btn.clicked.connect(lambda checked=False,cfg=cfg:self.use_preset(cfg))
            cl.addWidget(sample); cl.addWidget(title); cl.addWidget(btn)
            self.presets.append((name,card));
        self.filter_presets(); return w

    def filter_presets(self,*_):
        if not hasattr(self,"preset_grid"): return
        while self.preset_grid.count():
            item=self.preset_grid.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        query=self.preset_search.text().casefold().strip()
        visible=[(name,card) for name,card in self.presets if not query or query in name.casefold()]
        for i,(_,card) in enumerate(visible): self.preset_grid.addWidget(card,i//3,i%3)

    def use_preset(self,cfg):
        self.nav.setCurrentRow(2); self.load_crosshair_config(cfg)

    def load_crosshair_config(self,cfg):
        self.style_box.setCurrentText(cfg.get("style","Classic")); self.size.setValue(int(cfg.get("size",18)))
        self.gap.setValue(int(cfg.get("gap",5))); self.thick.setValue(int(cfg.get("thickness",2)))
        op=float(cfg.get("opacity",100)); self.opacity.setValue(int(op*100 if op<=1 else op))
        self.color_edit.setText(cfg.get("color","#00ff88")); self.outline_color_edit.setText(cfg.get("outline_color","#000000")); self.dot.setChecked(bool(cfg.get("dot",False)))
        self.outline.setChecked(bool(cfg.get("outline",False))); self.update_crosshair_preview()

    def crosshair(self):
        w=QWidget(); l=QVBoxLayout(w)
        info=QLabel("DESIGNER  /  Customize every detail, preview instantly, then apply or save your design. Overlay-only — it does not modify game files.")
        info.setObjectName("muted"); info.setWordWrap(True); l.addWidget(info)
        content=QHBoxLayout(); panel=QFrame(); panel.setObjectName("panel"); g=QGridLayout(panel)
        self.style_box=QComboBox(); self.style_box.addItems(["Classic","Dot","Circle"])
        self.size=QSpinBox(); self.size.setRange(2,100); self.size.setValue(18)
        self.gap=QSpinBox(); self.gap.setRange(0,50); self.gap.setValue(5)
        self.thick=QSpinBox(); self.thick.setRange(1,12); self.thick.setValue(2)
        self.opacity=QSlider(Qt.Horizontal); self.opacity.setRange(10,100); self.opacity.setValue(100)
        self.opacity_value=QLabel("100%"); self.dot=QCheckBox("Center dot"); self.outline=QCheckBox("Outline (black border)")
        self.color_edit=QLineEdit("#00ff88"); self.color_edit.setMaxLength(7)
        self.outline_color_edit=QLineEdit("#000000"); self.outline_color_edit.setMaxLength(7)
        outline_pick=QPushButton("Pick outline"); outline_pick.clicked.connect(lambda:self.choose_specific_color(self.outline_color_edit))
        outline_row=QHBoxLayout(); outline_row.addWidget(self.outline_color_edit); outline_row.addWidget(outline_pick)
        pick=QPushButton("Pick color"); pick.clicked.connect(self.choose_color)
        cr=QHBoxLayout(); cr.addWidget(self.color_edit); cr.addWidget(pick)
        for i,(name,widget) in enumerate([("Shape",self.style_box),("Size",self.size),("Gap",self.gap),("Thickness",self.thick),("Opacity",self.opacity)]):
            g.addWidget(QLabel(name),i,0); g.addWidget(widget,i,1)
        g.addWidget(self.opacity_value,4,2); g.addWidget(self.dot,5,1); g.addWidget(self.outline,5,2); g.addWidget(QLabel("Crosshair color"),6,0); g.addLayout(cr,6,1,1,2)
        g.addWidget(QLabel("Outline color"),7,0); g.addLayout(outline_row,7,1,1,2)
        content.addWidget(panel,3); pv=QVBoxLayout(); preview_title=QLabel("LIVE PREVIEW"); preview_title.setStyleSheet("font-weight:700;letter-spacing:1px;color:#aaa1d8"); pv.addWidget(preview_title); self.preview=CrosshairPreview(); pv.addWidget(self.preview,1); pv_frame=QFrame(); pv_frame.setObjectName("panel"); pv_frame.setLayout(pv); content.addWidget(pv_frame,2); l.addLayout(content,1)
        self.crosshair_game=QLineEdit(); self.crosshair_game.setPlaceholderText("Game name, e.g. Fortnite")
        row=QHBoxLayout(); row.addWidget(self.crosshair_game)
        save=QPushButton("Save game profile"); save.setObjectName("accent"); save.clicked.connect(self.save_studio_profile); row.addWidget(save)
        exp=QPushButton("Export preset"); exp.clicked.connect(self.export_crosshair); row.addWidget(exp)
        imp=QPushButton("Import preset"); imp.clicked.connect(self.import_crosshair); row.addWidget(imp); l.addLayout(row)
        actions=QHBoxLayout(); show=QPushButton("Apply & show overlay"); show.setObjectName("accent"); show.clicked.connect(self.apply_overlay)
        hide=QPushButton("Hide overlay"); hide.clicked.connect(self.hide_overlay); actions.addWidget(show); actions.addWidget(hide); l.addLayout(actions)
        for widget,signal in [(self.style_box,self.style_box.currentTextChanged),(self.size,self.size.valueChanged),(self.gap,self.gap.valueChanged),(self.thick,self.thick.valueChanged),(self.opacity,self.opacity.valueChanged),(self.dot,self.dot.toggled),(self.outline,self.outline.toggled),(self.color_edit,self.color_edit.textChanged),(self.outline_color_edit,self.outline_color_edit.textChanged)]:
            signal.connect(self.update_crosshair_preview)
        self.opacity.valueChanged.connect(lambda v:self.opacity_value.setText(f"{v}%"))
        self.update_crosshair_preview(); return w


    def crosshair_config(self):
        color=self.color_edit.text().strip()
        if not QColor.isValidColor(color): raise ValueError("Enter a valid HEX color such as #00ff88.")
        return {"style":self.style_box.currentText(),"size":self.size.value(),"gap":self.gap.value(),
                "thickness":self.thick.value(),"color":QColor(color).name(),"opacity":self.opacity.value(),"dot":self.dot.isChecked(),"outline":self.outline.isChecked(),"outline_color":QColor(self.outline_color_edit.text().strip()).name() if QColor.isValidColor(self.outline_color_edit.text().strip()) else "#000000"}

    def update_crosshair_preview(self,*_):
        try: self.preview.set_config(self.crosshair_config())
        except ValueError: self.preview.set_config({"style":"Classic","size":18,"gap":5,"thickness":2,"color":"#ff3355","opacity":100})

    def save_studio_profile(self):
        name=self.crosshair_game.text().strip()
        if not name: QMessageBox.warning(self,"Game missing","Enter a game name."); return
        try: cfg=self.crosshair_config()
        except ValueError as e: QMessageBox.warning(self,"Invalid color",str(e)); return
        storage.save_profile(name,{"crosshair":cfg}); self.load_profiles()
        QMessageBox.information(self,"Profile saved",f"Crosshair saved for {name}.")

    def export_crosshair(self):
        import json
        try: cfg=self.crosshair_config()
        except ValueError as e: QMessageBox.warning(self,"Invalid color",str(e)); return
        path,_=QFileDialog.getSaveFileName(self,"Export crosshair","aimforge-crosshair.json","JSON (*.json)")
        if path: Path(path).write_text(json.dumps(cfg,indent=2),encoding="utf-8")

    def import_crosshair(self):
        import json
        path,_=QFileDialog.getOpenFileName(self,"Import crosshair","","JSON (*.json)")
        if not path: return
        try:
            cfg=json.loads(Path(path).read_text(encoding="utf-8"))
            self.style_box.setCurrentText(cfg.get("style","Classic")); self.size.setValue(int(cfg.get("size",18)))
            self.gap.setValue(int(cfg.get("gap",5))); self.thick.setValue(int(cfg.get("thickness",2)))
            op=float(cfg.get("opacity",100)); self.opacity.setValue(int(op*100 if op<=1 else op))
            self.color_edit.setText(cfg.get("color","#00ff88")); self.dot.setChecked(bool(cfg.get("dot",False))); self.outline.setChecked(bool(cfg.get("outline",False)))
            self.update_crosshair_preview()
        except Exception as e: QMessageBox.critical(self,"Import failed",f"Invalid preset: {e}")

    def monitor_page(self):
        w=QWidget(); l=QVBoxLayout(w); n=QLabel("CPU/RAM are read locally. FPS requires PresentMon CSV. Unsupported GPU sensor fields stay unavailable.")
        n.setObjectName("muted"); l.addWidget(n); grid=QGridLayout(); self.metrics={}
        for i,k in enumerate(["fps","avg_fps","one_percent_low","cpu_usage","ram_used_gb","gpu_temp","gpu_usage","vram_used","cpu_clock","gpu_clock","gpu_power"]):
            f,v=make_card(k.replace("_"," ").title(),"—"); self.metrics[k]=v; grid.addWidget(f,i//3,i%3)
        l.addLayout(grid); b=QPushButton("Select PresentMon CSV"); b.clicked.connect(self.select_csv); l.addWidget(b); self.csv_note=QLabel("No telemetry file selected"); self.csv_note.setObjectName("muted"); l.addWidget(self.csv_note); l.addStretch(); return w

    def profiles_page(self):
        w=QWidget(); l=QVBoxLayout(w); row=QHBoxLayout(); self.game=QLineEdit(); self.game.setPlaceholderText("Game name")
        save=QPushButton("Save crosshair profile"); save.setObjectName("accent"); save.clicked.connect(self.save_profile); row.addWidget(self.game); row.addWidget(save); l.addLayout(row)
        self.profile_table=QTableWidget(0,3); self.profile_table.setHorizontalHeaderLabels(["Game","Style","Updated"]); self.profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.profile_table.cellDoubleClicked.connect(self.apply_selected_profile); l.addWidget(self.profile_table); l.addWidget(QLabel("Double-click a profile to load it in Crosshair Studio.")); self.load_profiles(); return w

    def benchmarks_page(self):
        w=QWidget(); l=QVBoxLayout(w)
        n=QLabel("Import benchmark measurements with their source. Search and compare saved records; FPS values are not invented.")
        n.setObjectName("muted"); n.setWordWrap(True); l.addWidget(n)
        bar=QHBoxLayout(); b=QPushButton("Import CSV"); b.clicked.connect(self.import_benchmarks); bar.addWidget(b)
        ex=QPushButton("Export CSV"); ex.clicked.connect(self.export_benchmarks); bar.addWidget(ex)
        self.bench_search=QLineEdit(); self.bench_search.setPlaceholderText("Filter by game, CPU, GPU, resolution or preset…")
        self.bench_search.textChanged.connect(self.load_benchmarks); bar.addWidget(self.bench_search,1); l.addLayout(bar)
        self.bench_count=QLabel(); l.addWidget(self.bench_count); self.bench_table=QTableWidget(0,9)
        self.bench_table.setHorizontalHeaderLabels(["Game","CPU","GPU","Resolution","Preset","Avg FPS","1% Low","Kind","Source"])
        self.bench_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.bench_table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.bench_table)
        self.load_benchmarks(); return w

    def advisor_page(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel("Compare sourced benchmark scores and real upgrade prices. This does not claim guaranteed FPS uplift."))
        self.score_a=QLineEdit(); self.score_a.setPlaceholderText("Current benchmark score")
        self.score_b=QLineEdit(); self.score_b.setPlaceholderText("Candidate benchmark score")
        self.price=QLineEdit(); self.price.setPlaceholderText("Upgrade price")
        for x in (self.score_a,self.score_b,self.price): l.addWidget(x)
        b=QPushButton("Compare scenario"); b.setObjectName("accent"); b.clicked.connect(self.compare); l.addWidget(b)
        self.advice=QLabel("Enter scores and price."); self.advice.setWordWrap(True); l.addWidget(self.advice); l.addStretch(); return w

    def tweaks_page(self):
        w=QWidget(); l=QVBoxLayout(w)
        intro=QLabel("Reversible Windows gaming tweaks. Choose exactly what to change; no drivers, services, BIOS or overclocking are touched. Some changes need sign-out or restart.")
        intro.setObjectName("muted"); intro.setWordWrap(True); l.addWidget(intro)
        items=[
            ("Windows Game Mode","Enable Game Mode for supported games.","game_mode"),
            ("Disable background game capture","Turn off Game DVR recording and capture hooks.","game_dvr"),
            ("Disable mouse acceleration","Turn off Enhance Pointer Precision (applies immediately).","mouse"),
            ("Disable transparency","Reduce Windows transparency effects; visual preference only.","transparency"),
            ("Best performance visual effects","Set Windows visual-effects preset to best performance. May make Windows look simpler.","animations"),
            ("Reduce Xbox Game Bar overlay","Disable Game Bar startup panel and Nexus overlay integration.","gamebar"),
            ("Restrict background apps","Set the per-user background-app permission switch off. May affect app notifications/sync.","background_apps"),
            ("High performance power plan","Switch to Windows High performance plan. Uses more electricity and can increase heat/fan noise.","power"),
        ]
        self.tweak_checks={}
        cards=QGridLayout(); l.addLayout(cards)
        for i,(name,desc,key) in enumerate(items):
            card=QFrame(); card.setObjectName("panel"); cl=QVBoxLayout(card)
            title=QLabel(name); title.setStyleSheet("font-weight:700;font-size:11pt")
            note=QLabel(desc); note.setObjectName("muted"); note.setWordWrap(True)
            check=QCheckBox("Select")
            check.setChecked(key in ("game_mode","game_dvr","mouse","power"))
            status=QLabel("Checking…"); status.setObjectName("muted")
            cl.addWidget(title); cl.addWidget(note); cl.addWidget(check); cl.addWidget(status)
            self.tweak_checks[key]=(check,status); cards.addWidget(card,i//2,i%2)
        actions=QHBoxLayout()
        apply=QPushButton("Apply selected tweaks"); apply.setObjectName("accent"); apply.clicked.connect(self.apply_selected_tweaks)
        preset=QPushButton("Apply all tweaks"); preset.clicked.connect(self.apply_tweaks)
        restore=QPushButton("Restore previous settings"); restore.clicked.connect(self.restore_tweaks)
        actions.addWidget(apply); actions.addWidget(preset); actions.addWidget(restore); l.addLayout(actions)
        self.tweak_note=QLabel("Original Windows values are saved before the first change. Restore returns them to their previous values.")
        self.tweak_note.setObjectName("muted"); self.tweak_note.setWordWrap(True); l.addWidget(self.tweak_note)
        refresh=QPushButton("Refresh actual status"); refresh.clicked.connect(self.refresh_tweak_status); l.addWidget(refresh)
        graphics=QPushButton("Open Windows Graphics settings"); graphics.clicked.connect(lambda:__import__("os").startfile("ms-settings:display-advancedgraphics"))
        display=QPushButton("Open Display settings"); display.clicked.connect(lambda:__import__("os").startfile("ms-settings:display"))
        l.addWidget(graphics); l.addWidget(display); l.addStretch()
        self.refresh_tweak_status()
        return w

    def refresh_tweak_status(self):
        try:
            from .tweaks import get_tweak_status
            statuses=get_tweak_status()
            for key,(check,label) in self.tweak_checks.items():
                label.setText(statuses.get(key,"Unknown"))
        except Exception as e:
            self.tweak_note.setText("Could not read Windows tweak status: "+str(e))

    def apply_selected_tweaks(self):
        selected=[key for key,(check,label) in self.tweak_checks.items() if check.isChecked()]
        try:
            from .tweaks import apply_tweaks
            changed=apply_tweaks(selected)
            self.tweak_note.setText("Applied: "+", ".join(changed)+". Changes depend on Windows version and hardware; FPS gains are not guaranteed.")
            self.refresh_tweak_status()
            QMessageBox.information(self,"Tweaks applied","Selected settings were applied. Some changes need sign-out, restart or a game relaunch. No FPS gain is guaranteed.")
        except Exception as e:
            self.refresh_tweak_status()
            QMessageBox.critical(self,"Could not apply tweaks",str(e))

    def apply_tweaks(self):
        for check,label in self.tweak_checks.values(): check.setChecked(True)
        self.apply_selected_tweaks()

    def restore_tweaks(self):
        try:
            from .tweaks import restore_previous_settings
            restored=restore_previous_settings()
            self.tweak_note.setText("Restored: "+(", ".join(restored) if restored else "No saved changes found."))
            self.refresh_tweak_status()
            QMessageBox.information(self,"Restore complete","AimForge restored saved Windows values. Sign out or restart if a setting does not visibly update.")
        except Exception as e:
            QMessageBox.critical(self,"Restore failed",str(e))

    def settings_page(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel("Preferences & local data"))
        lang=QComboBox(); lang.addItems(LANGUAGES); lang.currentTextChanged.connect(self.set_language); l.addWidget(QLabel("Language")); l.addWidget(lang)
        l.addWidget(QLabel("Hebrew and Arabic switch the interface direction to RTL."))
        b=QPushButton("Export local backup"); b.clicked.connect(self.backup); l.addWidget(b)
        r=QPushButton("Restore local backup"); r.clicked.connect(self.restore); l.addWidget(r)
        l.addWidget(QLabel("Shortcut Ctrl+Shift+X works while AimForge is active. Startup, tray, auto-update and system-wide hotkeys are not included yet."))
        l.addStretch(); return w

    def set_language(self,lang):
        self.language=lang; self.setLayoutDirection(Qt.RightToLeft if lang in RTL else Qt.LeftToRight)
        for i,label in enumerate(LABELS.get(lang,LABELS["English"])): self.nav.item(i).setText(label)

    def choose_specific_color(self, target):
        current=target.text().strip()
        c=QColorDialog.getColor(QColor(current if QColor.isValidColor(current) else "#000000"),self)
        if c.isValid(): target.setText(c.name())

    def choose_color(self):
        current=self.color_edit.text().strip() if hasattr(self,"color_edit") else self.color
        c=QColorDialog.getColor(QColor(current if QColor.isValidColor(current) else "#00ff88"),self)
        if c.isValid():
            if hasattr(self,"color_edit"): self.color_edit.setText(c.name())
            else: self.color=c.name()

    def apply_overlay(self):
        try: cfg=self.crosshair_config()
        except ValueError as e: QMessageBox.warning(self,"Invalid color",str(e)); return
        self.color=cfg["color"]
        self.overlay.configure(cfg["size"],cfg["gap"],cfg["thickness"],cfg["color"],cfg["opacity"]/100,cfg["style"],cfg["dot"],cfg["outline"],cfg.get("outline_color","#000000"))
        screen=self.screen()
        if screen: self.overlay.setGeometry(screen.geometry())
        self.overlay.show()
        self.overlay_status.setText("●  OVERLAY ON"); self.overlay_status.setStyleSheet("color:#8bdfb0;padding:12px")
        self.quick_toggle.setText("Hide Crosshair")

    def hide_overlay(self):
        self.overlay.hide(); self.overlay_status.setText("●  OVERLAY OFF"); self.overlay_status.setStyleSheet("color:#858ba3;padding:12px"); self.quick_toggle.setText("Show Crosshair")

    def toggle_overlay(self):
        if self.overlay.isVisible(): self.hide_overlay()
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
        try: cfg=self.crosshair_config()
        except ValueError as e: QMessageBox.warning(self,"Invalid color",str(e)); return
        storage.save_profile(name,{"crosshair":cfg}); self.load_profiles()

    def apply_selected_profile(self,row,column):
        item=self.profile_table.item(row,0)
        if not item: return
        cfg=storage.profiles().get(item.text(),{}).get("crosshair",{})
        self.nav.setCurrentRow(2)
        self.load_crosshair_config(cfg)

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
                headers={str(h or "").strip().lower() for h in (reader.fieldnames or [])}
                if not required.issubset(headers):
                    missing=", ".join(sorted(required-headers))
                    raise ValueError(f"Missing required columns: {missing}. Follow benchmark_template.csv.")
                rows=[]
                for line_no,r in enumerate(reader,2):
                    row={str(k or "").strip().lower():str(v or "").strip() for k,v in r.items() if k is not None}
                    if not any(row.values()): continue
                    for key in ("game","cpu","gpu","resolution","preset","source","benchmark_date","kind"):
                        if not row.get(key): raise ValueError(f"Row {line_no}: {key} cannot be blank.")
                    kind=row["kind"].lower()
                    if kind not in ("measured","estimated"): raise ValueError(f"Row {line_no}: kind must be measured or estimated.")
                    try: avg=float(row["avg_fps"]); low=float(row["one_percent_low"])
                    except (ValueError,TypeError): raise ValueError(f"Row {line_no}: FPS values must be numbers.")
                    if avg<=0 or low<=0 or low>avg: raise ValueError(f"Row {line_no}: FPS must be positive and 1% low cannot exceed average FPS.")
                    rows.append({**row,"kind":kind,"avg_fps":avg,"one_percent_low":low})
            if not rows: raise ValueError("The CSV contains no benchmark records.")
            storage.add_benchmarks(rows); self.load_benchmarks()
            QMessageBox.information(self,"Imported",f"{len(rows)} valid benchmark records imported.")
        except Exception as e: QMessageBox.critical(self,"Import failed",str(e))

    def load_benchmarks(self,*_):
        if not hasattr(self,"bench_table"): return
        rows=storage.benchmarks()
        if not isinstance(rows,list): rows=[]
        query=self.bench_search.text().strip().casefold() if hasattr(self,"bench_search") else ""
        filtered=[r for r in rows if isinstance(r,dict) and (not query or query in " ".join(str(r.get(k,"")) for k in ("game","cpu","gpu","resolution","preset","kind","source")).casefold())]
        self.bench_count.setText(f"Showing {min(500,len(filtered))} of {len(filtered)} matching records • {len(rows)} total saved")
        shown=filtered[-500:]; self.bench_table.setRowCount(len(shown))
        for i,r in enumerate(shown):
            vals=[r.get("game",""),r.get("cpu",""),r.get("gpu",""),r.get("resolution",""),r.get("preset",""),r.get("avg_fps",""),r.get("one_percent_low",""),r.get("kind",""),r.get("source","")]
            for j,v in enumerate(vals): self.bench_table.setItem(i,j,QTableWidgetItem(str(v)))

    def export_benchmarks(self):
        rows=storage.benchmarks()
        if not isinstance(rows,list) or not rows:
            QMessageBox.information(self,"No benchmarks","There are no saved benchmark records to export."); return
        path,_=QFileDialog.getSaveFileName(self,"Export benchmark CSV","aimforge-benchmarks.csv","CSV (*.csv)")
        if not path: return
        fields=["game","cpu","gpu","resolution","preset","avg_fps","one_percent_low","source","benchmark_date","kind"]
        try:
            with open(path,"w",encoding="utf-8-sig",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); writer.writeheader()
                for row in rows:
                    if isinstance(row,dict): writer.writerow({k:row.get(k,"") for k in fields})
            QMessageBox.information(self,"Export complete",f"Exported {len(rows)} records.")
        except OSError as e: QMessageBox.critical(self,"Export failed",str(e))

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
