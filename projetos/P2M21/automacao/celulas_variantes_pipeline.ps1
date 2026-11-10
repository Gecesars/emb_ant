param([int]$ContinuacaoPID)
$ErrorActionPreference='Stop'
$work='D:/dev/EMBRAER/P2M21'
$out="$work/comparacao_colunas_niveis"
function State([string]$s,[string]$v){[pscustomobject]@{estado=$s;variante=$v;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$out/pipeline.json" -Encoding utf8}
function Native([string]$script,[string]$root,[string]$stage){
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo; serializar'}
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit();if($p.ExitCode -ne 0){throw "AEDT $stage exit $($p.ExitCode)"}
}
try{
    State 'AGUARDANDO_PASSES7_E8' 'R15'
    if($ContinuacaoPID){
        $p=Get-CimInstance Win32_Process -Filter "ProcessId=$ContinuacaoPID"
        if($p){
            if($p.Name -notin @('powershell.exe','pwsh.exe') -or $p.CommandLine -notmatch 'oito_continuar_pipeline.ps1'){throw 'PID nao pertence a continuacao'}
            Wait-Process -Id $ContinuacaoPID
        }
    }
    $state=Get-Content -Raw "$work/R15_Oito_Celulas_8passes/pipeline.json"|ConvertFrom-Json
    if($state.estado -ne 'CONCLUIDO_AGUARDA_REVISAO'){throw 'Continuacao requer verificacao antes das variantes'}
    $r=Get-Content -Raw "$work/R15_Oito_Celulas_8passes/resultado.json"|ConvertFrom-Json
    if(!$r.fisica_ok){throw 'Referencia tem falha fisica'}
    foreach($v in @('R16_Oito_Celulas_78mm','R17_Dez_Celulas_78mm')){
        $root="$work/$v";$env:P2M21_OITO_ROOT=$root
        $cad=Get-Content -Raw "$root/cad/intersecoes.json"|ConvertFrom-Json
        if(!$cad.aprovado){throw "CAD $v nao aprovado"}
        $cfg=Get-Content -Raw "$root/configuracao.json"|ConvertFrom-Json
        if(Test-Path "$root/$($cfg.native)"){throw "Nativo existente em $v; nao duplicar"}
        State 'CRIANDO_HFSS' $v
        Native 'oito_celulas_hfss.py' $root 'criacao'
        $valid=Get-Content -Raw "$root/hfss_validacao.json"|ConvertFrom-Json
        if($valid.validacao -ne 1 -or $valid.erros.Count -ne 0 -or $valid.portas -ne $cfg.portas.Count){throw 'Modelo nao validado'}
        State 'RESOLVENDO_CENTRO_MAX6' $v
        Native 'oito_celulas_resolver.py' $root 'centro'
        State 'ANALISANDO' $v
        & python (Join-Path $PSScriptRoot 'oito_celulas_analisar.py') *> "$root/analise.log"
        if($LASTEXITCODE -ne 0){throw "Falha analise $v"}
        $r=Get-Content -Raw "$root/resultado.json"|ConvertFrom-Json
        if(!$r.fisica_ok){throw "Falha fisica $v; investigar antes de prosseguir"}
    }
    State 'CONCLUIDO_AGUARDA_COMPARACAO_E_REVISAO' 'R17'
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$out/pipeline.json" -Encoding utf8
    throw
}
