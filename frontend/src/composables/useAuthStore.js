import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { post, get } from '../utils/http.js';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '');
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'));

  const isLoggedIn = computed(() => !!token.value);
  const username = computed(() => userInfo.value?.username || '');
  const role = computed(() => userInfo.value?.role || '');

  /** 登录 → POST /api/user/login */
  async function login(usernameVal, password) {
    const data = await post('/user/login', { username: usernameVal, password });
    _saveSession(data);
    return data;
  }

  /** 注册 → POST /api/user/register（自动登录）*/
  async function register(usernameVal, password, email = '') {
    const data = await post('/user/register', { username: usernameVal, password, email });
    _saveSession(data);
    return data;
  }

  /** 注销 → POST /api/user/logout（让后端把 jti 加黑名单）*/
  async function logout() {
    try {
      await post('/user/logout');
    } catch { /* token 已失效时忽略 */ }
    _clearSession();
  }

  /** 刷新 token → POST /api/user/refresh */
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

  /** 从服务端拉取当前用户信息（页面刷新后恢复状态用）*/
  async function fetchMe() {
    const data = await get('/user/me');
    const info = { username: data.username, role: data.role, user_id: data.user_id };
    userInfo.value = info;
    localStorage.setItem('user_info', JSON.stringify(info));
    return data;
  }

  // ── 内部工具 ──────────────────────────────────────────────────────────────
  function _saveSession(data) {
    token.value = data.token;
    const info = { username: data.username, role: data.role };
    userInfo.value = info;
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user_info', JSON.stringify(info));
  }

  function _clearSession() {
    token.value = '';
    userInfo.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  return { token, userInfo, isLoggedIn, username, role, login, register, logout, refresh, fetchMe };
});
