const API_BASE = 'http://127.0.0.1:8001';

async function request(path, options = {}) {
  const response = await fetch(
    `${API_BASE}${path}`,
    {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new Error(errorData?.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  health: () => request('/health/db'),
  products: () => request('/api/products'),
  createProduct: (product) => request('/api/products', { method: 'POST', body: JSON.stringify(product) }),
  updateProduct: (productId, product) => request(`/api/products/${productId}`, { method: 'PUT', body: JSON.stringify(product) }),
  deleteProduct: (productId) => request(`/api/products/${productId}`, { method: 'DELETE' }),
  categories: () => request('/api/categories'),
  orders: () => request('/api/orders'),
  orderStatuses: () => request('/api/orders/statuses'),
  updateOrderStatus: (orderId, orderStatus) => request(`/api/orders/${orderId}/status`, { method: 'PATCH', body: JSON.stringify({ order_status: orderStatus }) }),

  branches: () => request('/api/hq/branches'),
  createBranch: (branch) => request('/api/hq/branches', { method: 'POST', body: JSON.stringify(branch) }),
  updateBranchStatus: (branchId, status) => request(`/api/hq/branches/${branchId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  deleteBranch: (branchId) => request(`/api/hq/branches/${branchId}`, { method: 'DELETE' }),
  
  // 🌟 [추가됨] 담당자 변경 함수
  updateBranchManager: (branchId, manager) => request(`/api/hq/branches/${branchId}/manager`, { method: 'PATCH', body: JSON.stringify({ manager }) }),
}


