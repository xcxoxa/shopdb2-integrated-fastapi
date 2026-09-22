import { useEffect, useMemo, useState } from 'react'
import './MemberManagement.css'

const initialMembers = [
  { user_id: 1, login_id: 'minsu01', name: '김민수', email: 'minsu@example.com', role: '구매자', status: '활성', joined_at: '2026-09-12' },
  { user_id: 2, login_id: 'seller02', name: '이지은', email: 'jieun@example.com', role: '판매자', status: '활성', joined_at: '2026-09-13' },
  { user_id: 3, login_id: 'user03', name: '박서준', email: 'seojun@example.com', role: '구매자', status: '휴면', joined_at: '2026-09-14' },
]

const emptyForm = {
  login_id: '',
  name: '',
  email: '',
  role: '구매자',
  status: '활성',
}

function loadMembers() {
  try {
    return JSON.parse(localStorage.getItem('shopdb2-members')) || initialMembers
  } catch {
    return initialMembers
  }
}

export default function MemberManagement() {
  const [members, setMembers] = useState(loadMembers)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('전체')
  const [form, setForm] = useState(null)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    localStorage.setItem('shopdb2-members', JSON.stringify(members))
  }, [members])

  useEffect(() => {
    if (!notice) return undefined
    const timer = setTimeout(() => setNotice(''), 2000)
    return () => clearTimeout(timer)
  }, [notice])

  const filteredMembers = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    return members.filter((member) => {
      const matchesRole = roleFilter === '전체' || member.role === roleFilter
      const matchesKeyword = !keyword ||
        member.login_id.toLowerCase().includes(keyword) ||
        member.name.toLowerCase().includes(keyword) ||
        member.email.toLowerCase().includes(keyword)
      return matchesRole && matchesKeyword
    })
  }, [members, search, roleFilter])

  function saveMember(event) {
    event.preventDefault()
    if (form.user_id) {
      setMembers((current) => current.map((member) =>
        member.user_id === form.user_id ? form : member,
      ))
      setNotice('회원 정보를 수정했습니다.')
    } else {
      const nextId = Math.max(0, ...members.map((member) => member.user_id)) + 1
      const newMember = {
        ...form,
        user_id: nextId,
        joined_at: new Date().toISOString().slice(0, 10),
      }
      setMembers((current) => [newMember, ...current])
      setNotice('새 회원을 등록했습니다.')
    }
    setForm(null)
  }

  function deleteMember(member) {
    if (!window.confirm(`'${member.name}' 회원을 삭제할까요?`)) return
    setMembers((current) => current.filter((item) => item.user_id !== member.user_id))
    setNotice('회원을 삭제했습니다.')
  }

  return (
    <section className="member-panel">
      {notice && <div className="member-toast">{notice}</div>}

      <header className="member-header">
        <div>
          <h2>회원 목록</h2>
          <p>회원 검색, 등록, 수정, 삭제 및 권한·상태를 관리합니다.</p>
        </div>
        <div className="member-tools">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="아이디, 이름 또는 이메일 검색"
          />
          <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
            <option>전체</option>
            <option>구매자</option>
            <option>판매자</option>
            <option>관리자</option>
          </select>
          <button className="member-primary" onClick={() => setForm({ ...emptyForm })}>
            + 회원 등록
          </button>
        </div>
      </header>

      <div className="member-table-wrap">
        <table className="member-table">
          <thead>
            <tr>
              <th>회원번호</th><th>로그인 ID</th><th>이름</th><th>이메일</th>
              <th>권한</th><th>상태</th><th>가입일</th><th>관리</th>
            </tr>
          </thead>
          <tbody>
            {filteredMembers.map((member) => (
              <tr key={member.user_id}>
                <td>{member.user_id}</td>
                <td><b>{member.login_id}</b></td>
                <td>{member.name}</td>
                <td>{member.email}</td>
                <td><span className={`member-role ${member.role}`}>{member.role}</span></td>
                <td><span className={`member-status ${member.status}`}>{member.status}</span></td>
                <td>{member.joined_at}</td>
                <td className="member-actions">
                  <button onClick={() => setForm({ ...member })}>수정</button>
                  <button className="member-danger" onClick={() => deleteMember(member)}>삭제</button>
                </td>
              </tr>
            ))}
            {!filteredMembers.length && (
              <tr><td colSpan="8" className="member-empty">검색 결과가 없습니다.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {form && (
        <div className="member-modal-backdrop" onMouseDown={() => setForm(null)}>
          <form className="member-form" onSubmit={saveMember} onMouseDown={(event) => event.stopPropagation()}>
            <div className="member-form-head">
              <div>
                <h2>{form.user_id ? '회원 수정' : '회원 등록'}</h2>
                <p>회원 기본 정보와 권한을 입력하세요.</p>
              </div>
              <button type="button" onClick={() => setForm(null)}>×</button>
            </div>

            <label>로그인 ID
              <input required value={form.login_id} onChange={(event) => setForm({ ...form, login_id: event.target.value })} />
            </label>
            <label>이름
              <input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>
            <label>이메일
              <input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <div className="member-form-row">
              <label>권한
                <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
                  <option>구매자</option><option>판매자</option><option>관리자</option>
                </select>
              </label>
              <label>상태
                <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
                  <option>활성</option><option>휴면</option><option>정지</option>
                </select>
              </label>
            </div>
            <div className="member-form-actions">
              <button type="button" onClick={() => setForm(null)}>취소</button>
              <button className="member-primary" type="submit">저장</button>
            </div>
          </form>
        </div>
      )}
    </section>
  )
}
