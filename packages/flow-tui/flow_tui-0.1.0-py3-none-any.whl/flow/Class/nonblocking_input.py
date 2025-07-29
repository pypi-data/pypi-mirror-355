import sys
import select
import termios
import tty

class NonBlockingInput:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = None

    def __enter__(self):
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)  # set terminal to cbreak mode (non-canonical)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_settings:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self, timeout: float = 0):
        """Return a single key pressed or None if no key was pressed within timeout seconds."""
        dr, _, _ = select.select([sys.stdin], [], [], timeout)
        if dr:
            return sys.stdin.read(1)
        return None
