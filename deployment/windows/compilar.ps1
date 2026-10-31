$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
function ExigirExito { if ($LASTEXITCODE -ne 0) { throw "Comando terminó con código $LASTEXITCODE" } }
python -m pip install pip==25.2
ExigirExito
python -m pip install -r deployment/windows/requirements-build.txt
ExigirExito
python -m pip check
ExigirExito
python deployment/windows/pruebas.py
ExigirExito
python -m PyInstaller --noconfirm --clean deployment/windows/panel.spec
ExigirExito
$herramientas = New-Item -ItemType Directory -Force build/herramientas
$descargas = @(
    @{Nombre='python.exe'; Url='https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe'; Editor='Python Software Foundation'},
    @{Nombre='git.exe'; Url='https://github.com/git-for-windows/git/releases/download/v2.51.0.windows.1/Git-2.51.0-64-bit.exe'; Editor='Open Source Developer, Johannes Schindelin'}
)
$manifest = @()
foreach ($item in $descargas) {
    $ruta = Join-Path $herramientas.FullName $item.Nombre
    Invoke-WebRequest $item.Url -OutFile $ruta
    $firma = Get-AuthenticodeSignature $ruta
    if ($firma.Status -ne 'Valid' -or $firma.SignerCertificate.Subject -notlike "*$($item.Editor)*") {
        throw "Firma o editor no válido: $($item.Nombre)"
    }
    $manifest += @{archivo=$item.Nombre; url=$item.Url; sha256=(Get-FileHash $ruta -Algorithm SHA256).Hash; editor=$firma.SignerCertificate.Subject}
}
$compilador = "${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe"
if (!(Test-Path $compilador)) { throw 'Falta Inno Setup 6.' }
& $compilador deployment/windows/usuario.iss
ExigirExito
& $compilador deployment/windows/desarrollo.iss
ExigirExito
python -m pip freeze | Out-File dist/instaladores/dependencias.txt -Encoding utf8
$manifest | ConvertTo-Json | Out-File dist/instaladores/herramientas.json -Encoding utf8
@{commit=$env:GITHUB_SHA; python=(python --version); runner=$env:ImageVersion; inno=(Get-Item $compilador).VersionInfo.ProductVersion} | ConvertTo-Json | Out-File dist/instaladores/compilacion.json -Encoding utf8
Get-ChildItem dist/instaladores/*.exe | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash)  $(Split-Path $_.Path -Leaf)" } | Out-File dist/instaladores/SHA256SUMS.txt -Encoding ascii
