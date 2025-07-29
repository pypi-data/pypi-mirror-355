# Windows installation script
Write-Host "🚀 Installing Moodle Developer Documentation MCP Server..." -ForegroundColor Green

# Check if uv is installed
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
}

# Create installation directory
$InstallDir = "$env:USERPROFILE\.local\bin\moodle_dev_mcp"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Install via pip
Write-Host "📥 Installing moodle_dev_mcp..." -ForegroundColor Yellow
pip install moodle_dev_mcp

Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host "Configuration examples saved to $InstallDir\examples\"
