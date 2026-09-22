import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function SettlementManagement() {
  const [settlements, setSettlements] = useState([]);
  const [loading, setLoading] = useState(true);

  // 백엔드 API에서 진짜 DB 데이터를 가져오는 함수
  const fetchSettlements = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/settlements');
      if (response.ok) {
        const data = await response.json();
        setSettlements(data);
      }
    } catch (error) {
      console.error('정산 API 연결 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  // 화면이 처음 켜질 때 자동으로 데이터 불러오기
  useEffect(() => {
    fetchSettlements();
  }, []);

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>월별 정산 및 재무 관리</h2>
          <p>지사 및 입점사의 월별 매출을 확인하고 수익을 정산합니다.</p>
        </div>
        <div className="member-tools" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input type="month" defaultValue="2026-08" style={{ padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} />
          {/* 갱신 버튼을 누르면 API를 다시 호출하여 최신 DB 데이터를 가져옵니다 */}
          <button className="member-primary" onClick={fetchSettlements}>+ 정산 데이터 갱신</button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>대상 (지사/파트너)</th>
                <th>정산 기간</th>
                <th>총 매출액</th>
                <th>본사 수수료</th>
                <th>최종 지급액</th>
                <th>상태</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              {settlements.length > 0 ? settlements.map((item) => (
                <tr key={item.id}>
                  <td style={{ fontWeight: 'bold' }}>{item.target_name}</td>
                  <td style={{ color: '#64748b' }}>{item.period}</td>
                  <td style={{ fontWeight: 'bold' }}>₩ {Number(item.total_sales).toLocaleString()}</td>
                  <td style={{ color: '#dc2626' }}>- ₩ {Number(item.commission).toLocaleString()}</td>
                  <td style={{ fontWeight: 'bold', color: '#2563eb' }}>₩ {Number(item.final_amount).toLocaleString()}</td>
                  <td>
                    <span className="member-status" style={{ 
                      backgroundColor: item.status === '정산대기' ? '#fef3c7' : '#dcfce7', 
                      color: item.status === '정산대기' ? '#d97706' : '#16a34a' 
                    }}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <div className="member-actions">
                      <button style={{ backgroundColor: 'white', border: '1px solid #cbd5e1', color: '#334155' }}>명세서</button>
                      {item.status === '정산대기' && (
                        <button style={{ marginLeft: '5px', backgroundColor: 'white', border: '1px solid #cbd5e1', color: '#334155' }}>
                          지급완료 처리
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>표시할 정산 데이터가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}