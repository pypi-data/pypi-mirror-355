from math import isnan
import argparse
import signal
import time
import sys

from ._version import __version__


def _handler(total: int | float, start: int, *_) -> None:
    """
    Bind total and start to make into a signal handler that prints elapsed time
    """
    if total != float("inf"):
        remain: int | str = round(max(0, round(total - (time.time_ns() - start) / 1e9)))
        t: int | float | str = int(total) if int(total) == total else total
    else:
        t, remain = ("infinity", "infinity")
    print(f"sleep: about {remain} seconds(s) left out of the original {t}")


def sigsleep(seconds: int | float, sig: signal.Signals) -> int:
    """
    Sleep, print elapsed time on intercepting signal
    :return Exit code
    """
    if seconds < 0:  # Just in case
        raise ValueError("sleep length must be non-negative")
    if isnan(seconds):  # Just in case
        raise ValueError("sleep length may not be NaN")
    # Put handler items in new item so edits don't change them later
    handler_args = (seconds, time.time_ns())
    signal.signal(sig, lambda *_: _handler(*handler_args))
    try:
        # Split sleep into multiple calls for large numbers, also
        # OS Schedulers can be wonky and have limits under the theoretical 2^64
        max_sleep = 1e9
        while seconds > 0:
            time.sleep(sec := min(seconds, max_sleep))
            seconds -= sec
    except KeyboardInterrupt:
        return 130
    return 0


def length(num: str) -> int | float:  # Name it length so that argparse error messages are cleaner
    """
    Convert the NUMBER[SUFFIX] num into an int or float
    """
    if not (n := num.lower()):
        raise ValueError("Empty string is not a valid number")
    if (scale := {"m": 60, "h": 3600, "d": 3600 * 24}.get(n[-1], 1)) != 1 or n[-1] == "s":
        n = n[:-1]
    return (int(n) if n.isdigit() else float(n)) * scale


def cli() -> None:
    """
    CLI for sigsleep
    Default signal is SIGINFO if it exists, else SIGUSR1
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} {__version__}")
    parser.add_argument(
        "seconds",
        metavar="NUMBER[SUFFIX]",
        type=length,
        nargs="+",
        help="Pause for NUMBER seconds, where NUMBER is an integer or floating-point (inf is allowed). SUFFIX may be 's', 'm', 'h', or 'd', for seconds, minuts, hours, days. With multiple arguments, pause for the sum of their values.",
    )
    to_signal = lambda d: signal.Signals(int(d))
    to_signal.__name__ = "signal"  # Cleaner output
    parser.add_argument(
        "-s",
        "--signal",
        type=to_signal,
        help="The signal to intercept",
        default=signal.SIGINFO if hasattr(signal, "SIGINFO") else signal.SIGUSR1,
    )
    ns = parser.parse_args()
    sys.exit(sigsleep(sum(ns.seconds), ns.signal))
