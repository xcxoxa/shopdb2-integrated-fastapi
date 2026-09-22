import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// 기존에 연결해두신 페이지들
import HqMain from './pages/HqMain';
import BranchManage from './pages/BranchManage';
import SettlementManagement from './pages/SettlementManagement'; 

// 🌟 방금 만든 로그인 컴포넌트를 불러옵니다.
// (만약 HqLogin.jsx를 pages 폴더 안에 만들었다면 './pages/HqLogin'으로 경로를 수정해주세요)
import { logout, requireHeadquartersAuth } from './auth';

import './styles.css'; 
import './MemberManagement.css';

function App() {
  const session = requireHeadquartersAuth();
  if (!session) return null;

  return (
    <BrowserRouter>
      <button type="button" onClick={logout} style={{position:'fixed',right:24,bottom:24,zIndex:9999,padding:'12px 18px',border:0,borderRadius:10,background:'#111',color:'#fff',fontWeight:800,cursor:'pointer'}}>로그아웃</button>
        <Routes>
          <Route path="/" element={<HqMain />} />
          <Route path="/branch" element={<BranchManage />} />
          <Route path="/hq/settlements" element={<SettlementManagement />} />
        </Routes>
    </BrowserRouter>
  );
}

export default App;
