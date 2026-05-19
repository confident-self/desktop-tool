"""使用 QPainter 绘制几何图标"""
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
import math


def _paint(paint_fn, size=24, color="#909090"):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint_fn(p, size, QColor(color))
    p.end()
    return pix


def home_icon(size=24, color="#909090"):
    def fn(p, s, c):
        pen = QPen(c, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        m = s * 0.15
        # 屋顶
        roof = [QPointF(m, s * 0.55), QPointF(s / 2, m), QPointF(s - m, s * 0.55)]
        p.drawPolyline(roof)
        # 底部屋檐
        p.drawLine(QLineF(roof[0], roof[2]))
        # 墙
        body_w = s * 0.43
        body_x = (s - body_w) / 2
        p.drawRect(QRectF(body_x, s * 0.5, body_w, s * 0.35))
        # 门
        door_w = s * 0.14
        door_x = (s - door_w) / 2
        p.drawRect(QRectF(door_x, s * 0.68, door_w, s * 0.17))
    return _paint(fn, size, color)


def tasks_icon(size=24, color="#909090"):
    def fn(p, s, c):
        pen = QPen(c, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        m = s * 0.2
        line_y = [s * 0.28, s * 0.5, s * 0.72]
        for y in line_y:
            p.drawLine(QLineF(m, y, s - m, y))
        # 左侧竖线
        bx = m + 2
        p.drawLine(QLineF(bx, line_y[0] - 7, bx, line_y[0] + 7))
        p.drawLine(QLineF(bx, line_y[1] - 7, bx, line_y[1] + 7))
        p.drawLine(QLineF(bx, line_y[2] - 7, bx, line_y[2] + 7))
    return _paint(fn, size, color)


def settings_icon(size=24, color="#909090"):
    def fn(p, s, c):
        pen = QPen(c, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = s * 0.26
        cx, cy = s / 2, s / 2
        # 外圈
        p.drawEllipse(QPointF(cx, cy), r, r)
        # 内圈
        inner_r = r * 0.35
        p.drawEllipse(QPointF(cx, cy), inner_r, inner_r)
        # 齿轮齿
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + (r + 1) * math.cos(rad)
            y1 = cy + (r + 1) * math.sin(rad)
            x2 = cx + (r + 5) * math.cos(rad)
            y2 = cy + (r + 5) * math.sin(rad)
            p.drawLine(QLineF(x1, y1, x2, y2))
    return _paint(fn, size, color)
