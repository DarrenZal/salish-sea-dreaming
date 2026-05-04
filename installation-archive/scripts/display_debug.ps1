Write-Output "=== GPU OUTPUTS ==="
Get-CimInstance Win32_VideoController | Select-Object Name, VideoProcessor, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate | Format-List

Write-Output "=== ALL DISPLAY DEVICES (including inactive) ==="
$sig = @'
[DllImport("user32.dll")]
public static extern bool EnumDisplayDevices(string lpDevice, uint iDevNum, ref DISPLAY_DEVICE lpDisplayDevice, uint dwFlags);

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
public struct DISPLAY_DEVICE {
    [MarshalAs(UnmanagedType.U4)] public int cb;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceString;
    [MarshalAs(UnmanagedType.U4)] public int StateFlags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceID;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceKey;
}
'@
Add-Type -MemberDefinition $sig -Name NativeMethods -Namespace Win32
$d = New-Object Win32.NativeMethods+DISPLAY_DEVICE
$d.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($d)
$i = 0
while ([Win32.NativeMethods]::EnumDisplayDevices($null, $i, [ref]$d, 0)) {
    $active = if ($d.StateFlags -band 1) {"ACTIVE"} else {"INACTIVE"}
    $primary = if ($d.StateFlags -band 4) {"PRIMARY"} else {""}
    Write-Output "  $($d.DeviceName) | $($d.DeviceString) | $active $primary | Flags=$($d.StateFlags)"
    
    # Get child device (monitor) for each adapter
    $m = New-Object Win32.NativeMethods+DISPLAY_DEVICE
    $m.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($m)
    $j = 0
    while ([Win32.NativeMethods]::EnumDisplayDevices($d.DeviceName, $j, [ref]$m, 1)) {
        $mactive = if ($m.StateFlags -band 1) {"ACTIVE"} else {"INACTIVE"}
        Write-Output "    -> $($m.DeviceName) | $($m.DeviceString) | $mactive | ID=$($m.DeviceID)"
        $j++
    }
    $i++
}
