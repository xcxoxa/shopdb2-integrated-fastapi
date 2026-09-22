# SHOPDB2 지사 관리 화면

기존 통합 관리자 화면을 지사 전용 운영 화면으로 분리한 React 프로젝트입니다. 기존 DB 테이블을 그대로 사용하며 `inventories.org_id`, `orders.org_id`, `users.org_id`를 기준으로 현재 지사의 데이터만 조회합니다.

## 포함 기능

- 지사 대시보드: 취급 상품, 재고, 오늘 주문, 지사 매출
- 상품·재고: 지사 취급 상품 조회, 등록, 수정, 판매 중지
- 주문·배송: 지사 주문 조회, 검색, 상태 변경
- 지사 고객: 지사 소속 고객 읽기 전용 조회
- 지사 정보: 현재 조직 정보와 데이터 접근 범위 표시
- FastAPI에서도 조직 ID를 조건으로 다시 검사

## 실행

### 1. FastAPI

```powershell
cd shopdb2_backend_uv_fastapi1
Copy-Item .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

### 2. React

```powershell
cd SHOPDB2_프론트엔드_최종통합
Copy-Item .env.example .env
npm install
npm run dev
```

접속 주소: `http://localhost:5174`

## 지사 선택

프론트엔드 `.env`의 조직 ID를 실제 지사 ID로 설정합니다.

```env
VITE_API_BASE=http://127.0.0.1:8001
VITE_BRANCH_ORG_ID=1
```

`org_units` 테이블에서 사용할 지사 ID를 확인할 수 있습니다.

```sql
SELECT org_id, org_code, org_name, org_type
FROM org_units
ORDER BY org_id;
```

## 주요 API

| 기능 | 메서드 | 경로 |
|---|---|---|
| 지사 정보 | GET | `/api/branch/me` |
| 대시보드 | GET | `/api/branch/dashboard` |
| 상품·재고 | GET, POST | `/api/branch/products` |
| 상품·재고 수정 | PUT, DELETE | `/api/branch/products/{product_id}` |
| 주문 | GET | `/api/branch/orders` |
| 주문 상태 | PATCH | `/api/branch/orders/{order_id}/status` |
| 지사 고객 | GET | `/api/branch/customers` |

모든 지사 API 요청은 `X-Org-Id` 헤더를 사용합니다. 실서비스 배포 전에는 이 값을 로그인 세션의 사용자·조직 정보에서 서버가 결정하도록 인증 미들웨어와 연결해야 합니다.

## 같은 네트워크에서 접속

```powershell
npm run dev -- --host 0.0.0.0
```

- 화면: `http://<내-IP>:5174`
- API 문서: `http://<내-IP>:8001/docs`
