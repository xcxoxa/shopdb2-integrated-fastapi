# SHOPDB2 통합 프로젝트

FastAPI·MySQL 백엔드와 React·Vite 화면 3개를 모은 프로젝트입니다. 제공된 ZIP의 소스만 포함하며, 가상환경·설치 패키지·실제 환경변수 파일은 제외했습니다.

## 폴더 구성

| 폴더 | 내용 |
| --- | --- |
| `backend/` | FastAPI API와 MySQL 연결 |
| `customer-frontend/` | 고객용 쇼핑몰 |
| `admin-frontend/` | 통합 운영 대시보드 |
| `branch-frontend/` | 지사 운영 화면 |

## 준비 사항

- Python 3.14 이상과 [uv](https://docs.astral.sh/uv/)
- Node.js와 npm (각 프론트엔드의 Vite 버전에 맞는 버전)
- `shopdb2` 데이터베이스가 준비된 MySQL 서버

데이터베이스 생성 SQL이나 데이터 덤프는 제공된 ZIP에 없습니다. 기존 SHOPDB2 스키마와 데이터를 별도로 준비해야 DB를 사용하는 기능이 동작합니다.

## 실행 방법 (PowerShell)

### 1. 백엔드

```powershell
cd backend
Copy-Item .env.example .env
```

`.env`의 `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`를 실제 MySQL 접속 정보로 바꿉니다.

```powershell
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

API 문서: <http://127.0.0.1:8001/docs>  
DB 연결 확인: <http://127.0.0.1:8001/health/db>

### 2. 프론트엔드

별도 터미널에서 사용할 화면의 폴더로 이동합니다. 예를 들어 고객용 화면은 다음과 같습니다.

```powershell
cd customer-frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

운영용은 `admin-frontend`, 지사용은 `branch-frontend`에서 같은 명령을 실행합니다. 각 화면의 `.env.example`에는 백엔드 주소 `VITE_API_BASE=http://127.0.0.1:8001`이 들어 있습니다. 지사용은 `VITE_BRANCH_ORG_ID`를 실제 지사 `org_id`로 설정합니다. 각 화면의 개발 서버 기본 주소는 <http://localhost:5173>이며, 여러 화면을 동시에 실행하면 Vite가 다른 포트를 사용할 수 있습니다.

## 주의 사항

- `.env`에는 비밀번호가 들어갈 수 있으므로 Git에 추가하지 마세요.
- 백엔드의 CORS 허용 주소는 `localhost`/`127.0.0.1`의 5173·5174 포트입니다. 다른 포트에서 API를 호출하면 `backend/app/main.py`의 허용 주소를 확인해야 합니다.
- 화면에는 예시 데이터와 브라우저 저장소를 사용하는 기능도 있습니다. 모든 화면이 실제 DB 데이터와 연결된 것으로 가정하지 마세요.

각 화면 및 백엔드의 세부 기능은 해당 폴더의 README를 참고하세요.

