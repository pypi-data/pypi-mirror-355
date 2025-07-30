# click_anim_async.py   ←  put this in its own file  (important for Windows "spawn")
import sys, multiprocessing as mp
from pathlib import Path
from PySide6.QtCore    import Qt, QPoint, QTimer, QEasingCurve, QPropertyAnimation, QSize
from PySide6.QtGui     import QMovie
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from threading import Thread

CLICK_GIF = Path(__file__).with_name("icons8-select-cursor-transparent-96.gif")

# ---------------------------- tiny in‑process GUI helpers ----------------------------
class ClickAnimation(QWidget):
    def __init__(self, pos: QPoint, life_ms: int, size_px: int = 50):
        super().__init__(None,
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label  = QLabel(self)
        movie       = QMovie(str(CLICK_GIF))
        movie.setScaledSize(QSize(size_px, size_px))
        self.label.setMovie(movie)
        self.label.setFixedSize(size_px, size_px)

        self.resize(size_px, size_px)
        self.move(pos.x() - size_px//2, pos.y() - size_px//2)

        movie.setCacheMode(QMovie.CacheAll)
        movie.start()
        QTimer.singleShot(life_ms, self.close)
        self.show()
        self.raise_()

# ------------------------- worker functions that live in a **child** -----------------
def _worker_click(x, y, duration_ms, existing_ms):
    app = QApplication(sys.argv)
    total = duration_ms + existing_ms
    widget = ClickAnimation(QPoint(x, y), total)  # Store in variable to prevent garbage collection
    QTimer.singleShot(total + 200, app.quit)      # close event‑loop afterwards
    app.exec()

def _worker_move(x1, y1, x2, y2, duration_ms, existing_ms):
    app     = QApplication(sys.argv)
    total   = duration_ms + existing_ms
    widget  = ClickAnimation(QPoint(x1, y1), total)

    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration_ms)
    anim.setStartValue(widget.pos())
    anim.setEndValue(QPoint(x2 - widget.width()//2, y2 - widget.height()//2))
    anim.setEasingCurve(QEasingCurve.OutQuad)
    anim.start()

    QTimer.singleShot(total + 200, app.quit)
    app.exec()

# ------------------------------- public API (non‑blocking) ---------------------------
def show_click(x: int, y: int, duration_ms: int = 8000, existing_ms: int = 8000):
    return  # Animation temporarily disabled
    if not CLICK_GIF.exists():
        raise FileNotFoundError(f"GIF not found at {CLICK_GIF}")
    
    # Use a thread instead of a process to avoid spawn issues
    thread = Thread(
        target=_worker_click,
        args=(x, y, duration_ms, existing_ms),
        daemon=True  # Set to True to not block program exit
    )
    thread.start()

def show_move_to(x1: int, y1: int, x2: int, y2: int,
                 duration_ms: int = 8000, existing_ms: int = 8000):
    return  # Animation temporarily disabled
    if not CLICK_GIF.exists():
        raise FileNotFoundError(f"GIF not found at {CLICK_GIF}")

    # Use a thread instead of a process
    thread = Thread(
        target=_worker_move,
        args=(x1, y1, x2, y2, duration_ms, existing_ms),
        daemon=True  # Set to True to not block program exit
    )
    thread.start()



if __name__ == "__main__":
    # from click_anim_async import show_click

    import pyautogui
    x, y = pyautogui.position()

    show_move_to(x, y, 600, 600)

    show_click(600, 600)