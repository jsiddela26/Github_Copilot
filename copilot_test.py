# ...existing code...
import ctypes
import datetime
import platform
import re
import shutil
import subprocess
import sys
import logging

logging.basicConfig(level=logging.WARNING)

def _uptime_from_windows_ctypes() -> float:
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        ms = kernel32.GetTickCount64()
        if ms is None:
            raise OSError("GetTickCount64 returned None")
        return float(ms) / 1000.0
    except Exception as e:
        logging.debug("ctypes uptime failed: %s", e)
        raise

def _uptime_from_windows_wmic() -> float:
    if not shutil.which("wmic"):
        raise FileNotFoundError("wmic not available")
    output = subprocess.check_output(
        ["wmic", "os", "get", "LastBootUpTime", "/VALUE"],
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=3,
    )
    for line in output.splitlines():
        if line.startswith("LastBootUpTime="):
            value = line.split("=", 1)[1].strip()
            # WMIC returns YYYYMMDDHHMMSS(.xxxx...) format
            boot_time = datetime.datetime.strptime(value[:14], "%Y%m%d%H%M%S")
            return (datetime.datetime.now() - boot_time).total_seconds()
    raise RuntimeError("WMIC output parsing failed")

def _uptime_from_proc() -> float:
    with open("/proc/uptime", "r", encoding="utf-8") as f:
        parts = f.readline().split()
        if not parts:
            raise RuntimeError("/proc/uptime empty")
        uptime = float(parts[0])
        if uptime < 0:
            raise ValueError("Negative uptime")
        return uptime

def _uptime_from_sysctl() -> float:
    if not shutil.which("sysctl"):
        raise FileNotFoundError("sysctl not available")
    output = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True, timeout=3)
    # Example: { sec = 1610000000, usec = 0 } Sun Jan  7 10:00:00 2021
    m = re.search(r"sec\s*=\s*(\d+)", output)
    if not m:
        # Some macOS versions print raw timestamp
        try:
            ts = int(output.strip())
            return (datetime.datetime.now() - datetime.datetime.fromtimestamp(ts)).total_seconds()
        except Exception as e:
            raise RuntimeError("sysctl output parsing failed") from e
    boot_ts = int(m.group(1))
    return (datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_ts)).total_seconds()

def get_uptime_seconds() -> float:
    system = platform.system()
    last_error = None

    if system == "Windows":
        for fn in (_uptime_from_windows_ctypes, _uptime_from_windows_wmic):
            try:
                return fn()
            except Exception as e:
                last_error = e
        raise RuntimeError("Unable to determine uptime on Windows") from last_error

    if system == "Linux":
        try:
            return _uptime_from_proc()
        except Exception as e:
            last_error = e

    if system == "Darwin":
        try:
            return _uptime_from_sysctl()
        except Exception as e:
            last_error = e

    raise RuntimeError(f"Unable to determine system uptime on this platform: {system}") from last_error

def format_uptime(seconds: float) -> str:
    delta = datetime.timedelta(seconds=int(max(0, int(seconds))))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return ", ".join(parts)

def main():
    try:
        uptime_seconds = get_uptime_seconds()
        print(f"System uptime: {format_uptime(uptime_seconds)}")
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
# ...existing code...
