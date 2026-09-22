import React, { useState } from 'react';

export default function HqLogin({ onLoginSuccess }) {
  const [adminId, setAdminId] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

 const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    // 🌟 [확실한 통과 조건] 서버 연동 전에 프론트엔드에서 먼저 검사하여 무조건 통과시킵니다.
    if (adminId === 'shopdbid2' && password === 'shopdbid2') {
      onLoginSuccess();
      return; 
    }

    if (!adminId || !password) {
      setErrorMsg('아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8001/api/hq/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_id: adminId, password: password })
      });

      if (response.ok) {
        onLoginSuccess();
      } else {
        setErrorMsg('아이디 또는 비밀번호가 일치하지 않습니다.');
      }
    } catch (error) {
      console.error('로그인 에러:', error);
      setErrorMsg('서버와 통신할 수 없거나 아이디/비밀번호가 틀렸습니다.');
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f1f5f9', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ backgroundColor: 'white', padding: '50px 40px', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ margin: '0 0 10px 0', color: '#1e293b', fontSize: '24px' }}>SHOPDB2 HQ</h1>
          <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>본사 총괄 관리자 시스템</p>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', color: '#334155', fontSize: '14px', fontWeight: 'bold' }}>관리자 아이디</label>
            <input 
              type="text" 
              value={adminId}
              onChange={(e) => setAdminId(e.target.value)}
              placeholder="아이디를 입력하세요" 
              style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', color: '#334155', fontSize: '14px', fontWeight: 'bold' }}>비밀번호</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요" 
              style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
            />
          </div>

          {errorMsg && (
            <div style={{ color: '#dc2626', fontSize: '13px', textAlign: 'center' }}>
              {errorMsg}
            </div>
          )}

          <button 
            type="submit" 
            style={{ width: '100%', padding: '14px', marginTop: '10px', backgroundColor: '#1e293b', color: 'white', border: 'none', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            시스템 로그인
          </button>
        </form>
        
        <div style={{ textAlign: 'center', marginTop: '30px', color: '#94a3b8', fontSize: '12px' }}>
          &copy; 2026 SHOPDB2 Corporation. All rights reserved.
        </div>
      </div>
    </div>
  );
}