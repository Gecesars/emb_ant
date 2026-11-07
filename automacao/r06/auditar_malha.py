"""Extrair mensagens de reparo sem copiar triangulos g3derr para o repositorio."""
import argparse, collections, json
from pathlib import Path

def audit(folder):
    files=list(folder.rglob('nominalmesh.g3derr'))
    assert len(files)==1,files
    blocks=[];header=[]
    with files[0].open(encoding='latin1') as f:
        active=False
        for line in f:
            if line.strip()=='BEGIN_ERR':
                active=True;header=[]
            elif active and '#ntets' in line:
                blocks.append(header);active=False
            elif active:header.append(line.strip())
    major=[b for b in blocks if any('Major repaired bodies' in x for x in b)]
    minor=[b for b in blocks if any('Minor repaired bodies' in x for x in b)]
    def ids(items):
        return sorted({int(v) for b in items for line in b if '# nbids' in line
                       for v in line.split('#')[0].split()[1:] if int(v)>=0})
    unique=collections.Counter(tuple(b) for b in blocks)
    return dict(fonte=str(files[0]),bytes=files[0].stat().st_size,
                reparos_major=len(ids(major)),reparos_minor=len(ids(minor)),
                corpos_major_ids=ids(major),corpos_minor_ids=ids(minor),
                ocorrencias_major=len(major),ocorrencias_minor=len(minor),
                avisos=[dict(cabecalho=list(k),ocorrencias=v) for k,v in unique.items()],
                nota='Contagem de corpos unicos; avisos podem se repetir nos passes. Codigos numericos dos cabecalhos nao sao contagens.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pasta',type=Path);parser.add_argument('destino',type=Path)
    args=parser.parse_args();result=audit(args.pasta)
    args.destino.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='avisos'},indent=2))
