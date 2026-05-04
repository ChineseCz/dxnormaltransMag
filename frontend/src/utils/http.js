/**
 * src/utils/http.js  ──  统一 fetch 封装
 * - 自动附加 Authorization: Bearer <token>
 * - 统一解析 JSON 响应
 * - 非 2xx 时抛出带 message 的 Error
 * - 401 时清除本地 token 并跳转登录页
 */

const BASE_URL = '/api';   // vite.config.js 已代理到 http://127.0.0.1:5000

function getToken() {
  return localStorage.getItem('auth_token') || '';
}

function _handleUnauthorized() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');
  localStorage.removeItem('auth_expires');
  // 用 ElMessage 提示（动态导入避免循环依赖）
  import('element-plus').then(({ ElMessage }) => {
    ElMessage.error({ message: '登录已过期，请重新登录', duration: 3000, grouping: true });
  });
  // 跳转登录（用 location 避免 router 实例不可用的时序问题）
  if (!window.location.pathname.startsWith('/login')) {
    setTimeout(() => { window.location.href = '/login'; }, 800);
  }
}

export async function http(path, options = {}) {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  // 401 → 清除凭证并跳转登录
  if (res.status === 401) {
    _handleUnauthorized();
  }

  let data;
  try {
    data = await res.json();
  } catch {
    data = {};
  }

  if (!res.ok) {
    const msg = data?.msg || data?.detail || data?.error || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.data   = data;
    throw err;
  }

  return data;
}

export const get  = (path, opts = {}) => http(path, { method: 'GET',    ...opts });
export const post = (path, body, opts = {}) => http(path, { method: 'POST', body, ...opts });
export const put  = (path, body, opts = {}) => http(path, { method: 'PUT',  body, ...opts });
export const del  = (path, opts = {}) => http(path, { method: 'DELETE', ...opts });
