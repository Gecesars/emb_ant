param([switch]$EstabilidadeFinal)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P1H/R06_sem_cabos'
$env:P1H_R06=$root
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
function Estado([string]$etapa,$detalhe) {
    @{processo=$PID;instante=(Get-Date -Format o);etapa=$etapa;detalhe=$detalhe} |
      ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$root/qualificacao.json" -Encoding utf8
}
function Python([string]$script,[string[]]$argumentos=@()) {
    & $py (Join-Path $PSScriptRoot $script) @argumentos >> "$root/qualificacao_estrita.log" 2>&1
    if ($LASTEXITCODE -ne 0) {throw "Falha em $script, codigo $LASTEXITCODE"}
}
function Nativo([string]$script,[string]$log) {
    $p=Start-Process -FilePath $aedt -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$root+'/'+$log+'"'),'-RunScriptAndExit',('"'+(Join-Path $PSScriptRoot $script)+'"'))
    Estado $script @{processo_aedt=$p.Id}
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) {throw "Falha AEDT em $script, codigo $($p.ExitCode)"}
}
try {
    $referencia=if($EstabilidadeFinal){'antena_estrita21'}else{'antena_refinada1'}
    $logEstado=if($EstabilidadeFinal){'estabilidade_final.log'}else{'convergencia_estrita.log'}
    if (Test-Path -LiteralPath "$root/antena/$logEstado") {throw 'Continuacao ja iniciada; nao duplicar.'}
    if (-not (Test-Path -LiteralPath "$root/$referencia/antena.s20p")) {throw 'Falta preservar a malha de referencia.'}
    $running=Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'ansysedt.exe' -and $_.CommandLine -match 'R06_sem_cabos|automacao[/\\]r06'}
    if ($running) {throw 'Existe AEDT do R06 ativo; confirmar antes de iniciar outro.'}
    if($EstabilidadeFinal) {
        Nativo 'validar_estabilidade.py' 'estabilidade_final_aedt.log'
        if ((Get-Content -LiteralPath "$root/antena/estabilidade_final.log" -Tail 1) -ne 'ESTABILIDADE_FINAL_CONCLUIDA') {throw 'Verificacao de estabilidade incompleta.'}
    } else {
        Nativo 'apertar_convergencia.py' 'convergencia_estrita_aedt.log'
        if ((Get-Content -LiteralPath "$root/antena/convergencia_estrita.log" -Tail 1) -ne 'CONTINUACAO_ESTRITA_CONCLUIDA') {throw 'Continuacao incompleta.'}
    }
    Python 'auditar_convergencia.py' @("$root/antena/PCB_R06.aedt")
    $audit=Get-Content -LiteralPath "$root/antena/auditoria_convergencia.json" -Raw | ConvertFrom-Json
    if (-not $audit.convergencia_aprovada -or $audit.criterio_s_usado -gt .004 -or $audit.criterio_campo_dB_usado -gt .02) {throw 'PCB nao convergiu nos criterios estritos.'}
    Python 'auditar_malha.py' @("$root/antena","$root/antena/malha.json")
    Nativo 'extrair_campos.py' 'campos_estrita_aedt.log'
    if ((Get-Content -LiteralPath "$root/antena/padroes.log" -Tail 1) -ne 'PADROES_R06_OK') {throw 'Campos incompletos.'}
    Python 'circuito.py' @($root)
    Python 'comparar_malhas.py' @($root,'--referencia',$referencia)
    Python 'circuito_aedt.py' @($root)
    Python 'graficos.py' @($root)
    Estado 'calculos_concluidos_aguardando_revisao_relatorio' ('Conferir aceite e estabilidade frente a '+$referencia+'; preservar comparacoes anteriores reprovadas.')
} catch {
    Estado 'requer_verificacao' $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath "$root/qualificacao_estrita.log"
    exit 1
}
