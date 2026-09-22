import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function PartnerManage() {
  const [sellers, setSellers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchSellers = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/sellers');
      if (response.ok) {
        const data = await response.json();
        setSellers(data);
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSellers();
  }, []);

  const getStatusText = (status) => {
    if (status === 'ACTIVE' || status === '정상') return '정상';
    if (status === 'PENDING' || status === '승인대기') return '승인대기';
    if (status === 'SUSPENDED' || status === '정지') return '정지';
    if (status === 'REJECTED' || status === '거절됨') return '거절됨';
    return status || '정상';
  };

  const handleRegisterSeller = async () => {
    const companyName = window.prompt('신규 입점사(상호명)를 입력하세요:');
    if (!companyName) return;
    const repName = window.prompt('대표자 이름을 입력하세요:');

    try {
      const response = await fetch('http://localhost:8001/api/hq/sellers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          representative_name: repName || '미등록',
          seller_status: 'PENDING'
        })
      });
      
      if (response.ok) {
        alert('입점사가 등록되었습니다. (승인 대기 상태)');
        fetchSellers(); 
      } else {
        alert('입점사 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('입점사 등록 에러:', error);
    }
  };

  const handleApprove = async (id, name) => {
    if (!window.confirm(`[${name}] 입점 신청을 승인하시겠습니까?`)) return;
    try {
      const response = await fetch(`http://localhost:8001/api/hq/sellers/${id}/approve`, { method: 'PATCH' });
      if (response.ok) {
        alert('승인 처리가 완료되었습니다.');
        fetchSellers();
      } else {
        alert('승인 처리에 실패했습니다.');
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  const handleReject = async (id, name) => {
    if (!window.confirm(`[${name}] 입점 신청을 거절하시겠습니까?`)) return;
    try {
      const response = await fetch(`http://localhost:8001/api/hq/sellers/${id}/reject`, { method: 'PATCH' });
      if (response.ok) {
        alert('입점 거절 처리가 완료되었습니다.');
        fetchSellers();
      } else {
        alert('거절 처리에 실패했습니다.');
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  // 🌟 새롭게 추가된 입점 거절 취소(승인대기 복구) 함수
  const handleRevertReject = async (id, name) => {
    if (!window.confirm(`[${name}] 입점 거절을 취소하고 다시 승인 대기 상태로 복구하시겠습니까?`)) return;
    try {
      const response = await fetch(`http://localhost:8001/api/hq/sellers/${id}/revert-reject`, { method: 'PATCH' });
      if (response.ok) {
        alert('승인 대기 상태로 복구되었습니다.');
        fetchSellers();
      } else {
        alert('복구 처리에 실패했습니다.');
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  const handleSuspend = async (id, name) => {
    if (!window.confirm(`[${name}] 파트너의 판매 자격을 정말로 정지하시겠습니까?`)) return;
    try {
      const response = await fetch(`http://localhost:8001/api/hq/sellers/${id}/suspend`, { method: 'PATCH' });
      if (response.ok) {
        alert('판매 자격이 정지되었습니다.');
        fetchSellers();
      } else {
        alert('정지 처리에 실패했습니다.');
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  const handleRestore = async (id, name) => {
    if (!window.confirm(`[${name}] 파트너의 권한 정지를 해제(복구)하시겠습니까?`)) return;
    try {
      const response = await fetch(`http://localhost:8001/api/hq/sellers/${id}/approve`, { method: 'PATCH' });
      if (response.ok) {
        alert('권한 정지가 해제되어 정상 상태로 복구되었습니다.');
        fetchSellers();
      } else {
        alert('정지 해제 처리에 실패했습니다.');
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>입점사 및 파트너 관리 (SCM)</h2>
          <p>플랫폼에 입점하는 판매자들의 심사, 승인 및 상태를 모니터링합니다.</p>
        </div>
        <div className="member-tools">
          <button className="member-primary" onClick={handleRegisterSeller} style={{ marginRight: '10px' }}>
            + 신규 등록
          </button>
          <button className="member-primary" onClick={fetchSellers}>+ 목록 갱신</button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>파트너 ID</th>
                <th>상호명 (법인명)</th>
                <th>대표자명</th>
                <th>계정 상태</th>
                <th>신청/등록일</th>
                <th>관리 액션</th>
              </tr>
            </thead>
            <tbody>
              {sellers.length > 0 ? (
                sellers.map((seller) => {
                  const displayStatus = getStatusText(seller.seller_status);
                  return (
                    <tr key={seller.seller_id}>
                      <td style={{ fontWeight: 'bold', color: '#2563eb' }}>PTN-{String(seller.seller_id).padStart(4, '0')}</td>
                      <td style={{ fontWeight: 'bold' }}>{seller.company_name}</td>
                      <td>{seller.representative_name || '미등록'}</td>
                      <td>
                        <span className="member-status" style={{ 
                          backgroundColor: displayStatus === '승인대기' ? '#fef3c7' : (displayStatus === '정지' || displayStatus === '거절됨') ? '#fee2e2' : '#dcfce7', 
                          color: displayStatus === '승인대기' ? '#d97706' : (displayStatus === '정지' || displayStatus === '거절됨') ? '#dc2626' : '#16a34a' 
                        }}>
                          {displayStatus}
                        </span>
                      </td>
                      <td style={{ color: '#64748b' }}>{seller.created_at ? String(seller.created_at).substring(0, 10) : '-'}</td>
                      <td>
                        <div className="member-actions">
                          {displayStatus === '승인대기' ? (
                            <>
                              <button className="member-primary" onClick={() => handleApprove(seller.seller_id, seller.company_name)}>입점승인</button>
                              <button 
                                className="member-danger" 
                                style={{ marginLeft: '5px', backgroundColor: 'white', color: '#dc2626', border: '1px solid #dc2626' }}
                                onClick={() => handleReject(seller.seller_id, seller.company_name)}
                              >
                                입점거절
                              </button>
                            </>
                          ) : displayStatus === '거절됨' ? (
                            // 🌟 글자 대신 거절취소(복구) 버튼을 보여줍니다.
                            <button 
                              style={{ backgroundColor: '#f1f5f9', color: '#64748b', border: '1px solid #cbd5e1' }}
                              onClick={() => handleRevertReject(seller.seller_id, seller.company_name)}
                            >
                              거절취소 (복구)
                            </button>
                          ) : displayStatus === '정지' ? (
                            <button 
                              style={{ backgroundColor: '#f1f5f9', color: '#64748b', border: '1px solid #cbd5e1' }}
                              onClick={() => handleRestore(seller.seller_id, seller.company_name)}
                            >
                              정지해제
                            </button>
                          ) : (
                            <>
                              <button onClick={() => alert('상세 정보 조회')}>상세보기</button>
                              <button className="member-danger" style={{ marginLeft: '5px' }} onClick={() => handleSuspend(seller.seller_id, seller.company_name)}>권한정지</button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b', backgroundColor: '#f8fafc' }}>
                    등록된 입점사(파트너) 데이터가 없습니다.
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