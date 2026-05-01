"""
文件管理 API - 支持文件夹、文件树、批量上传和用户隔离
路径结构：users/{user_id}/files/{uuid}

核心功能：
1. 文件夹树形结构管理
2. 批量文件上传
3. 用户隔离（每个用户独立的文件空间）
4. 文件去重（基于SHA256哈希）
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os, uuid, hashlib, mimetypes, io, json
from datetime import datetime

from backend.storage import get_storage
from backend.db_pg import get_conn, get_dict_cursor
from backend.api.auth.jwt import get_current_user

router = APIRouter()
storage = get_storage()


# ───────────── Pydantic 模型 ─────────────
class CreateFolderRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = ""


class RenameFolderRequest(BaseModel):
    name: str


class MoveFilesRequest(BaseModel):
    file_ids: List[int]
    target_folder_id: Optional[int] = None


class RenameFileRequest(BaseModel):
    filename: str


# ───────────── 工具函数 ─────────────
def _get_user_id(user: dict) -> int:
    """从JWT payload获取用户ID"""
    return int(user["sub"])


def _calculate_file_hash(content: bytes) -> str:
    """计算文件SHA256哈希"""
    return hashlib.sha256(content).hexdigest()


def _build_folder_path(conn, folder_id: int, user_id: int) -> str:
    """构建文件夹的完整路径"""
    if folder_id is None:
        return "/root"
    with get_dict_cursor(conn) as cur:
        cur.execute("SELECT path FROM t_folder WHERE id=%s AND user_id=%s", (folder_id, user_id))
        row = cur.fetchone()
        return row['path'] if row else "/root"


def _verify_folder_ownership(conn, folder_id: int, user_id: int) -> bool:
    """验证文件夹所有权"""
    if folder_id is None:
        return True
    with get_dict_cursor(conn) as cur:
        cur.execute("SELECT id FROM t_folder WHERE id=%s AND user_id=%s", (folder_id, user_id))
        return cur.fetchone() is not None


def _verify_file_ownership(conn, file_id: int, user_id: int) -> bool:
    """验证文件所有权"""
    with get_dict_cursor(conn) as cur:
        cur.execute("SELECT id FROM t_file WHERE id=%s AND user_id=%s", (file_id, user_id))
        return cur.fetchone() is not None


def _get_root_folder(conn, user_id: int) -> Optional[int]:
    """获取用户的根文件夹ID"""
    with get_dict_cursor(conn) as cur:
        cur.execute("SELECT id FROM t_folder WHERE user_id=%s AND parent_id IS NULL LIMIT 1", (user_id,))
        row = cur.fetchone()
        return row['id'] if row else None


# ───────────── 文件夹管理接口 ─────────────

@router.get('/folders/tree')
def get_folder_tree(user: dict = Depends(get_current_user)):
    """获取用户的文件夹树形结构"""
    user_id = _get_user_id(user)
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            # 获取所有文件夹
            cur.execute("""
                SELECT id, parent_id, name, path, description, created_at, updated_at
                FROM t_folder
                WHERE user_id = %s
                ORDER BY path
            """, (user_id,))
            folders = cur.fetchall()

            # 获取每个文件夹的文件数量和总大小
            cur.execute("""
                SELECT folder_id, COUNT(*) as file_count, COALESCE(SUM(file_size), 0) as total_size
                FROM t_file
                WHERE user_id = %s
                GROUP BY folder_id
            """, (user_id,))
            stats = {row['folder_id']: row for row in cur.fetchall()}
    finally:
        conn.close()

    # 构建树形结构
    def build_tree(parent_id):
        children = []
        for folder in folders:
            if folder['parent_id'] == parent_id:
                folder_stats = stats.get(folder['id'], {'file_count': 0, 'total_size': 0})
                node = {
                    'id': folder['id'],
                    'name': folder['name'],
                    'path': folder['path'],
                    'description': folder['description'],
                    'fileCount': int(folder_stats['file_count'] or 0),
                    'totalSize': int(folder_stats['total_size'] or 0),
                    'createdAt': folder['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                    'children': build_tree(folder['id'])
                }
                children.append(node)
        return children

    tree = build_tree(None)
    return {'code': 200, 'tree': tree}


@router.post('/folders')
def create_folder(body: CreateFolderRequest, user: dict = Depends(get_current_user)):
    """创建文件夹"""
    user_id = _get_user_id(user)

    # 验证文件夹名称
    if not body.name or '/' in body.name:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '文件夹名称不能为空或包含斜杠'})

    conn = get_conn()
    try:
        # 验证父文件夹所有权
        if body.parent_id and not _verify_folder_ownership(conn, body.parent_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该父文件夹'})

        # 构建完整路径
        parent_path = _build_folder_path(conn, body.parent_id, user_id)
        full_path = f"{parent_path}/{body.name}"

        # 检查是否已存在同名文件夹
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                SELECT id FROM t_folder
                WHERE user_id=%s AND parent_id=%s AND name=%s
            """, (user_id, body.parent_id, body.name))
            if cur.fetchone():
                return JSONResponse(status_code=409, content={'code': 409, 'msg': '该文件夹已存在'})

            # 创建文件夹
            cur.execute("""
                INSERT INTO t_folder (user_id, parent_id, name, path, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, path, created_at
            """, (user_id, body.parent_id, body.name, full_path, body.description))
            folder = cur.fetchone()
        conn.commit()

        return {
            'code': 200,
            'msg': '文件夹创建成功',
            'folder': {
                'id': folder['id'],
                'name': folder['name'],
                'path': folder['path'],
                'createdAt': folder['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    finally:
        conn.close()


@router.put('/folders/{folder_id}')
def rename_folder(folder_id: int, body: RenameFolderRequest, user: dict = Depends(get_current_user)):
    """重命名文件夹"""
    user_id = _get_user_id(user)

    if not body.name or '/' in body.name:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '文件夹名称不能为空或包含斜杠'})

    conn = get_conn()
    try:
        # 验证所有权
        if not _verify_folder_ownership(conn, folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件夹'})

        with get_dict_cursor(conn) as cur:
            # 获取当前文件夹信息
            cur.execute("""
                SELECT parent_id, path FROM t_folder
                WHERE id=%s AND user_id=%s
            """, (folder_id, user_id))
            folder = cur.fetchone()
            if not folder:
                return JSONResponse(status_code=404, content={'code': 404, 'msg': '文件夹不存在'})

            # 构建新路径
            parent_path = _build_folder_path(conn, folder['parent_id'], user_id)
            new_path = f"{parent_path}/{body.name}"
            old_path = folder['path']

            # 更新文件夹及其子文件夹的路径
            cur.execute("""
                UPDATE t_folder
                SET name=%s, path=%s, updated_at=NOW()
                WHERE id=%s AND user_id=%s
            """, (body.name, new_path, folder_id, user_id))

            # 更新所有子文件夹的路径
            cur.execute("""
                UPDATE t_folder
                SET path = REPLACE(path, %s, %s), updated_at=NOW()
                WHERE user_id=%s AND path LIKE %s
            """, (old_path, new_path, user_id, f"{old_path}/%"))

        conn.commit()
        return {'code': 200, 'msg': '文件夹重命名成功'}
    finally:
        conn.close()


@router.delete('/folders/{folder_id}')
def delete_folder(folder_id: int, user: dict = Depends(get_current_user)):
    """删除文件夹（级联删除子文件夹和文件）"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        # 验证所有权
        if not _verify_folder_ownership(conn, folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件夹'})

        with get_dict_cursor(conn) as cur:
            # 检查是否为根文件夹
            cur.execute("SELECT parent_id FROM t_folder WHERE id=%s", (folder_id,))
            folder = cur.fetchone()
            if folder and folder['parent_id'] is None:
                return JSONResponse(status_code=400, content={'code': 400, 'msg': '不能删除根文件夹'})

            # 获取该文件夹及其子文件夹下的所有文件
            cur.execute("""
                SELECT f.storage_path
                FROM t_file f
                WHERE f.user_id=%s AND (
                    f.folder_id=%s OR
                    f.folder_id IN (
                        SELECT id FROM t_folder
                        WHERE user_id=%s AND path LIKE (
                            SELECT path || '%%' FROM t_folder WHERE id=%s
                        )
                    )
                )
            """, (user_id, folder_id, user_id, folder_id))
            files = cur.fetchall()

            # 从存储层删除文件
            for file in files:
                try:
                    storage.delete(file['storage_path'])
                except Exception as e:
                    print(f"删除文件失败: {file['storage_path']}, 错误: {e}")

            # 数据库会自动级联删除（ON DELETE CASCADE）
            cur.execute("DELETE FROM t_folder WHERE id=%s AND user_id=%s", (folder_id, user_id))

        conn.commit()
        return {'code': 200, 'msg': '文件夹删除成功'}
    finally:
        conn.close()


# ───────────── 文件管理接口 ─────────────

@router.get('/list')
def list_files(
    folder_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """列出文件（支持按文件夹筛选和分页）"""
    user_id = _get_user_id(user)
    offset = (page - 1) * size

    conn = get_conn()
    try:
        # 验证文件夹所有权
        if folder_id and not _verify_folder_ownership(conn, folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件夹'})

        with get_dict_cursor(conn) as cur:
            # 查询文件列表
            where_clause = "user_id=%s"
            params = [user_id]
            if folder_id is not None:
                where_clause += " AND folder_id=%s"
                params.append(folder_id)

            cur.execute(f"""
                SELECT COUNT(*) as total FROM t_file WHERE {where_clause}
            """, params)
            total = cur.fetchone()['total']

            cur.execute(f"""
                SELECT id, filename, original_filename, file_size, mime_type,
                       folder_id, metadata, tags, created_at, updated_at
                FROM t_file
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [size, offset])
            files = cur.fetchall()

        items = [{
            'id': f['id'],
            'filename': f['filename'],
            'originalFilename': f['original_filename'],
            'fileSize': f['file_size'],
            'mimeType': f['mime_type'],
            'folderId': f['folder_id'],
            'metadata': f['metadata'],
            'tags': f['tags'] or [],
            'createdAt': f['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'updatedAt': f['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        } for f in files]

        return {'code': 200, 'total': total, 'list': items}
    finally:
        conn.close()


@router.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """单文件上传"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        # 验证文件夹所有权
        if folder_id and not _verify_folder_ownership(conn, folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件夹'})

        # 如果没有指定文件夹，使用根文件夹
        if folder_id is None:
            folder_id = _get_root_folder(conn, user_id)

        # 读取文件内容
        content = await file.read()
        file_hash = _calculate_file_hash(content)
        file_size = len(content)
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'

        # 检查是否已存在相同哈希的文件（去重）
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                SELECT storage_path FROM t_file
                WHERE user_id=%s AND file_hash=%s LIMIT 1
            """, (user_id, file_hash))
            existing = cur.fetchone()

            if existing:
                # 复用已存在的文件
                storage_path = existing['storage_path']
            else:
                # 保存新文件
                file_uuid = str(uuid.uuid4())
                ext = os.path.splitext(file.filename)[1]
                storage_path = f"users/{user_id}/files/{file_uuid}{ext}"
                storage.save_bytes(content, storage_path)

            # 解析标签
            tag_list = []
            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]

            # 插入文件记录
            cur.execute("""
                INSERT INTO t_file
                (user_id, folder_id, filename, original_filename, file_size,
                 mime_type, storage_path, file_hash, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, filename, created_at
            """, (user_id, folder_id, file.filename, file.filename, file_size,
                  mime_type, storage_path, file_hash, tag_list))
            file_record = cur.fetchone()

        conn.commit()

        return {
            'code': 200,
            'msg': '文件上传成功',
            'file': {
                'id': file_record['id'],
                'filename': file_record['filename'],
                'fileSize': file_size,
                'createdAt': file_record['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={'code': 500, 'msg': f'上传失败: {str(e)}'})
    finally:
        conn.close()


@router.post('/batch-upload')
async def batch_upload(
    files: List[UploadFile] = File(...),
    folder_id: Optional[int] = Form(None),
    user: dict = Depends(get_current_user)
):
    """批量文件上传"""
    user_id = _get_user_id(user)

    if not files:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '没有选择文件'})

    conn = get_conn()
    try:
        # 验证文件夹所有权
        if folder_id and not _verify_folder_ownership(conn, folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件夹'})

        # 如果没有指定文件夹，使用根文件夹
        if folder_id is None:
            folder_id = _get_root_folder(conn, user_id)

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # 读取文件内容
                content = await file.read()
                file_hash = _calculate_file_hash(content)
                file_size = len(content)
                mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'

                with get_dict_cursor(conn) as cur:
                    # 检查是否已存在相同哈希的文件
                    cur.execute("""
                        SELECT storage_path FROM t_file
                        WHERE user_id=%s AND file_hash=%s LIMIT 1
                    """, (user_id, file_hash))
                    existing = cur.fetchone()

                    if existing:
                        storage_path = existing['storage_path']
                    else:
                        file_uuid = str(uuid.uuid4())
                        ext = os.path.splitext(file.filename)[1]
                        storage_path = f"users/{user_id}/files/{file_uuid}{ext}"
                        storage.save_bytes(content, storage_path)

                    # 插入文件记录
                    cur.execute("""
                        INSERT INTO t_file
                        (user_id, folder_id, filename, original_filename, file_size,
                         mime_type, storage_path, file_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, filename
                    """, (user_id, folder_id, file.filename, file.filename, file_size,
                          mime_type, storage_path, file_hash))
                    file_record = cur.fetchone()

                uploaded_files.append({
                    'id': file_record['id'],
                    'filename': file_record['filename'],
                    'fileSize': file_size
                })
            except Exception as e:
                failed_files.append({
                    'filename': file.filename,
                    'error': str(e)
                })

        conn.commit()

        return {
            'code': 200,
            'msg': f'批量上传完成：成功 {len(uploaded_files)} 个，失败 {len(failed_files)} 个',
            'uploaded': uploaded_files,
            'failed': failed_files
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={'code': 500, 'msg': f'批量上传失败: {str(e)}'})
    finally:
        conn.close()


@router.post('/move')
def move_files(body: MoveFilesRequest, user: dict = Depends(get_current_user)):
    """批量移动文件到指定文件夹"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        # 验证目标文件夹所有权
        if body.target_folder_id and not _verify_folder_ownership(conn, body.target_folder_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问目标文件夹'})

        # 验证所有文件的所有权
        for file_id in body.file_ids:
            if not _verify_file_ownership(conn, file_id, user_id):
                return JSONResponse(status_code=403, content={'code': 403, 'msg': f'无权访问文件 {file_id}'})

        # 批量移动文件
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                UPDATE t_file
                SET folder_id=%s, updated_at=NOW()
                WHERE id = ANY(%s) AND user_id=%s
            """, (body.target_folder_id, body.file_ids, user_id))

        conn.commit()
        return {'code': 200, 'msg': f'成功移动 {len(body.file_ids)} 个文件'}
    finally:
        conn.close()


@router.put('/{file_id}/rename')
def rename_file(file_id: int, body: RenameFileRequest, user: dict = Depends(get_current_user)):
    """重命名文件"""
    user_id = _get_user_id(user)

    if not body.filename:
        return JSONResponse(status_code=400, content={'code': 400, 'msg': '文件名不能为空'})

    conn = get_conn()
    try:
        # 验证所有权
        if not _verify_file_ownership(conn, file_id, user_id):
            return JSONResponse(status_code=403, content={'code': 403, 'msg': '无权访问该文件'})

        with get_dict_cursor(conn) as cur:
            cur.execute("""
                UPDATE t_file
                SET filename=%s, updated_at=NOW()
                WHERE id=%s AND user_id=%s
            """, (body.filename, file_id, user_id))

        conn.commit()
        return {'code': 200, 'msg': '文件重命名成功'}
    finally:
        conn.close()


@router.delete('/{file_id}')
def delete_file(file_id: int, user: dict = Depends(get_current_user)):
    """删除文件"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        # 验证所有权并获取存储路径
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                SELECT storage_path, file_hash FROM t_file
                WHERE id=%s AND user_id=%s
            """, (file_id, user_id))
            file = cur.fetchone()

            if not file:
                return JSONResponse(status_code=404, content={'code': 404, 'msg': '文件不存在'})

            # 检查是否有其他文件使用相同的存储路径（去重场景）
            cur.execute("""
                SELECT COUNT(*) as cnt FROM t_file
                WHERE user_id=%s AND file_hash=%s AND id!=%s
            """, (user_id, file['file_hash'], file_id))
            count = cur.fetchone()['cnt']

            # 删除数据库记录
            cur.execute("DELETE FROM t_file WHERE id=%s AND user_id=%s", (file_id, user_id))

            # 如果没有其他文件使用该存储路径，则删除物理文件
            if count == 0:
                try:
                    storage.delete(file['storage_path'])
                except Exception as e:
                    print(f"删除物理文件失败: {file['storage_path']}, 错误: {e}")

        conn.commit()
        return {'code': 200, 'msg': '文件删除成功'}
    finally:
        conn.close()


@router.get('/{file_id}/download')
def download_file(file_id: int, user: dict = Depends(get_current_user)):
    """下载文件"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        # 验证所有权并获取文件信息
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                SELECT filename, original_filename, storage_path, mime_type
                FROM t_file
                WHERE id=%s AND user_id=%s
            """, (file_id, user_id))
            file = cur.fetchone()

            if not file:
                return JSONResponse(status_code=404, content={'code': 404, 'msg': '文件不存在'})

        # 从存储层读取文件
        try:
            content = storage.load_bytes(file['storage_path'])
            return StreamingResponse(
                io.BytesIO(content),
                media_type=file['mime_type'],
                headers={
                    'Content-Disposition': f'attachment; filename="{file["original_filename"]}"'
                }
            )
        except Exception as e:
            return JSONResponse(status_code=500, content={'code': 500, 'msg': f'文件读取失败: {str(e)}'})
    finally:
        conn.close()


@router.get('/stats')
def get_user_stats(user: dict = Depends(get_current_user)):
    """获取用户文件统计信息"""
    user_id = _get_user_id(user)

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            # 统计文件数量和总大小
            cur.execute("""
                SELECT
                    COUNT(*) as file_count,
                    COALESCE(SUM(file_size), 0) as total_size
                FROM t_file
                WHERE user_id=%s
            """, (user_id,))
            file_stats = cur.fetchone()

            # 统计文件夹数量
            cur.execute("""
                SELECT COUNT(*) as folder_count
                FROM t_folder
                WHERE user_id=%s
            """, (user_id,))
            folder_stats = cur.fetchone()

        return {
            'code': 200,
            'stats': {
                'fileCount': file_stats['file_count'],
                'totalSize': file_stats['total_size'],
                'folderCount': folder_stats['folder_count']
            }
        }
    finally:
        conn.close()
