import csv, os, time
from collections import deque
import psutil

class PerformanceMonitor:
    def __init__(self):
        self.samples = deque(maxlen=240)
        self.csv_path = None
        psutil.cpu_percent(interval=None)

    def set_csv(self, path):
        self.csv_path = path
        self.samples.clear()

    def _read_csv(self):
        if not self.csv_path or not os.path.isfile(self.csv_path): return
        try:
            with open(self.csv_path, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            keys = ("MsBetweenPresents", "msBetweenPresents",
                    "MsBetweenDisplayChange", "msBetweenDisplayChange")
            self.samples.clear()
            for row in rows[-240:]:
                key = next((k for k in keys if k in row), None)
                if key:
                    try:
                        ms = float(row[key])
                        if 0.05 <= ms <= 1000: self.samples.append(ms)
                    except (ValueError, TypeError): pass
        except (OSError, csv.Error): pass

    def snapshot(self):
        self._read_csv()
        fps = avg = low = None
        if self.samples:
            vals = list(self.samples)
            fps = 1000.0 / vals[-1]
            avg = 1000.0 / (sum(vals) / len(vals))
            ordered = sorted(1000.0 / x for x in vals)
            low = sum(ordered[:max(1, (len(ordered)+99)//100)]) / max(1, (len(ordered)+99)//100)
        vm = psutil.virtual_memory()
        return {"fps":fps, "avg_fps":avg, "one_percent_low":low,
                "cpu_usage":psutil.cpu_percent(interval=None),
                "ram_used_gb":(vm.total-vm.available)/1024**3,
                "ram_total_gb":vm.total/1024**3, "timestamp":time.time(),
                "cpu_temp":None, "gpu_temp":None, "gpu_usage":None,
                "vram_used":None, "cpu_clock":None, "gpu_clock":None, "gpu_power":None}
