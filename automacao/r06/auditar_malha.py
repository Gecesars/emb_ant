"""Extrair mensagens de reparo sem copiar triangulos g3derr para o repositorio."""
import argparse, collections, json, re
from datetime import datetime
from pathlib import Path

def audit(folder):
    files=list(folder.rglob('nominalmesh.g3derr'))
    assert len(files)==1,files
    scope_path=folder/'malha_execucao.json'
    scope=json.loads(scope_path.read_text(encoding='utf8')) if scope_path.exists() else None
    since=datetime.fromisoformat(scope['inicio']).timestamp() if scope else None
    blocks=[];historical=[];header=[];timestamp=None;timestamps=set()
    with files[0].open(encoding='latin1') as f:
        active=False
        for line in f:
            if ':TimeStamp' in line:
                match=re.search(r'(\d+)\s*:TimeStamp',line)
                assert match,line
                timestamp=int(match[1]);timestamps.add(timestamp)
            elif line.strip()=='BEGIN_ERR':
                active=True;header=[]
            elif active and '#ntets' in line:
                assert timestamp is not None,'Aviso sem data de origem'
                (blocks if since is None or timestamp>=since else historical).append(header)
                active=False
            elif active:header.append(line.strip())
    major=[b for b in blocks if any('Major repaired bodies' in x for x in b)]
    minor=[b for b in blocks if any('Minor repaired bodies' in x for x in b)]
    def ids(items):
        return sorted({int(v) for b in items for line in b if '# nbids' in line
                       for v in line.split('#')[0].split()[1:] if int(v)>=0})
    unique=collections.Counter(tuple(b) for b in blocks)
    historical_major=[b for b in historical if any('Major repaired bodies' in x for x in b)]
    assert since is None or any(t>=since for t in timestamps),'Nenhum bloco de metadados no escopo solicitado'
    return dict(fonte=str(files[0]),bytes=files[0].stat().st_size,
                escopo_execucao=scope,blocos_historicos_excluidos=len(historical),
                corpos_major_historicos_ids=ids(historical_major),
                origem_timestamps=sorted(timestamps),
                reparos_major=len(ids(major)),reparos_minor=len(ids(minor)),
                corpos_major_ids=ids(major),corpos_minor_ids=ids(minor),
                ocorrencias_major=len(major),ocorrencias_minor=len(minor),
                avisos=[dict(cabecalho=list(k),ocorrencias=v) for k,v in unique.items()],
                nota='Corpos unicos no escopo. G3derr agrega execucoes; filtro usa o TimeStamp de cada bloco, preservando a contagem historica. Codigos dos cabecalhos nao sao contagens.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pasta',type=Path);parser.add_argument('destino',type=Path)
    args=parser.parse_args();result=audit(args.pasta)
    args.destino.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='avisos'},indent=2))
