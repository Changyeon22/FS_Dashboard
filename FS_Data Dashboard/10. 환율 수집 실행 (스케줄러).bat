@echo off
chcp 65001 > nul
echo ========================================
echo 환율 수집 스케줄러 실행
echo ========================================
echo.

cd /d "%~dp0"

REM Python 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 로그 파일명 생성 (날짜 포함)
set log_file=logs\exchange_rate_collection_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set log_file=%log_file: =0%

echo 로그 파일: %log_file%
echo.

REM Python 스크립트 실행 및 로그 기록
python exchange_rate_scheduler.py 2>&1 | tee %log_file%

echo.
echo ========================================
echo 실행 완료
echo ========================================
echo.

REM Windows Task Scheduler에서 실행 시 자동 종료
REM 수동 실행 시 확인용 대기
if "%1"=="" (
    pause
)
