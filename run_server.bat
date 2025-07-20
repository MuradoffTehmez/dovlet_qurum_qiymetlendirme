@echo off
echo Q360 Performance Management System Server Starting...
echo =====================================================

REM Activate virtual environment
call venv\Scripts\activate

REM Check if activation worked
echo Virtual Environment: %VIRTUAL_ENV%

REM Install missing dependencies if needed
echo Installing/Checking dependencies...
python -m pip install -r requirements_minimal.txt

REM Run migrations if needed
echo Running migrations...
python manage.py migrate --run-syncdb

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Start development server
echo =====================================================
echo Starting Django Development Server...
echo Server will be available at: http://127.0.0.1:8001/
echo Press Ctrl+C to stop the server
echo =====================================================
python manage.py runserver 127.0.0.1:8001