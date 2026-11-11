"""Safe, reversible Windows gaming tweaks for AimForge."""
from __future__ import annotations
import json
import os
import re
import subprocess
import winreg
from pathlib import Path

BACKUP = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AimForge" / "tweaks_backup.json"

# Per-user settings only: no driver flashing, overclocking, service disabling or BCD edits.
REGISTRY_CHANGES = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AutoGameModeEnabled", winreg.REG_DWORD, 1, "Game Mode"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AllowAutoGameMode", winreg.REG_DWORD, 1, "Game Mode"),
    (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_Enabled", winreg.REG_DWORD, 0, "Game DVR"),
    (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", winreg.REG_SZ, "0", "Mouse acceleration"),
    (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold1", winreg.REG_SZ, "0", "Mouse acceleration"),
    (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold2", winreg.REG_SZ, "0", "Mouse acceleration"),
]

def _read_value(root, path, name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            value, kind = winreg.QueryValueEx(key, name)
            return {"exists": True, "value": value, "kind": kind}
    except FileNotFoundError:
        return {"exists": False}

def _write_value(root, path, name, kind, value):
    with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, kind, value)

def _power_plan():
    p = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, check=True)
    m = re.search(r"([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})", p.stdout)
    if not m:
        raise RuntimeError("Could not identify the active Windows power plan.")
    return m.group(1)

def apply_competitive_preset():
    if os.name != "nt":
        raise RuntimeError("Gaming Tweaks are available on Windows only.")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    saved = {}
    if BACKUP.exists():
        try:
            saved = json.loads(BACKUP.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            saved = {}
    changed = []
    for root, path, name, kind, value, label in REGISTRY_CHANGES:
        ident = "HKCU\\" + path + "\\" + name
        if ident not in saved:
            saved[ident] = _read_value(root, path, name)
        _write_value(root, path, name, kind, value)
        if label not in changed:
            changed.append(label)
    if "power_plan" not in saved:
        saved["power_plan"] = _power_plan()
    subprocess.run(["powercfg", "/setactive", "SCHEME_MIN"], capture_output=True, text=True, check=True)
    changed.append("High performance power plan")
    BACKUP.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return changed

def restore_previous_settings():
    if not BACKUP.exists():
        return []
    saved = json.loads(BACKUP.read_text(encoding="utf-8"))
    restored = []
    for root, path, name, kind, value, label in REGISTRY_CHANGES:
        ident = "HKCU\\" + path + "\\" + name
        old = saved.get(ident)
        if old is None:
            continue
        try:
            if old.get("exists"):
                _write_value(root, path, name, old["kind"], old["value"])
            else:
                with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
            if label not in restored:
                restored.append(label)
        except FileNotFoundError:
            pass
    if saved.get("power_plan"):
        subprocess.run(["powercfg", "/setactive", saved["power_plan"]], capture_output=True, text=True, check=True)
        restored.append("Power plan")
    BACKUP.unlink(missing_ok=True)
    return restored
