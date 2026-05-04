"""
数据集管理 API —— PostgreSQL 为唯一数据源
每个数据集拥有独立的目录结构：
  datasets/<id>/raw/         原始上传文件（MinIO）
  datasets/<id>/data/        处理后的数据文件（本地）
  datasets/<id>/pca_result/  PCA 结果（本地）
  datasets/<id>/model/       模型文件（本地）
  datasets/<id>/result/      预测结果（本地）
"""

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any, List
import os, json, uuid, shutil, io
from datetime import datetime
import numpy as np

from backend.storage import get_storage
from backend.db_pg import get_conn, get_dict_cursor

router = APIRouter()

_HERE        = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(os.path.dirname(_HERE))
DATASETS_DIR = os.path.join(_BACKEND_DIR, 'datasets')

storage = get_storage()
os.makedirs(DATASETS_DIR, exist_ok=True)

# ───────────── 预定义的设备类型与物理场类型 ─────────────

DEVICE_TYPES = [
    {"value": "transformer",  "label": "变压器",  "icon": "⚡"},
    {"value": "reactor",      "label": "电抗器",  "icon": "🔌"},
    {"value": "motor",        "label": "电机",    "icon": "⚙️"},
    {"value": "gis",          "label": "GIS",     "icon": "🏗️"},
    {"value": "cable",        "label": "电缆",    "icon": "🔗"},
    {"value": "busbar",       "label": "母线",    "icon": "📏"},
    {"value": "other",        "label": "其他",    "icon": "📦"},
]

FIELD_TYPES = [
    {"value": "magnetic",     "label": "磁场",   "unit": "T",    "unitLabel": "磁通密度 B"},
    {"value": "temperature",  "label": "温度场", "unit": "°C",   "unitLabel": "温度 T"},
    {"value": "stress",       "label": "应力场", "unit": "Pa",   "unitLabel": "应力 σ"},
    {"value": "electric",     "label": "电场",   "unit": "V/m",  "unitLabel": "电场强度 E"},
    {"value": "flow",         "label": "流场",   "unit": "m/s",  "unitLabel": "流速 v"},
    {"value": "other",        "label": "其他",   "unit": "",     "unitLabel": "自定义"},
]

# ───────────── PG 工具函数 ─────────────

def _row_to_ds(row: dict, files: list) -> dict:
    """将 PG 行 + 文件列表转换为前端期望的 dataset dict"""
    return {
        'id':             row['id'],
        'name':           row['name'],
        'deviceType':     row['device_type'],
        'fieldType':      row['field_type'],
        'description':    row['description'] or '',
        'createdAt':      row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
        'updatedAt':      row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
        'inputVariables': row['input_variables'] or [],
        'outputVariable': row['output_variable'] or {},
        'timeStep':       row['time_step'],
        'coordCols':      row['coord_cols'],
        'coordSystem':    row['coord_system'] or 'xyz',
        'dataOrg':        row['data_org'] or 'multicolumn',
        'processConfig':  row['process_config'] or {},
        'pipelineStatus': row['pipeline_status'] or {'cut':False,'split':False,'zscore':False,'pca':False},
        'trainInfo':      row['train_info'],
        'files':          files,
    }

def _file_row_to_dict(r: dict) -> dict:
    return {
        'filename':       r['filename'],
        'role':           r['role'],
        'variableIndex':  r['variable_index'],
        'conditionValue': r['condition_value'],
        'size':           r['file_size'],
        'analysis':       r['analysis'] or {'rows': 0, 'cols': 0},
        'uploadTime':     r['upload_time_str'] or '',
        'storagePath':    r['storage_path'] or '',
    }

def _get_files(conn, ds_id: str) -> list:
    with get_dict_cursor(conn) as cur:
        cur.execute(
            "SELECT * FROM t_dataset_file WHERE dataset_id=%s ORDER BY id",
            (ds_id,)
        )
        return [_file_row_to_dict(r) for r in cur.fetchall()]

def _find_ds(conn, ds_id: str) -> Optional[dict]:
    with get_dict_cursor(conn) as cur:
        cur.execute("SELECT * FROM t_dataset WHERE id=%s", (ds_id,))
        row = cur.fetchone()
    if not row:
        return None
    return _row_to_ds(row, _get_files(conn, ds_id))

def _ds_dir(ds_id):
    return os.path.join(DATASETS_DIR, ds_id)

# ───────────── Pydantic 请求模型 ─────────────

class CreateDatasetBody(BaseModel):
    name:           str       = "未命名数据集"
    deviceType:     str       = "other"
    fieldType:      str       = "other"
    description:    str       = ""
    inputVariables: List[Any] = []
    outputVariable: dict      = {}
    timeStep:       float     = 0.0005
    coordCols:      int       = 3
    coordSystem:    str       = "xyz"
    dataOrg:        str       = "multicolumn"
    t0:             float     = 0.04
    tEnd:           float     = 0.1

class ProcessBody(BaseModel):
    step:   str  = ""
    params: dict = {}


STORAGE_TEMPLATE_MAP = {
    "multicolumn": "单文件多时步模板",
    "perfile": "逐工况多文件模板",
    "separated": "输入输出分离模板",
    "custom": "自定义模板",
}

# ───────────── 元数据接口 ─────────────

@router.get('/types')
def get_types():
    return {"deviceTypes": DEVICE_TYPES, "fieldTypes": FIELD_TYPES}


@router.get('/storage/templates')
def list_storage_templates():
    return {
        "templates": [
            {"key": k, "name": v}
            for k, v in STORAGE_TEMPLATE_MAP.items()
        ]
    }


@router.get('/storage/files')
def list_storage_files(template: Optional[str] = None, folder: Optional[str] = None):
    """获取指定模板和文件夹下的文件列表（只返回当前文件夹的文件，不递归）"""
    base = "template_storage/"
    prefix = f"{base}{template}/" if template else base

    # 如果指定了文件夹，添加到前缀
    if folder and folder != '/':
        folder_path = folder.strip('/')
        prefix = f"{prefix}{folder_path}/"

    try:
        all_files = storage.list_files(prefix)
    except Exception:
        all_files = []

    items = []
    for p in sorted(all_files):
        if p.endswith('/'):
            continue

        # 只返回当前文件夹的文件，不包含子文件夹的文件
        rel = p[len(prefix):] if p.startswith(prefix) else p

        # 如果路径中还包含 '/'，说明是子文件夹中的文件，跳过
        if '/' in rel:
            continue

        filename = rel

        # 获取完整的相对路径（从base开始）
        full_rel = p[len(base):] if p.startswith(base) else p
        parts = full_rel.split('/')
        if len(parts) < 2:
            continue
        template_key = parts[0]

        meta = storage.get_metadata(p)
        items.append({
            "template": template_key,
            "filename": filename,
            "path": p,
            "size": int(meta.size) if meta else None,
            "modified_at": meta.modified_at.strftime('%Y-%m-%d %H:%M:%S') if meta else None,
        })
    return {"files": items}


@router.post('/storage/upload')
async def upload_storage_file(
    file: UploadFile = File(...),
    template: str = Form("custom"),
    folder: str = Form("/"),
):
    if template not in STORAGE_TEMPLATE_MAP:
        return JSONResponse(status_code=400, content={"error": "未知模板类型"})
    filename = file.filename
    contents = await file.read()
    # 支持文件夹路径
    folder_path = folder.strip('/') if folder and folder != '/' else ''
    if folder_path:
        remote_path = f"template_storage/{template}/{folder_path}/{filename}"
    else:
        remote_path = f"template_storage/{template}/{filename}"
    try:
        storage.save_bytes(contents, remote_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"上传失败: {str(e)}"})
    return {"message": "上传成功", "path": remote_path}


@router.get('/storage/folders')
def list_storage_folders(template: Optional[str] = None):
    """获取指定模板下的文件夹树形结构"""
    if not template or template not in STORAGE_TEMPLATE_MAP:
        return {"tree": [{"name": "根目录", "path": "/", "fileCount": 0, "children": []}]}

    base = f"template_storage/{template}/"
    try:
        all_files = storage.list_files(base)
    except Exception:
        return {"tree": [{"name": "根目录", "path": "/", "fileCount": 0, "children": []}]}

    # 构建文件夹树
    folders = {}  # path -> {name, path, children, fileCount}

    for file_path in all_files:
        if not file_path.startswith(base):
            continue
        rel_path = file_path[len(base):]
        if not rel_path:
            continue

        parts = rel_path.split('/')
        # 构建文件夹路径
        current_path = ""
        for i, part in enumerate(parts[:-1]):  # 排除文件名
            parent_path = current_path
            current_path = f"{current_path}/{part}" if current_path else part

            if current_path not in folders:
                folders[current_path] = {
                    "name": part,
                    "path": f"/{current_path}",
                    "fileCount": 0,
                    "children": []
                }

        # 统计文件数量
        if len(parts) > 1:
            folder_path = '/'.join(parts[:-1])
            if folder_path in folders:
                folders[folder_path]["fileCount"] += 1

    # 构建树形结构
    def build_tree(parent_path=""):
        children = []
        for path, folder in folders.items():
            # 检查是否是直接子文件夹
            if parent_path == "":
                # 根级别
                if '/' not in path:
                    folder["children"] = build_tree(path)
                    children.append(folder)
            else:
                # 子级别
                if path.startswith(parent_path + '/'):
                    remaining = path[len(parent_path)+1:]
                    if '/' not in remaining:
                        folder["children"] = build_tree(path)
                        children.append(folder)
        return sorted(children, key=lambda x: x["name"])

    tree = build_tree()

    # 如果没有文件夹，返回根目录
    if not tree:
        tree = []

    # 添加根目录
    root_file_count = sum(1 for f in all_files if f.startswith(base) and '/' not in f[len(base):].strip('/'))
    root = {
        "name": "根目录",
        "path": "/",
        "fileCount": root_file_count,
        "children": tree
    }

    return {"tree": [root]}


@router.post('/storage/folder/create')
async def create_storage_folder(request: Request):
    """创建文件夹（虚拟操作，文件夹在上传文件时自动创建）"""
    body = await request.json()
    template = body.get("template")
    parent_path = body.get("parentPath", "/")
    name = body.get("name", "").strip()

    if not template or template not in STORAGE_TEMPLATE_MAP:
        return JSONResponse(status_code=400, content={"error": "未知模板类型"})

    if not name or '/' in name:
        return JSONResponse(status_code=400, content={"error": "文件夹名称不能为空或包含斜杠"})

    # 构建文件夹路径
    parent_path = parent_path.strip('/')
    if parent_path:
        folder_path = f"{parent_path}/{name}"
    else:
        folder_path = name

    # 对象存储中的文件夹是虚拟的，不需要实际创建
    # 当用户上传文件到这个路径时，文件夹会自动存在
    # 这里只是验证路径格式并返回成功
    return {"message": "文件夹创建成功", "path": f"/{folder_path}"}


@router.post('/storage/folder/rename')
async def rename_storage_folder(request: Request):
    """重命名文件夹"""
    body = await request.json()
    template = body.get("template")
    old_path = body.get("oldPath", "").strip('/')
    new_name = body.get("newName", "").strip()

    if not template or template not in STORAGE_TEMPLATE_MAP:
        return JSONResponse(status_code=400, content={"error": "未知模板类型"})

    if not new_name or '/' in new_name:
        return JSONResponse(status_code=400, content={"error": "文件夹名称不能为空或包含斜杠"})

    # 构建新路径
    parts = old_path.split('/')
    parts[-1] = new_name
    new_path = '/'.join(parts)

    base = f"template_storage/{template}/"
    old_prefix = f"{base}{old_path}/"
    new_prefix = f"{base}{new_path}/"

    try:
        # 获取所有需要移动的文件
        all_files = storage.list_files(old_prefix)

        # 移动文件
        for old_file_path in all_files:
            if old_file_path.startswith(old_prefix):
                rel_path = old_file_path[len(old_prefix):]
                new_file_path = f"{new_prefix}{rel_path}"

                # 复制文件
                content = storage.load_bytes(old_file_path)
                storage.save_bytes(content, new_file_path)

                # 删除旧文件
                storage.delete(old_file_path)

        return {"message": "重命名成功"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"重命名失败: {str(e)}"})


@router.post('/storage/folder/delete')
async def delete_storage_folder(request: Request):
    """删除文件夹"""
    body = await request.json()
    template = body.get("template")
    path = body.get("path", "").strip('/')

    if not template or template not in STORAGE_TEMPLATE_MAP:
        return JSONResponse(status_code=400, content={"error": "未知模板类型"})

    if not path:
        return JSONResponse(status_code=400, content={"error": "不能删除根目录"})

    base = f"template_storage/{template}/"
    folder_prefix = f"{base}{path}/"

    try:
        # 获取所有需要删除的文件
        all_files = storage.list_files(folder_prefix)

        # 删除所有文件
        for file_path in all_files:
            if file_path.startswith(folder_prefix):
                storage.delete(file_path)

        return {"message": "删除成功"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"删除失败: {str(e)}"})


@router.post('/storage/file/rename')
async def rename_storage_file(request: Request):
    """重命名文件"""
    body = await request.json()
    old_path = body.get("oldPath", "")
    new_filename = body.get("newFilename", "").strip()

    if not new_filename:
        return JSONResponse(status_code=400, content={"error": "文件名不能为空"})

    # 构建新路径
    parts = old_path.rsplit('/', 1)
    if len(parts) == 2:
        new_path = f"{parts[0]}/{new_filename}"
    else:
        new_path = new_filename

    try:
        # 复制文件
        content = storage.load_bytes(old_path)
        storage.save_bytes(content, new_path)

        # 删除旧文件
        storage.delete(old_path)

        return {"message": "重命名成功"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"重命名失败: {str(e)}"})


@router.post('/storage/file/delete')
async def delete_storage_file(request: Request):
    """删除文件"""
    body = await request.json()
    path = body.get("path", "")

    if not path:
        return JSONResponse(status_code=400, content={"error": "文件路径不能为空"})

    try:
        storage.delete(path)
        return {"message": "删除成功"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"删除失败: {str(e)}"})


@router.post('/storage/file/move')
async def move_storage_files(request: Request):
    """移动文件"""
    body = await request.json()
    template = body.get("template")
    files = body.get("files", [])
    target_path = body.get("targetPath", "/").strip('/')

    if not template or template not in STORAGE_TEMPLATE_MAP:
        return JSONResponse(status_code=400, content={"error": "未知模板类型"})

    base = f"template_storage/{template}/"

    try:
        for file_path in files:
            # 获取文件名
            filename = file_path.split('/')[-1]

            # 构建新路径
            if target_path:
                new_path = f"{base}{target_path}/{filename}"
            else:
                new_path = f"{base}{filename}"

            # 复制文件
            content = storage.load_bytes(file_path)
            storage.save_bytes(content, new_path)

            # 删除旧文件
            storage.delete(file_path)

        return {"message": f"成功移动 {len(files)} 个文件"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"移动失败: {str(e)}"})


@router.get('/storage/download')
def download_storage_file(path: str):
    """下载文件"""
    try:
        content = storage.load_bytes(path)
        filename = path.split('/')[-1]
        from fastapi.responses import StreamingResponse
        import io
        return StreamingResponse(
            io.BytesIO(content),
            media_type='application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"下载失败: {str(e)}"})


@router.get('/list')
def list_datasets():
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("SELECT * FROM t_dataset ORDER BY created_at DESC")
            rows = cur.fetchall()
        result = []
        for row in rows:
            result.append(_row_to_ds(row, _get_files(conn, row['id'])))
        return {"datasets": result}
    finally:
        conn.close()


@router.post('/create')
def create_dataset(body: CreateDatasetBody):
    ds_id = 'ds_' + uuid.uuid4().hex[:8]
    process_config = {
        't0': body.t0, 'tEnd': body.tEnd, 'dt': body.timeStep,
        'splitRatio': 0.8, 'pcaComponents': 60,
    }
    pipeline_status = {'cut': False, 'split': False, 'zscore': False, 'pca': False}

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO t_dataset
                    (id, name, device_type, field_type, description,
                     input_variables, output_variable, time_step, coord_cols,
                     coord_system, data_org, process_config, pipeline_status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
            """, (
                ds_id, body.name, body.deviceType, body.fieldType, body.description,
                json.dumps(body.inputVariables), json.dumps(body.outputVariable),
                body.timeStep, body.coordCols, body.coordSystem, body.dataOrg,
                json.dumps(process_config), json.dumps(pipeline_status),
            ))
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    for sub in ('raw', 'data', 'pca_result', 'model', 'result'):
        os.makedirs(os.path.join(_ds_dir(ds_id), sub), exist_ok=True)

    dataset = _row_to_ds(row, [])
    return {"message": "数据集创建成功", "dataset": dataset}


# ───────────── 动态路由 ─────────────

@router.get('/{ds_id}')
def get_dataset(ds_id: str):
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})
    return {"dataset": ds}


@router.get('/{ds_id}/storage/tree')
def get_dataset_storage_tree(ds_id: str):
    """返回数据集在存储层的目录树（用于前端资源管理器）"""
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    base_prefix = f"datasets/{ds_id}/"
    fixed_dirs = ['raw/', 'data/', 'pca_result/', 'model/', 'result/']
    paths = set(fixed_dirs)

    try:
        all_files = storage.list_files(base_prefix)
    except Exception:
        all_files = []

    for full_path in all_files:
        if not full_path.startswith(base_prefix):
            continue
        rel = full_path[len(base_prefix):].strip('/')
        if not rel:
            continue
        parts = rel.split('/')
        cur = ""
        for idx, part in enumerate(parts):
            cur = f"{cur}/{part}" if cur else part
            if idx < len(parts) - 1:
                paths.add(cur + '/')
            else:
                paths.add(cur)

    role_map = {}
    for f in ds.get('files', []):
        role_map[f.get('filename')] = f.get('role') or 'unknown'

    items = []
    for rel_path in sorted(paths):
        is_dir = rel_path.endswith('/')
        item = {
            "path": rel_path,
            "name": rel_path.strip('/').split('/')[-1] if rel_path else "",
            "type": "dir" if is_dir else "file",
            "size": None,
            "modified_at": None,
            "role": None,
        }
        if not is_dir:
            meta = storage.get_metadata(base_prefix + rel_path)
            if meta:
                item["size"] = int(meta.size)
                item["modified_at"] = meta.modified_at.strftime('%Y-%m-%d %H:%M:%S')
            if rel_path.startswith('raw/'):
                item["role"] = role_map.get(rel_path.split('/')[-1])
        items.append(item)

    return {
        "dataset_id": ds_id,
        "base": base_prefix,
        "items": items,
    }


@router.put('/{ds_id}')
async def update_dataset_api(ds_id: str, request: Request):
    patch = await request.json()
    # 允许更新的字段映射（camelCase → snake_case）
    field_map = {
        'name': 'name', 'description': 'description',
        'deviceType': 'device_type', 'fieldType': 'field_type',
        'timeStep': 'time_step', 'coordCols': 'coord_cols',
        'coordSystem': 'coord_system', 'dataOrg': 'data_org',
        'inputVariables': 'input_variables', 'outputVariable': 'output_variable',
        'processConfig': 'process_config', 'pipelineStatus': 'pipeline_status',
        'trainInfo': 'train_info',
    }
    sets, params = ["updated_at=NOW()"], []
    for key, col in field_map.items():
        if key in patch:
            val = patch[key]
            sets.append(f"{col}=%s")
            params.append(json.dumps(val) if isinstance(val, (dict, list)) else val)
    if len(sets) == 1:
        conn = get_conn()
        try:
            ds = _find_ds(conn, ds_id)
        finally:
            conn.close()
        return {"message": "无变更", "dataset": ds}

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(
                f"UPDATE t_dataset SET {','.join(sets)} WHERE id=%s RETURNING *",
                params + [ds_id]
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            return JSONResponse(status_code=404, content={"error": "数据集不存在"})
        ds = _row_to_ds(row, _get_files(conn, ds_id))
    finally:
        conn.close()
    return {"message": "更新成功", "dataset": ds}


@router.delete('/{ds_id}')
def delete_dataset(ds_id: str):
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("DELETE FROM t_dataset WHERE id=%s RETURNING id", (ds_id,))
            if not cur.fetchone():
                return JSONResponse(status_code=404, content={"error": "数据集不存在"})
        conn.commit()
    finally:
        conn.close()
    d = _ds_dir(ds_id)
    if os.path.exists(d):
        shutil.rmtree(d)
    return {"message": "数据集已删除"}


@router.post('/{ds_id}/import-storage')
async def import_storage_file_to_dataset(ds_id: str, request: Request):
    body = await request.json()
    src_path = (body.get("path") or "").strip()
    role = body.get("role") or "unknown"
    variable_index = body.get("variableIndex")
    condition_value = body.get("conditionValue")
    if not src_path.startswith("template_storage/"):
        return JSONResponse(status_code=400, content={"error": "非法源文件路径"})

    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "鏁版嵁闆嗕笉瀛樺湪"})

    filename = os.path.basename(src_path)
    dst_path = f"datasets/{ds_id}/raw/{filename}"

    try:
        contents = storage.load_bytes(src_path)
        storage.save_bytes(contents, dst_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"文件导入失败: {str(e)}"})

    suggested = _parse_file_header(contents, filename)
    analysis = {'rows': 0, 'cols': 0}
    try:
        arr = np.loadtxt(io.BytesIO(contents), comments='%')
        analysis = {
            'rows': int(arr.shape[0]),
            'cols': int(arr.shape[1]) if arr.ndim > 1 else 1
        }
    except Exception:
        pass

    vi = int(variable_index) if variable_index is not None else None
    cv = None
    if condition_value is not None:
        try:
            cv = float(condition_value)
        except Exception:
            cv = None
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(
                "DELETE FROM t_dataset_file WHERE dataset_id=%s AND filename=%s",
                (ds_id, filename)
            )
            cur.execute("""
                INSERT INTO t_dataset_file
                    (dataset_id, filename, role, variable_index, condition_value,
                     file_size, analysis, storage_path, upload_time_str)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
            """, (
                ds_id, filename, role, vi, cv,
                len(contents), json.dumps(analysis),
                dst_path, now_str,
            ))
            frow = cur.fetchone()
        conn.commit()
        file_info = _file_row_to_dict(frow)
    finally:
        conn.close()
    return {"message": "导入成功", "file": file_info, "analysis": analysis, "suggested": suggested}


@router.post('/{ds_id}/upload')
async def upload_to_dataset(
    ds_id: str,
    file: UploadFile = File(...),
    role: str = Form("unknown"),
    variableIndex: Optional[str] = Form(None),
    conditionValue: Optional[str] = Form(None),
):
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    filename    = file.filename
    remote_path = f'datasets/{ds_id}/raw/{filename}'
    contents    = await file.read()

    try:
        storage.save_bytes(contents, remote_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"文件保存失败: {str(e)}"})

    # ── 解析文件头，推断列结构 ──
    suggested = _parse_file_header(contents, filename)

    # 分析文件
    analysis = {'rows': 0, 'cols': 0}
    try:
        arr = np.loadtxt(io.BytesIO(contents), comments='%')
        analysis = {
            'rows': int(arr.shape[0]),
            'cols': int(arr.shape[1]) if arr.ndim > 1 else 1
        }
    except Exception as e:
        print(f"[dataset] 文件分析警告: {e}")

    # 解析 conditionValue
    cv = None
    if conditionValue is not None:
        try: cv = float(conditionValue)
        except: pass
    if cv is None and ds.get('dataOrg') == 'perfile':
        import re
        # 支持 "100[A].txt" / "100A.txt" / "val_100.5.txt" 等格式，提取第一个数字串
        m = re.search(r'(\d+(?:\.\d+)?)', filename)
        if m:
            try: cv = float(m.group(1))
            except: pass

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    vi      = int(variableIndex) if variableIndex is not None else None

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            # 先删已有同名记录
            cur.execute(
                "DELETE FROM t_dataset_file WHERE dataset_id=%s AND filename=%s",
                (ds_id, filename)
            )
            cur.execute("""
                INSERT INTO t_dataset_file
                    (dataset_id, filename, role, variable_index, condition_value,
                     file_size, analysis, storage_path, upload_time_str)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
            """, (
                ds_id, filename, role, vi, cv,
                len(contents), json.dumps(analysis),
                remote_path, now_str,
            ))
            frow = cur.fetchone()

            # 同步更新 outputVariable.spatialPoints
            if role == 'output' and analysis['rows'] > 0 and ds.get('dataOrg') != 'perfile':
                cur.execute(
                    "UPDATE t_dataset SET output_variable = output_variable || %s WHERE id=%s",
                    (json.dumps({'spatialPoints': analysis['rows']}), ds_id)
                )
            if ds.get('dataOrg') == 'perfile':
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM t_dataset_file WHERE dataset_id=%s AND role='output'",
                    (ds_id,)
                )
                n_cond = cur.fetchone()['cnt']
                cur.execute(
                    "UPDATE t_dataset SET output_variable = output_variable || %s WHERE id=%s",
                    (json.dumps({'conditionCount': n_cond, 'spatialPoints': analysis['rows']}), ds_id)
                )
        conn.commit()
        file_info = _file_row_to_dict(frow)
    finally:
        conn.close()

    return {"message": f"{filename} 上传成功", "file": file_info, "analysis": analysis, "suggested": suggested}


@router.delete('/{ds_id}/files/{filename}')
def delete_file(ds_id: str, filename: str):
    remote_path = f'datasets/{ds_id}/raw/{filename}'
    try:
        storage.delete(remote_path)
    except Exception as e:
        print(f"[dataset] 删除文件警告: {e}")

    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(
                "DELETE FROM t_dataset_file WHERE dataset_id=%s AND filename=%s",
                (ds_id, filename)
            )
        conn.commit()
    finally:
        conn.close()
    return {"message": f"{filename} 已删除"}


@router.post('/{ds_id}/import-storage')
async def import_from_storage(ds_id: str, request: Request):
    """从数据存储导入文件到数据集"""
    body = await request.json()
    path = body.get('path')
    role = body.get('role', 'unknown')

    if not path:
        return JSONResponse(status_code=400, content={"error": "缺少文件路径"})

    # 检查数据集是否存在
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()

    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    # 从数据存储下载文件
    try:
        contents = storage.load_bytes(path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"读取文件失败: {str(e)}"})

    # 提取文件名
    filename = path.split('/')[-1]

    # 保存到数据集的raw目录
    remote_path = f'datasets/{ds_id}/raw/{filename}'
    try:
        storage.save_bytes(contents, remote_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"保存文件失败: {str(e)}"})

    # 解析文件头，推断列结构
    suggested = _parse_file_header(contents, filename)

    # 分析文件
    analysis = {'rows': 0, 'cols': 0}
    try:
        arr = np.loadtxt(io.BytesIO(contents), comments='%')
        analysis = {
            'rows': int(arr.shape[0]),
            'cols': int(arr.shape[1]) if arr.ndim > 1 else 1
        }
    except Exception as e:
        print(f"[dataset] 文件分析警告: {e}")

    # 解析 conditionValue（针对perfile模式）
    cv = None
    if ds.get('dataOrg') == 'perfile':
        import re
        m = re.search(r'(\d+(?:\.\d+)?)', filename)
        if m:
            try:
                cv = float(m.group(1))
            except:
                pass

    # 保存文件记录到数据库
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            var_idx = None
            if role == 'input':
                var_idx = 0  # 默认第一个输入变量

            cur.execute("""
                INSERT INTO t_dataset_file
                (dataset_id, filename, role, variable_index, condition_value, file_size, analysis, storage_path, upload_time_str)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW()::text)
                RETURNING *
            """, (
                ds_id, filename, role, var_idx, cv,
                len(contents), json.dumps(analysis), remote_path
            ))
            frow = cur.fetchone()

            # 更新数据集的 outputVariable.spatialPoints
            if role == 'output' and analysis.get('rows'):
                cur.execute(
                    "UPDATE t_dataset SET output_variable = output_variable || %s WHERE id=%s",
                    (json.dumps({'spatialPoints': analysis['rows']}), ds_id)
                )

            # 更新 perfile 模式的工况数量
            if ds.get('dataOrg') == 'perfile':
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM t_dataset_file WHERE dataset_id=%s AND role='output'",
                    (ds_id,)
                )
                n_cond = cur.fetchone()['cnt']
                cur.execute(
                    "UPDATE t_dataset SET output_variable = output_variable || %s WHERE id=%s",
                    (json.dumps({'conditionCount': n_cond, 'spatialPoints': analysis['rows']}), ds_id)
                )

        conn.commit()
        file_info = _file_row_to_dict(frow)
    finally:
        conn.close()

    return {
        "message": f"{filename} 导入成功",
        "file": file_info,
        "analysis": analysis,
        "suggested": suggested
    }


@router.put('/{ds_id}/files/{filename}/role')
async def update_file_role(ds_id: str, filename: str, request: Request):
    body = await request.json()
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute("""
                UPDATE t_dataset_file
                SET role=%s, variable_index=%s, condition_value=%s
                WHERE dataset_id=%s AND filename=%s
            """, (
                body.get('role'),
                body.get('variableIndex'),
                body.get('conditionValue'),
                ds_id, filename,
            ))
        conn.commit()
    finally:
        conn.close()
    return {"message": "角色已更新"}


@router.post('/{ds_id}/process')
def process_dataset(ds_id: str, body: ProcessBody):
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    data_dir = os.path.join(_ds_dir(ds_id), 'data')
    pca_dir  = os.path.join(_ds_dir(ds_id), 'pca_result')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(pca_dir,  exist_ok=True)

    try:
        if body.step == 'cut':
            return _step_cut(ds, data_dir, body.params)
        elif body.step == 'split':
            return _step_split(ds, data_dir, body.params)
        elif body.step == 'normalize':
            return _step_normalize(ds, data_dir, body.params)
        elif body.step == 'pca':
            return _step_pca(ds, data_dir, pca_dir, body.params)
        else:
            return JSONResponse(status_code=400, content={"error": f"未知步骤: {body.step}"})
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@router.get('/{ds_id}/status')
def get_status(ds_id: str):
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    dd = os.path.join(_ds_dir(ds_id), 'data')
    pd = os.path.join(_ds_dir(ds_id), 'pca_result')

    def _exists(*names, base=dd):
        return all(os.path.isfile(os.path.join(base, n)) for n in names)

    pipeline = {
        'cut':    {'done': _exists('cutInput.txt', 'cutOutput.txt')},
        'split':  {'done': _exists('trainInput.txt', 'trainOutput.txt', 'testInput.txt', 'testOutput.txt')},
        'zscore': {'done': _exists('zstrainInput.txt', 'zstestInput.txt')},
        'pca':    {'done': _exists('trainPCA.txt', 'testPCA.txt') and _exists('mean_pca.txt', base=pd)},
    }
    ready      = all(v['done'] for v in pipeline.values())
    train_info = ds.get('trainInfo')

    if ready and not train_info:
        try:
            zsX  = np.loadtxt(os.path.join(dd, 'zstrainInput.txt'))
            zsXt = np.loadtxt(os.path.join(dd, 'zstestInput.txt'))
            trP  = np.loadtxt(os.path.join(dd, 'trainPCA.txt'))
            trY  = np.loadtxt(os.path.join(dd, 'trainOutput.txt'))
            train_info = {
                'trainSamples': int(zsX.shape[0]),
                'testSamples':  int(zsXt.shape[0]),
                'inputDim':     int(zsX.shape[1]) if zsX.ndim > 1 else 1,
                'outputDim':    int(trP.shape[1]) if trP.ndim > 1 else 1,
                'rawOutputDim': int(trY.shape[1]) if trY.ndim > 1 else 1,
                'trainRatio':   round(zsX.shape[0] / (zsX.shape[0] + zsXt.shape[0]), 2),
            }
            _pg_update(ds_id, {'trainInfo': train_info})
        except Exception:
            pass

    return {
        'pipeline':      pipeline,
        'ready':         ready,
        'trainInfo':     train_info,
        'processConfig': ds.get('processConfig', {}),
    }


@router.post('/{ds_id}/auto-detect')
def auto_detect(ds_id: str):
    conn = get_conn()
    try:
        ds = _find_ds(conn, ds_id)
    finally:
        conn.close()
    if not ds:
        return JSONResponse(status_code=404, content={"error": "数据集不存在"})

    input_files = [f for f in ds.get('files', []) if f['role'] == 'input']
    if not input_files:
        return JSONResponse(status_code=400, content={"error": "未找到输入数据文件"})

    remote_path = f"datasets/{ds_id}/raw/{input_files[0]['filename']}"
    try:
        file_data = storage.load_bytes(remote_path)
        data = np.loadtxt(io.BytesIO(file_data), comments='%')
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"读取文件失败: {str(e)}"})

    signal = data[:, 1] if data.ndim > 1 else data
    dt             = float(ds.get('timeStep', 0.0005))
    period_samples = int(round(1.0 / 50 / dt))
    n              = len(signal)

    best_t0, best_score = 0.0, float('inf')
    for start in range(0, n - 2 * period_samples, period_samples // 4):
        c1, c2 = signal[start:start+period_samples], signal[start+period_samples:start+2*period_samples]
        if len(c1) != len(c2): continue
        rmse = float(np.sqrt(np.mean((c1 - c2) ** 2)))
        if rmse < best_score:
            best_score, best_t0 = rmse, start * dt

    return {
        "t0":            round(best_t0, 4),
        "suggested_msg": f"检测到稳态起始约 {best_t0:.4f}s (相邻周期 RMSE={best_score:.6f})"
    }


# ───────────── PG 更新工具 ─────────────

def _pg_update(ds_id: str, patch: dict):
    """将 patch dict 中的键更新到 t_dataset，支持 camelCase"""
    field_map = {
        'name': 'name', 'description': 'description',
        'deviceType': 'device_type', 'fieldType': 'field_type',
        'timeStep': 'time_step', 'coordCols': 'coord_cols',
        'coordSystem': 'coord_system', 'dataOrg': 'data_org',
        'inputVariables': 'input_variables', 'outputVariable': 'output_variable',
        'processConfig': 'process_config', 'pipelineStatus': 'pipeline_status',
        'trainInfo': 'train_info',
    }
    sets, params = ["updated_at=NOW()"], []
    for key, col in field_map.items():
        if key in patch:
            val = patch[key]
            sets.append(f"{col}=%s")
            params.append(json.dumps(val) if isinstance(val, (dict, list)) else val)
    if len(sets) == 1:
        return
    conn = get_conn()
    try:
        with get_dict_cursor(conn) as cur:
            cur.execute(
                f"UPDATE t_dataset SET {','.join(sets)} WHERE id=%s",
                params + [ds_id]
            )
        conn.commit()
    finally:
        conn.close()


# ───────────── 文件头自动解析 ─────────────

_FIELD_KEYWORDS = [
    (['normb', 'b_norm', 'mf.normb', 'magnetic', 'normB'],  ('磁通密度', 'T')),
    (['bx', 'by', 'bz'],                                      ('磁通密度分量', 'T')),
    (['temperature', 'temp', 'ht.t'],                         ('温度', '°C')),
    (['norme', 'e_norm', 'es.norme', 'electric'],             ('电场强度', 'V/m')),
    (['stress', 'solid.mises', 'vonmises', 'mises'],          ('等效应力', 'Pa')),
    (['velocity', 'spf.u', 'u_mag', 'speed'],                 ('流速', 'm/s')),
]
_COORD_KEYWORDS = {'x', 'y', 'z', 'r', 'coord.x', 'coord.y', 'coord.z', 'r-coordinate', 'z-coordinate'}


def _parse_unit_from_col(col: str) -> str:
    import re
    m = re.search(r'\(([^)]+)\)', col)
    return m.group(1).strip() if m else ''


def _col_base(col: str) -> str:
    import re
    return re.sub(r'\s*\([^)]*\)', '', col).strip().lower()


def _parse_file_header(contents: bytes, filename: str) -> dict:
    """解析 txt/csv 文件头，返回推断的配置建议"""
    import re, csv as csv_mod

    result = {
        'coordCols': None, 'coordSystem': None,
        'outputVariable': None, 'columns': [],
        'conditionValue': None, 'conditionSource': None,
        'warnings': [],
    }

    try:
        text = contents.decode('utf-8', errors='replace')
    except Exception:
        return result

    lines = text.splitlines()
    comment_lines = [l.strip() for l in lines if l.strip().startswith('%')]

    # ── 1. 从注释行提取工况值（优先级最高）──
    # 模式 A: "% Table: mf.normB (T) @ I=100 (A)" 或 "@ I=100[A]"
    for cl in comment_lines:
        m = re.search(r'@\s*\w+\s*=\s*([\d.]+)', cl)
        if m:
            result['conditionValue'] = float(m.group(1))
            result['conditionSource'] = 'file_header_table'
            break

    # 模式 B: "% Parameter:  I=100" 或 "% I (A) = 100"
    if result['conditionValue'] is None:
        for cl in comment_lines:
            m = re.search(r'(?:parameter|param)[:\s]+\w+\s*=\s*([\d.]+)', cl, re.IGNORECASE)
            if not m:
                m = re.search(r'\w+\s*\([^)]+\)\s*=\s*([\d.]+)', cl)
            if m:
                result['conditionValue'] = float(m.group(1))
                result['conditionSource'] = 'file_header_param'
                break

    # 模式 C: 注释行里只有数字表格（第一列为参数值）
    if result['conditionValue'] is None:
        for cl in comment_lines:
            stripped = cl.lstrip('%').strip()
            parts = stripped.split()
            if len(parts) >= 2:
                try:
                    val = float(parts[0])
                    # 验证其余列也是数字（说明是数据行）
                    all_num = all(p.replace('.','').replace('-','').replace('e','').replace('E','').replace('+','').isdigit() for p in parts[1:3])
                    if all_num and val != 0:
                        result['conditionValue'] = val
                        result['conditionSource'] = 'file_header_data'
                        break
                except ValueError:
                    pass

    # ── 2. 兜底：从文件名提取工况值 ──
    if result['conditionValue'] is None:
        m = re.search(r'(\d+(?:\.\d+)?)', filename)
        if m:
            result['conditionValue'] = float(m.group(1))
            result['conditionSource'] = 'filename'

    is_csv = filename.lower().endswith('.csv')
    col_names = []

    if is_csv:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            reader = csv_mod.reader([line])
            cols = [c.strip() for c in next(reader)]
            if any(c and not c.replace('.','').replace('-','').replace('e','').replace('E','').replace('+','').isdigit() for c in cols):
                col_names = cols
            break
    else:
        # COMSOL txt：找最后一行以 % 开头且含字母的注释行（通常是列名行）
        header_line = None
        for line in lines:
            s = line.strip()
            if s.startswith('%') and any(c.isalpha() for c in s):
                header_line = s.lstrip('%').strip()
        if header_line:
            col_names = [c.strip() for c in re.split(r'\s{2,}|\t', header_line) if c.strip()]
        else:
            for line in lines:
                s = line.strip()
                if s and not s.startswith('%'):
                    try:
                        n = len(s.split())
                        if n >= 2:
                            result['coordCols'] = n - 1
                            result['coordSystem'] = 'rz' if n - 1 == 2 else 'xyz'
                        result['warnings'].append(f'未找到列名行，按数据列数推断（共 {n} 列，前 {n-1} 列视为坐标）')
                    except Exception:
                        pass
                    break
            return result

    if not col_names:
        return result

    coord_indices, field_indices = [], []
    for i, col in enumerate(col_names):
        base = _col_base(col)
        unit = _parse_unit_from_col(col)
        role = 'unknown'

        if base in _COORD_KEYWORDS or base.split('.')[0] in {'x','y','z','r'}:
            role = 'coord'
            coord_indices.append(i)
        else:
            matched = None
            for keywords, field_info in _FIELD_KEYWORDS:
                if any(kw in base for kw in keywords):
                    matched = field_info
                    break
            role = 'field'
            field_indices.append(i)
            if matched and not unit:
                unit = matched[1]

        result['columns'].append({'name': col, 'unit': unit, 'role': role})

    n_coord = len(coord_indices) or max(0, len(col_names) - max(len(field_indices), 1))
    result['coordCols'] = n_coord

    coord_names_set = {_col_base(col_names[i]).split('(')[0].strip() for i in coord_indices}
    if {'r', 'z'}.issubset(coord_names_set) and 'y' not in coord_names_set:
        result['coordSystem'] = 'rz'
    elif {'x', 'y'}.issubset(coord_names_set) and 'z' not in coord_names_set:
        result['coordSystem'] = 'xy'
    elif n_coord >= 3:
        result['coordSystem'] = 'xyz'
    elif n_coord == 2:
        result['coordSystem'] = 'rz'
    else:
        result['coordSystem'] = 'xyz'

    if field_indices:
        fi = field_indices[0]
        col = col_names[fi]
        base = _col_base(col)
        unit = _parse_unit_from_col(col)
        name = '场量'
        for keywords, field_info in _FIELD_KEYWORDS:
            if any(kw in base for kw in keywords):
                name = field_info[0]
                if not unit:
                    unit = field_info[1]
                break
        result['outputVariable'] = {'name': name, 'unit': unit, 'sourceCol': col}

    return result
def _sync_to_storage(dataset_id: str, local_dir: str, filenames: list, sub: str = "data"):
    """把本地预处理文件同步到存储层（MinIO 或本地副本）。
    sub: MinIO 中的子目录名，如 'data' 或 'pca_result'
    """
    try:
        for fname in filenames:
            local_path = os.path.join(local_dir, fname)
            if os.path.exists(local_path):
                remote_path = f"datasets/{dataset_id}/{sub}/{fname}"
                storage.save_file(local_path, remote_path)
    except Exception as e:
        print(f"[Storage] 同步失败（非致命）: {e}")


# ───────────── 流水线步骤实现 ─────────────

def _step_cut(ds, data_dir, params):
    if ds.get('dataOrg') == 'perfile':
        return _step_cut_perfile(ds, data_dir, params)
    else:
        return _step_cut_multicolumn(ds, data_dir, params)


def _step_cut_perfile(ds, data_dir, params):
    import re
    coord_cols   = int(ds.get('coordCols', 2))
    output_files = sorted(
        [f for f in ds.get('files', []) if f['role'] == 'output'],
        key=lambda x: float(x.get('conditionValue') or 0)
    )
    if not output_files:
        return JSONResponse(status_code=400, content={"error": "未找到「输出」角色文件（逐工况模式）"})

    rows_list, cond_vals = [], []
    coords_saved = False

    for fobj in output_files:
        cv = fobj.get('conditionValue')
        if cv is None:
            m = re.search(r'(\d+(?:\.\d+)?)', fobj['filename'])
            cv = float(m.group(1)) if m else 0.0

        remote_path = f"datasets/{ds['id']}/raw/{fobj['filename']}"
        try:
            arr = np.loadtxt(io.BytesIO(storage.load_bytes(remote_path)), comments='%')
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"读取文件失败 {fobj['filename']}: {e}"})

        if not coords_saved:
            np.savetxt(os.path.join(data_dir, 'coordinates.txt'), arr[:, :coord_cols])
            coords_saved = True

        field_vals = arr[:, coord_cols:]
        row_vals   = field_vals.mean(axis=1) if field_vals.ndim > 1 and field_vals.shape[1] > 1 else field_vals.ravel()
        rows_list.append(row_vals)
        cond_vals.append(cv)

    cut_output = np.array(rows_list)
    cut_input  = np.array(cond_vals).reshape(-1, 1)
    np.savetxt(os.path.join(data_dir, 'cutOutput.txt'), cut_output)
    np.savetxt(os.path.join(data_dir, 'cutInput.txt'),  cut_input)

    _pg_update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'cut': True},
        'outputVariable': {**ds.get('outputVariable', {}), 'spatialPoints': cut_output.shape[1]},
        'processConfig':  {**ds.get('processConfig', {}), 'coordCols': coord_cols},
    })
    # 若 inputVariables 为空（老数据集或用户未填），自动补一条工况变量
    if not ds.get('inputVariables'):
        _pg_update(ds['id'], {'inputVariables': [{'name': '激励量', 'unit': ''}]})
    _sync_to_storage(ds['id'], data_dir, ['cutInput.txt', 'cutOutput.txt', 'coordinates.txt'])
    return {"status": "success", "msg": f"逐工况装配完成：{len(output_files)} 个工况 × {cut_output.shape[1]} 个空间测点，输入工况值：{cond_vals}"}


def _step_cut_multicolumn(ds, data_dir, params):
    t0         = float(params.get('t0',   ds['processConfig']['t0']))
    tEnd       = float(params.get('tEnd', ds['processConfig'].get('tEnd', 0.1)))
    dt         = float(params.get('dt',   ds['processConfig']['dt']))
    coord_cols = int(ds.get('coordCols', 3))

    output_files = [f for f in ds.get('files', []) if f['role'] == 'output']
    if not output_files:
        return JSONResponse(status_code=400, content={"error": "未找到角色为「输出」的数据文件"})

    remote_path = f"datasets/{ds['id']}/raw/{output_files[0]['filename']}"
    try:
        out_data = np.loadtxt(io.BytesIO(storage.load_bytes(remote_path)), comments='%')
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"读取输出文件失败: {e}"})

    n_total_time = out_data.shape[1] - coord_cols
    start_idx    = int(round(t0 / dt))
    end_idx      = min(int(round(tEnd / dt)), n_total_time)
    n_cut        = end_idx - start_idx

    np.savetxt(os.path.join(data_dir, 'coordinates.txt'), out_data[:, :coord_cols])
    cut_output = out_data[:, (coord_cols + start_idx):(coord_cols + end_idx)]
    np.savetxt(os.path.join(data_dir, 'cutOutput.txt'), cut_output)

    input_files  = sorted([f for f in ds.get('files', []) if f['role'] == 'input'],
                           key=lambda x: x.get('variableIndex', 0) or 0)
    input_arrays = []
    for fobj in input_files:
        try:
            arr = np.loadtxt(io.BytesIO(storage.load_bytes(f"datasets/{ds['id']}/raw/{fobj['filename']}")), comments='%')
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"读取输入文件失败 {fobj['filename']}: {e}"})
        vals = arr[:, 1] if arr.ndim > 1 and arr.shape[1] >= 2 else arr
        input_arrays.append(vals[start_idx:end_idx])

    cut_input = np.column_stack(input_arrays) if input_arrays else np.zeros((n_cut, 1))
    np.savetxt(os.path.join(data_dir, 'cutInput.txt'), cut_input)

    _pg_update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'cut': True},
        'processConfig':  {**ds['processConfig'],  't0': t0, 'tEnd': tEnd, 'dt': dt},
    })
    _sync_to_storage(ds['id'], data_dir, ['cutInput.txt', 'cutOutput.txt', 'coordinates.txt'])
    return {"status": "success", "msg": f"截取完成：{n_cut} 个时间步 × {cut_output.shape[0]} 个空间点，输入 {cut_input.shape[1] if cut_input.ndim > 1 else 1} 维"}


def _step_split(ds, data_dir, params):
    ratio      = float(params.get('splitRatio', ds['processConfig']['splitRatio']))
    val_ratio  = float(params.get('valRatio', 0.15))
    cut_input  = np.loadtxt(os.path.join(data_dir, 'cutInput.txt'))
    cut_output = np.loadtxt(os.path.join(data_dir, 'cutOutput.txt'))

    if ds.get('dataOrg') != 'perfile' and cut_output.shape[0] > cut_output.shape[1]:
        cut_output = cut_output.T

    n       = cut_input.shape[0] if cut_input.ndim > 1 else len(cut_input)
    n_train = int(n * ratio)
    n_val   = int(n * val_ratio)
    idx     = np.random.permutation(n)
    tr, val_idx, te = idx[:n_train], idx[n_train:n_train+n_val], idx[n_train+n_val:]

    np.savetxt(os.path.join(data_dir, 'trainInput.txt'),  cut_input[tr])
    np.savetxt(os.path.join(data_dir, 'valInput.txt'),    cut_input[val_idx])
    np.savetxt(os.path.join(data_dir, 'testInput.txt'),   cut_input[te])
    np.savetxt(os.path.join(data_dir, 'trainOutput.txt'), cut_output[tr])
    np.savetxt(os.path.join(data_dir, 'valOutput.txt'),   cut_output[val_idx])
    np.savetxt(os.path.join(data_dir, 'testOutput.txt'),  cut_output[te])

    _pg_update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'split': True},
        'processConfig':  {**ds['processConfig'],  'splitRatio': ratio, 'valRatio': val_ratio},
    })
    _sync_to_storage(ds['id'], data_dir, [
        'trainInput.txt', 'valInput.txt', 'testInput.txt',
        'trainOutput.txt', 'valOutput.txt', 'testOutput.txt',
    ])
    return {"status": "success", "msg": f"划分完成：训练 {len(tr)} / 验证 {len(val_idx)} / 测试 {len(te)} 条"}


def _step_normalize(ds, data_dir, params):
    trX = np.loadtxt(os.path.join(data_dir, 'trainInput.txt'))
    teX = np.loadtxt(os.path.join(data_dir, 'testInput.txt'))
    if trX.ndim == 1:
        trX, teX = trX.reshape(-1, 1), teX.reshape(-1, 1)
    mu    = np.mean(trX, axis=0, keepdims=True)
    sigma = np.std(trX,  axis=0, keepdims=True)
    sigma[sigma == 0] = 1.0
    np.savetxt(os.path.join(data_dir, 'zstrainInput.txt'),      (trX - mu) / sigma)
    np.savetxt(os.path.join(data_dir, 'zstestInput.txt'),       (teX - mu) / sigma)
    np.savetxt(os.path.join(data_dir, 'zstrainmuInput.txt'),    mu)
    np.savetxt(os.path.join(data_dir, 'zstrainsigmaInput.txt'), sigma)
    _pg_update(ds['id'], {'pipelineStatus': {**ds['pipelineStatus'], 'zscore': True}})
    _sync_to_storage(ds['id'], data_dir, [
        'zstrainInput.txt', 'zstestInput.txt',
        'zstrainmuInput.txt', 'zstrainsigmaInput.txt',
    ])
    return {"status": "success", "msg": f"归一化完成：输入 {trX.shape[1]} 维"}


def _step_pca(ds, data_dir, pca_dir, params):
    from sklearn.decomposition import PCA
    n_comp = int(params.get('pcaComponents', ds['processConfig']['pcaComponents']))
    trY    = np.loadtxt(os.path.join(data_dir, 'trainOutput.txt'))
    teY    = np.loadtxt(os.path.join(data_dir, 'testOutput.txt'))

    actual = min(n_comp, trY.shape[1], trY.shape[0])
    pca    = PCA(n_components=actual)
    tr_pca = pca.fit_transform(trY)
    te_pca = np.matmul(teY - pca.mean_, pca.components_.T)

    np.savetxt(os.path.join(data_dir, 'trainPCA.txt'),     tr_pca)
    np.savetxt(os.path.join(data_dir, 'testPCA.txt'),      te_pca)
    np.savetxt(os.path.join(pca_dir,  'mean_pca.txt'),     pca.mean_)
    np.savetxt(os.path.join(pca_dir,  'vector_pca.txt'),   pca.components_)
    np.savetxt(os.path.join(pca_dir,  'variance_pca.txt'), pca.explained_variance_ratio_)

    var_sum = float(pca.explained_variance_ratio_.sum())
    try:
        zsX   = np.loadtxt(os.path.join(data_dir, 'zstrainInput.txt'))
        zsXt  = np.loadtxt(os.path.join(data_dir, 'zstestInput.txt'))
        in_dim = zsX.shape[1] if zsX.ndim > 1 else 1
        train_info = {
            'trainSamples':      int(tr_pca.shape[0]),
            'testSamples':       int(te_pca.shape[0]),
            'inputDim':          int(in_dim),
            'outputDim':         int(actual),
            'rawOutputDim':      int(trY.shape[1]),
            'trainRatio':        round(tr_pca.shape[0] / (tr_pca.shape[0] + te_pca.shape[0]), 2),
            'varianceExplained': round(var_sum, 4),
        }
        _pg_update(ds['id'], {'trainInfo': train_info})
    except Exception:
        pass

    _pg_update(ds['id'], {
        'pipelineStatus': {**ds['pipelineStatus'], 'pca': True},
        'processConfig':  {**ds['processConfig'],  'pcaComponents': actual},
    })
    _sync_to_storage(ds['id'], data_dir, ['trainPCA.txt', 'testPCA.txt'])
    _sync_to_storage(ds['id'], pca_dir,  ['mean_pca.txt', 'vector_pca.txt', 'variance_pca.txt'], sub='pca_result')
    return {"status": "success",
            "msg": f"PCA 降维完成：{trY.shape[1]} → {actual} 维，累计方差解释率 {var_sum*100:.1f}%"}

