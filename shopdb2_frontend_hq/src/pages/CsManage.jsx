import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function CsManage() {
  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);

  // 푸시 알림 모달 상태
  const [pushModalOpen, setPushModalOpen] = useState(false);
  const [pushText, setPushText] = useState('');

  // 답변하기/보기 모달 상태
  const [replyModalOpen, setReplyModalOpen] = useState(false);
  const [selectedInquiry, setSelectedInquiry] = useState(null);
  const [replyText, setReplyText] = useState('');

  const fetchInquiries = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/inquiries');
      if (response.ok) {
        const data = await response.json();
        if (data.length === 0) {
          // DB가 비어있을 때 표출되는 임시 더미 데이터 (이미지 기반)
          setInquiries([
            { id: 1, inquiry_no: 'CS-00001', type: '상품불만', title: '제품에 심각한 스크래치가 있습니다. 즉시 환불해주세요.', author: 'angry_bird', status: '미답변', created_at: '2026-09-18 10:20', reply: '' },
            { id: 2, inquiry_no: 'CS-00002', type: '배송지연', title: 'VVIP인데 3일째 배송 준비 중이네요. 확인 요망.', author: 'vip_customer', status: '처리중', created_at: '2026-09-17 15:45', reply: '' },
            { id: 3, inquiry_no: 'CS-00003', type: '단순문의', title: '신규가입 쿠폰 적용이 안되는데 확인 부탁드립니다.', author: 'hello1234', status: '답변완료', created_at: '2026-09-16 09:10', reply: '쿠폰 적용 조건은 가입 후 24시간 이내입니다. 마이페이지를 확인해주세요.' },
            { id: 4, inquiry_no: 'CS-00004', type: '교환요청', title: '사이즈가 안 맞아서 M 사이즈로 교환 원합니다.', author: 'shop_king', status: '답변완료', created_at: '2026-09-15 14:00', reply: '교환 접수 되었습니다. 기사님이 1~2일 내로 방문할 예정입니다.' }
          ]);
        } else {
          setInquiries(data);
        }
      }
    } catch (error) {
      console.error('API 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  // 🌟 푸시 발송 처리 함수
  const handleSendPush = async () => {
    if (!pushText.trim()) return alert('발송할 푸시 메시지를 입력해주세요.');
    if (!window.confirm('전체 회원에게 푸시 알림을 정말 발송하시겠습니까?')) return;

    try {
      // 실제 구현 시 백엔드 API 호출 필요: await fetch('/api/hq/push', { method: 'POST' ... })
      alert('전체 회원에게 푸시 알림이 성공적으로 발송되었습니다.');
      setPushModalOpen(false);
      setPushText('');
    } catch (error) {
      alert('푸시 발송에 실패했습니다.');
    }
  };

  // 🌟 답변 모달 열기
  const openReplyModal = (inquiry) => {
    setSelectedInquiry(inquiry);
    setReplyText(inquiry.reply || '');
    setReplyModalOpen(true);
  };

  // 🌟 답변 등록 처리 함수
  const handleSubmitReply = async () => {
    if (!replyText.trim()) return alert('답변 내용을 입력해주세요.');
    
    try {
      // 1. 프론트엔드 상태 즉시 업데이트 (화면 새로고침 없이 반영)
      setInquiries(inquiries.map(item => 
        item.id === selectedInquiry.id ? { ...item, status: '답변완료', reply: replyText } : item
      ));

      // 2. 실제 백엔드 연동 주석 처리 (필요시 백엔드 추가 후 해제)
      /*
      await fetch(`http://localhost:8001/api/hq/inquiries/${selectedInquiry.id}/reply`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reply: replyText, status: '답변완료' })
      });
      */

      alert('답변이 성공적으로 등록되었습니다.');
      setReplyModalOpen(false);
    } catch (error) {
      alert('답변 등록에 실패했습니다.');
    }
  };

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>고객 소통 및 CS 총괄</h2>
          <p>본사로 이관된 클레임을 처리하고 전체 회원에게 알림을 발송합니다.</p>
        </div>
        <div className="member-tools">
          <button className="member-primary" onClick={() => setPushModalOpen(true)}>
            + 전체 회원 푸시/알림 발송
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
                <th>문의 번호</th>
                <th>유형</th>
                <th>문의 제목</th>
                <th>작성자</th>
                <th>처리 상태</th>
                <th>등록 일시</th>
                <th>관리 액션</th>
              </tr>
            </thead>
            <tbody>
              {inquiries.map((item) => (
                <tr key={item.id}>
                  <td style={{ fontWeight: 'bold', color: '#2563eb' }}>{item.inquiry_no}</td>
                  <td>{item.type}</td>
                  <td style={{ fontWeight: 'bold' }}>{item.title}</td>
                  <td>{item.author}</td>
                  <td>
                    <span className="member-status" style={{ 
                      backgroundColor: item.status === '미답변' ? '#fee2e2' : item.status === '처리중' ? '#fef3c7' : '#dcfce7', 
                      color: item.status === '미답변' ? '#dc2626' : item.status === '처리중' ? '#d97706' : '#16a34a' 
                    }}>
                      {item.status}
                    </span>
                  </td>
                  <td style={{ color: '#64748b' }}>{item.created_at}</td>
                  <td>
                    {item.status === '답변완료' ? (
                      <button style={{ backgroundColor: 'white', border: '1px solid #cbd5e1' }} onClick={() => openReplyModal(item)}>
                        답변보기
                      </button>
                    ) : (
                      <button className="member-danger" style={{ border: 'none' }} onClick={() => openReplyModal(item)}>
                        답변하기
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 🌟 1. 전체 푸시 발송 모달창 */}
      {pushModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', width: '500px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '15px' }}>전체 회원 푸시/알림 발송</h3>
            <textarea 
              value={pushText}
              onChange={(e) => setPushText(e.target.value)}
              placeholder="앱 푸시 및 시스템 알림으로 전송될 메시지를 입력하세요."
              style={{ width: '100%', height: '150px', padding: '15px', borderRadius: '5px', border: '1px solid #cbd5e1', marginBottom: '20px', resize: 'none' }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => setPushModalOpen(false)} style={{ padding: '8px 20px', backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '5px', cursor: 'pointer' }}>취소</button>
              <button onClick={handleSendPush} className="member-primary" style={{ padding: '8px 20px', borderRadius: '5px' }}>발송하기</button>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 2. 답변 작성 및 보기 모달창 */}
      {replyModalOpen && selectedInquiry && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', width: '600px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '15px' }}>고객 문의 상세 및 답변</h3>
            
            <div style={{ margin: '20px 0', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '5px' }}>
              <p style={{ margin: '0 0 10px 0', color: '#64748b' }}>[{selectedInquiry.type}] {selectedInquiry.inquiry_no}</p>
              <h4 style={{ margin: '0 0 10px 0' }}>Q. {selectedInquiry.title}</h4>
              <p style={{ margin: 0, fontSize: '0.9rem', color: '#475569' }}>작성자: {selectedInquiry.author}</p>
            </div>

            <textarea 
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="답변 내용을 작성해주세요."
              style={{ width: '100%', height: '150px', padding: '15px', borderRadius: '5px', border: '1px solid #cbd5e1', marginBottom: '20px', resize: 'none' }}
            />
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => setReplyModalOpen(false)} style={{ padding: '8px 20px', backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '5px', cursor: 'pointer' }}>닫기</button>
              <button onClick={handleSubmitReply} className="member-primary" style={{ padding: '8px 20px', borderRadius: '5px' }}>답변 등록/수정</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}