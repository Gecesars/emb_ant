"""Identificar objetos sinalizados pelo TAU Flex, sem copiar os triângulos ao Git."""
import argparse
from collections import defaultdict
import json
import re
from pathlib import Path


def main(project):
    text=project.read_bytes().decode('latin1')
    mapping={}
    for block in text.split("$begin 'GeometryPart'")[1:]:
        name=re.search("Name='([^']+)'",block)
        number=re.search(r'ParentPartID=(\d+)',block)
        if name and number:mapping[int(number[1])]=name[1]
    source=next(project.with_suffix('.aedtresults').rglob('nominalmesh.g3derr'))
    groups=defaultdict(list)
    for block in source.read_text().split('BEGIN_ERR')[1:]:
        label=re.sub(r'^\d+\s+','',block.strip().splitlines()[0])
        ids=[]
        for line in re.findall(r'(?m)^([\d ]+)# nbids',block):
            numbers=list(map(int,line.split()))
            assert numbers[0]==len(numbers)-1
            ids.extend(numbers[1:])
        groups[label].extend(mapping.get(number,'ID_'+str(number)) for number in ids)
    result=dict(arquivo=str(project),avisos={key:sorted(set(names)) for key,names in groups.items()},
                nota='Os avisos de representação geométrica não são o critério de convergência em S. Conferir influência nas métricas.')
    (project.parent/'auditoria_malha.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('projeto',type=Path)
    main(parser.parse_args().projeto)
