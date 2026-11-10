# AimForge — Windows Gaming Command Center

A modular Windows desktop starter application. Includes a PySide6 UI, transparent desktop crosshair, local game profiles, CPU/RAM monitoring, PresentMon CSV FPS ingestion, benchmark CSV import, and local backup/restore.

## Run
Install Python 3.11+, then in PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```
Build an executable with `pip install pyinstaller` then `pyinstaller --noconfirm --windowed --name AimForge main.py`.

## Accuracy and safety
FPS is shown only when supported frame-time samples are read from a PresentMon CSV; otherwise it is unavailable. CPU/RAM use psutil. GPU sensors and temperatures remain unavailable without a supported telemetry provider. No benchmark measurements are bundled or fabricated. Import real benchmark CSV data using `benchmark_template.csv`. Crosshair is an external desktop overlay; it does not inject into games or alter game memory. Use only where the game and anti-cheat permit overlays.

Benchmark CSV required columns: `game,cpu,gpu,resolution,preset,avg_fps,one_percent_low,source,benchmark_date,kind` where kind is `measured` or `estimated`.

This is a working foundation; features such as global hotkeys, system tray, automatic updates, full GPU sensor support, community sync, and automatic game detection still require implementation.
