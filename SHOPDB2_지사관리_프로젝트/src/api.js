const API_BASE =
  import.meta.env.VITE_API_BASE ||
  'http://127.0.0.1:8001'

const storedSession = JSON.parse(localStorage.getItem('offit_auth') || 'null')
export const BRANCH_ORG_ID = Number(storedSession?.user?.org_id || import.meta.env.VITE_BRANCH_ORG_ID || 1)

async function request(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Org-Id': String(BRANCH_ORG_ID),
        ...(storedSession?.access_token ? { Authorization: `Bearer ${storedSession.access_token}` } : {}),
        ...options.headers,
      },
    }
  )

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => null)

    throw new Error(
      errorData?.detail ||
      `HTTP ${response.status}`
    )
  }

  return response.json()
}

export const api = {
  health: () =>
    request('/health/db'),

  branch: () => request('/api/branch/me'),

  dashboard: () => request('/api/branch/dashboard'),

  products: () => request('/api/branch/products'),

  createProduct: (product) =>
    request('/api/branch/products', {
      method: 'POST',
      body: JSON.stringify(product),
    }),

  updateProduct: (productId, product) =>
    request(`/api/branch/products/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(product),
    }),

  deleteProduct: (productId) =>
    request(`/api/branch/products/${productId}`, {
      method: 'DELETE',
    }),

  categories: () =>
    request('/api/categories'),

  orders: () => request('/api/branch/orders'),

  customers: () => request('/api/branch/customers'),

  orderStatuses: () =>
    request('/api/orders/statuses'),

  updateOrderStatus: (
    orderId,
    orderStatus
  ) =>
    request(
      `/api/branch/orders/${orderId}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          order_status: orderStatus,
        }),
      }
    ),
}

export { API_BASE }
