$ErrorActionPreference = "Stop"
$path = "c:\Users\lordo\OneDrive\Desktop\project _uldathon\backend\app\models"
Get-ChildItem -Path $path -Filter *.py -Recurse | ForEach-Object {
    $f = $_.FullName
    $c = Get-Content $f -Raw
    $orig = $c
    # Replace import line that imports JSONB/UUID/INET from postgresql
    $c = $c -replace 'from sqlalchemy\.dialects\.postgresql import ([^\n]+?)UUID', 'from app.db_types import GUID, JSONBCompat'
    $c = $c -replace 'from sqlalchemy\.dialects\.postgresql import ([^\n]+?)JSONB', 'from app.db_types import GUID, JSONBCompat'
    $c = $c -replace 'from sqlalchemy\.dialects\.postgresql import ([^\n]+?)INET', 'from app.db_types import GUID, JSONBCompat'
    $c = $c -replace 'UUID\(as_uuid=True\)', 'GUID()'
    $c = $c -replace 'mapped_column\(JSONB', 'mapped_column(JSONBCompat()'
    $c = $c -replace 'INET', 'String(64)'
    if ($c -ne $orig) {
        Set-Content $f -Value $c -NoNewline
        Write-Host "Patched: $f"
    }
}
Write-Host "Done"
