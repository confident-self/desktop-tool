from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QRect


def _sample_brightness(image: QImage, rect: QRect) -> float:
    """计算指定矩形区域内像素的平均感知亮度 (0-255)"""
    if rect.width() <= 0 or rect.height() <= 0:
        return 128
    cropped = image.copy(rect)
    total = 0
    count = 0
    step = max(1, min(rect.width(), rect.height()) // 4)
    for y in range(0, cropped.height(), step):
        for x in range(0, cropped.width(), step):
            px = cropped.pixelColor(x, y)
            r, g, b = px.red(), px.green(), px.blue()
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            total += luminance
            count += 1
    return total / max(count, 1)


def sample_global_rect(rect: QRect) -> list[int]:
    """截取屏幕指定区域，返回整个矩形内自上而下分段的平均亮度列表"""
    screen = QApplication.primaryScreen()
    if not screen:
        return [128] * 10
    screenshot = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
    img = screenshot.toImage()
    result = []
    segment_height = max(1, rect.height() // 10)
    for i in range(10):
        seg_rect = QRect(0, i * segment_height, rect.width(), segment_height)
        brightness = _sample_brightness(img, seg_rect)
        result.append(int(brightness))
    return result


def brightness_to_text_color(brightness: int) -> str:
    """根据背景亮度返回合适的文字颜色"""
    if brightness > 150:
        return "#1a1a1a"
    elif brightness > 90:
        return "#333333"
    else:
        return "#e0e0e0"
