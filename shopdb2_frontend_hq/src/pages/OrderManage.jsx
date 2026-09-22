import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function OrderManage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // 🌟 주문 상세보기를 위한 상태 추가
  const [selectedOrder, setSelectedOrder] = useState(null);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/orders');
      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      }
    } catch (error) {
      console.error('주문 API 호출 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const getOrderStatus = (status) => {
    const statusMap = {
      'ORDERED': '주문접수', 'PAYMENT_PENDING': '결제대기', 'PAID': '결제완료',
      'PREPARING': '상품준비중', 'SHIPPING': '배송중', 'DELIVERED': '배송완료',
      'COMPLETED': '구매확정', 'CANCELLED': '주문취소', 'REFUNDED': '환불완료'
    };
    return statusMap[status] || status;
  };

  // 🌟 모달 열기/닫기 함수
  const handleViewDetails = (order) => setSelectedOrder(order);
  const closeModal = () => setSelectedOrder(null);

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>주문·결제·환불 총괄 (OMS)</h2>
          <p>전체 주문 결제 내역과 배송 상태를 확인합니다.</p>
        </div>
        <div className="member-tools">
          <button className="member-primary" onClick={fetchOrders}>+ 목록 갱신</button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>주문 번호</th>
                <th>주문자/수령인</th>
                <th>결제 금액</th>
                <th>진행 상태</th>
                <th>주문 일시</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              {orders.length > 0 ? (
                orders.map((order) => (
                  <tr key={order.order_id}>
                    <td style={{ fontWeight: 'bold', color: '#2563eb' }}>{order.order_no}</td>
                    <td style={{ fontWeight: 'bold' }}>{order.receiver_name}</td>
                    <td>₩ {Number(order.total_amount).toLocaleString()}</td>
                    <td>
                      <span className="member-status" style={{ 
                        backgroundColor: ['PAID', 'COMPLETED'].includes(order.order_status) ? '#dcfce7' : '#f1f5f9', 
                        color: ['PAID', 'COMPLETED'].includes(order.order_status) ? '#16a34a' : '#475569' 
                      }}>
                        {getOrderStatus(order.order_status)}
                      </span>
                    </td>
                    <td style={{ color: '#64748b' }}>{order.ordered_at ? String(order.ordered_at).substring(0, 16) : '-'}</td>
                    <td>
                      {/* 🌟 상세보기 버튼 이벤트 연결 */}
                      <button style={{ backgroundColor: 'white', border: '1px solid #cbd5e1' }} onClick={() => handleViewDetails(order)}>
                        상세보기
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>표시할 주문 데이터가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* 🌟 주문 상세 내역 모달창 UI */}
      {selectedOrder && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', width: '500px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '15px' }}>주문 상세 내역</h3>
            <div style={{ margin: '20px 0', lineHeight: '1.8' }}>
              <p><strong>주문 번호:</strong> {selectedOrder.order_no}</p>
              <p><strong>수령인(구매자):</strong> {selectedOrder.receiver_name}</p>
              <p><strong>결제 금액:</strong> ₩ {Number(selectedOrder.total_amount).toLocaleString()}</p>
              <p><strong>진행 상태:</strong> {getOrderStatus(selectedOrder.order_status)}</p>
              <p><strong>주문 일시:</strong> {selectedOrder.ordered_at}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <button onClick={closeModal} style={{ padding: '8px 20px', backgroundColor: '#334155', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}