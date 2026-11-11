"""Reversible, per-user Windows gaming and responsiveness tweaks."""
from __future__ import annotations
import ctypes
import json
import os
import re
import subprocess
import winreg
from pathlib import Path

BACKUP = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AimForge" / "tweaks_backup.json"

TWEAKS = {
    "game_mode": ("Windows Game Mode", [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AutoGameModeEnabled", winreg.REG_DWORD, 1),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AllowAutoGameMode", winreg.REG_DWORD, 1),
    ]),
    "game_dvr": ("Background game capture", [
        (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_Enabled", winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", winreg.REG_DWORD, 2),
        (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode", winreg.REG_DWORD, 1),
        (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", winreg.REG_DWORD, 1),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", winreg.REG_DWORD, 0),
    ]),
    "mouse": ("Mouse acceleration", [
        (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", winreg.REG_SZ, "0"),
        (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold1", winreg.REG_SZ, "0"),
        (winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold2", winreg.REG_SZ, "0"),
    ]),
    "transparency": ("Windows transparency effects", [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", winreg.REG_DWORD, 0),
    ]),
    "animations": ("Windows visual effects", [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", winreg.REG_DWORD, 2),
    ]),
    "gamebar": ("Xbox Game Bar overlay", [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "ShowStartupPanel", winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "UseNexusForGameBarEnabled", winreg.REG_DWORD, 0),
    ]),
    "background_apps": ("Background app permissions", [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", "GlobalUserDisabled", winreg.REG_DWORD, 1),
    ]),
}

def _ident(root, path, name):
    return ("HKCU\\" if root == winreg.HKEY_CURRENT_USER else "HKLM\\") + path + "\\" + name

def _read_value(root, path, name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            value, kind = winreg.QueryValueEx(key, name)
            return {"exists": True, "value": value, "kind": kind}
    except OSError:
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

def _load_backup():
    if not BACKUP.exists():
        return {}
    try:
        data = json.loads(BACKUP.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return data
    except (ValueError, OSError):
        raise RuntimeError("AimForge's tweak backup is unreadable; no settings were changed.")

def _save_backup(saved):
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    temp = BACKUP.with_suffix(".tmp")
    temp.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    temp.replace(BACKUP)

def _apply_mouse_now():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_READ) as key:
            values = [int(winreg.QueryValueEx(key, name)[0]) for name in ("MouseThreshold1", "MouseThreshold2", "MouseSpeed")]
        params = (ctypes.c_int * 3)(*values)
        user32 = ctypes.windll.user32
        user32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        user32.SystemParametersInfoW.restype = ctypes.c_bool
        user32.SystemParametersInfoW(4, 0, ctypes.byref(params), 3)
    except Exception:
        pass

def apply_tweaks(selected):
    if os.name != "nt":
        raise RuntimeError("Gaming Tweaks are available on Windows only.")
    selected = list(dict.fromkeys(selected))
    unknown = set(selected) - set(TWEAKS) - {"power"}
    if unknown:
        raise ValueError("Unknown tweak: " + ", ".join(sorted(unknown)))
    if not selected:
        raise ValueError("Select at least one tweak.")
    saved = _load_backup()
    for tweak_id in selected:
        if tweak_id == "power":
            if "power_plan" not in saved:
                saved["power_plan"] = _power_plan()
            continue
        for root, path, name, kind, value in TWEAKS[tweak_id][1]:
            ident = _ident(root, path, name)
            if ident not in saved:
                saved[ident] = _read_value(root, path, name)
    _save_backup(saved)
    changed = []
    for tweak_id in selected:
        if tweak_id == "power":
            subprocess.run(["powercfg", "/setactive", "SCHEME_MIN"], capture_output=True, text=True, check=True)
            changed.append("High performance power plan")
        else:
            for root, path, name, kind, value in TWEAKS[tweak_id][1]:
                _write_value(root, path, name, kind, value)
            changed.append(TWEAKS[tweak_id][0])
            if tweak_id == "mouse":
                _apply_mouse_now()
    return changed

def apply_competitive_preset():
    return apply_tweaks([*TWEAKS.keys(), "power"])

def restore_previous_settings():
    if not BACKUP.exists():
        return []
    saved = _load_backup()
    restored = []
    for tweak_id, (label, entries) in TWEAKS.items():
        touched = False
        for root, path, name, kind, value in entries:
            ident = _ident(root, path, name)
            old = saved.get(ident)
            if old is None:
                continue
            if old.get("exists"):
                _write_value(root, path, name, old["kind"], old["value"])
            else:
                try:
                    with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
            touched = True
        if touched:
            restored.append(label)
    if saved.get("power_plan"):
        subprocess.run(["powercfg", "/setactive", saved["power_plan"]], capture_output=True, text=True, check=True)
        restored.append("Previous power plan")
    if any(k.startswith("HKCU\\Control Panel\\Mouse\\") for k in saved):
        _apply_mouse_now()
    BACKUP.unlink(missing_ok=True)
    return restored

def get_tweak_status():
    status = {}
    for tweak_id, (label, entries) in TWEAKS.items():
        matches = []
        for root, path, name, kind, target in entries:
            current = _read_value(root, path, name)
            matches.append(current.get("exists") and current.get("value") == target)
        status[tweak_id] = "Applied" if all(matches) else ("Partially applied" if any(matches) else "Not applied")
    try:
        active = _power_plan()
        status["power"] = "Applied" if active.lower() == "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" else "Not applied"
    except Exception:
        status["power"] = "Unavailable"
    return status
