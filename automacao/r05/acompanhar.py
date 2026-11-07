"""Acompanhar etapas e Delta S do perfil nativo, sem alterar o solver."""
import argparse
from datetime import datetime
import re
import time
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('estudo',type=Path)
parser.add_argument('--minutos',type=float,default=60)
args=parser.parse_args()
limit=time.monotonic()+60*args.minutos
previous=None
while time.monotonic()<limit:
    profiles=list(args.estudo.glob('*.aedtresults/**/*.profile'))
    state='Aguardando perfil'
    if profiles:
        data=max(profiles,key=lambda p:p.stat().st_mtime).read_text(errors='replace')
        steps=re.findall(r"Name='(Initial Meshing|Adaptive Pass \d+|Frequency - [^']+)'",data)
        deltas=re.findall(r"Max Mag\. Delta S.*?([0-9]+\.[0-9]+),",data)
        if steps:state=steps[-1]
        if deltas:state+='; último Delta S = '+deltas[-1]
        items=re.findall(r"ProfileItem\('([^']+)'",data)
        if items and items[-1]:state+='; '+items[-1]
    log=args.estudo/'solucao.log'
    if log.exists():
        content=log.read_text(errors='replace')
        if 'CENTRO_CONVERGIDO' in content or 'Traceback' in content:
            print(datetime.now().isoformat(timespec='seconds'),content[-1000:],flush=True)
            break
    if state!=previous:
        print(datetime.now().isoformat(timespec='seconds'),state,flush=True)
        previous=state
    time.sleep(20)
