const PORTAL_URL = process.env.REACT_APP_PORTAL_URL || 'http://127.0.0.1:4173';
const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8001';

function decodeAuth(value) {
  try {
    return JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(value)))));
  } catch {
    return null;
  }
}

export function requireHeadquartersAuth() {
  const url = new URL(window.location.href);
  const auth = url.searchParams.get('auth');
  if (auth) {
    const session = decodeAuth(auth);
    if (session?.user?.destination === 'HEADQUARTER') {
      localStorage.setItem('offit_auth', JSON.stringify(session));
    }
    url.searchParams.delete('auth');
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
  }

  const session = JSON.parse(localStorage.getItem('offit_auth') || 'null');
  if (!session?.access_token || session?.user?.destination !== 'HEADQUARTER') {
    window.location.replace(PORTAL_URL);
    return null;
  }
  return session;
}

export async function logout() {
  const session = JSON.parse(localStorage.getItem('offit_auth') || 'null');
  if (session?.access_token) {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${session.access_token}` },
    }).catch(() => null);
  }
  localStorage.removeItem('offit_auth');
  window.location.replace(PORTAL_URL);
}
