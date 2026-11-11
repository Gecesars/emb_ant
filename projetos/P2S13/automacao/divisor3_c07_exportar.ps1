$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$kc=Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/kicad-cli.exe'
$kpython=Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/python.exe'
$fc='C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe'
$out=Join-Path $repo 'projetos/P2S13/kicad/divisor_duplo_1x3_C07'
$board=Join-Path $out 'divisor_duplo_1x3_C07.kicad_pcb'
function Checked([string]$Program,[string[]]$Arguments){
    & $Program @Arguments
    if($LASTEXITCODE -ne 0){throw "Falha em $Program ($LASTEXITCODE)"}
}
Checked $fc @((Join-Path $PSScriptRoot 'divisor3_c07_conferir_cad.py'))
Checked $kpython @((Join-Path $PSScriptRoot 'divisor3_c07_kicad.py'))
Checked $kc @('pcb','drc','--format','json','-o',"$out/drc.json",$board)
Checked $kc @('pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,Edge.Cuts','--precision','6','--disable-aperture-macros','-o',"$out/gerbers/",$board)
Checked $kpython @((Join-Path $PSScriptRoot 'divisor3_c07_furacao.py'))
Checked $kc @('pcb','export','svg','-l','F.Cu,B.Cu','--common-layers','Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--mode-multi','-o',"$out/preview/",$board)
Checked 'python' @((Join-Path $PSScriptRoot 'divisor3_c07_conferir.py'))
Checked 'python' @((Join-Path $PSScriptRoot 'divisor3_c07_empacotar.py'))
Write-Output 'C07 convertida. Rever imagens. Nove violacoes DFM preservadas; nao liberada para fabricacao padrao.'
