$ErrorActionPreference = "Continue"
try {
    & "C:\Users\user\meta_watchdog.ps1"
} catch {
    "ERROR at line $($_.InvocationInfo.ScriptLineNumber): $_" | Out-File C:\Users\user\meta_debug.log -Encoding UTF8
}
