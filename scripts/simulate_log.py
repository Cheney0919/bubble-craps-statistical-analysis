"""Generate realistic simulated raw logs in the exact Google Sheet format.

Used to test the cleaning and analysis scripts before real data exist. A
simulated bubble craps machine rolls dice and tracks its true game phase; a
simulated collector logs the rolls following docs/field_protocol.md: row 0,
roll 1 with `CO`, two-digit dice, `C` corrections, `R` recoveries, breaks that
are fully recovered or create a `GAP`, and an optional switch to machine B.

Usage (from the repository root):

    python scripts/simulate_log.py                      # fair dice
    python scripts/simulate_log.py --stuck-prob 0.05    # dice sometimes don't tumble
    python scripts/simulate_log.py --switch-after 600   # machine A fails after 600 rolls

then, for example:

    python scripts/prepare_data.py --raw-dir data/simulated \\
        --out data/simulated/analysis_data.csv --summary data/simulated/validation_summary.md --force
    python scripts/analyze.py --data data/simulated/analysis_data.csv \\
        --report data/simulated/analysis_report.md --json data/simulated/analysis_results.json

Simulated output goes to data/simulated/, which is git-ignored and never mixed
with data/raw/.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import craps_core as core

REPO_ROOT = Path(__file__).resolve().parent.parent
SECONDS_PER_ROLL = 12  # about 5 rolls per minute


@dataclass
class Machine:
    """A bubble craps machine with a true game phase and a history display."""

    rng: np.random.Generator
    history_length: int = 20
    stuck_prob: float = 0.0
    seven_boost: float = 0.0
    state: object = "CO"  # 'CO' or the point number
    last: tuple[int, int] | None = None
    history: deque = field(default_factory=deque)
    serial: int = 0

    def roll(self) -> tuple[tuple[int, int], tuple[int, object]]:
        """Roll once. Returns (dice, (serial number, phase before the roll))."""
        phase = self.state
        self.serial += 1
        if self.last is not None and self.rng.random() < self.stuck_prob:
            dice = self.last  # the dice didn't tumble
        elif phase != "CO" and self.rng.random() < self.seven_boost:
            dice = [(1, 6), (2, 5), (3, 4)][self.rng.integers(3)]
        else:
            dice = (int(self.rng.integers(1, 7)), int(self.rng.integers(1, 7)))
        self.last = dice
        truth = (self.serial, phase)
        self.history.append((dice, truth))
        while len(self.history) > self.history_length:
            self.history.popleft()
        self.state = core.next_state(phase, sum(dice))
        return dice, truth


def phase_code(phase) -> str:
    return "CO" if phase == "CO" else f"P{phase}"


class Collector:
    """Writes rows the way the field protocol says to."""

    def __init__(self, rng: np.random.Generator, start_minutes: int):
        self.rng = rng
        self.seconds = start_minutes * 60
        self.rows: dict[str, list[dict]] = {}
        self.truth: dict[str, list[object]] = {}
        self.counted = 0

    def clock(self) -> str:
        minutes = (self.seconds // 60) % (24 * 60)
        hour, minute = divmod(minutes, 60)
        suffix = "AM" if hour < 12 else "PM"
        return f"{(hour % 12) or 12}:{minute:02d} {suffix}"

    def typed(self, dice: tuple[int, int]) -> str:
        a, b = dice
        return f"{a}{b}" if self.rng.random() < 0.5 else f"{b}{a}"  # either order

    def add(self, machine: str, dice=None, flag="", phase="", time="", notes="", truth=None, counts=True):
        self.rows.setdefault(machine, []).append(
            {"dice": "" if dice is None else self.typed(dice), "flag": flag, "phase": phase,
             "time": time, "notes": notes})
        self.truth.setdefault(machine, []).append(truth)
        if counts and flag != "GAP":
            self.counted += 1

    def tick(self, rolls: int = 1) -> None:
        self.seconds += SECONDS_PER_ROLL * rolls


def start_machine(col: Collector, m: Machine, name: str, require_come_out: bool) -> None:
    """Warm up the machine, then log row 0 from its history display."""
    for _ in range(int(col.rng.integers(5, 30))):
        m.roll()
        col.tick()
    if require_come_out:
        while m.state != "CO":
            m.roll()
            col.tick()
    dice, truth = m.history[-1]
    col.add(name, dice, flag="R", time=col.clock(),
            notes="row 0; matches physical dice", truth=truth, counts=False)


def simulate_session(seed: int = 1, target: int = core.TARGET_ROLLS, history_length: int = 20,
                     stuck_prob: float = 0.0, seven_boost: float = 0.0,
                     short_break_at: int | None = 300, short_break_rolls: int = 8,
                     long_break_at: int | None = 650, long_break_rolls: int = 35,
                     missed_at: tuple[int, ...] = (120, 480), corrected_at: tuple[int, ...] = (45, 777),
                     switch_after: int | None = None, start_minutes: int = 14 * 60):
    """Simulate one session. Returns (rows, truth) keyed by machine.

    `truth[machine][i]` is (machine roll serial number, true phase before the
    roll) for row i, or None for a GAP row. The phase is 'CO' or the point.
    """
    rng = np.random.default_rng(seed)
    col = Collector(rng, start_minutes)

    def new_machine():
        return Machine(rng, history_length, stuck_prob, seven_boost,
                       state=["CO", 4, 5, 6, 8, 9, 10][rng.integers(7)])

    name, m = "A", new_machine()
    start_machine(col, m, name, require_come_out=True)
    need_phase = True
    switched = False

    while col.counted < target:
        dice, truth = m.roll()
        col.tick()
        n = col.counted + 1  # index of the counted roll being logged
        if n in missed_at:
            col.add(name, dice, flag="R", notes="missed live; read from history", truth=truth)
        else:
            col.add(name, dice, flag="C" if n in corrected_at else "",
                    phase=phase_code(truth[1]) if need_phase else "", truth=truth)
            need_phase = False

        if col.counted >= target:
            break

        if switch_after is not None and not switched and col.counted == switch_after:
            last = col.rows[name][-1]
            last["time"], last["notes"] = col.clock(), "machine A serviced; switching to B"
            name, m = "B", new_machine()
            start_machine(col, m, name, require_come_out=False)
            need_phase = True
            switched = True
            continue

        for at, length in ((short_break_at, short_break_rolls), (long_break_at, long_break_rolls)):
            if at is not None and col.counted == at:
                last = col.rows[name][-1]
                last["time"], last["notes"] = col.clock(), "break"
                rolled = [m.roll() for _ in range(length)]
                col.tick(length)
                if length + 3 <= history_length:
                    # The last 3 logged rolls are still visible: recover everything, no gap.
                    for i, (d, p) in enumerate(rolled):
                        col.add(name, d, flag="R", notes="back from break" if i == 0 else "", truth=p)
                else:
                    col.add(name, flag="GAP", time=col.clock(), notes="break", truth=None)
                    # Skip the 3 oldest visible rolls: up to 2 of them may already be logged.
                    for d, p in list(m.history)[3:]:
                        col.add(name, d, flag="R", truth=p)
                    need_phase = True

    last = col.rows[name][-1]
    last["time"] = last["time"] or col.clock()
    last["notes"] = (last["notes"] + "; " if last["notes"] else "") + "session end"
    return col.rows, col.truth


def write_logs(rows: dict[str, list[dict]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for machine, machine_rows in rows.items():
        path = core.raw_log_path(out_dir, machine)
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=core.RAW_COLUMNS)
            writer.writeheader()
            writer.writerows(machine_rows)
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate simulated raw roll logs.")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "simulated")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--target", type=int, default=core.TARGET_ROLLS)
    parser.add_argument("--history", type=int, default=20, help="rolls kept by the history display")
    parser.add_argument("--stuck-prob", type=float, default=0.0,
                        help="chance the dice repeat exactly (a tumbling fault); 0 = fair")
    parser.add_argument("--seven-boost", type=float, default=0.0,
                        help="extra chance of a 7 on point-set rolls; 0 = fair")
    parser.add_argument("--switch-after", type=int, default=None,
                        help="switch to machine B after this many counted rolls")
    args = parser.parse_args(argv)

    for old in (core.raw_log_path(args.out_dir, m) for m in core.MACHINES):
        if old.exists():
            old.unlink()
    rows, _ = simulate_session(seed=args.seed, target=args.target, history_length=args.history,
                               stuck_prob=args.stuck_prob, seven_boost=args.seven_boost,
                               switch_after=args.switch_after)
    for path in write_logs(rows, args.out_dir):
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
