/**
 * API client for backend (FastAPI). Uses relative URLs so proxy works in dev.
 */
const API_BASE = ''

export async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  return res
}

export async function getMe() {
  const res = await apiFetch('/api/auth/me')
  if (res.status === 401) return null
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function login(username, password) {
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.message || 'Login failed')
  }
  return res.json()
}

function apiErrorFromResponse(res, text) {
  let message = text
  try {
    const data = JSON.parse(text)
    message = data.detail ?? data.message ?? text
    if (Array.isArray(message)) message = message.map((m) => m.msg ?? m).join('; ')
  } catch {
    /* use text */
  }
  return new Error(message)
}

export async function getMeDevice(deviceId) {
  const res = await apiFetch('/api/me/device', {
    headers: { 'X-Device-ID': deviceId },
  })
  if (res.status === 404) return null
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function registerDevice(deviceId, name, deviceType = 'tablet') {
  const res = await apiFetch('/api/me/device', {
    method: 'POST',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify({ name, device_type: deviceType, fingerprint: deviceId }),
  })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function patchMeDevice(deviceId, body) {
  const res = await apiFetch('/api/me/device', {
    method: 'PATCH',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getProductByBarcode(deviceId, code) {
  const res = await apiFetch(`/api/me/product-by-barcode/${encodeURIComponent(code)}`, {
    headers: { 'X-Device-ID': deviceId },
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getMeProducts(deviceId, q = '') {
  const url = q ? `/api/me/products?q=${encodeURIComponent(q)}` : '/api/me/products'
  const res = await apiFetch(url, { headers: { 'X-Device-ID': deviceId } })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getMeProductDetail(deviceId, productId) {
  const res = await apiFetch(`/api/me/products/${productId}`, {
    headers: { 'X-Device-ID': deviceId },
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function addStock(deviceId, productId, quantity = 1, locationId = null) {
  const res = await apiFetch('/api/me/stock/add', {
    method: 'POST',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify({ product_id: productId, quantity, location_id: locationId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function consumeStock(deviceId, productId, quantity = 1, locationId = null) {
  const res = await apiFetch('/api/me/stock/consume', {
    method: 'POST',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify({ product_id: productId, quantity, location_id: locationId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function patchMeProduct(deviceId, productId, body) {
  const res = await apiFetch(`/api/me/products/${productId}`, {
    method: 'PATCH',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

// Locations (session + device)
export async function getMeLocations(deviceId) {
  const res = await apiFetch('/api/me/locations', {
    headers: { 'X-Device-ID': deviceId },
  })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function createMeLocation(deviceId, data) {
  const res = await apiFetch('/api/me/locations', {
    method: 'POST',
    headers: { 'X-Device-ID': deviceId },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

// Logs (session only)
export async function getLogs() {
  const res = await apiFetch('/api/logs')
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function clearLogs() {
  const res = await apiFetch('/api/logs/clear', { method: 'POST' })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

// Settings (session only)
export async function getSettings() {
  const res = await apiFetch('/api/settings')
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function getSettingsSection(section) {
  const res = await apiFetch(`/api/settings/${section}`)
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function saveSettings(section, values) {
  const res = await apiFetch(`/api/settings/${section}`, {
    method: 'PUT',
    body: JSON.stringify({ values }),
  })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function testGrocyConnection() {
  const res = await apiFetch('/api/settings/grocy/test', { method: 'POST' })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function testLookupProvider(provider) {
  const res = await apiFetch(`/api/settings/lookup/test/${provider}`, { method: 'POST' })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

// Jobs (session only)
export async function getJobs(status = null, limit = 100) {
  let url = `/api/jobs?limit=${limit}`
  if (status) url += `&status=${status}`
  const res = await apiFetch(url)
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function retryJob(jobId) {
  const res = await apiFetch(`/api/jobs/${jobId}/retry`, { method: 'POST' })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}

export async function cancelJob(jobId) {
  const res = await apiFetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' })
  if (!res.ok) throw apiErrorFromResponse(res, await res.text())
  return res.json()
}
