$ErrorActionPreference='Stop'
$records=@()
foreach($mode in @('original','corrigido','handle_preservado')) {
    foreach($expected in @(0,7)) {
        $parameters=@{
            FilePath='python';ArgumentList=@('-c',('"import time; time.sleep(0.3); raise SystemExit('+ $expected +')"'))
            WindowStyle='Hidden';PassThru=$true
            RedirectStandardOutput=(Join-Path $PSScriptRoot ('probe_'+$mode+'_'+$expected+'.out'))
            RedirectStandardError=(Join-Path $PSScriptRoot ('probe_'+$mode+'_'+$expected+'.err'))
        }
        if($mode -eq 'corrigido'){$parameters.Wait=$true}
        $p=Start-Process @parameters
        if($mode -eq 'handle_preservado'){$nativeHandle=$p.Handle}
        if($mode -ne 'corrigido'){$p.WaitForExit()}
        if($mode -ne 'original' -and ($null -eq $p.ExitCode -or $p.ExitCode -ne $expected)){throw "Expected $expected; observed $($p.ExitCode)"}
        $records += [pscustomobject]@{mode=$mode;expected=$expected;observed=$p.ExitCode}
    }
}
$records | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'verificacao_exitcode.json') -Encoding utf8
$records | ConvertTo-Json
