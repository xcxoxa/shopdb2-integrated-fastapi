import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function SystemOps() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/logs');
      if (response.ok) {
        const data = await response.json();
        
        if (data.length === 0) {
          setLogs([
            { id: 101, level: 'CRITICAL', source: 'Database', message: 'DB Connection Timeout (연결 시간 초과)', status: '미조치', created_at: '2026-09-18 14:10:00' },
            { id: 102, level: 'SECURITY', source: 'Auth', message: '비정상적인 로그인 시도 감지 (동일 IP 50회 실패)', status: '차단완료', created_at: '2026-09-18 13:05:00' },
            { id: 103, level: 'AI_AUDIT', source: 'RAG_Chatbot', message: 'AI 챗봇 할루시네이션(환각) 의심 답변 발생', status: '조치완료', created_at: '2026-09-18 11:45:00' },
            { id: 104, level: 'WARNING', source: 'Payment', message: 'PG사 결제 웹훅(Webhook) 응답 지연', status: '조치완료', created_at: '2026-09-17 09:20:00' }
          ]);
        } else {
          setLogs(data);
        }
      }
    } catch (error) {
      console.error('API 호출 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const getLevelStyle = (level) => {
    switch(level) {
      case 'CRITICAL': return { bg: '#fee2e2', text: '#dc2626' }; 
      case 'SECURITY': return { bg: '#e0e7ff', text: '#4338ca' }; 
      case 'AI_AUDIT': return { bg: '#fae8ff', text: '#a21caf' }; 
      case 'WARNING': return { bg: '#fef3c7', text: '#d97706' };  
      default: return { bg: '#f1f5f9', text: '#64748b' };
    }
  };

  const openDetailModal = (log) => {
    setSelectedLog(log);
    setModalOpen(true);
  };

  const handleResolve = async (id, logId) => {
    if (!window.confirm(`[${logId}] 해당 이슈를 '조치완료' 상태로 변경하시겠습니까?`)) return;
    try {
      setLogs(logs.map(log => log.id === id ? { ...log, status: '조치완료' } : log));
      await fetch(`http://localhost:8001/api/hq/logs/${id}/resolve`, { method: 'PATCH' });
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  const handleUnblock = async (id, logId) => {
    if (!window.confirm(`[${logId}] 해당 IP/유저의 시스템 차단을 해제하시겠습니까?`)) return;
    try {
      setLogs(logs.map(log => log.id === id ? { ...log, status: '차단해제' } : log));
      await fetch(`http://localhost:8001/api/hq/logs/${id}/unblock`, { method: 'PATCH' });
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  const handleRevertResolve = async (id, logId) => {
    if (!window.confirm(`[${logId}] 조치완료 상태를 취소하고 다시 '미조치' 상태로 돌리시겠습니까?`)) return;
    try {
      setLogs(logs.map(log => log.id === id ? { ...log, status: '미조치' } : log));
      await fetch(`http://localhost:8001/api/hq/logs/${id}/revert-resolve`, { method: 'PATCH' });
    } catch (error) {
      console.error('API 호출 에러:', error);
    }
  };

  // 🌟 새롭게 추가된 CSV 다운로드 함수
  const handleDownloadCSV = () => {
    if (logs.length === 0) return alert('다운로드할 데이터가 없습니다.');

    // 1. 헤더 설정
    const headers = ['로그 ID', '분류 수준', '발생 출처', '조치 상태', '발생 일시', '메시지'];

    // 2. 데이터 변환 (메시지 내용에 쉼표가 있을 수 있으므로 쌍따옴표로 감쌈)
    const csvRows = logs.map(log => {
      const logCode = `LOG-${String(log.id).padStart(5, '0')}`;
      const level = log.level || 'ERROR';
      const source = log.source || log.logger_name || 'System';
      const status = log.status || (level === 'CRITICAL' ? '미조치' : '조치완료');
      const createdAt = log.created_at ? String(log.created_at).substring(0, 16) : '-';
      const message = (log.message || log.error_message || '').replace(/"/g, '""'); // 쌍따옴표 이스케이프

      return `${logCode},${level},${source},${status},${createdAt},"${message}"`;
    });

    // 3. 파일 병합 및 한글 인코딩 처리(BOM)
    const csvContent = [headers.join(','), ...csvRows].join('\n');
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    // 4. 가상의 링크를 만들어 클릭(다운로드) 유도 후 삭제
    const link = document.createElement('a');
    link.href = url;
    // 다운로드될 파일명 (예: system_logs_2026-09-21.csv)
    link.setAttribute('download', `system_logs_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>시스템 운영 및 AI 감사</h2>
          <p>관리자 접속 로그와 시스템 장애 내역, AI 챗봇의 트랜잭션 기록을 모니터링합니다.</p>
        </div>
        <div className="member-tools">
          {/* 🌟 엑셀 다운로드 함수 연결 */}
          <button className="member-primary" onClick={handleDownloadCSV}>로그 엑셀(CSV) 추출</button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>로그 ID</th>
                <th>분류 수준</th>
                <th>발생 출처</th>
                <th style={{ width: '35%' }}>메시지 / 상세 내용</th>
                <th>조치 상태</th>
                <th>발생 일시</th>
                <th>관리 액션</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const levelStyle = getLevelStyle(log.level || 'ERROR');
                const logCode = `LOG-${String(log.id).padStart(5, '0')}`;
                
                const isUnresolved = log.status === '미조치' || log.status === '확인필요';
                const isBlocked = log.status === '차단완료';
                const isResolved = log.status === '조치완료';

                return (
                  <tr key={log.id}>
                    <td style={{ fontWeight: 'bold', color: '#64748b' }}>{logCode}</td>
                    <td>
                      <span className="member-status" style={{ backgroundColor: levelStyle.bg, color: levelStyle.text, fontWeight: 'bold', fontSize: '0.8rem' }}>
                        {log.level || 'ERROR'}
                      </span>
                    </td>
                    <td style={{ fontWeight: 'bold' }}>{log.source || log.logger_name || 'System'}</td>
                    <td style={{ textAlign: 'left', color: '#334155' }}>{log.message || log.error_message}</td>
                    <td>
                      <span style={{ 
                        color: isUnresolved ? '#dc2626' : (log.status === '차단해제' ? '#64748b' : '#16a34a'),
                        fontWeight: 'bold',
                        fontSize: '0.9rem'
                      }}>
                        {log.status || (log.level === 'CRITICAL' ? '미조치' : '조치완료')}
                      </span>
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.85rem' }}>{log.created_at ? String(log.created_at).substring(0, 16) : '-'}</td>
                    <td>
                      <div className="member-actions">
                        <button onClick={() => openDetailModal({ ...log, logCode })}>상세조회</button>
                        
                        {isUnresolved && (
                          <button className="member-danger" style={{ marginLeft: '5px', backgroundColor: 'white', color: '#dc2626', border: '1px solid #dc2626' }} onClick={() => handleResolve(log.id, logCode)}>
                            이슈종결
                          </button>
                        )}

                        {isBlocked && (
                          <button style={{ marginLeft: '5px', backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' }} onClick={() => handleUnblock(log.id, logCode)}>
                            차단해제
                          </button>
                        )}

                        {isResolved && (
                          <button style={{ marginLeft: '5px', backgroundColor: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0' }} onClick={() => handleRevertResolve(log.id, logCode)}>
                            조치취소
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {modalOpen && selectedLog && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', width: '600px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '15px' }}>시스템 로그 상세 정보</h3>
            <div style={{ margin: '20px 0', lineHeight: '1.8' }}>
              <p><strong>로그 ID:</strong> {selectedLog.logCode}</p>
              <p><strong>분류 수준:</strong> {selectedLog.level || 'ERROR'}</p>
              <p><strong>발생 출처:</strong> {selectedLog.source || selectedLog.logger_name || 'System'}</p>
              <p><strong>상태:</strong> {selectedLog.status}</p>
              <p><strong>발생 일시:</strong> {selectedLog.created_at ? String(selectedLog.created_at).substring(0, 16) : '-'}</p>
              <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '5px', border: '1px solid #e2e8f0', overflowX: 'auto' }}>
                <strong>상세 메시지 (에러 스택):</strong><br/>
                <pre style={{ margin: '10px 0 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.9rem', color: '#334155' }}>
                  {selectedLog.message || selectedLog.error_message}
                </pre>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <button onClick={() => setModalOpen(false)} style={{ padding: '8px 20px', backgroundColor: '#334155', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}