import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function OrganizationManage() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOrgs = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/branches');
      if (response.ok) {
        const data = await response.json();
        setOrgs(data);
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const handleRegister = async () => {
    const branchName = window.prompt('신규 등록할 지사(조직) 이름을 입력하세요:');
    if (!branchName) return;
    const managerName = window.prompt('담당자 이름을 입력하세요:');

    try {
      const response = await fetch('http://localhost:8001/api/hq/branches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: branchName,
          manager: managerName || '미지정',
          role: '일반지사',
          status: '정상',
          lastLogin: ''
        })
      });
      
      if (response.ok) {
        alert('신규 조직이 성공적으로 등록되었습니다.');
        fetchOrgs(); 
      } else {
        alert('조직 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('조직 등록 에러:', error);
    }
  };

  // 🌟 실제 DB 데이터를 삭제하는 함수 추가
  const handleDelete = async (id, name) => {
    if (!window.confirm(`[${name}] 조직을 정말로 삭제하시겠습니까?`)) return;

    try {
      // 백엔드의 DELETE /api/hq/branches/{id} 라우터를 호출합니다.
      const response = await fetch(`http://localhost:8001/api/hq/branches/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert('성공적으로 삭제되었습니다.');
        fetchOrgs(); // 삭제 후 목록을 다시 불러와 화면을 갱신합니다.
      } else {
        alert('조직 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('삭제 에러:', error);
    }
  };

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>조직 및 권한 관리</h2>
          <p>본사 및 하위 지사 조직도와 관리자들의 시스템 접근 권한을 중앙 통제합니다.</p>
        </div>
        <div className="member-tools">
          <button className="member-primary" onClick={handleRegister}>
            + 신규 조직/지사 등록
          </button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>조직 코드</th>
                <th>조직명 (지사명)</th>
                <th>분류</th>
                <th>상태</th>
                <th>등록일자</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              {orgs.length > 0 ? (
                orgs.map((org) => (
                  <tr key={org.id}>
                    <td style={{ fontWeight: 'bold', color: '#2563eb' }}>ORG-{String(org.id).padStart(4, '0')}</td>
                    <td style={{ fontWeight: 'bold' }}>{org.name}</td>
                    <td>{org.role}</td>
                    <td>
                      <span className="member-status" style={{ 
                        backgroundColor: org.status === '정상' ? '#dcfce7' : '#f1f5f9', 
                        color: org.status === '정상' ? '#16a34a' : '#64748b' 
                      }}>
                        {org.status}
                      </span>
                    </td>
                    <td style={{ color: '#64748b' }}>{org.lastLogin ? String(org.lastLogin).substring(0, 10) : '-'}</td>
                    <td>
                      <div className="member-actions">
                        <button onClick={() => alert(`[${org.name}] 권한 설정 화면으로 이동 (개발 예정)`)}>권한설정</button>
                        {/* 🌟 껍데기 알림창 대신 실제 삭제 함수(handleDelete)를 연결합니다 */}
                        <button 
                          style={{ marginLeft: '5px', backgroundColor: 'transparent', color: '#dc3545', border: '1px solid #dc3545' }}
                          onClick={() => handleDelete(org.id, org.name)}
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b', backgroundColor: '#f8fafc' }}>
                    등록된 조직 및 지사 데이터가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}