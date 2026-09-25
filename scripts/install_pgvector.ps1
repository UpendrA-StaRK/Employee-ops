$ErrorActionPreference = "Stop"

# URL for PostgreSQL 16 Windows binary for pgvector
$url = "https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.6_16/vector.v0.8.6-pg16.zip"
$zipPath = "$env:TEMP\vector.zip"
$extractPath = "$env:TEMP\pgvector_extracted"
$pgRoot = "C:\Program Files\PostgreSQL\16"

Write-Host "Downloading pgvector..."
Invoke-WebRequest -Uri $url -OutFile $zipPath

Write-Host "Extracting..."
if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

Write-Host "Installing to PostgreSQL directory..."
# Copy the extension files
Copy-Item -Path "$extractPath\share\extension\*" -Destination "$pgRoot\share\extension\" -Force

# Copy the lib file
Copy-Item -Path "$extractPath\lib\*" -Destination "$pgRoot\lib\" -Force

Write-Host "pgvector installation complete! You can now run CREATE EXTENSION vector;"
