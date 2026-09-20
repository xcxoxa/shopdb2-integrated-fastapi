# SHOPDB2 React 프론트엔드

FastAPI + MySQL 기반 SHOPDB2 프로젝트의 운영 대시보드입니다.

## 담당 기능

- 상품관리: 상품 검색, 등록, 수정, 삭제, 재고·판매 상태 관리
- 주문관리: 주문 검색, 상태 필터, 배송 상태 변경
- 대시보드: 상품·재고·주문 지표와 최근 주문
- FastAPI 및 MySQL 연결 상태 확인
- 백엔드 연결 전에도 브라우저 저장소로 기능 확인 가능

회원관리는 팀원이 만든 컴포넌트를 합칠 수 있도록 메뉴와 위치만 준비했습니다.

## 실행 방법

### 1. FastAPI 실행

백엔드 프로젝트 터미널에서 실행합니다.

```powershell
uv run uvicorn app.main:app --reload --port 8001
```

### 2. React 실행

이 프로젝트 폴더에서 실행합니다.

```powershell
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속합니다.

## API 주소 설정

`.env.example`을 복사하여 `.env`로 만들고 다음 값을 사용합니다.

```env
VITE_API_BASE=http://127.0.0.1:8001
```

## IP 접속 주소

같은 네트워크의 다른 기기에서 접속하려면 Vite를 다음과 같이 실행합니다.

```powershell
npm run dev -- --host 0.0.0.0
```

접속 주소:

```text
http://<내-IP>:5173
```

공개 GitHub 문서에는 실제 IP 대신 `<내-IP>`를 사용하세요.

## 참고

현재 API 요청 경로는 다음과 같습니다.

- `GET /health/db`
- `GET /api/products`
- `GET /api/orders`
- `GET /api/categories`

백엔드의 실제 경로가 다르면 `src/api.js`에서 수정하면 됩니다.
