# resolume_uia_probe.ps1 -- discover Arena's UI Automation tree.
#
# Resolume Arena is built on JUCE (C++). Many JUCE apps render their own
# menus and do not publish them to the Windows UI Automation tree, which
# would make accessibility-driven menu clicks impossible. This script
# checks whether Arena exposes its menu bar and "Output -> Advanced Output"
# item via UIA, so we know before writing the rebind automation.
#
# Run: powershell -ExecutionPolicy Bypass -File C:\Users\user\resolume_uia_probe.ps1
# Log: C:\Users\user\resolume_uia_probe.log

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$log = "C:\Users\user\resolume_uia_probe.log"

function Write-Log {
    param($msg)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "$stamp  $msg"
    Write-Output $line
    Add-Content -Path $log -Value $line
}

Write-Log "--- start probe ---"

$arena = Get-Process -Name Arena -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $arena) {
    Write-Log "ERROR: Arena process not found"
    exit 1
}
$pidStr = [string]$arena.Id
$hwndStr = [string]$arena.MainWindowHandle
$titleStr = [string]$arena.MainWindowTitle
Write-Log ("Arena PID=" + $pidStr + " HWND=" + $hwndStr + " Title=" + $titleStr)

if ($arena.MainWindowHandle -eq 0) {
    Write-Log "ERROR: MainWindowHandle is 0 (window not accessible)"
    exit 1
}

$root = [System.Windows.Automation.AutomationElement]::FromHandle($arena.MainWindowHandle)
if (-not $root) {
    Write-Log "ERROR: FromHandle returned null"
    exit 1
}

$rn = [string]$root.Current.Name
$rc = [string]$root.Current.ClassName
$rt = [string]$root.Current.ControlType.ProgrammaticName
Write-Log ("Root: Name=" + $rn + " Class=" + $rc + " Type=" + $rt)

# Supported patterns on the root (tells us if app is UIA-native)
$patterns = $root.GetSupportedPatterns()
$patternNames = ""
foreach ($p in $patterns) { $patternNames = $patternNames + $p.ProgrammaticName + "; " }
Write-Log ("Root patterns: " + $patternNames)

# --- direct children
Write-Log "--- direct children (up to 30) ---"
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$child = $walker.GetFirstChild($root)
$i = 0
while ($child -and $i -lt 30) {
    $cn = [string]$child.Current.Name
    $cc = [string]$child.Current.ClassName
    $ct = [string]$child.Current.ControlType.ProgrammaticName
    Write-Log ("  [" + $i + "] Name=" + $cn + " Class=" + $cc + " Type=" + $ct)
    $child = $walker.GetNextSibling($child)
    $i = $i + 1
}
Write-Log ("direct child count: " + $i)

# --- total descendant count (cap 500 to avoid runaway)
Write-Log "--- total descendants (all control types) ---"
$allDesc = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
Write-Log ("total descendants: " + $allDesc.Count)

# --- MenuItems anywhere in tree
Write-Log "--- MenuItem control types ---"
$menuCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::MenuItem)
$menuItems = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $menuCond)
Write-Log ("MenuItem count: " + $menuItems.Count)
$j = 0
foreach ($mi in $menuItems) {
    if ($j -ge 30) { break }
    $mn = [string]$mi.Current.Name
    Write-Log ("  MenuItem[" + $j + "] Name=" + $mn)
    $j = $j + 1
}

# --- Menus (control type Menu = menu bar containers)
Write-Log "--- Menu control types ---"
$menuBarCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Menu)
$menus = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $menuBarCond)
Write-Log ("Menu count: " + $menus.Count)

# --- Buttons (fallback - JUCE often renders menus as buttons)
Write-Log "--- Button control types (first 20) ---"
$btnCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
$btns = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
Write-Log ("Button count: " + $btns.Count)
$k = 0
foreach ($b in $btns) {
    if ($k -ge 20) { break }
    $bn = [string]$b.Current.Name
    Write-Log ("  Button[" + $k + "] Name=" + $bn)
    $k = $k + 1
}

# --- Search by name for "Output" anywhere in tree
Write-Log "--- Name=Output search ---"
$outCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, "Output")
$outEl = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $outCond)
if ($outEl) {
    $ocn = [string]$outEl.Current.ClassName
    $oct = [string]$outEl.Current.ControlType.ProgrammaticName
    Write-Log ("FOUND Name=Output Class=" + $ocn + " Type=" + $oct)
} else {
    Write-Log "NOT FOUND: Name=Output"
}

# --- Search for "Advanced Output"
Write-Log "--- Name=Advanced Output search ---"
$advCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, "Advanced Output")
$advEl = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $advCond)
if ($advEl) {
    $acn = [string]$advEl.Current.ClassName
    $act = [string]$advEl.Current.ControlType.ProgrammaticName
    Write-Log ("FOUND Name=Advanced Output Class=" + $acn + " Type=" + $act)
} else {
    Write-Log "NOT FOUND: Name=Advanced Output"
}

Write-Log "--- probe complete ---"
