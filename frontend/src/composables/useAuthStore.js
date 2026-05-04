import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { post, get } from '../utils/http.js';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '');
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'));
  const expires = ref(Number(localStorage.getItem('auth_expires') || '0'));

  const isLoggedIn = computed(() => !!token.value);
  const username = computed(() => userInfo.value?.username || '');
  const role = computed(() => userInfo.value?.role || '');

  /** 距 token 过期还有多少秒（<0 表示已过期）*/
  const expiresIn = computed(() => expires.value - Math.floor(Date.now() / 1000));

  /** 登录 */
  async function login(usernameVal, password) {
    const data = await post('/user/login', { username: usernameVal, password });
    _saveSession(data);
    return data;
  }

  /** 注册（自动登录）*/
  async function register(usernameVal, password, email = '') {
    const data = await post('/user/register', { username: usernameVal, password, email });
    _saveSession(data);
    return data;
  }

  /** 注销 */
  async function logout() {
    try { await post('/user/logout'); } catch { /* token 已失效时忽略 */ }
    _clearSession();
  }

  /** 刷新 token */
  async function refresh() {
    try {
      const data = await post('/user/refresh');
      _saveSession(data);
      return data;
    } catch {
      _clearSession();
      throw new Error('会话已失效，请重新登录');
    }
  }

  /** 拉取当前用户信息（页面刷新后恢复状态用）*/
  async function fetchMe() {
    const data = await get('/user/me');
    const info = { username: data.username, role: data.role, user_id: data.user_id };
    userInfo.value = info;
    localStorage.setItem('user_info', JSON.stringify(info));
    return data;
  }

  /**
   * 应用启动时调用：
   * - token 已过期 → 清除
   * - token 将在 5 分钟内过期 → 静默刷新
   */
  async function checkExpiry() {
    if (!token.value) return;
    const remaining = expiresIn.value;
    if (remaining <= 0) {
      _clearSession();
      return;
    }
    // 剩余不足 5 分钟，静默刷新
    if (remaining < 300) {
      try { await refresh(); } catch { /* 刷新失败由 http.js 处理 */ }
    }
  }

  // ── 内部工具 ──────────────────────────────────────────────────────────────
  function _saveSession(data) {
    token.value = data.token;
    const exp = data.expires || Math.floor(Date.now() / 1000) + 86400;
    expires.value = exp;
    const info = { username: data.username, role: data.role };
    userInfo.value = info;
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user_info', JSON.stringify(info));
    localStorage.setItem('auth_expires', String(exp));
  }

  function _clearSession() {
    token.value = '';
    userInfo.value = null;
    expires.value = 0;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('auth_expires');
  }

  return {
    token, userInfo, expires, isLoggedIn, username, role, expiresIn,
    login, register, logout, refresh, fetchMe, checkExpiry,
  };
});
