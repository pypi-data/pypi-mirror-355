from typing import Optional

import itertools
import asyncio
import time
import sys

from minwei_tools.dotter import piano, slash  # Importing from the dotter module

class AsyncDotter:
    def __init__(self, message: str = "Thinking", delay: float = 0.1,
                 cycle: list[str] = ["", ".", ". .", ". . ."],
                 show_timer: bool = False) -> None:

        self.spinner = itertools.cycle(cycle)
        self.message    : str                    = message
        self.delay      : float                  = delay
        self.show_timer : bool                   = show_timer
        self._task      : Optional[asyncio.Task] = None
        self._start_time: Optional[float]        = None
        self._running   : bool                   = False
        self.inserted_messages: list[str]       = []  # Store inserted messages

        
    def format_elapsed(self, elapsed: float) -> str:
        if elapsed < 300:
            return f"{elapsed:.1f}s"
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            return f"{mins}m{secs:02d}s"

    async def _dot(self):
        self._start_time = time.time()
        while self._running:
            elapsed = time.time() - self._start_time
            text = f"{self.message} {next(self.spinner)}"

            if self.show_timer:
                timer_str = f"[{self.format_elapsed(elapsed)}]"
                text = timer_str + ' ' + text

            sys.stdout.write(f"\r{text}\n")
            for msg in self.inserted_messages:
                sys.stdout.write(f"   {msg}\n")
            sys.stdout.flush()
            await asyncio.sleep(self.delay)
            lines_to_clear = 1 + len(self.inserted_messages)
            for _ in range(lines_to_clear):
                sys.stdout.write("\033[F")  # Move cursor up one line
                sys.stdout.write("\033[K")  # Clear the entire line
            sys.stdout.flush()
            
    async def insert_message(self, new_message: str, max_str : int = 5):
        self.inserted_messages.append(new_message)
        if len(self.inserted_messages) > max_str:
            self.inserted_messages.pop(0)

    async def update_message(self, new_message: str, delay: float = 0.1):
        await asyncio.sleep(delay)
        sys.stdout.write(f"\r{' ' * (len(self.message) + 20)}\r")
        sys.stdout.flush()
        self.message = new_message

    async def __aenter__(self):
        self._running = True
        self._task = asyncio.create_task(self._dot())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._running = False
        if self._task:
            await self._task
        sys.stdout.write(f"\r{' ' * (len(self.message) + 20)}\r")
        sys.stdout.flush()
        
        
if __name__ == "__main__":
    import asyncio

    async def main():
        async with AsyncDotter("Loading", show_timer=False, cycle=piano, delay=0.1) as d:
            
            await d.insert_message("This is a test message 1")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 2")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 3")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 4")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 5")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 6")
            await asyncio.sleep(1)
            await d.update_message("[*] Player log grabbed", delay=0.1)
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 7")
            await asyncio.sleep(1)
            await d.insert_message("This is a test message 8")
            await asyncio.sleep(1)        
            await d.insert_message("This is a test message 9")

    asyncio.run(main())