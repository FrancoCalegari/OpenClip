import os
import platform
import subprocess

def abrir_carpeta(path):
    if platform.system() == "Windows":
        os.startfile(os.path.abspath(path))
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def listar_videos(path):
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if f.endswith(".mp4")]
