from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget

class CrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AimForge Crosshair")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                            Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.size_px, self.gap, self.thickness = 18, 5, 2
        self.opacity, self.color, self.style = 1.0, QColor("#00ff88"), "Classic"
        self.center_dot = False; self.outline = False

    def configure(self, size_px, gap, thickness, color, opacity, style, center_dot=False, outline=False):
        self.size_px=max(2,min(100,int(size_px))); self.gap=max(0,min(50,int(gap)))
        self.thickness=max(1,min(12,int(thickness))); self.color=QColor(color)
        self.opacity=max(.1,min(1,float(opacity))); self.style=style; self.center_dot=bool(center_dot); self.outline=bool(outline); self.update()

    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        c=QColor(self.color); c.setAlphaF(self.opacity)
        x,y=self.width()//2,self.height()//2; s,g=self.size_px,self.gap
        def draw(color,width):
            p.setPen(QPen(color,width,Qt.SolidLine,Qt.RoundCap)); p.setBrush(Qt.NoBrush)
            if self.style=="Circle": p.drawEllipse(x-s//2,y-s//2,s,s)
            elif self.style!="Dot":
                p.drawLine(x-s,y,x-g,y); p.drawLine(x+g,y,x+s,y)
                p.drawLine(x,y-s,x,y-g); p.drawLine(x,y+g,x,y+s)
        if self.outline and self.style!="Dot":
            draw(QColor(0,0,0,c.alpha()),self.thickness+4)
        if self.style=="Dot":
            d=max(2,self.thickness*2)
            if self.outline:
                p.setPen(Qt.NoPen); p.setBrush(QColor(0,0,0,c.alpha())); p.drawEllipse(x-d//2-2,y-d//2-2,d+4,d+4)
            p.setBrush(c); p.setPen(Qt.NoPen); p.drawEllipse(x-d//2,y-d//2,d,d)
        else: draw(c,self.thickness)
        if self.center_dot and self.style!="Dot":
            d=max(2,self.thickness*2)
            if self.outline:
                p.setBrush(QColor(0,0,0,c.alpha())); p.setPen(Qt.NoPen); p.drawEllipse(x-d//2-2,y-d//2-2,d+4,d+4)
            p.setBrush(c); p.setPen(Qt.NoPen); p.drawEllipse(x-d//2,y-d//2,d,d)
