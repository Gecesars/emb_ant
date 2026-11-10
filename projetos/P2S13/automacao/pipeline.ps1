param([string[]]$Variantes=@('v00_plano','v01_b20_a60','v02_b30_a60'),[switch]$UsarNativosPreparados)
$ErrorActionPreference='Stop'
$study='D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado'
function State([string]$s,[string]$v){[pscustomobject]@{estado=$s;variante=$v;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$study/pipeline.json" -Encoding utf8}
function Native([string]$script,[string]$root,[string]$stage){
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo'}
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit();if($p.ExitCode -ne 0){throw "AEDT $stage terminou com $($p.ExitCode)"}
}
try{
    foreach($v in $Variantes){
        $root="$study/$v";$env:P2S13_ROOT=$root
        $cfg=Get-Content -Raw "$root/configuracao.json"|ConvertFrom-Json
        $cad=Get-Content -Raw "$root/cad/intersecoes.json"|ConvertFrom-Json
        if(!$cad.aprovado){throw 'CAD nao aprovado'}
        if(Test-Path "$root/$($cfg.native)"){
            if(!$UsarNativosPreparados){throw 'Nativo existente; nao duplicar'}
            $results=[IO.Path]::ChangeExtension((Join-Path $root $cfg.native),'.aedtresults')
            if((Test-Path "$root/convergencia.txt") -or (Get-ChildItem -LiteralPath $results -Recurse -Force -Filter '*.EMConvData' -ErrorAction SilentlyContinue)){throw 'Resultado existente; nao reiniciar ciclo'}
        }else{State 'CRIANDO_HFSS' $v;Native 'criar_hfss.py' $root 'criacao'}
        $valid=Get-Content -Raw "$root/hfss_validacao.json"|ConvertFrom-Json
        if($valid.validacao -ne 1 -or $valid.erros.Count -ne 0 -or $valid.portas -ne 4){throw 'Modelo nao validado'}
        State 'RESOLVENDO_CENTRO' $v;Native 'resolver.py' $root 'centro'
        $sol=Get-Content -Raw "$root/qualificacao.json"|ConvertFrom-Json
        if($sol.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA'){throw 'Solver nao exportou; consultar centro.log e falha.json'}
        State 'ANALISANDO' $v
        $analise=Start-Process 'python' -ArgumentList @((Join-Path $PSScriptRoot 'analisar.py')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$root/analise.log" -RedirectStandardError "$root/analise_erro.log"
        if($analise.ExitCode -ne 0){throw 'Falha de analise; consultar analise_erro.log'}
        $r=Get-Content -Raw "$root/resultado.json"|ConvertFrom-Json
        if(!$r.fisica_ok){throw 'Falha fisica; investigar antes do proximo solve'}
    }
    State 'CONCLUIDO_AGUARDA_COMPARACAO' $v
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$study/pipeline.json" -Encoding utf8
    throw
}
