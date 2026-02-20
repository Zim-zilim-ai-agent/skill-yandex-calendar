import subprocess
from pathlib import Path


def test_python_scripts_have_help():
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if not scripts_dir.exists():
        return
    py_scripts = sorted(scripts_dir.glob("*.py"))
    for script in py_scripts:
        proc = subprocess.run(["python3", str(script), "--help"], capture_output=True, text=True)
        assert proc.returncode == 0, f"--help failed for {script}: {proc.stderr}"
