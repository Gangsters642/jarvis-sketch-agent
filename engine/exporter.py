import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_SAVE_DIR = BASE_DIR / "saved_projects"
LOCAL_SAVE_DIR.mkdir(parents=True, exist_ok=True)

ANDROID_DOWNLOAD_DIRS = [
    Path("/storage/emulated/0/Download/JarvisSketches"),
    Path.home() / "storage" / "downloads" / "JarvisSketches",
]


def _get_android_export_dir() -> Path | None:
    for d in ANDROID_DOWNLOAD_DIRS:
        try:
            parent = d.parent
            if parent.exists() and os.access(parent, os.W_OK):
                d.mkdir(parents=True, exist_ok=True)
                return d
        except Exception:
            continue
    return None


def save_sketch(svg_content: str, name: str = "jarvis_sketch") -> dict:
    """
    Saves SVG sketch in project history and exports to Android Downloads if accessible.
    """
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", (name or "jarvis_sketch").strip())
    clean_name = clean_name[:40] or "jarvis_sketch"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_{timestamp}.svg"

    local_path = LOCAL_SAVE_DIR / filename
    local_path.write_text(svg_content, encoding="utf-8")

    android_path_str = None
    android_dir = _get_android_export_dir()
    if android_dir:
        try:
            target = android_dir / filename
            shutil.copyfile(local_path, target)
            android_path_str = str(target)
        except Exception:
            android_path_str = None

    return {
        "filename": filename,
        "local_path": str(local_path),
        "android_path": android_path_str,
    }


def list_saved_sketches() -> list:
    """
    Returns list of saved SVG files in saved_projects/ sorted newest first.
    """
    files = sorted(
        LOCAL_SAVE_DIR.glob("*.svg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    result = []
    for f in files[:25]:
        result.append(
            {
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    return result


def get_safe_sketch_path(filename: str) -> Path | None:
    """
    Safely resolves a filename inside saved_projects/ to prevent directory traversal.
    """
    safe_name = os.path.basename(filename)
    target = (LOCAL_SAVE_DIR / safe_name).resolve()
    if target.parent == LOCAL_SAVE_DIR.resolve() and target.exists():
        return target
    return None


def open_in_android_app(filename: str) -> tuple[bool, str]:
    """
    Uses termux-open to hand off the exported SVG file to a compatible Android app.
    """
    local_target = get_safe_sketch_path(filename)
    if not local_target:
        return False, "Error: Sketch file nahi mili."

    # Prefer opening from shared Android Downloads if available so external apps have read permission
    android_dir = _get_android_export_dir()
    open_target = local_target
    if android_dir and (android_dir / local_target.name).exists():
        open_target = android_dir / local_target.name

    termux_open_bin = shutil.which("termux-open")
    if not termux_open_bin:
        return (
            False,
            "termux-open command nahi mili. File Download/JarvisSketches folder mein save hai.",
        )

    try:
        subprocess.Popen(
            [termux_open_bin, "--chooser", str(open_target)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True, f"Android App Chooser opened for {local_target.name}"
    except Exception as exc:
        return False, f"Android app open karne mein masla aaya: {exc}"
