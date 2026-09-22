import { useEffect, useState } from 'react'

// 개발 환경에서는 Vite 프록시를 사용해 CORS 없이 8001 백엔드로 전달합니다.
// 운영 배포에서만 VITE_API_BASE에 실제 API 주소를 지정합니다.
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
const APP_HOST = window.location.hostname || '127.0.0.1'
const destinations = {
  HEADQUARTER: import.meta.env.VITE_HQ_URL || `http://${APP_HOST}:3000`,
  BRANCH: import.meta.env.VITE_BRANCH_URL || `http://${APP_HOST}:5174`,
  CUSTOMER: import.meta.env.VITE_CUSTOMER_URL || `http://${APP_HOST}:5173`,
}

const roles = [
  { key: 'HEADQUARTER', title: '본사 관리자', description: '매출, 정책, 환불과 전체 운영 데이터를 관리합니다.', sample: 'admin01', tone: 'hq' },
  { key: 'BRANCH', title: '지사 관리자', description: '지사 상품, 재고, 주문과 고객 현황을 관리합니다.', sample: 'seller02', tone: 'branch' },
  { key: 'CUSTOMER', title: '구매 고객', description: 'OFFIT 상품을 검색하고 주문 내역을 확인합니다.', sample: 'buyer03', tone: 'customer' },
]

function encodeSession(session) {
  return encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(session)))))
}

export default function App() {
  const [loginId, setLoginId] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState('확인 중')

  useEffect(() => {
    fetch(`${API_BASE}/health/db`)
      .then((response) => setApiStatus(response.ok ? '정상 연결' : '연결 오류'))
      .catch(() => setApiStatus('연결 오류'))
  }, [])

  const selectRole = (role) => {
    setLoginId(role.sample)
    setError('')
    document.getElementById('password')?.focus()
  }

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login_id: loginId.trim(), password }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || '로그인에 실패했습니다.')

      const destination = destinations[data.user.destination]
      if (!destination) throw new Error('이 계정에 연결된 화면이 없습니다.')

      localStorage.setItem('offit_portal_session', JSON.stringify(data))
      window.location.assign(`${destination}?auth=${encodeSession(data)}`)
    } catch (loginError) {
      setError(loginError.message === 'Failed to fetch'
        ? 'FastAPI 서버에 연결할 수 없습니다. 8001번 포트를 확인해주세요.'
        : loginError.message)
    } finally {
      setLoading(false)
    }
  }

  return <main className="portal">
    <section className="intro-panel">
      <div className="brand"><span>O</span><div><strong>OFFIT</strong><small>EVERYDAY DIFFERENT</small></div></div>
      <p className="eyebrow">OFFIT UNIFIED COMMERCE</p>
      <h1>본사, 지사, 고객을<br />하나의 로그인으로 연결합니다.</h1>
      <p className="lead">계정의 권한과 소속 조직을 확인한 뒤 알맞은 운영 화면으로 자동 이동합니다.</p>

      <div className="role-grid">
        {roles.map((role) => <article className={`role-card ${role.tone}`} key={role.key}>
          <span className="role-label">{role.title}</span>
          <p>{role.description}</p>
          <button type="button" onClick={() => selectRole(role)}>{role.sample} 선택</button>
        </article>)}
      </div>

      <div className="security-info">
        <span className={apiStatus === '정상 연결' ? 'online' : ''} />
        <div><b>OFFIT API {apiStatus}</b><small>로그인 기록·세션·접속 권한을 데이터베이스에서 검증합니다.</small></div>
      </div>
    </section>

    <section className="login-panel">
      <div className="login-heading"><span>SECURE ACCESS</span><h2>통합 로그인</h2><p>본사·지사·고객 계정 모두 같은 로그인 창을 사용합니다.</p></div>
      <form onSubmit={submit}>
        <label>로그인 아이디
          <input value={loginId} onChange={(event) => setLoginId(event.target.value)} autoComplete="username" placeholder="아이디를 입력하세요" required />
        </label>
        <label>비밀번호
          <div className="password-field">
            <input id="password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" placeholder="비밀번호를 입력하세요" required />
            <button type="button" onClick={() => setShowPassword((current) => !current)}>{showPassword ? '숨김' : '보기'}</button>
          </div>
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="login-button" disabled={loading}>{loading ? '권한 확인 중…' : '로그인'}</button>
      </form>
      <div className="login-note"><b>권한별 자동 이동</b><p>본사 → 본사 관리 · 지사 → 지사 운영 · 고객 → OFFIT 쇼핑몰</p></div>
    </section>
  </main>
}
