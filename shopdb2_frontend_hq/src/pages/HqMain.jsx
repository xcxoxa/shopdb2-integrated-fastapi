import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import SettlementManagement from './SettlementManagement';
import OrganizationManage from './OrganizationManage';
import PartnerManage from './PartnerManage';
import OrderManage from './OrderManage';
import ProductManage from './ProductManage';
import CsManage from './CsManage';
import SystemOps from './SystemOps';

export default function HqMain() {
  const [activeMenu, setActiveMenu] = useState('통합 대시보드 (BI)');
  
  // 🌟 대시보드 실데이터 상태 관리 (차트를 위한 chart_data 배열 추가)
  const [dashboardData, setDashboardData] = useState({
    total_sales: 0,
    total_orders: 0,
    active_sellers: 0,
    pending_orders: 0,
    chart_data: []
  });

  // 🌟 대시보드 화면일 때만 백엔드 API를 호출하여 최신 통계와 차트 데이터를 가져옵니다.
  useEffect(() => {
    const fetchDashboard = async () => {
      if (activeMenu !== '통합 대시보드 (BI)') return;
      try {
        const response = await fetch('http://localhost:8001/api/hq/dashboard');
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error('대시보드 통계 연동 에러:', error);
      }
    };
    fetchDashboard();
  }, [activeMenu]);

  const menuList = [
    '통합 대시보드 (BI)', '조직 및 권한 관리', '입점사 및 파트너 관리', 
    '주문·결제·환불 총괄 (OMS)', '상품 및 카테고리 운영 (CMS)', 
    '고객 소통 및 CS 총괄', '시스템 운영 및 AI 감사', '정산 및 재무 관리 (Settlement)'
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f7f9' }}>
      <div style={{ width: '280px', backgroundColor: '#1e293b', color: 'white', padding: '20px', flexShrink: 0 }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '30px', paddingBottom: '15px', borderBottom: '1px solid #334155', whiteSpace: 'nowrap' }}>
          SHOPDB2 HQ Admin
        </h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {menuList.map((menu) => (
            <li 
              key={menu}
              onClick={() => setActiveMenu(menu)}
              style={{
                padding: '12px 15px', marginBottom: '10px', borderRadius: '6px',
                cursor: 'pointer', transition: 'background 0.2s',
                backgroundColor: activeMenu === menu ? '#3b82f6' : 'transparent',
                fontWeight: activeMenu === menu ? 'bold' : 'normal',
                fontSize: '0.95rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
              }}
            >
              {menu}
            </li>
          ))}
        </ul>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        {activeMenu === '통합 대시보드 (BI)' && (
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '20px', color: '#1e293b' }}>통합 비즈니스 현황</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '8px' }}>총 매출 (누적)</p>
                <h3 style={{ fontSize: '1.8rem', color: '#0f172a', margin: 0 }}>₩ {Number(dashboardData.total_sales).toLocaleString()}</h3>
              </div>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '8px' }}>전체 누적 주문</p>
                <h3 style={{ fontSize: '1.8rem', color: '#0f172a', margin: 0 }}>{Number(dashboardData.total_orders).toLocaleString()} 건</h3>
              </div>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '8px' }}>활성 입점사</p>
                <h3 style={{ fontSize: '1.8rem', color: '#0f172a', margin: 0 }}>{dashboardData.active_sellers} 개사</h3>
              </div>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '8px' }}>주문 처리 대기</p>
                <h3 style={{ fontSize: '1.8rem', color: '#0f172a', margin: 0 }}>{dashboardData.pending_orders} 건</h3>
              </div>
            </div>

            <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
              <h3 style={{ fontSize: '1.1rem', color: '#1e293b', margin: '0 0 20px 0' }}>📈 매출 추이 분석</h3>
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  {/* 🌟 가짜 데이터(getChartData) 대신 실제 상태값인 dashboardData.chart_data를 바인딩합니다 */}
                  <LineChart data={dashboardData.chart_data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip formatter={(value) => [`₩ ${value.toLocaleString()}`, '매출액']} />
                    <Line type="monotone" dataKey="sales" stroke="#3b82f6" strokeWidth={3} dot={{ r: 6 }} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeMenu === '조직 및 권한 관리' && <OrganizationManage />}
        {activeMenu === '입점사 및 파트너 관리' && <PartnerManage />}
        {activeMenu === '주문·결제·환불 총괄 (OMS)' && <OrderManage />}
        {activeMenu === '상품 및 카테고리 운영 (CMS)' && <ProductManage />}
        {activeMenu === '고객 소통 및 CS 총괄' && <CsManage />}
        {activeMenu === '시스템 운영 및 AI 감사' && <SystemOps />}
        {activeMenu === '정산 및 재무 관리 (Settlement)' && <SettlementManagement />}
      </div>
    </div>
  );
}