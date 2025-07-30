# click_anim_async.py   ←  put this in its own file  (important for Windows "spawn")
import sys
import queue
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
        self.daemon = True  # Allows main program to exit

    def run(self):
        try:
            # A QApplication instance is required for any GUI operations.
            # This gets the existing instance or creates a new one, preventing the error.
            self.app = QApplication.instance() or QApplication(sys.argv)

            # Use a timer to periodically check the queue for new animation requests.
            # This allows the Qt event loop to process GUI events.
            timer = QTimer()
            timer.timeout.connect(self.process_queue)
            timer.start(50)  # Check for new animations every 50ms

            self.app.exec()
        except Exception as e:
            print(f"Error initializing AnimationManager: {e}")

    def process_queue(self):
        try:
            request = self.request_queue.get_nowait()

            if request['type'] == 'click':
                total_duration = request['duration_ms'] + request['existing_ms']
                # The widget will be managed by the Qt event loop and self-destruct.
                ClickAnimation(QPoint(request['x'], request['y']), total_duration)
            
            elif request['type'] == 'move':
                total_duration = request['duration_ms'] + request['existing_ms']
                widget = ClickAnimation(QPoint(request['x1'], request['y1']), total_duration)
                
                anim = QPropertyAnimation(widget, b"pos", parent=widget)
                anim.setDuration(request['duration_ms'])
                anim.setStartValue(widget.pos())
                anim.setEndValue(QPoint(request['x2'] - widget.width()//2, request['y2'] - widget.height()//2))
                anim.setEasingCurve(QEasingCurve.OutQuad)
                # The animation will delete itself once it's finished.
                anim.start(QPropertyAnimation.DeleteWhenStopped)

        except queue.Empty:
            # This is expected when the queue is empty.
            pass
        except Exception as e:
            print(f"Error processing animation request: {e}")

# Global singleton instance of the AnimationManager.
animation_manager = AnimationManager()
animation_manager.start()

# ------------------------------- public API (non‑blocking) ---------------------------
def show_click(x: int, y: int, duration_ms: int = 8000, existing_ms: int = 8000):
    if not CLICK_GIF.exists():
        print(f"Animation GIF not found at {CLICK_GIF}")
        return
    
    request = {
        'type': 'click', 'x': x, 'y': y,
        'duration_ms': duration_ms, 'existing_ms': existing_ms,
    }
    animation_manager.request_queue.put(request)

def show_move_to(x1: int, y1: int, x2: int, y2: int,
                 duration_ms: int = 8000, existing_ms: int = 8000):
    if not CLICK_GIF.exists():
        print(f"Animation GIF not found at {CLICK_GIF}")
        return

    request = {
        'type': 'move', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
        'duration_ms': duration_ms, 'existing_ms': existing_ms,
    }
    animation_manager.request_queue.put(request)

if __name__ == "__main__":
    # from click_anim_async import show_click

    import pyautogui
    x, y = pyautogui.position()

    show_move_to(x, y, 600, 600)

    show_click(600, 600)