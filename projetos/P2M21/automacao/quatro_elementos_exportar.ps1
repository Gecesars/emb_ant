$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$kc=Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/kicad-cli.exe'
$kpython=Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/python.exe'
$out=Join-Path $repo 'projetos/P2M21/kicad/4_elementos'
$board=Join-Path $out '4_elementos.kicad_pcb'
function Checked([string]$Program,[string[]]$Arguments){
    & $Program @Arguments
    if($LASTEXITCODE -ne 0){throw "Falha em $Program ($LASTEXITCODE)"}
}
Checked $kpython @((Join-Path $PSScriptRoot 'quatro_elementos_kicad.py'))
Checked $kc @('pcb','drc','--format','json','-o',"$out/drc.json",$board)
Checked $kc @('pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,Edge.Cuts','--precision','6','--disable-aperture-macros','-o',"$out/gerbers/",$board)
Checked $kc @('pcb','export','drill','--format','excellon','--excellon-separate-th','--excellon-units','mm','--generate-report','--report-path',"$out/furacao.txt",'-o',"$out/gerbers/",$board)
Checked $kc @('pcb','export','svg','-l','F.Cu,B.Cu','--common-layers','Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--mode-multi','-o',"$out/preview/",$board)
Checked 'python' @((Join-Path $PSScriptRoot 'quatro_elementos_conferir.py'))
Checked 'python' @((Join-Path $PSScriptRoot 'quatro_elementos_gerbers.py'))
Checked 'python' @((Join-Path $PSScriptRoot 'quatro_elementos_empacotar.py'))
Write-Output 'Pacote gerado; revisar visualmente as imagens atualizadas antes de enviar para fabricacao.'
