@echo off
chcp 65001 > nul
echo ========================================
echo 데이터 수집 (수동 실행)
echo ========================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM Python 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Python 스크립트 실행 중...
echo.

python data_collector.py

echo.
echo ========================================
echo 완료
echo ========================================
pause

