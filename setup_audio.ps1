$ErrorActionPreference = 'Stop'

# Install NAudio via NuGet if not present
if (-not (Test-Path "C:\Program Files\NAudio\NAudio.dll")) {
    Write-Host "Installing NAudio..."
    
    # Create directory if it doesn't exist
    New-Item -ItemType Directory -Force -Path "C:\Program Files\NAudio"
    
    # Download nuget.exe if not present
    if (-not (Test-Path "C:\Program Files\NAudio\nuget.exe")) {
        Invoke-WebRequest -Uri "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe" -OutFile "C:\Program Files\NAudio\nuget.exe"
    }
    
    # Install NAudio
    Set-Location "C:\Program Files\NAudio"
    .\nuget.exe install NAudio -OutputDirectory .
    Copy-Item ".\NAudio*\lib\net45\NAudio.dll" .
    
    Write-Host "NAudio installed successfully!"
}

# Test audio capture
try {
    Add-Type -Path "C:\Program Files\NAudio\NAudio.dll"
    $waveIn = New-Object NAudio.Wave.WaveInEvent
    $waveIn.DeviceNumber = 0
    $waveIn.Dispose()
    Write-Host "Audio capture device available!"
} catch {
    Write-Host "Error testing audio capture: $_"
    exit 1
}