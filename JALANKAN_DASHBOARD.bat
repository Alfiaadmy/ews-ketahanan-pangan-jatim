@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   EWS KETAHANAN PANGAN JAWA TIMUR
echo ================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher "py" tidak ditemukan.
    echo Instal Python 3.11 atau 3.12 dan centang Add Python to PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Membuat virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Gagal membuat virtual environment.
        echo Pastikan Python 3.11 atau 3.12 sudah terinstal.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

echo.
echo Memasang / memperbarui library...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Instalasi library gagal. Periksa koneksi internet.
    pause
    exit /b 1
)

echo.
echo Menjalankan dashboard...
echo Browser akan dibuka pada http://localhost:8501
echo Tutup jendela ini untuk menghentikan dashboard.
echo.
python -m streamlit run app.py

pause
