# System Uptime Script

This repository includes a small, secure, and reliable Python script to print the current system uptime.

Usage:

```powershell
python copilot_test.py
```

Notes:
- Avoids shell invocation and external command injection.
- Uses Windows API via ctypes when available (more reliable than external tools).
- Uses timeouts and command-path checks for subprocess calls.
- Works on Windows, Linux, and macOS.
