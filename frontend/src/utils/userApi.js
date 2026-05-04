/**
 * src/utils/userApi.js  ──  用户中心 API（用户/角色/部门）
 */
import { get, post, put, del } from './http.js';

// ── 用户管理 ─────────────────────────────────────────────
export const getUserList = (params = {}) => {
  const q = new URLSearchParams();
  if (params.page)     q.set('page', params.page);
  if (params.size)     q.set('size', params.size);
  if (params.username) q.set('username', params.username);
  if (params.dept_id)  q.set('dept_id', params.dept_id);
  return get(`/user/list?${q.toString()}`);
};

export const createUser = (data) => post('/user/create', data);
export const updateUser = (id, data) => put(`/user/${id}`, data);
export const deleteUser = (id) => del(`/user/${id}`);
export const toggleUserStatus = (id, status) =>
  fetch(`/api/user/${id}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
    },
    body: JSON.stringify({ status }),
  }).then((r) => r.json());

// ── 角色管理 ─────────────────────────────────────────────
export const getRoleList = () => get('/user/roles');
export const createRole  = (data) => post('/user/roles', data);
export const updateRole  = (id, data) => put(`/user/roles/${id}`, data);
export const deleteRole  = (id) => del(`/user/roles/${id}`);

// ── 部门管理 ─────────────────────────────────────────────
export const getDeptTree   = (name = '') => get(`/user/depts?name=${encodeURIComponent(name)}`);
export const createDept    = (data) => post('/user/depts', data);
export const updateDept    = (id, data) => put(`/user/depts/${id}`, data);
export const deleteDept    = (id) => del(`/user/depts/${id}`);

