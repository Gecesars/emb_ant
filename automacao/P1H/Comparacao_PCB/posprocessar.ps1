param([ValidateSet("Continua","Separadas")][string]$Caso,
      [string]$Aedt="C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe")
$ErrorActionPreference="Stop"
$base=$PSScriptRoot
$painel=Join-Path $base $Caso
$sistema=Join-Path $painel "Sistema"
foreach($model in @("$painel/solucao.log","$base/Divisor/solucao_placa.log","$base/Junta/solucao.log")){
    if(-not (Test-Path -LiteralPath $model)){throw "Sem solução em $model"}
}
if((Get-Content "$painel/solucao.log" -Tail 1) -ne "FEM_OK" -or (Get-Content "$base/Divisor/solucao_placa.log" -Tail 1) -ne "PCB_FEM_COMPLETO" -or (Get-Content "$base/Junta/solucao.log" -Tail 1) -ne "FIM"){throw "Solução incompleta"}
py -3.12 "$base/../conectar_rede.py" Dez --painel "$painel/painel.s20p" --divisor "$base/Divisor/distribuidor_EM.s22p" --junta "$base/Junta/junta.s2p" --saida "$sistema" --passo-mhz 10
if($LASTEXITCODE -ne 0){throw "Falha ao interligar as matrizes"}
$env:P1H_PCB=$Caso
$proc=Start-Process -FilePath $Aedt -ArgumentList @('-ng','-LogFile',('"'+$sistema+'/aedt_campos.log"'),'-RunScriptAndExit',('"'+$base+'/radiacao.py"')) -WindowStyle Hidden -PassThru
$proc.WaitForExit()
if((Get-Content "$sistema/campos.log" -Tail 1) -ne "CAMPOS_OK"){throw "Falha nos campos do painel"}
py -3.12 "$base/medir.py" $Caso
if($LASTEXITCODE -ne 0){throw "Falha ao verificar o sistema"}
