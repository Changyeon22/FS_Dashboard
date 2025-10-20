@echo off
chcp 65001 > nul
echo ========================================
echo 환율 수집 (수동)
echo ========================================
echo.

cd /d "%~dp0"

echo 환율 테이블 생성 중...
python -c "from exchange_rate_handler import create_exchange_rate_table; create_exchange_rate_table()"

echo.
echo 최근 30일 환율 수집 중...
echo - 1순위: 한국수출입은행 API (최초 고시 매매기준율)
echo - 2순위: 한국은행 API  
echo - 3순위: 예시 데이터
echo.
python -c "from exchange_rate_handler import collect_exchange_rates_for_period; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); collect_exchange_rates_for_period(start_date, end_date)"

echo.
echo 환율 수집이 완료되었습니다.
echo.
echo API 키 설정 방법:
echo .env 파일에 다음을 추가하세요:
echo KEXIM_API_KEY=실제_한국수출입은행_API_키
echo BOK_API_KEY=실제_한국은행_API_키
pause
