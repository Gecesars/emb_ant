param([Parameter(Mandatory=$true)][string]$Variante)
$ErrorActionPreference='Stop'
$study='D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2'
if($Variante -notmatch '^m[0-9]{2}$'){throw 'Variante fora do estudo'}
$root=Join-Path $study $Variante
$env:P2S13_ROOT=$root
function State([string]$s){[pscustomobject]@{estado=$s;variante=$Variante;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$study/pipeline.json" -Encoding utf8}
function Native([string]$script,[string]$stage){
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo'}
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit();if($p.ExitCode -ne 0){throw "AEDT $stage terminou com $($p.ExitCode)"}
}
try{
    $cfg=Get-Content -Raw "$root/configuracao.json"|ConvertFrom-Json
    $cad=Get-Content -Raw "$root/cad/intersecoes.json"|ConvertFrom-Json
    if(!$cad.aprovado){throw 'CAD nao aprovado'}
    $cell=Get-Content -Raw "$root/placa2/conectividade.json"|ConvertFrom-Json
    if(!$cell.aprovado){throw 'Continuidade/isolacao PCB2 nao aprovada'}
    $delta=Get-Content -Raw "$root/placa2/alteracoes_conferidas.json"|ConvertFrom-Json
    if(!$delta.radiadores_retornos_portas_vias_outline_preservados){throw 'Escopo da alteracao nao conferido'}
    if(Test-Path "$root/$($cfg.native)"){throw 'Nativo existente; nao duplicar fila'}
    State 'CRIANDO_HFSS';Native 'criar_hfss.py' 'criacao'
    $valid=Get-Content -Raw "$root/hfss_validacao.json"|ConvertFrom-Json
    if($valid.validacao -ne 1 -or $valid.erros.Count -ne 0 -or $valid.portas -ne 4){throw 'Modelo nao validado'}
    State 'GERANDO_MALHA';Native 'gerar_malha.py' 'malha'
    & python (Join-Path $PSScriptRoot 'auditar_malha_inicial.py') $root *> "$root/auditoria_malha.log"
    if($LASTEXITCODE -ne 0){throw 'Auditoria da malha inicial falhou'}
    State 'RESOLVENDO_CENTRO';Native 'resolver.py' 'centro'
    $sol=Get-Content -Raw "$root/qualificacao.json"|ConvertFrom-Json
    if($sol.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA'){throw 'Solver nao exportou'}
    State 'ANALISANDO'
    $a=Start-Process 'python' -ArgumentList @((Join-Path $PSScriptRoot 'analisar.py')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$root/analise.log" -RedirectStandardError "$root/analise_erro.log"
    if($a.ExitCode -ne 0){throw 'Falha de analise; consultar analise_erro.log'}
    State 'CONCLUIDO_AGUARDA_COMPARACAO'
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';variante=$Variante;erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$study/pipeline.json" -Encoding utf8
    throw
}
