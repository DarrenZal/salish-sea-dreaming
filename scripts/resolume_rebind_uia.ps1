# resolume_rebind_uia.ps1 -- open Arena's Output -> Advanced Output via UIA.
#
# Triggers Arena to re-enumerate displays and re-bind outputs without
# stealing foreground focus. Works by driving the accessibility tree
# the same way a screen reader would. Safe to run while the gallery is
# live -- invocation goes through UI Automation, not simulated keystrokes.
#
# Probe confirmed (2026-04-16): Arena JUCE window exposes all 10 top-level
# menu items. Top-level items advertise InvokePattern (not ExpandCollapse).
# Submenu popups are hosted as separate windows parented to the desktop,
# so we search AutomationElement.RootElement after invoking the top-level
# item.
#
# Must run in the console user session (not SSH's service session) -- register
# as a scheduled task with /it /ru user. Trigger remotely with:
#   ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Rebind-UIA"
#
# Log: C:\Users\user\resolume_rebind_uia.log

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$log = "C:\Users\user\resolume_rebind_uia.log"

function Write-Log {
    param($msg)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "$stamp  $msg"
    Write-Output $line
    Add-Content -Path $log -Value $line
}

function Try-Invoke {
    param($element, $label)
    try {
        $iv = $element.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        if ($iv) {
            $iv.Invoke()
            Write-Log ($label + ": Invoke() ok")
            return $true
        }
    } catch {
        Write-Log ($label + ": Invoke failed - " + $_.Exception.Message)
    }
    return $false
}

Write-Log "--- start rebind ---"

$arena = Get-Process -Name Arena -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $arena) { Write-Log "ERROR: Arena not running"; exit 1 }
if ($arena.MainWindowHandle -eq 0) { Write-Log "ERROR: MainWindowHandle is 0"; exit 1 }
Write-Log ("Arena PID=" + [string]$arena.Id)

$root = [System.Windows.Automation.AutomationElement]::FromHandle($arena.MainWindowHandle)
if (-not $root) { Write-Log "ERROR: FromHandle returned null"; exit 1 }

$miType = [System.Windows.Automation.ControlType]::MenuItem
$typeCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, $miType)

# Find Output top-level menu item
$nameCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, "Output")
$andCond = New-Object System.Windows.Automation.AndCondition($typeCond, $nameCond)
$output = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $andCond)
if (-not $output) {
    Write-Log "ERROR: Output MenuItem not found in Arena window"
    # Dump what we see -- helps diagnose focus/visibility issues
    $allMi = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $typeCond)
    Write-Log ("MenuItems visible at start: " + $allMi.Count)
    $i = 0
    foreach ($m in $allMi) {
        if ($i -ge 20) { break }
        Write-Log ("  [" + $i + "] " + [string]$m.Current.Name)
        $i = $i + 1
    }
    exit 1
}
Write-Log "Output MenuItem located in Arena window"

if (-not (Try-Invoke -element $output -label "Output")) {
    Write-Log "ERROR: Could not invoke Output"
    exit 1
}

# Submenu lives in a popup window parented to desktop, not Arena.
# Give it a moment to materialise, then search the whole desktop tree.
Start-Sleep -Milliseconds 600

$desktop = [System.Windows.Automation.AutomationElement]::RootElement

# Arena names the menu item "Advanced..." (with ellipsis), not "Advanced Output"
$advNameCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, "Advanced...")
$advCond = New-Object System.Windows.Automation.AndCondition($typeCond, $advNameCond)

$advanced = $desktop.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $advCond)
if (-not $advanced) {
    Start-Sleep -Milliseconds 600
    $advanced = $desktop.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $advCond)
}

if (-not $advanced) {
    Write-Log "ERROR: Advanced Output not found in desktop tree after invoke"
    # Dump all MenuItems visible anywhere on desktop to help diagnose
    $allDeskMi = $desktop.FindAll([System.Windows.Automation.TreeScope]::Descendants, $typeCond)
    Write-Log ("Desktop MenuItems post-invoke: " + $allDeskMi.Count)
    $k = 0
    foreach ($m in $allDeskMi) {
        if ($k -ge 60) { break }
        Write-Log ("  [" + $k + "] " + [string]$m.Current.Name)
        $k = $k + 1
    }
    exit 1
}

Write-Log "Advanced... located in desktop tree"

if (Try-Invoke -element $advanced -label "Advanced...") {
    Write-Log "--- rebind complete ---"
    exit 0
} else {
    Write-Log "ERROR: Could not invoke Advanced Output"
    exit 1
}
