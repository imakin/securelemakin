#!/usr/bin/env python3
import os
import requests

r = requests.get('http://127.0.0.1:5000/list/')
files = r.text.split('\n')
print(files)

APPDIR = os.path.join(
        os.environ['HOME'],
        '.local/share/applications'
    )
for target in files:
    t = f"""[Desktop Entry]
Type=Application
Name={target} (securelemakin)
Exec=curl http://127.0.0.1:5000/type/{target}
"""
    desktopfile = os.path.join(APPDIR,f"securelemakin_{target}.desktop")
    with open(desktopfile,'w') as f:
        f.write(t)
    os.chmod(desktopfile,0o755)
