# OFFIT 통합 로그인 포털

본사·지사·고객 계정을 하나의 화면에서 인증하고, 데이터베이스 권한에 따라 각 서비스로 자동 이동시키는 React 화면입니다.

## 실행

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

접속 주소: `http://127.0.0.1:4173`

개발 서버의 `/api`, `/health` 요청은 Vite 프록시를 통해 자동으로
`http://127.0.0.1:8001`에 전달됩니다. 설정을 변경한 뒤에는 반드시
`npm run dev`를 종료하고 다시 실행해야 합니다.

## 권한별 이동

| 권한 | 이동 화면 | 기본 주소 |
|---|---|---|
| ADMIN, HQ, HEADQUARTER | 본사 관리 | `http://127.0.0.1:3000` |
| SELLER, BRANCH, BRANCH_MANAGER | 지사 관리 | `http://127.0.0.1:5174` |
| BUYER, CUSTOMER | 고객 쇼핑몰 | `http://127.0.0.1:5173` |

## IP 접속 주소

- 통합 로그인: `http://<내-IP>:4173`
- FastAPI: `http://<내-IP>:8001`
- 본사 관리: `http://<내-IP>:3000`
- 지사 관리: `http://<내-IP>:5174`
- 고객 쇼핑몰: `http://<내-IP>:5173`
