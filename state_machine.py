#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

SCRIPT = "./wait-and-touch.sh"
BASE_DIR = Path(__file__).parent


class State:
    RUN_SCRIPT = "RUN_SCRIPT"
    VERIFY_FILE = "VERIFY_FILE"
    DONE = "DONE"


class StateMachine:
    def __init__(self, iterations: int, probability: float, retries: int):
        self.iterations = iterations
        self.probability = probability
        self.max_retries = retries
        self.current_iter = 0
        self.retry_count = 0
        self.state = State.RUN_SCRIPT
        self.filepath = BASE_DIR / f"tmp_{self.current_iter}.txt"

    def step(self):
        if self.state == State.RUN_SCRIPT:
            print(f"[{self.current_iter + 1}/{self.iterations}] Running: {SCRIPT} 5 {self.probability} {self.filepath.name}")
            result = subprocess.run(
                [SCRIPT, "5", str(self.probability), str(self.filepath)],
                cwd=BASE_DIR,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Script failed with exit code {result.returncode}")
            self.state = State.VERIFY_FILE

        elif self.state == State.VERIFY_FILE:
            if self.filepath.exists():
                print(f"  -> {self.filepath.name} confirmed")
                self.filepath.unlink()
                self.current_iter += 1
                self.retry_count = 0
                if self.current_iter >= self.iterations:
                    self.state = State.DONE
                else:
                    self.filepath = BASE_DIR / f"tmp_{self.current_iter}.txt"
                    self.state = State.RUN_SCRIPT
            else:
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    raise RuntimeError(f"File {self.filepath} not created after {self.max_retries} retries")
                print(f"  -> retry {self.retry_count}/{self.max_retries}")
                self.state = State.RUN_SCRIPT

    def run(self):
        while self.state != State.DONE:
            self.step()
        print("State machine complete.")


if __name__ == "__main__":
    sm = StateMachine(iterations=5, probability=0.4, retries=4)
    sm.run()
