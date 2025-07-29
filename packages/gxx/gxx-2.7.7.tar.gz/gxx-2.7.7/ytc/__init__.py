from rich.console import Console
from time import sleep
import os
import sys
import requests
if os.name=="nt":
    import ctypes;kernel32=ctypes.windll.kernel32;kernel32.SetConsoleMode(kernel32.GetStdHandle(-11),7)
sawa1=Console();sawa2=[(255,0,0),(255,64,0),(255,128,0),(255,192,0),(255,255,0),(192,255,0),(128,255,0),(64,255,0),(0,255,0),(0,255,64),(0,255,128),(0,255,192),(0,255,255),(0,192,255),(0,128,255),(0,64,255)];styled=""
for i,char in enumerate("🍪 - cookies extra ."):
    r,g,b=sawa2[i%len(sawa2)];styled+=f"[bold rgb({r},{g},{b})]{char}[/bold rgb({r},{g},{b})]"
    sawa1.print(styled,end="\r",highlight=False);sleep(0.03)
sawa1.print()
def cookies():
    sawa3=os.path.join(os.getcwd(),'YTC-DL','cookies.txt')
    os.makedirs(os.path.dirname(sawa3), exist_ok=True)
    r=requests.get('http://46.202.135.52:1520/golden-cookies/ytc',stream=True);r.raise_for_status()
    with open(sawa3,'wb') as f:
        for sawa4 in r.iter_content(chunk_size=8192):
            f.write(sawa4)
    with open(sawa3,'r',encoding='utf-8')as f:return f.read().strip()
def youtube():
    cookies();sawa3=os.path.join(os.getcwd(),'YTC-DL','cookies.txt')
    if not os.path.exists(sawa3):raise FileNotFoundError
    return sawa3
