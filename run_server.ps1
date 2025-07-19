# Q360 Performance Management System - PowerShell Launcher
Write-Host "Q360 Performance Management System Server Starting..." -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Yellow

# Change to project directory
Set-Location $PSScriptRoot

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Check if activation worked
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual Environment Active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "Warning: Virtual environment not detected" -ForegroundColor Red
}

# Install/Update dependencies
Write-Host "Checking dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

# Run Django checks
Write-Host "Running Django system checks..." -ForegroundColor Cyan
python manage.py check

# Collect static files (non-interactive)
Write-Host "Collecting static files..." -ForegroundColor Cyan
python manage.py collectstatic --noinput --clear

# Display system info
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "Django Server Information:" -ForegroundColor Green
Write-Host "  Server URL: http://127.0.0.1:8001/" -ForegroundColor White
Write-Host "  Admin URL:  http://127.0.0.1:8001/admin/" -ForegroundColor White
Write-Host "  Debug Mode: ON (Development)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Available Modules:" -ForegroundColor Green
Write-Host "  📊 Interactive Dashboard: /interactive-dashboard/" -ForegroundColor White
Write-Host "  📅 Calendar Module:       /teqvim/" -ForegroundColor White
Write-Host "  🔔 Notifications:         /bildirisler/" -ForegroundColor White
Write-Host "  📈 Reports Center:        /hesabatlar/" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "=====================================================" -ForegroundColor Yellow

# Start Django development server
python manage.py runserver 127.0.0.1:8001