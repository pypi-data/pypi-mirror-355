# A dotter while I'm thinking
from typing import Optional

import itertools
import threading
import time
import sys

piano = ['▉▁▁▁▁▁', '▉▉▂▁▁▁', '▉▉▉▃▁▁', '▉▉▉▉▅▁', 
         '▉▉▉▉▉▇', '▉▉▉▉▉▉', '▉▉▉▉▇▅', '▉▉▉▆▃▁', 
         '▉▉▅▃▁▁', '▉▇▃▁▁▁', '▇▃▁▁▁▁', '▃▁▁▁▁▁', 
         '▁▁▁▁▁▁', '▁▁▁▁▁▉', '▁▁▁▁▃▉', '▁▁▁▃▅▉', 
         '▁▁▃▅▇▉', '▁▃▅▇▉▉', '▃▅▉▉▉▉', '▅▉▉▉▉▉',
         '▇▉▉▉▉▉', '▉▉▉▉▉▉', '▇▉▉▉▉▉', '▅▉▉▉▉▉', 
         '▃▅▉▉▉▉', '▁▃▅▉▉▉', '▁▁▃▅▉▉', '▁▁▁▃▅▉',
         '▁▁▁▁▃▅', '▁▁▁▁▁▃', '▁▁▁▁▁▁', '▁▁▁▁▁▁', 
         '▁▁▃▁▁▁', '▁▃▅▃▁▁', '▁▅▉▅▁▁', '▃▉▉▉▃▁', 
         '▅▉▁▉▅▃', '▇▃▁▃▇▅', '▉▁▁▁▉▇', '▉▅▃▁▃▅', 
         '▇▉▅▃▅▇', '▅▉▇▅▇▉', '▃▇▉▇▉▅', '▁▅▇▉▇▃', 
         '▁▃▅▇▅▁', '▁▁▃▅▃▁', '▁▁▁▃▁▁', '▁▁▁▁▁▁',
        ]

slash = ["\\","|","/", "-"]

class Dotter:
    # A dotter while I'm thinking
    def __init__(self, message: str = "Thinking", delay: float = 0.5, 
                 cycle: list[str] = ["", ".", ". .", ". . ."], 
                 show_timer: bool = False) -> None:
        
        self.spinner          : itertools.cycle            = itertools.cycle(cycle)
        self.show_timer       : bool                       = show_timer
        self.message          : str                        = message
        self.delay            : float                      = delay
        self.dotter_thread    : Optional[threading.Thread] = None
        self.start_time       : Optional[float]            = None
        self.running          : bool                       = False

    def format_elapsed(self, elapsed: float) -> str:
        if elapsed < 300:
            return f"{elapsed:.1f}s"
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            return f"{mins}m{secs:02d}s"
        
    def dot(self):
        self.start_time = time.time()
        while self.running:
            elapsed = time.time() - self.start_time
            text  = f"{self.message} {next(self.spinner)}"
            
            if self.show_timer:
                timer_str = f"[{self.format_elapsed(elapsed)}]"
                text = timer_str + ' ' + text
                
            sys.stdout.write(f"\r{text}")
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write(f"\r{' ' * (len(text))}\r")  # Clear line

    def update_message(self, new_message, delay=0.1):
        time.sleep(delay)
        sys.stdout.write(
            f"\r{' ' * (len(self.message) + 20)}\r"
        )  # Clear the current message
        sys.stdout.flush()
        self.message = new_message
        self.delay = delay  # Update the delay if needed

    def __enter__(self):
        self.running = True
        self.dotter_thread = threading.Thread(target=self.dot)
        self.dotter_thread.start()
        return self

    def __exit__(self, *args) -> None:
        self.running = False
        if self.dotter_thread is not None:
            self.dotter_thread.join()
        sys.stdout.write(f"\r{' ' * (len(self.message) + 20)}\r")
        sys.stdout.flush()

if __name__ == "__main__":
    from time import sleep
    import asyncio
    from minwei_tools.dotter import AsyncDotter

    with Dotter(message="[*] Grabing player log", cycle=slash, delay=0.1, show_timer=1) as d:
        sleep(5)
        d.update_message("[*] Player log grabbed", delay=0.1)
        sleep(5)