# SHOPDB2 통합 FastAPI 프로젝트

조원 1·2·3이 구현한 쇼핑몰 데이터베이스 API를 하나의 FastAPI 프로젝트로 통합한 백엔드 프로젝트입니다.

## 주요 기술

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- MySQL
- Uvicorn
- uv

## 담당 기능

### 조원 1

- 회원 목록 및 상세 조회
- 회원 권한 조회
- 배송지 조회·등록·수정·삭제
- 주문 목록 및 상세 조회
- 구매자 문의 조회·등록
- 문의 첨부파일 조회·연결·삭제

### 조원 2

- 카테고리 목록 조회
- 판매자 프로필 목록 조회
- 상품 목록 조회
- 상품 상세 통합 조회
- 지점별 재고 조회

### 조원 3

- 본사 및 지사 목록 조회
- 결제 목록 및 상세 조회
- 환불 신청·목록·상세 조회
- 회사 정책 목록 및 상세 조회
- RAG 문서 및 검색 기록 조회

## 프로젝트 구조

```text
shopdb2_backend_uv_fastapi1
├─ app
│  ├─ models
│  │  ├─ __init__.py
│  │  ├─ buyer.py
│  │  └─ member2.py
│  ├─ routers
│  │  ├─ users.py
│  │  ├─ addresses.py
│  │  ├─ orders.py
│  │  ├─ inquiries.py
│  │  ├─ inquiry_files.py
│  │  ├─ categories.py
│  │  ├─ sellers.py
│  │  ├─ products.py
│  │  ├─ inventories.py
│  │  ├─ org_units.py
│  │  ├─ payments.py
│  │  ├─ refunds.py
│  │  ├─ policies.py
│  │  └─ rag.py
│  ├─ schemas
│  │  ├─ buyer.py
│  │  ├─ member2.py
│  │  └─ refunds.py
│  ├─ database.py
│  └─ main.py
├─ .env.example
├─ .gitignore
├─ pyproject.toml
├─ uv.lock
└─ README.md
```

## 실행 방법

### 1. 프로젝트 폴더 이동

```powershell
cd "C:\bangminjung\05_shopdb2_front_back\shopdb2_backend_uv_fastapi1"
```

### 2. 패키지 설치

```powershell
uv sync
```

### 3. 환경변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 MySQL 접속 정보를 입력합니다.

```powershell
Copy-Item ".env.example" ".env"
```

> `.env`에는 데이터베이스 비밀번호가 포함될 수 있으므로 GitHub에 올리지 않습니다.

### 4. FastAPI 서버 실행

```powershell
uv run uvicorn app.main:app --reload
```

## 접속 주소

### 로컬 접속

- 기본 주소: http://127.0.0.1:8000
- Swagger API 문서: http://127.0.0.1:8000/docs
- OpenAPI 문서: http://127.0.0.1:8000/openapi.json
- DB 연결 확인: http://127.0.0.1:8000/health/db

### 같은 네트워크의 다른 기기에서 접속

서버를 다음 명령으로 실행합니다.

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 주소: `http://<내-IP>:8000`
- Swagger 주소: `http://<내-IP>:8000/docs`
- DB 연결 확인: `http://<내-IP>:8000/health/db`

Windows에서 IP 주소 확인:

```powershell
ipconfig
```

## 주요 API

| 구분 | Method | API |
|---|---|---|
| 회원 | GET | `/api/users` |
| 회원 상세 | GET | `/api/users/{user_id}` |
| 회원 권한 | GET | `/api/users/{user_id}/roles` |
| 배송지 | GET, POST | `/api/users/{user_id}/addresses` |
| 배송지 | PUT, DELETE | `/api/addresses/{address_id}` |
| 주문 | GET | `/api/orders` |
| 주문 상세 | GET | `/api/orders/{order_id}` |
| 문의 | GET, POST | `/api/inquiries` |
| 문의 상세 | GET | `/api/inquiries/{inquiry_id}` |
| 문의 파일 | GET, POST | `/api/inquiries/{inquiry_id}/files` |
| 카테고리 | GET | `/api/categories` |
| 판매자 | GET | `/api/sellers` |
| 상품 | GET | `/api/products` |
| 상품 상세 | GET | `/api/products/{product_id}` |
| 재고 | GET | `/api/inventories` |
| 조직 | GET | `/api/admin/org-units` |
| 결제 | GET | `/api/admin/payments` |
| 환불 | GET | `/api/admin/refunds` |
| 환불 신청 | POST | `/api/refunds` |
| 정책 | GET | `/api/admin/policies` |
| RAG 문서 | GET | `/api/admin/rag/documents` |
| DB 상태 | GET | `/health/db` |

## 통합 검증 결과

- FastAPI 서버 정상 실행
- MySQL `shopdb2` 연결 확인
- Swagger API 문서 생성 확인
- 조원 1·2·3 라우터 통합 확인
- 주요 목록 및 상세 조회 API `200 OK` 확인
- 등록 API `201 Created` 확인

## 보안 주의사항

다음 파일 및 폴더는 GitHub에 업로드하지 않습니다.

```text
.env
.venv
__pycache__
*.pyc
```