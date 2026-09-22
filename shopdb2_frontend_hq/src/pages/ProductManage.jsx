import React, { useState, useEffect } from 'react';
import '../MemberManagement.css';

export default function ProductManage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/hq/products');
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('상품 API 호출 에러:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // DB의 영문 상태값을 한글로 변환
  const getStatusText = (status) => {
    if (status === 'SALE') return '판매중';
    if (status === 'READY') return '판매대기';
    if (status === 'SOLD_OUT') return '품절';
    if (status === 'STOPPED') return '판매중지';
    if (status === 'DELETED') return '삭제됨';
    return status;
  };

  return (
    <div className="member-panel">
      <div className="member-header">
        <div>
          <h2>상품 및 카테고리 운영 (CMS)</h2>
          <p>쇼핑몰 전체 상품 진열 상태를 통제합니다.</p>
        </div>
        <div className="member-tools">
          <button className="member-primary" onClick={fetchProducts}>+ 목록 갱신</button>
        </div>
      </div>
      
      <div className="member-table-wrap">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <table className="member-table">
            <thead>
              <tr>
                <th>상품 번호</th>
                <th>상품 코드</th>
                <th>상품명</th>
                <th>판매가</th>
                <th>전시 상태</th>
                <th>등록일</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              {products.length > 0 ? (
                products.map((prod) => (
                  <tr key={prod.product_id}>
                    <td style={{ fontWeight: 'bold', color: '#2563eb' }}>{prod.product_id}</td>
                    <td>{prod.product_code}</td>
                    <td style={{ fontWeight: 'bold' }}>{prod.product_name}</td>
                    <td>₩ {Number(prod.sale_price).toLocaleString()}</td>
                    <td>
                      <span className="member-status" style={{ 
                        backgroundColor: prod.product_status === 'SALE' ? '#dcfce7' : '#fee2e2', 
                        color: prod.product_status === 'SALE' ? '#16a34a' : '#dc2626' 
                      }}>
                        {getStatusText(prod.product_status)}
                      </span>
                    </td>
                    <td style={{ color: '#64748b' }}>{prod.created_at ? String(prod.created_at).substring(0, 10) : '-'}</td>
                    <td>
                      <button style={{ backgroundColor: 'white', border: '1px solid #cbd5e1' }}>노출 차단</button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>표시할 상품 데이터가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}