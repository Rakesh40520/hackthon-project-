$ErrorActionPreference = "Stop"
$path = "c:\Users\lordo\OneDrive\Desktop\project _uldathon\backend\app\models"
Get-ChildItem -Path $path -Filter *.py -Recurse | ForEach-Object {
    $f = $_.FullName
    $c = Get-Content $f -Raw
    $orig = $c
    $c = $c -replace 'JSONBCompat\(\)Compat\(\)', 'JSONBCompat()'
    $c = $c -replace 'GUID\(\)Compat\(\)', 'GUID()'
    if ($c -ne $orig) {
        Set-Content $f -Value $c -NoNewline
        Write-Host "Patched: $f"
    }
}
Write-Host "Done"
