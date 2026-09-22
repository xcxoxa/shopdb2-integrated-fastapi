import { useEffect, useMemo, useState } from 'react'
import { API_BASE, api } from './api'
import MemberManagement from './MemberManagement'

const seedProducts = [
  { id: 1, name: '무선 노이즈 캔슬링 헤드폰', category: '디지털', price: 189000, stock: 34, status: '판매중' },
  { id: 2, name: '초경량 데일리 백팩', category: '패션', price: 59000, stock: 8, status: '재고부족' },
  { id: 3, name: '스테인리스 텀블러 600ml', category: '리빙', price: 32000, stock: 62, status: '판매중' },
  { id: 4, name: '저소음 무선 키보드', category: '디지털', price: 79000, stock: 21, status: '판매중' },
]

const seedOrders = [
  { id: 'ORD-260916-001', buyer: '김민수', date: '2026-09-16 09:21', total: 221000, status: '결제완료' },
  { id: 'ORD-260916-002', buyer: '이지은', date: '2026-09-16 10:04', total: 79000, status: '배송준비' },
  { id: 'ORD-260916-003', buyer: '박서준', date: '2026-09-16 10:38', total: 59000, status: '배송중' },
  { id: 'ORD-260916-004', buyer: '최유진', date: '2026-09-16 11:12', total: 32000, status: '배송완료' },
]

const emptyForm = { name: '', category: '', price: '', stock: '', status: '판매중' }
const statusLabels = {
  ORDERED: '주문접수',
  CREATED: '주문접수',
  PENDING: '주문대기',
  PAYMENT_PENDING: '결제대기',
  PAID: '결제완료',
  PREPARING: '배송준비',
  SHIPPING: '배송중',
  SHIPPED: '배송중',
  DELIVERING: '배송중',
  DELIVERED: '배송완료',
  COMPLETED: '배송완료',
  CANCELLED: '주문취소',
  CANCELED: '주문취소',
  REFUNDED: '환불완료',
}
const defaultOrderStatuses = ['PAID', 'COMPLETED']

const load = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) || fallback } catch { return fallback }
}
const list = (value) => Array.isArray(value) ? value : value?.items || value?.data || []
const money = (value) => `${Number(value || 0).toLocaleString('ko-KR')}원`
const statusLabel = (value) => statusLabels[value] ?? value
const normalizeProducts = (value) => list(value).map((p) => {
  const stock = Number(p.stock_quantity ?? p.stock ?? p.quantity ?? 0)
  return {
    id: p.product_id ?? p.id,
    name: p.product_name ?? p.name ?? '상품명 없음',
    category: p.category_name ?? p.category ?? '미분류',
    price: Number(p.sale_price ?? p.regular_price ?? p.price ?? 0),
    stock,
    status: stock === 0 ? '품절' : stock <= 10 ? '재고부족' : '판매중',
  }
})

export default function App() {
  const [page, setPage] = useState('대시보드')
  const [products, setProducts] = useState(() => load('shopdb2-products', seedProducts))
  const [orders, setOrders] = useState(() => load('shopdb2-orders', seedOrders))
  const [productQuery, setProductQuery] = useState('')
  const [orderQuery, setOrderQuery] = useState('')
  const [orderFilter, setOrderFilter] = useState('전체')
  const [orderStatuses, setOrderStatuses] = useState(defaultOrderStatuses)
  const [form, setForm] = useState(null)
  const [apiStatus, setApiStatus] = useState('연결 대기')
  const [notice, setNotice] = useState('')

  useEffect(() => localStorage.setItem('shopdb2-products', JSON.stringify(products)), [products])
  useEffect(() => localStorage.setItem('shopdb2-orders', JSON.stringify(orders)), [orders])
  useEffect(() => {
    Promise.allSettled([
      api.health(),
      api.products(),
      api.orders(),
      api.orderStatuses(),
    ]).then(([health, productResult, orderResult, statusResult]) => {
      if (health.status === 'fulfilled') setApiStatus('정상 연결')
      if (productResult.status === 'fulfilled' && list(productResult.value).length) {
        setProducts(normalizeProducts(productResult.value))
      }
      if (orderResult.status === 'fulfilled' && list(orderResult.value).length) {
        setOrders(list(orderResult.value).map((o) => ({
          dbId: o.order_id ?? o.id,
          id: String(o.order_no ?? o.order_id ?? o.id ?? ''),
          buyer: o.buyer_name ?? o.buyer ?? o.user_name ?? '구매자',
          date: o.ordered_at ?? o.created_at ?? '-',
          total: o.total_amount ?? o.total ?? 0,
          status: o.order_status ?? o.status ?? '결제완료',
        })))
      }
      if (statusResult.status === 'fulfilled') {
        const values = statusResult.value?.statuses
        if (Array.isArray(values) && values.length) setOrderStatuses(values)
      }
    })
  }, [])
  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(() => setNotice(''), 2000)
    return () => clearTimeout(timer)
  }, [notice])

  const shownProducts = useMemo(() => {
    const q = productQuery.toLowerCase()
    return products.filter((p) =>
      String(p.name ?? '').toLowerCase().includes(q) ||
      String(p.category ?? '').toLowerCase().includes(q)
    )
  }, [products, productQuery])
  const shownOrders = useMemo(() => {
    const q = orderQuery.toLowerCase()
    return orders.filter((o) =>
      (orderFilter === '전체' || o.status === orderFilter) &&
      (
        String(o.id ?? '').toLowerCase().includes(q) ||
        String(o.buyer ?? '').toLowerCase().includes(q)
      )
    )
  }, [orders, orderQuery, orderFilter])

  const totalStock = products.reduce((sum, p) => sum + Number(p.stock), 0)
  const totalSales = orders.filter((o) => o.status !== '주문취소').reduce((sum, o) => sum + Number(o.total), 0)

  const refreshProducts = async () => {
    const data = await api.products()
    setProducts(normalizeProducts(data))
  }

  const saveProduct = async (event) => {
    event.preventDefault()
    const value = { ...form, price: Number(form.price), stock: Number(form.stock) }
    value.status = value.stock === 0 ? '품절' : value.status
    try {
      const payload = {
        name: value.name,
        category: value.category,
        price: value.price,
        stock: value.stock,
      }
      if (form.id) {
        await api.updateProduct(form.id, payload)
        setNotice('상품을 수정했습니다.')
      } else {
        await api.createProduct(payload)
        setNotice('상품을 등록했습니다.')
      }
      await refreshProducts()
      setForm(null)
    } catch (error) {
      setNotice(`저장 실패: ${error.message}`)
    }
  }

  const removeProduct = async (product) => {
    if (!confirm(`'${product.name}' 상품을 삭제할까요?`)) return
    try {
      await api.deleteProduct(product.id)
      await refreshProducts()
      setNotice('상품을 삭제했습니다.')
    } catch (error) {
      setNotice(`삭제 실패: ${error.message}`)
    }
  }

  const updateOrder = async (order, status) => {
    try {
      await api.updateOrderStatus(order.dbId, status)
      setOrders(orders.map((o) => o.dbId === order.dbId ? { ...o, status } : o))
      setNotice(`${order.id} 상태를 변경했습니다.`)
    } catch (error) {
      setNotice(`상태 변경 실패: ${error.message}`)
    }
  }

  const ProductTable = ({ actions = false }) => <div className="table-wrap"><table>
    <thead><tr><th>상품</th><th>카테고리</th><th>가격</th><th>재고</th><th>상태</th>{actions && <th>관리</th>}</tr></thead>
    <tbody>{shownProducts.map((p) => <tr key={p.id}>
      <td><span className="product-icon">{p.name[0]}</span><b>{p.name}</b></td><td>{p.category}</td><td>{money(p.price)}</td><td>{p.stock}</td>
      <td><span className={`badge ${p.status}`}>{p.status}</span></td>
      {actions && <td className="row-actions"><button onClick={() => setForm({ ...p })}>수정</button><button className="danger" onClick={() => removeProduct(p)}>삭제</button></td>}
    </tr>)}{!shownProducts.length && <tr><td className="empty-row" colSpan={actions ? 6 : 5}>검색 결과가 없습니다.</td></tr>}</tbody>
  </table></div>

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">S2</span><div><strong>SHOPDB2</strong><small>Commerce Admin</small></div></div>
      <nav>{['대시보드', '상품관리', '주문관리', '회원관리'].map((name) => <button key={name} className={page === name ? 'active' : ''} onClick={() => setPage(name)}><span className="nav-dot" />{name}{name === '회원관리' && <em>팀원</em>}</button>)}</nav>
      <div className="sidebar-foot"><span className={`status-dot ${apiStatus === '정상 연결' ? 'online' : ''}`} /><div><b>FastAPI</b><small>{apiStatus}</small></div></div>
    </aside>
    <main>
      <header className="topbar"><div><p className="eyebrow">SHOPDB2 / {page}</p><h1>{page}</h1></div><div className="top-actions"><a href={`${API_BASE}/docs`} target="_blank">API 문서</a><div className="avatar">BM</div></div></header>
      {notice && <div className="toast">{notice}</div>}

      {page === '대시보드' && <>
        <section className="metrics"><article><span>등록 상품</span><strong>{products.length}</strong><small>전체 상품 수</small></article><article><span>총 재고</span><strong>{totalStock}</strong><small>판매 가능 수량</small></article><article><span>오늘 주문</span><strong>{orders.length}</strong><small>접수된 주문</small></article><article className="accent"><span>주문 금액</span><strong>{money(totalSales)}</strong><small>취소 주문 제외</small></article></section>
        <section className="content-grid"><article className="panel"><div className="panel-head"><div><h2>상품 현황</h2><p>민정 담당 기능</p></div></div><ProductTable /></article><aside className="panel"><div className="panel-head"><div><h2>최근 주문</h2><p>민정 담당 기능</p></div></div><div className="order-list">{orders.map((o) => <div className="order-card" key={o.id}><div><b>{o.id}</b><span>{o.buyer}</span></div><div><strong>{money(o.total)}</strong><small>{statusLabel(o.status)}</small></div></div>)}</div></aside></section>
      </>}

      {page === '상품관리' && <section className="panel management-panel"><div className="panel-head management-head"><div><h2>상품 목록</h2><p>상품 등록·수정·삭제와 재고를 관리합니다.</p></div><div className="management-tools"><input value={productQuery} onChange={(e) => setProductQuery(e.target.value)} placeholder="상품명 또는 카테고리 검색" /><button className="primary" onClick={() => setForm({ ...emptyForm })}>+ 상품 등록</button></div></div><ProductTable actions /></section>}

      {page === '주문관리' && <section className="panel management-panel"><div className="panel-head management-head"><div><h2>주문 목록</h2><p>주문을 조회하고 배송 상태를 변경합니다.</p></div><div className="management-tools"><input value={orderQuery} onChange={(e) => setOrderQuery(e.target.value)} placeholder="주문번호 또는 구매자 검색" /><select value={orderFilter} onChange={(e) => setOrderFilter(e.target.value)}><option>전체</option>{orderStatuses.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}</select></div></div><div className="table-wrap"><table><thead><tr><th>주문번호</th><th>구매자</th><th>주문일시</th><th>결제금액</th><th>상태 변경</th></tr></thead><tbody>{shownOrders.map((o) => <tr key={o.id}><td><b>{o.id}</b></td><td>{o.buyer}</td><td>{o.date}</td><td>{money(o.total)}</td><td><select className="status-select" value={o.status} onChange={(e) => updateOrder(o, e.target.value)}>{orderStatuses.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}</select></td></tr>)}{!shownOrders.length && <tr><td className="empty-row" colSpan="5">검색 결과가 없습니다.</td></tr>}</tbody></table></div></section>}

      {page === '회원관리' && <MemberManagement />}
    </main>

    {form && <div className="modal-backdrop" onMouseDown={() => setForm(null)}><form className="product-form" onSubmit={saveProduct} onMouseDown={(e) => e.stopPropagation()}><div className="form-head"><div><h2>{form.id ? '상품 수정' : '상품 등록'}</h2><p>상품 기본 정보와 판매 상태를 입력하세요.</p></div><button type="button" onClick={() => setForm(null)}>×</button></div><label>상품명<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label><label>카테고리<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></label><div className="form-row"><label>가격<input required min="0" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></label><label>재고<input required min="0" type="number" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} /></label></div><label>판매 상태<select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option>판매중</option><option>재고부족</option><option>품절</option></select></label><div className="form-actions"><button type="button" onClick={() => setForm(null)}>취소</button><button className="primary">저장</button></div></form></div>}
  </div>
}
