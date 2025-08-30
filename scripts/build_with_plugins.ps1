param(
  [string]$Profile = "WithPlugins",
  [string]$PluginsUpdateUrl = "",
  [string]$PluginsPipUrl = "https://pypi.org/simple/",
  [switch]$Debug
)

$ErrorActionPreference = 'Stop'

# cd to repo root (pyappify.yml lives here)
Set-Location -LiteralPath (Join-Path $PSScriptRoot '..')

Write-Host "[build] Using profile: $Profile"
if ($PluginsUpdateUrl) {
  Write-Host "[build] OK_PLUGINS_UPDATE_URL=$PluginsUpdateUrl"
  $env:OK_PLUGINS_UPDATE_URL = $PluginsUpdateUrl
  $env:OK_PLUGINS_PIP_URL = $PluginsPipUrl
}
if ($Debug) {
  $env:OK_DEBUG = '1'
}

Write-Host "[build] Ensure pyappify is installed"
python -m pip install --upgrade pip
python -m pip install pyappify==1.0.2

function Invoke-Pyappify {
  param([string[]]$Args)
  $exe = (Get-Command pyappify -ErrorAction SilentlyContinue).Path
  if (-not $exe) {
    $exe = Join-Path $env:APPDATA "Python\Python$((python -c 'import sys;print(str(sys.version_info.major)+str(sys.version_info.minor))'))\Scripts\pyappify.exe"
  }
  if (-not (Test-Path $exe)) {
    throw "pyappify CLI not found. Ensure pyappify installs console script."
  }
  Write-Host "[build] Run: $exe $($Args -join ' ')"
  & $exe @Args
}

try {
  Write-Host "[build] Build exe"
  Invoke-Pyappify @('build-exe-only','--profile', $Profile)
  Write-Host "[build] Build setup exe"
  Invoke-Pyappify @('build-setup-exe','--profile', $Profile)
} catch {
  Write-Warning "Local pyappify CLI does not support build commands or failed to run."
  Write-Warning "Please use GitHub Actions (build.yml) which is already configured for WithPlugins, or install a CLI version that supports these commands."
}

Write-Host "[build] Done. Artifacts in pyappify_dist/"
