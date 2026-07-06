#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

SCRIPT = "./wait-and-touch.sh"
SLEEP_SECONDS = 5
BASE_DIR = Path(__file__).parent


class State:
    RUN_SCRIPT = "RUN_SCRIPT"
    VERIFY_FILE = "VERIFY_FILE"
    DONE = "DONE"


class StateMachine:
    def __init__(self, iterations: int):
        self.iterations = iterations
        self.current_iter = 0
        self.state = State.RUN_SCRIPT
        self.filepath = BASE_DIR / f"tmp_{self.current_iter}.txt"

    def step(self):
        if self.state == State.RUN_SCRIPT:
            print(f"[{self.current_iter + 1}/{self.iterations}] Running: {SCRIPT} {SLEEP_SECONDS} {self.filepath.name}")
            result = subprocess.run(
                [SCRIPT, str(SLEEP_SECONDS), str(self.filepath)],
                cwd=BASE_DIR,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Script failed with exit code {result.returncode}")
            self.state = State.VERIFY_FILE

        elif self.state == State.VERIFY_FILE:
            if self.filepath.exists():
                print(f"  -> {self.filepath.name} confirmed")
                self.current_iter += 1
                if self.current_iter >= self.iterations:
                    self.state = State.DONE
                else:
                    self.filepath = BASE_DIR / f"tmp_{self.current_iter}.txt"
                    self.state = State.RUN_SCRIPT
            else:
                raise RuntimeError(f"File {self.filepath} was not created")

    def run(self):
        while self.state != State.DONE:
            self.step()
        print("State machine complete.")


if __name__ == "__main__":
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    sm = StateMachine(iterations)
    sm.run()
