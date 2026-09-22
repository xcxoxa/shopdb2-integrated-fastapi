# OFFIT SHOPDB2 통합 커머스 플랫폼

FastAPI·MySQL 백엔드와 통합 로그인, 본사 관리, 지사 관리, 고객 쇼핑몰을 함께 실행하는 통합 프로젝트입니다.

## 프로젝트 구성

| 폴더 | 역할 | 기본 주소 |
| --- | --- | --- |
| `shopdb2_backend_uv_fastapi1` | 통합 FastAPI·MySQL API | `http://127.0.0.1:8001` |
| `SHOPDB2_통합로그인_포털` | 통합 로그인 및 권한별 화면 이동 | `http://127.0.0.1:4173` |
| `shopdb2_frontend_hq` | 본사 관리 화면 | `http://127.0.0.1:3000` |
| `SHOPDB2_지사관리_프로젝트` | 지사 관리 화면 | `http://127.0.0.1:5174` |
| `shopdb2_customer_frontend` | 고객 쇼핑몰 | `http://127.0.0.1:5173` |

## 최초 설치

백엔드 폴더에서 환경변수와 Python 패키지를 준비합니다.

```powershell
cd shopdb2_backend_uv_fastapi1
Copy-Item .env.example .env
uv sync
```

생성된 `.env`에 실제 MySQL 접속 정보를 입력합니다. 각 프론트엔드 폴더에서는 최초 한 번 `npm install`을 실행합니다.

## 데모 계정 비밀번호 초기화

`shopdb2_backend_uv_fastapi1` 폴더를 VS Code로 열고 터미널에서 다음 명령을 실행합니다.

```powershell
uv run python reset_demo_passwords.py
```

이 명령을 실행하면 데모 계정 비밀번호가 모두 **`offit1234`**로 변경됩니다.

| 구분 | 로그인 ID | 변경되는 비밀번호 |
| --- | --- | --- |
| 본사 관리자 | `admin01` | `offit1234` |
| 지사 관리자 | `seller02` | `offit1234` |
| 구매 고객 | `buyer03` | `offit1234` |

## 사이트 실행 순서

아래 서버를 각각 별도의 VS Code 창과 터미널에서 실행합니다. 명령이 끝나지 않고 계속 실행되는 상태가 정상입니다.

### 1. 백엔드 실행

`shopdb2_backend_uv_fastapi1` 폴더를 VS Code로 열고 터미널에서 실행합니다.

```powershell
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 2. 통합 로그인 포털 실행

`SHOPDB2_통합로그인_포털` 폴더를 VS Code로 열고 터미널에서 실행합니다.

```powershell
npm run dev
```

터미널에 표시되는 로컬호스트 링크를 브라우저에서 엽니다. 기본 주소는 `http://127.0.0.1:4173`입니다.

### 3. 본사 관리 화면 실행

`shopdb2_frontend_hq` 폴더를 VS Code로 열고 터미널에서 다음 명령을 순서대로 실행합니다. `npm run`은 사용 가능한 명령을 확인합니다.

```powershell
npm run
npm start
```

### 4. 지사 관리 화면 실행

`SHOPDB2_지사관리_프로젝트` 폴더를 VS Code로 열고 터미널에서 실행합니다.

```powershell
npm run dev
```

### 5. 고객 쇼핑몰 실행

`shopdb2_customer_frontend` 폴더를 VS Code로 열고 터미널에서 실행합니다.

```powershell
npm run dev
```

위 다섯 서버가 모두 실행되면 사이트가 정상 작동합니다. 통합 로그인 포털의 로컬호스트 링크에서 로그인하면 계정 권한에 맞는 화면으로 이동합니다.

## 주요 접속 주소

- 통합 로그인: <http://127.0.0.1:4173>
- 고객 쇼핑몰: <http://127.0.0.1:5173>
- 지사 관리: <http://127.0.0.1:5174>
- 본사 관리: <http://127.0.0.1:3000>
- FastAPI 문서: <http://127.0.0.1:8001/docs>

## 보안 및 저장소 관리

- 실제 DB 비밀번호가 들어가는 `.env`는 GitHub에 올리지 않습니다. `.env.example`을 복사해서 사용합니다.
- `.venv`, `node_modules`, `dist`, 캐시 파일은 저장소에 포함하지 않습니다. `uv sync`와 `npm install`로 다시 생성할 수 있습니다.
- 비밀번호 초기화 스크립트는 데모·개발 환경에서만 사용하세요.
