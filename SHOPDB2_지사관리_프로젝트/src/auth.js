const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || 'http://127.0.0.1:4173'

function decodeAuth(value) {
  try {
    return JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(value)))))
  } catch {
    return null
  }
}

export function receiveAuth() {
  const url = new URL(window.location.href)
  const auth = url.searchParams.get('auth')
  if (auth) {
    const session = decodeAuth(auth)
    if (session?.user?.destination === 'BRANCH') {
      localStorage.setItem('offit_auth', JSON.stringify(session))
    }
    url.searchParams.delete('auth')
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`)
  }
  return JSON.parse(localStorage.getItem('offit_auth') || 'null')
}

export function requireBranchAuth() {
  const session = receiveAuth()
  if (!session?.access_token || session?.user?.destination !== 'BRANCH') {
    window.location.replace(PORTAL_URL)
    return null
  }
  return session
}

export async function logout() {
  const session = JSON.parse(localStorage.getItem('offit_auth') || 'null')
  if (session?.access_token) {
    await fetch(`${import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8001'}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${session.access_token}` },
    }).catch(() => null)
  }
  localStorage.removeItem('offit_auth')
  window.location.replace(PORTAL_URL)
}
