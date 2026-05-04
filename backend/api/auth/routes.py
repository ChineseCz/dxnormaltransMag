"""api/auth/routes.py  ──  用户鉴权 + 用户中心 CRUD 路由"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import bcrypt, time, os, threading, json
from typing import Optional

# db_pg 位于 backend/ 目录，run.py 已将其加入 sys.path，直接导入即可
from db_pg import get_conn, get_dict_cursor  # noqa: E402
from .jwt import create_access_token, revoke_token, get_current_user

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────────────────────────────
def _query_one(conn, sql, params):
    with get_dict_cursor(conn) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _audit_async(user_id: int, ip: str):
    def _run():
        try:
            conn = get_conn()
            with get_dict_cursor(conn) as cur:
                cur.execute(
                    "INSERT INTO t_audit_log(user_id,action,ip) VALUES(%s,'login',%s)",
                    (user_id, ip),
                )
                cur.execute(
                    "UPDATE t_user SET last_login_at=NOW() WHERE id=%s", (user_id,)
                )
            conn.commit()
            conn.close()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


def _fmt_time(ts):
    return ts.strftime('%Y-%m-%d %H:%M:%S') if ts else ''


def _build_dept_tree(rows, parent_id=0):
    nodes = []
    for r in rows:
        if r['parent_id'] == parent_id:
            node = {
                'deptId': r['id'], 'deptName': r['name'],
                'parentId': r['parent_id'], 'orderNum': r['order_num'],
                'status': str(1 - r['status']),        # DB:1=active→'0', DB:0=disabled→'1'
                'createTime': _fmt_time(r['created_at']),
            }
            children = _build_dept_tree(rows, r['id'])
            if children:
                node['children'] = children
            nodes.append(node)
    nodes.sort(key=lambda x: x['orderNum'])
    return nodes


# ──────────────────────────────────────────────────────────────────────
#  Pydantic 请求体
# ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str = ""
    password: str = ""


class RegisterRequest(BaseModel):
    username: str = ""
    password: str = ""
    email:    Optional[str] = ""


class UserCreateRequest(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = ""
    phone:    Optional[str] = ""
    email:    Optional[str] = ""
    role_id:  Optional[int] = 2
    dept_id:  Optional[int] = None
    status:   Optional[int] = 1


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    phone:    Optional[str] = None
    email:    Optional[str] = None
    role_id:  Optional[int] = None
    dept_id:  Optional[int] = None
    status:   Optional[int] = None
    password: Optional[str] = None


class RoleRequest(BaseModel):
    role_name: str
    role_key:  Optional[str] = ""
    role_sort: Optional[int] = 1
    status:    Optional[int] = 1
    permissions: Optional[dict] = {}


class DeptRequest(BaseModel):
    name:      str
    parent_id: Optional[int] = 0
    order_num: Optional[int] = 0
    status:    Optional[int] = 1


# ──────────────────────────────────────────────────────────────────────
#  认证接口（登录 / 注册 / 登出 / 刷新 / 当前用户）
# ──────────────────────────────────────────────────────────────────────
@router.post('/login')
def login(body: LoginRequest, request: Request):
    username = body.username.strip()
    password = body.password
    if not username or not password:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '用户名和密码不能为空'})

    conn = get_conn()
    try:
        row = _query_one(
            conn,
            "SELECT id,username,password_hash,role_id FROM t_user WHERE username=%s AND status=1",
            (username,),
        )
    finally:
        conn.close()

    if row is None:
        return JSONResponse(status_code=401, content={'code': 401, 'msg': '用户名或密码错误'})
    if not bcrypt.checkpw(password.encode(), row['password_hash'].encode()):
        return JSONResponse(status_code=401, content={'code': 401, 'msg': '用户名或密码错误'})

    role_name = '管理员' if row['role_id'] == 1 else '工程师'
    token, _ = create_access_token(row['id'], row['username'], role_name)
    _audit_async(row['id'], request.client.host if request.client else '127.0.0.1')

    return {
        'code': 200, 'token': token, 'token_type': 'bearer',
        'username': row['username'], 'role': role_name,
        'expires': int(time.time()) + int(os.environ.get("JWT_EXPIRE", "86400")),
    }


@router.post('/register')
def register(body: RegisterRequest, request: Request):
    username = body.username.strip()
    password = body.password
    email    = (body.email or '').strip()

    if not username or not password:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '用户名和密码不能为空'})
    if len(username) < 3 or len(username) > 20:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '用户名长度需在 3~20 位之间'})
    if len(password) < 6:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '密码长度不能少于 6 位'})

    conn = get_conn()
    try:
        exist = _query_one(conn, "SELECT id FROM t_user WHERE username=%s", (username,))
        if exist:
            return JSONResponse(status_code=409, content={'code': 409, 'msg': '用户名已存在'})

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()
        with get_dict_cursor(conn) as cur:
            cur.execute(
                "INSERT INTO t_user(username,password_hash,role_id,email) VALUES(%s,%s,2,%s) RETURNING id",
                (username, pw_hash, email),
            )
            new_id = cur.fetchone()['id']
        conn.commit()
    finally:
        conn.close()

    token, _ = create_access_token(new_id, username, '工程师')
    return {
        'code': 200, 'token': token, 'token_type': 'bearer',
        'username': username, 'role': '工程师',
        'expires': int(time.time()) + int(os.environ.get("JWT_EXPIRE", "86400")),
    }


@router.post('/logout')
def logout(user: dict = Depends(get_current_user)):
    jti = user.get("jti", "")
    if jti:
        revoke_token(jti, user.get("exp", time.time()))
    return {'code': 200, 'msg': '已注销'}


@router.post('/refresh')
def refresh(user: dict = Depends(get_current_user)):
    jti = user.get("jti", "")
    if jti:
        revoke_token(jti, user.get("exp", time.time()))
    new_token, _ = create_access_token(int(user["sub"]), user["username"], user["role"])
    return {
        'code': 200, 'token': new_token, 'token_type': 'bearer',
        'expires': int(time.time()) + int(os.environ.get("JWT_EXPIRE", "86400")),
    }


@router.get('/me')
def me(user: dict = Depends(get_current_user)):
    return {'code': 200, 'user_id': user['sub'], 'username': user['username'],
            'role': user['role'], 'exp': user['exp']}


@router.get('/db_mode')
def db_mode():
    return {'db': 'postgresql'}


# ──────────────────────────────────────────────────────────────────────
#  用户管理 CRUD
# ──────────────────────────────────────────────────────────────────────
@router.get('/list')
def user_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    username: str = Query(""),
    dept_id: Optional[int] = Query(None),
    _user: dict = Depends(get_current_user),
):
    offset = (page - 1) * size
    where, params = ["u.id > 0"], []
    if username:
        where.append("u.username ILIKE %s");  params.append(f"%{username}%")
    if dept_id:
        where.append("u.dept_id = %s");       params.append(dept_id)
    wc = " AND ".join(where)

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(f"SELECT COUNT(*) as cnt FROM t_user u WHERE {wc}", params)
            total = cur.fetchone()['cnt']
            cur.execute(f"""
                SELECT u.id, u.username, u.nickname, u.phone, u.email,
                       u.role_id, r.role_name, u.dept_id, d.name AS dept_name,
                       u.status, u.created_at
                FROM t_user u
                LEFT JOIN t_role r ON u.role_id = r.id
                LEFT JOIN t_dept d ON u.dept_id = d.id
                WHERE {wc}
                ORDER BY u.id
                LIMIT %s OFFSET %s
            """, params + [size, offset])
            rows = cur.fetchall()
    finally:
        conn.close()

    items = [{
        'userId': r['id'], 'userName': r['username'],
        'nickName': r['nickname'] or r['username'],
        'email': r['email'] or '', 'phoneNumber': r['phone'] or '',
        'dept': r['dept_name'] or '未分配', 'deptId': r['dept_id'],
        'roleId': r['role_id'], 'roleName': r['role_name'] or '',
        'status': r['status'] == 1,
        'createTime': _fmt_time(r['created_at']),
    } for r in rows]
    return {'code': 200, 'total': total, 'list': items}


@router.post('/create')
def user_create(body: UserCreateRequest, _user: dict = Depends(get_current_user)):
    if len(body.username) < 3:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '用户名至少 3 位'})
    if len(body.password) < 6:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '密码至少 6 位'})

    conn = get_conn()
    try:
        if _query_one(conn, "SELECT id FROM t_user WHERE username=%s", (body.username,)):
            return JSONResponse(status_code=409, content={'code': 409, 'msg': '用户名已存在'})
        pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt(10)).decode()
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO t_user(username,password_hash,nickname,phone,email,role_id,dept_id,status)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
            """, (body.username, pw_hash, body.nickname, body.phone,
                  body.email, body.role_id, body.dept_id, body.status))
            new_id = cur.fetchone()['id']
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '创建成功', 'userId': new_id}


@router.put('/{user_id}')
def user_update(user_id: int, body: UserUpdateRequest, _user: dict = Depends(get_current_user)):
    sets, params = [], []
    if body.nickname  is not None: sets.append("nickname=%s");      params.append(body.nickname)
    if body.phone     is not None: sets.append("phone=%s");         params.append(body.phone)
    if body.email     is not None: sets.append("email=%s");         params.append(body.email)
    if body.role_id   is not None: sets.append("role_id=%s");       params.append(body.role_id)
    if body.dept_id   is not None: sets.append("dept_id=%s");       params.append(body.dept_id)
    if body.status    is not None: sets.append("status=%s");        params.append(body.status)
    if body.password:
        pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt(10)).decode()
        sets.append("password_hash=%s"); params.append(pw_hash)
    if not sets:
        return {'code': 200, 'msg': '无变更'}

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(f"UPDATE t_user SET {','.join(sets)} WHERE id=%s", params + [user_id])
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '更新成功'}


@router.delete('/{user_id}')
def user_delete(user_id: int, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("DELETE FROM t_user WHERE id=%s", (user_id,))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '删除成功'}


@router.patch('/{user_id}/status')
def user_toggle_status(user_id: int, body: dict, _user: dict = Depends(get_current_user)):
    status = 1 if body.get('status') else 0
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("UPDATE t_user SET status=%s WHERE id=%s", (status, user_id))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '状态已更新'}


# ──────────────────────────────────────────────────────────────────────
#  角色管理 CRUD
# ──────────────────────────────────────────────────────────────────────
@router.get('/roles')
def role_list(_user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("SELECT id,role_name,role_key,role_sort,status,created_at FROM t_role ORDER BY role_sort")
            rows = cur.fetchall()
    finally:
        conn.close()
    return {'code': 200, 'list': [{
        'roleId': r['id'], 'roleName': r['role_name'],
        'roleKey': r['role_key'] or '', 'roleSort': r['role_sort'] or 1,
        'status': str(1 - (r['status'] or 1)),   # DB:1=active→'0'
        'createTime': _fmt_time(r['created_at']),
    } for r in rows]}


@router.post('/roles')
def role_create(body: RoleRequest, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO t_role(role_name,role_key,role_sort,status,permissions)
                VALUES(%s,%s,%s,%s,%s) RETURNING id
            """, (body.role_name, body.role_key, body.role_sort, body.status,
                  json.dumps(body.permissions or {})))
            new_id = cur.fetchone()['id']
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '创建成功', 'roleId': new_id}


@router.put('/roles/{role_id}')
def role_update(role_id: int, body: RoleRequest, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                UPDATE t_role SET role_name=%s,role_key=%s,role_sort=%s,status=%s
                WHERE id=%s
            """, (body.role_name, body.role_key, body.role_sort, body.status, role_id))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '更新成功'}


@router.delete('/roles/{role_id}')
def role_delete(role_id: int, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("DELETE FROM t_role WHERE id=%s", (role_id,))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '删除成功'}


# ──────────────────────────────────────────────────────────────────────
#  部门管理 CRUD
# ──────────────────────────────────────────────────────────────────────
@router.get('/depts')
def dept_tree(name: str = Query(""), _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            if name:
                cur.execute("SELECT * FROM t_dept WHERE name ILIKE %s ORDER BY order_num", (f"%{name}%",))
            else:
                cur.execute("SELECT * FROM t_dept ORDER BY order_num")
            rows = cur.fetchall()
    finally:
        conn.close()
    # Build tree from root (parent_id=0)
    tree = _build_dept_tree(rows, 0)
    return {'code': 200, 'list': tree}


@router.post('/depts')
def dept_create(body: DeptRequest, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO t_dept(parent_id,name,order_num,status)
                VALUES(%s,%s,%s,%s) RETURNING id
            """, (body.parent_id, body.name, body.order_num, body.status))
            new_id = cur.fetchone()['id']
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '创建成功', 'deptId': new_id}


@router.put('/depts/{dept_id}')
def dept_update(dept_id: int, body: DeptRequest, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                UPDATE t_dept SET parent_id=%s,name=%s,order_num=%s,status=%s
                WHERE id=%s
            """, (body.parent_id, body.name, body.order_num, body.status, dept_id))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '更新成功'}


@router.delete('/depts/{dept_id}')
def dept_delete(dept_id: int, _user: dict = Depends(get_current_user)):
    conn = get_conn()
    try:
        # 检查是否有子部门
        with get_dict_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM t_dept WHERE parent_id=%s", (dept_id,))
            if cur.fetchone()['cnt'] > 0:
                return JSONResponse(status_code=400, content={'code': 400, 'msg': '请先删除子部门'})
            cur.execute("DELETE FROM t_dept WHERE id=%s", (dept_id,))
        conn.commit()
    finally:
        conn.close()
    return {'code': 200, 'msg': '删除成功'}
