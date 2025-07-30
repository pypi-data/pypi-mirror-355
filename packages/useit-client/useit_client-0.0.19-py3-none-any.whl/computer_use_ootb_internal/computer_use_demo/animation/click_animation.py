# click_anim_async.py   ←  put this in its own file  (important for Windows "spawn")
import sys
import queue
import time
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

class AnimationManager(Thread):
    def __init__(self):
        super().__init__()
        self.request_queue = queue.Queue()
        self.daemon = True
        self.active_animations = []

    def run(self):
        try:
            self.app = QApplication.instance() or QApplication(sys.argv)
            
            while True:
                # 1. Process new animation requests from the queue
                try:
                    request = self.request_queue.get_nowait()
                    if request['type'] == 'click':
                        anim = ClickAnimation(QPoint(request['x'], request['y']), request['duration_ms'])
                        self.active_animations.append(anim)
                    
                    elif request['type'] == 'move':
                        widget = ClickAnimation(QPoint(request['x1'], request['y1']), request['duration_ms'])
                        self.active_animations.append(widget)
                        
                        qanim = QPropertyAnimation(widget, b"pos", parent=widget)
                        qanim.setDuration(request['duration_ms'])
                        qanim.setStartValue(widget.pos())
                        qanim.setEndValue(QPoint(request['x2'] - widget.width()//2, request['y2'] - widget.height()//2))
                        qanim.setEasingCurve(QEasingCurve.OutQuad)
                        qanim.start(QPropertyAnimation.DeleteWhenStopped)

                except queue.Empty:
                    pass # Normal when no new requests

                # 2. Process Qt events to show/update/close animations
                self.app.processEvents()

                # 3. Clean up closed widgets from our list
                self.active_animations = [anim for anim in self.active_animations if anim.isVisible()]

                # 4. Sleep to prevent busy-looping and yield to other threads
                time.sleep(0.01)
                
        except Exception as e:
            print(f"[ERROR] AnimationManager thread failed: {e}")

# Global singleton instance of the AnimationManager.
animation_manager = AnimationManager()
animation_manager.start()

# ------------------------------- public API (non‑blocking) ---------------------------
def show_click(x: int, y: int, duration_ms: int = 800, **kwargs):
    if not CLICK_GIF.exists():
        print(f"Animation GIF not found at {CLICK_GIF}")
        return
    
    request = {'type': 'click', 'x': x, 'y': y, 'duration_ms': duration_ms}
    animation_manager.request_queue.put(request)

def show_move_to(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 800, **kwargs):
    if not CLICK_GIF.exists():
        print(f"Animation GIF not found at {CLICK_GIF}")
        return

    request = {'type': 'move', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'duration_ms': duration_ms}
    animation_manager.request_queue.put(request)

if __name__ == "__main__":
    import pyautogui
    time.sleep(2)
    x, y = pyautogui.position()
    print(f"Start pos: {x}, {y}")
    show_move_to(x, y, 600, 600)
    time.sleep(1)
    show_click(600, 600)
    print("Animations requested")
    time.sleep(2) # Keep main thread alive to see animations
    print("Done")