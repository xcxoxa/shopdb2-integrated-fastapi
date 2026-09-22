import { useEffect, useMemo, useState } from 'react'
import { API_BASE, BRANCH_ORG_ID, api } from './api'
import { logout } from './auth'

const labels = { ORDERED:'주문접수', PAYMENT_PENDING:'결제대기', PAID:'결제완료', PREPARING:'배송준비', SHIPPING:'배송중', SHIPPED:'배송중', DELIVERING:'배송중', DELIVERED:'배송완료', COMPLETED:'배송완료', CANCELLED:'주문취소', CANCELED:'주문취소', REFUNDED:'환불완료' }
const defaultStatuses = ['PAID', 'PREPARING', 'SHIPPING', 'DELIVERED', 'CANCELLED']
const list = (v) => Array.isArray(v) ? v : v?.data || v?.items || []
const money = (v) => `${Number(v || 0).toLocaleString('ko-KR')}원`
const label = (v) => labels[v] || v
const maskEmail = (value='') => {
  const [name, domain] = value.split('@')
  if (!domain) return '-'
  return `${name.slice(0, 2)}${'*'.repeat(Math.max(2, name.length - 2))}@${domain}`
}
const maskPhone = (value='') => value ? value.replace(/(\d{3})-?\d{3,4}-?(\d{4})/, '$1-****-$2') : '-'

export default function App() {
  const [page, setPage] = useState('대시보드')
  const signedUser = JSON.parse(localStorage.getItem('offit_auth') || 'null')?.user
  const [branch, setBranch] = useState({ org_id: BRANCH_ORG_ID, org_code: 'OFFIT-BRANCH', org_name: signedUser?.org_name || 'OFFIT 지사', org_type: 'BRANCH' })
  const [metrics, setMetrics] = useState({})
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [customers, setCustomers] = useState([])
  const [statuses, setStatuses] = useState(defaultStatuses)
  const [productQuery, setProductQuery] = useState('')
  const [orderQuery, setOrderQuery] = useState('')
  const [orderFilter, setOrderFilter] = useState('전체')
  const [form, setForm] = useState(null)
  const [apiStatus, setApiStatus] = useState('연결 중')
  const [notice, setNotice] = useState('')

  const loadAll = async () => {
    try {
      const [b, d, ps, os, cs, ss] = await Promise.all([api.branch(), api.dashboard(), api.products(), api.orders(), api.customers(), api.orderStatuses()])
      setBranch(b); setMetrics(d)
      setProducts(list(ps).map((p) => {
        const stock = Number(p.stock_quantity || 0)
        return { id:p.product_id, name:p.product_name, category:p.category_name, price:Number(p.sale_price || p.regular_price || 0), stock, reserved:Number(p.reserved_quantity || 0), safety:Number(p.safety_stock || 0), status:stock === 0 ? '품절' : stock <= Number(p.safety_stock || 10) ? '재고부족' : '판매중' }
      }))
      setOrders(list(os).map((o) => ({ dbId:o.order_id, id:String(o.order_no || o.order_id), buyer:o.buyer_name || '구매자', date:o.ordered_at || '-', total:Number(o.total_amount || 0), status:o.order_status })))
      setCustomers(list(cs))
      if (ss?.statuses?.length) setStatuses(ss.statuses)
      setApiStatus('정상 연결')
    } catch (e) { setApiStatus('연결 오류'); setNotice(`조회 실패: ${e.message}`) }
  }

  useEffect(() => { loadAll() }, [])
  useEffect(() => { if (!notice) return; const id = setTimeout(() => setNotice(''), 3500); return () => clearTimeout(id) }, [notice])

  const shownProducts = useMemo(() => { const q=productQuery.toLowerCase(); return products.filter((p) => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q)) }, [products, productQuery])
  const shownOrders = useMemo(() => { const q=orderQuery.toLowerCase(); return orders.filter((o) => (orderFilter === '전체' || o.status === orderFilter) && (o.id.toLowerCase().includes(q) || o.buyer.toLowerCase().includes(q))) }, [orders, orderQuery, orderFilter])

  const saveProduct = async (e) => {
    e.preventDefault()
    const payload = { name:form.name, category:form.category, price:Number(form.price), stock:Number(form.stock) }
    try { await api.updateProduct(form.id, payload); setNotice('OFFIT 상품과 재고를 수정했습니다.'); setForm(null); await loadAll() }
    catch (err) { setNotice(`저장 실패: ${err.message}`) }
  }
  const changeOrder = async (o, status) => {
    try { await api.updateOrderStatus(o.dbId, status); setOrders((v) => v.map((x) => x.dbId === o.dbId ? {...x, status} : x)); setNotice(`${o.id} 상태를 변경했습니다.`) }
    catch (e) { setNotice(`상태 변경 실패: ${e.message}`) }
  }

  const ProductTable = ({ actions=false }) => <div className="table-wrap"><table><thead><tr><th>상품</th><th>카테고리</th><th>가격</th><th>가용 재고</th><th>예약</th><th>상태</th>{actions && <th>관리</th>}</tr></thead><tbody>
    {shownProducts.map((p) => <tr key={p.id}><td><span className="product-icon">{p.name[0]}</span><b>{p.name}</b></td><td>{p.category}</td><td>{money(p.price)}</td><td>{p.stock}</td><td>{p.reserved}</td><td><span className={`badge ${p.status}`}>{p.status}</span></td>{actions && <td className="row-actions"><button onClick={() => setForm({...p})}>상품·재고 수정</button></td>}</tr>)}
    {!shownProducts.length && <tr><td className="empty-row" colSpan={actions ? 7 : 6}>이 지사에 등록된 상품이 없습니다.</td></tr>}
  </tbody></table></div>

  const branchName = branch.org_name || branch.name || 'OFFIT 성수점'
  const pages = ['대시보드', '상품·재고', '주문·배송', '지사고객', '지사정보']
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">O</span><div><strong>OFFIT</strong><small>FASHION BRANCH</small></div></div><div className="branch-chip"><span>OFFIT STORE</span><b>{branchName}</b><small>EVERYDAY DIFFERENT</small></div><nav>{pages.map((name) => <button key={name} className={page === name ? 'active' : ''} onClick={() => setPage(name)}><span className="nav-dot" />{name}</button>)}</nav><div className="sidebar-foot"><span className={`status-dot ${apiStatus === '정상 연결' ? 'online' : ''}`} /><div><b>OFFIT API</b><small>{apiStatus}</small></div></div></aside>
    <main><header className="topbar"><div><p className="eyebrow">OFFIT / {branchName} / {page}</p><h1>{page}</h1></div><div className="top-actions"><span className="scope-badge">{signedUser?.user_name || '지사 관리자'} · {signedUser?.role_code || 'BRANCH'}</span><a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API 문서</a><button type="button" onClick={logout}>로그아웃</button><div className="avatar">{String(signedUser?.user_name || 'BM').slice(0, 2)}</div></div></header>{notice && <div className="toast">{notice}</div>}

      {page === '대시보드' && <><section className="metrics"><article><span>지사 상품</span><strong>{Number(metrics.product_count || products.length)}</strong><small>이 지사 취급 상품</small></article><article><span>지사 재고</span><strong>{Number(metrics.total_stock || 0)}</strong><small>옵션별 재고 합계</small></article><article><span>오늘 주문</span><strong>{Number(metrics.today_orders || 0)}</strong><small>오늘 접수된 주문</small></article><article className="accent"><span>지사 매출</span><strong>{money(metrics.total_sales)}</strong><small>취소 주문 제외</small></article></section><section className="content-grid"><article className="panel"><div className="panel-head"><div><h2>재고 현황</h2><p>{branchName} 재고만 표시합니다.</p></div></div><ProductTable /></article><aside className="panel"><div className="panel-head"><div><h2>최근 주문</h2><p>{branchName} 주문만 표시합니다.</p></div></div><div className="order-list">{orders.slice(0,8).map((o) => <div className="order-card" key={o.id}><div><b>{o.id}</b><span>{o.buyer}</span></div><div><strong>{money(o.total)}</strong><small>{label(o.status)}</small></div></div>)}{!orders.length && <p className="empty-note">지사 주문이 없습니다.</p>}</div></aside></section></>}

      {page === '상품·재고' && <section className="panel management-panel"><div className="panel-head management-head"><div><h2>OFFIT 상품·재고</h2><p>성수점에서 판매하는 패션 상품 6개만 관리합니다.</p></div><div className="management-tools"><input value={productQuery} onChange={(e) => setProductQuery(e.target.value)} placeholder="상품명 또는 카테고리 검색" /></div></div><ProductTable actions /></section>}

      {page === '주문·배송' && <section className="panel management-panel"><div className="panel-head management-head"><div><h2>지사 주문·배송</h2><p>이 지사로 접수된 주문만 조회하고 배송 상태를 변경합니다.</p></div><div className="management-tools"><input value={orderQuery} onChange={(e) => setOrderQuery(e.target.value)} placeholder="주문번호 또는 구매자 검색" /><select value={orderFilter} onChange={(e) => setOrderFilter(e.target.value)}><option>전체</option>{statuses.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select></div></div><div className="table-wrap"><table><thead><tr><th>주문번호</th><th>구매자</th><th>주문일시</th><th>결제금액</th><th>상태 변경</th></tr></thead><tbody>{shownOrders.map((o) => <tr key={o.id}><td><b>{o.id}</b></td><td>{o.buyer}</td><td>{String(o.date).replace('T',' ')}</td><td>{money(o.total)}</td><td><select className="status-select" value={o.status} onChange={(e) => changeOrder(o,e.target.value)}>{statuses.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select></td></tr>)}{!shownOrders.length && <tr><td className="empty-row" colSpan="5">이 지사의 주문이 없습니다.</td></tr>}</tbody></table></div></section>}

      {page === '지사고객' && <section className="customer-page"><div className="customer-hero"><div><span>OFFIT CUSTOMER</span><h2>성수점 구매 고객</h2><p>OFFIT 상품을 실제 주문한 고객의 이용 현황입니다. 개인정보는 마스킹하여 표시합니다.</p></div><strong>{customers.length}<small>구매 고객</small></strong></div><div className="customer-grid">{customers.map((c) => <article className="customer-card" key={c.user_id}><div className="customer-profile"><span>{String(c.user_name || 'O')[0]}</span><div><h3>{c.user_name}</h3><p>OFFIT MEMBER · {c.user_status}</p></div></div><dl><div><dt>주문 횟수</dt><dd>{Number(c.order_count || 0)}회</dd></div><div><dt>누적 구매</dt><dd>{money(c.purchase_amount)}</dd></div><div><dt>최근 구매</dt><dd>{String(c.last_order_at || '-').slice(0,10)}</dd></div></dl><div className="customer-contact"><span>{maskEmail(c.email)}</span><span>{maskPhone(c.phone)}</span></div></article>)}{!customers.length && <div className="customer-empty"><b>OFFIT 구매 고객이 없습니다.</b><p>성수점 상품 주문이 생성되면 이곳에 표시됩니다.</p></div>}</div></section>}

      {page === '지사정보' && <section className="panel branch-info"><div className="panel-head"><div><h2>{branchName}</h2><p>현재 로그인한 지사 관리자의 데이터 범위입니다.</p></div></div><dl><div><dt>조직 ID</dt><dd>{branch.org_id || BRANCH_ORG_ID}</dd></div><div><dt>조직 코드</dt><dd>{branch.org_code || '-'}</dd></div><div><dt>조직 유형</dt><dd>{branch.org_type || 'BRANCH'}</dd></div><div><dt>활성 상태</dt><dd>{branch.active_yn || branch.org_status || '-'}</dd></div></dl><div className="security-note"><b>접근 범위</b><p>FastAPI가 모든 상품·재고·주문 요청의 조직 ID를 검증합니다. 다른 지사의 데이터는 조회하거나 수정할 수 없습니다.</p></div></section>}
    </main>

    {form && <div className="modal-backdrop" onMouseDown={() => setForm(null)}><form className="product-form" onSubmit={saveProduct} onMouseDown={(e) => e.stopPropagation()}><div className="form-head"><div><h2>OFFIT 상품·재고 수정</h2><p>{branchName}의 판매 정보입니다.</p></div><button type="button" onClick={() => setForm(null)}>×</button></div><label>상품명<input readOnly value={form.name} /></label><label>카테고리<input readOnly value={form.category} /></label><div className="form-row"><label>가격<input required min="0" type="number" value={form.price} onChange={(e) => setForm({...form,price:e.target.value})} /></label><label>성수점 재고<input required min="0" type="number" value={form.stock} onChange={(e) => setForm({...form,stock:e.target.value})} /></label></div><div className="form-actions"><button type="button" onClick={() => setForm(null)}>취소</button><button className="primary">저장</button></div></form></div>}
  </div>
}
