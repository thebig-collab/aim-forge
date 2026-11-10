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
        self.center_dot = False

    def configure(self, size_px, gap, thickness, color, opacity, style, center_dot=False):
        self.size_px=max(2,min(100,int(size_px))); self.gap=max(0,min(50,int(gap)))
        self.thickness=max(1,min(12,int(thickness))); self.color=QColor(color)
        self.opacity=max(.1,min(1,float(opacity))); self.style=style; self.center_dot=bool(center_dot); self.update()

    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        c=QColor(self.color); c.setAlphaF(self.opacity)
        p.setPen(QPen(c,self.thickness,Qt.SolidLine,Qt.RoundCap))
        x,y=self.width()//2,self.height()//2; s,g=self.size_px,self.gap
        if self.style=="Dot":
            p.setBrush(c); p.setPen(Qt.NoPen); p.drawEllipse(x-self.thickness,y-self.thickness,2*self.thickness,2*self.thickness)
        elif self.style=="Circle":
            p.setBrush(Qt.NoBrush); p.drawEllipse(x-s//2,y-s//2,s,s)
        else:
            p.drawLine(x-s,y,x-g,y); p.drawLine(x+g,y,x+s,y)
            p.drawLine(x,y-s,x,y-g); p.drawLine(x,y+g,x,y+s)
        if self.center_dot and self.style!="Dot":
            p.setBrush(c); p.setPen(Qt.NoPen); d=max(2,self.thickness*2)
            p.drawEllipse(x-d//2,y-d//2,d,d)
