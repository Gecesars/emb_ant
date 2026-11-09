"""Preparar MIME depois da revisao visual; envio usa o conector Gmail autorizado."""
import json,base64,hashlib
from pathlib import Path
root=Path('D:/dev/EMBRAER/P2M21/R04_Centro_Classic')
assert not (root/'email_6passes_enviado.json').exists(),'Recibo existente; nao enviar novamente.'
audit=json.loads((root/'antena/auditoria_centro.json').read_text(encoding='utf-8-sig'))
assert audit['convergencia']['passes']==6
norm=json.loads((root/'polares/normalizacao.json').read_text(encoding='utf-8-sig'));assert norm['passes']==6
review=json.loads((root/'polares/revisao_visual.json').read_text(encoding='utf-8-sig'));assert review['revisado']
parts=[dict(mime_type='text/html',charset='UTF-8',body=dict(content=(root/'email_polares_6passes.html').read_text(encoding='utf-8')))]
for axis in ['Horizontal','Vertical']:
    name='P2M21_'+axis+'_polar_E_Emax.png';blob=(root/'polares'/name).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==review['sha256'][name]
    parts.append(dict(mime_type='image/png',filename=name,content_disposition='attachment',body=dict(base64_url_content=base64.urlsafe_b64encode(blob).decode('ascii').rstrip('='))))
payload=dict(to='gecesars@gmail.com',subject='P2M21 — 6 passes — diagramas polares E/Emax em 5,17 GHz',payload=dict(mime_type='multipart/mixed',parts=parts),response_fields=['id','thread_id','label_ids','size_estimate'])
path=root/'email_payload_6passes.json';path.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(payload=str(path),bytes=path.stat().st_size,anexos=[p['filename'] for p in parts[1:]],enviado=False)))
