import os
import subprocess

BASE_DIR = r"D:\SceneryX"
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")

print("Building single-file SceneryX.exe in D:\\SceneryX with custom icon...")

pyinstaller_cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name=SceneryX",
    f"--icon={ICON_PATH}",
    f"--distpath={BASE_DIR}",
    f"--add-data={os.path.join(BASE_DIR, 'airports.json')};.",
    f"--add-data={os.path.join(BASE_DIR, 'airport_airlines.json')};.",
    f"--add-data={os.path.join(BASE_DIR, 'airport_routes.json')};.",
    f"--add-data={os.path.join(BASE_DIR, 'airport_runways.json')};.",
    f"--add-data={os.path.join(BASE_DIR, 'installed_airports.json')};.",
    f"--add-data={ICON_PATH};.",
    f"--add-data={os.path.join(BASE_DIR, 'web')};web",
    os.path.join(BASE_DIR, "main.py")
]

res = subprocess.run(pyinstaller_cmd, cwd=BASE_DIR)

if res.returncode == 0:
    print("Single-file build successful!")
    print(f"Executable created at: {os.path.join(BASE_DIR, 'SceneryX.exe')}")
else:
    print(f"Build failed with code {res.returncode}")
