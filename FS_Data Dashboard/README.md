# 📊 FS 프로젝트 지표 대시보드 시스템

게임 백업 DB에서 자동으로 지표 데이터를 수집하여 웹 DB에 저장하고, Streamlit 기반 웹 대시보드를 통해 시각화하는 시스템입니다.

## ✨ 주요 기능

- 🗄️ 게임 백업 DB 자동 연동 (SQL Server)
- 💾 웹 DB 기반 데이터 저장 및 관리
- ⏰ 매일 자동 데이터 수집 (Windows Task Scheduler)
- 📈 Streamlit 기반 인터랙티브 대시보드
- 🔒 로컬 환경에서 완전히 작동 (데이터 보안)
- 📊 다중 프로젝트/국가 지원 (FS1, FS2)

## 🛠️ 기술 스택

- **Python 3.9+**
- **SQL Server**: 게임 백업 DB 및 웹 DB
- **pyodbc**: SQL Server 연결
- **Pandas**: 데이터 처리
- **Streamlit**: 웹 대시보드 구축
- **python-dotenv**: 환경 변수 관리
- **Windows Task Scheduler**: 자동 데이터 수집

## 📦 설치 방법

### 1. 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# 게임 백업 DB 설정 (SQL Server)
BACKUP_DB_SERVER=10.20.252.178
BACKUP_DB_PORT=1433
BACKUP_DB_USER=your_username
BACKUP_DB_PASSWORD=your_password
BACKUP_DB_DRIVER=ODBC Driver 17 for SQL Server

# 프로젝트별 DB 이름 (실제 DB 이름으로 변경)
BACKUP_DB_FS1_KOR=FS1_KOR_DB
BACKUP_DB_FS1_CHN=FS1_CHN_DB
BACKUP_DB_FS1_SEA=FS1_SEA_DB
BACKUP_DB_FS2_KOR=FS2_KOR_DB
BACKUP_DB_FS2_CHN=FS2_CHN_DB
BACKUP_DB_FS2_GSP=FS2_GSP_DB

# 웹 DB 설정 (로컬 SQL Server)
WEB_DB_SERVER=localhost
WEB_DB_NAME=FS_Dashboard
WEB_DB_PORT=1433
WEB_DB_USE_WINDOWS_AUTH=True

# 데이터 수집 스케줄
COLLECTION_TIME=09:00
COLLECTION_TIMEZONE=Asia/Seoul
```

### 3. SQL Server 드라이버 설치

ODBC Driver 17 for SQL Server를 설치하세요:
- [다운로드 링크](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 4. 웹 DB 초기 설정

```bash
"6. 웹 DB 초기 설정.bat"
```

또는:
```bash
python setup_web_db.py
```

### 5. 기존 데이터 마이그레이션 (선택사항)

기존 엑셀 파일이 있다면 웹 DB로 마이그레이션하세요:

```bash
"7. 데이터 마이그레이션.bat"
```

⚠️ **주의**: `.env` 파일을 Git에 커밋하지 마세요!

## 📖 사용 방법

### 게임 백업 DB 쿼리 설정

⚠️ **중요**: 먼저 `backup_db_handler.py` 파일의 SQL 쿼리를 실제 DB 구조에 맞게 수정하세요.

자세한 내용은 `새로운 시스템 가이드.md`를 참조하세요.

### 데이터 수집 실행

게임 백업 DB에서 데이터를 조회하여 웹 DB에 저장합니다:

```bash
"8. 데이터 수집 (수동).bat"
```

또는:
```bash
python data_collector.py
```

**실행 과정:**
1. 게임 백업 DB에서 지표 데이터를 조회합니다
2. 웹 DB에 저장합니다 (INSERT or UPDATE)
3. 로그를 기록합니다

### 대시보드 실행

웹 DB의 데이터를 시각화하는 웹 대시보드를 실행합니다:

```bash
"3. 대시보드 실행.bat"
```

또는:
```bash
streamlit run dashboard.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 대시보드에 접근할 수 있습니다.

## 📊 대시보드 기능

### 주요 기능

- **🎯 프로젝트/국가 선택**: 여러 프로젝트와 국가를 쉽게 전환
- **📅 기준 날짜 선택**: 사업계획 달성 현황 기준 날짜 설정
- **📈 사업계획 달성 현황**: 월간 목표 대비 실적 및 달성률
- **💰 주요 KPI**: DAU, DRU, DBU, 매출, PU, 동접 등
- **📉 시계열 트렌드 차트**: 일별 지표 추이 시각화
- **📋 데이터 테이블**: 정렬 가능한 전체 데이터 테이블
- **📊 통계 정보**: 선택된 기간의 평균값 및 합계

### 지원하는 지표

- DAU (Daily Active Users)
- DRU (Daily Returning Users)
- DBU (Daily Buyers)
- 일일 매출
- PC방 매출
- PU (Paying Users)
- 평균 동접
- 최대 동접
- 플레이 판 수
- 플레이 타임

## 🗂️ 프로젝트 구조

```
FS_Data Dashboard/
├── backup_db_handler.py           # 게임 백업 DB 연결 및 조회
├── web_db_handler.py              # 웹 DB CRUD 작업
├── data_collector.py              # 데이터 수집 메인 로직
├── db_migration.py                # 엑셀 → DB 마이그레이션
├── scheduler_service.py           # 스케줄러 실행 스크립트
├── setup_web_db.py                # 웹 DB 초기 설정
├── config.py                      # 프로젝트/국가 설정
├── data_manager.py                # 데이터 로드 관리
├── dashboard.py                   # Streamlit 대시보드
├── requirements.txt               # 필수 라이브러리 목록
├── .env                           # 환경 변수 (직접 생성 필요)
├── 5. 데이터 수집 실행 (스케줄러).bat
├── 6. 웹 DB 초기 설정.bat
├── 7. 데이터 마이그레이션.bat
├── 8. 데이터 수집 (수동).bat
├── logs/                          # 수집 로그
├── data/                          # 레거시 엑셀 파일
├── 새로운 시스템 가이드.md        # 상세 설정 가이드
└── README.md                      # 프로젝트 문서
```

## ⚙️ 지표 커스터마이징

지표를 추가하거나 변경하려면:

1. **웹 DB 스키마 수정** (`setup_web_db.py`)
2. **게임 백업 DB 쿼리 수정** (`backup_db_handler.py`)
3. **config.py의 METRIC_NAMES에 지표 추가**
4. **대시보드 수정** (필요시)

## 🔧 문제 해결

### 웹 DB 연결 실패

- SQL Server가 실행 중인지 확인
- `.env` 파일의 `WEB_DB_SERVER`, `WEB_DB_NAME` 확인
- Windows 인증 사용 시 `WEB_DB_USE_WINDOWS_AUTH=True` 설정
- SQL Server 인증 사용 시 사용자명/비밀번호 확인

### 게임 백업 DB 연결 실패

- 네트워크 연결 확인 (10.20.252.178 접근 가능한지)
- 방화벽 설정 확인
- `.env` 파일의 프로젝트/국가별 DB 이름 확인
- 사용자 권한 확인

### ODBC 드라이버 오류

- ODBC Driver 17 for SQL Server 설치 확인
- 설치 후 시스템 재시작
- `.env`의 드라이버 이름 확인

### 데이터가 표시되지 않음

- 웹 DB에 데이터가 있는지 확인: `python web_db_handler.py`
- 데이터 수집이 정상적으로 실행되었는지 로그 확인 (`logs/`)
- 필요시 수동으로 데이터 수집 실행

자세한 문제 해결 방법은 `새로운 시스템 가이드.md`를 참조하세요.

## 🔄 자동 데이터 수집 설정

### Windows 작업 스케줄러 (매일 오전 9시)

**방법 1: GUI로 설정**

1. **작업 스케줄러** 실행 (`taskschd.msc`)
2. **작업 만들기** 클릭
3. **일반 탭**: 이름 `FS Dashboard 데이터 수집`, 사용자 로그온 여부에 관계없이 실행 체크
4. **트리거 탭**: 매일, 오전 9:00 설정
5. **동작 탭**: 
   - 프로그램: `프로젝트경로\5. 데이터 수집 실행 (스케줄러).bat`
   - 시작 위치: 프로젝트 폴더 경로
6. 저장 및 테스트

**방법 2: PowerShell로 설정**

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\bae22\FS_Data Dashboard\5. 데이터 수집 실행 (스케줄러).bat" -WorkingDirectory "C:\Users\bae22\FS_Data Dashboard"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "FS Dashboard 데이터 수집" -Action $action -Trigger $trigger -Settings $settings
```

### 로그 확인

수집 로그는 `logs/` 폴더에 저장됩니다.

자세한 설정 방법은 `새로운 시스템 가이드.md`를 참조하세요.

## 📝 라이선스

이 프로젝트는 개인 및 내부 업무용으로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 제안은 언제든지 환영합니다!

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.

## 📚 추가 문서

- **새로운 시스템 가이드.md**: 상세한 설정 및 사용 방법
- **시작 가이드.md**: 빠른 시작 가이드 (레거시)

---

**제작일**: 2025년 10월  
**버전**: 3.0 (DB 기반 시스템)  
**상태**: ✅ 프로덕션 준비 완료

### 변경 이력

- **v3.0 (2025-10)**: DB 기반 자동 수집 시스템으로 전환
- **v2.0**: 다중 프로젝트/국가 지원, 월간 목표 기능 추가
- **v1.0**: 이메일 기반 초기 시스템

