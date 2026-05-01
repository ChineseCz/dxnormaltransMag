# 前后端对齐现状报告

> 生成时间：2026-04-18  
> 范围：除 AI 助手模块外的全部服务逻辑

---

## 一、总体评分

| 模块 | 前端 | 后端 | 对齐度 | 问题等级 |
|------|------|------|:------:|:------:|
| 用户鉴权 | ✅ 完整 | ✅ 完整 | ★★★★★ | — |
| 用户/角色/部门管理 | ✅ 完整 | ✅ 完整 | ★★★★★ | — |
| 数据集管理（CRUD + 上传）| ✅ 完整 | ✅ 完整 | ★★★★☆ | 低 |
| 数据处理流水线 | ✅ 完整 | ✅ 完整 | ★★★★☆ | 低 |
| 模型架构设计 | ✅ 完整 | N/A（纯前端配置）| ★★★★★ | — |
| 模型训练任务 | ✅ 完整 | ✅ 已接入真实训练 | ★★★★☆ | 低 |
| **模型仓库** | ⚠️ 硬编码 mock | ✅ 有真实 API | ★★☆☆☆ | **高** |
| **训练结果评估** | ⚠️ 需检查 | ✅ 通过 status 接口 | ★★★☆☆ | 中 |
| **实时预测（realtime）** | ✅ 调用后端 | ⚠️ Mock 随机数 | ★★☆☆☆ | **高** |
| 预测历史/对比 | ✅ localStorage | N/A（纯前端）| ★★★★★ | — |

---

## 二、各模块详细对齐分析

### 2.1 用户鉴权 ✅ 完全对齐

| 前端调用 | 后端路由 | 状态 |
|---------|---------|:----:|
| `POST /api/user/login` | `auth/routes.py → login()` | ✅ |
| `POST /api/user/register` | `auth/routes.py → register()` | ✅ |
| `POST /api/user/logout` | `auth/routes.py → logout()` | ✅ |
| `POST /api/user/refresh` | `auth/routes.py → refresh()` | ✅ |
| `GET  /api/user/me` | `auth/routes.py → me()` | ✅ |

响应字段完全匹配，JWT 鉴权已替换 SHA256。

---

### 2.2 用户/角色/部门管理 ✅ 完全对齐

| 前端调用 | 后端路由 | 状态 |
|---------|---------|:----:|
| `GET /api/user/list` | `user_list()` | ✅ |
| `POST /api/user/create` | `user_create()` | ✅ |
| `PUT /api/user/{id}` | `user_update()` | ✅ |
| `DELETE /api/user/{id}` | `user_delete()` | ✅ |
| `PATCH /api/user/{id}/status` | `user_toggle_status()` | ✅ |
| `GET /api/user/roles` | `role_list()` | ✅ |
| `POST /api/user/roles` | `role_create()` | ✅ |
| `PUT /api/user/roles/{id}` | `role_update()` | ✅ |
| `DELETE /api/user/roles/{id}` | `role_delete()` | ✅ |
| `GET /api/user/depts` | `dept_tree()` | ✅ |
| `POST /api/user/depts` | `dept_create()` | ✅ |
| `PUT /api/user/depts/{id}` | `dept_update()` | ✅ |
| `DELETE /api/user/depts/{id}` | `dept_delete()` | ✅ |

---

### 2.3 数据集管理 ✅ 基本对齐，小差异

| 前端调用 | 后端路由 | 状态 | 备注 |
|---------|---------|:----:|------|
| `GET /api/dataset/list` | `list_datasets()` | ✅ | |
| `POST /api/dataset/create` | `create_dataset()` | ✅ | |
| `GET /api/dataset/{id}` | `get_dataset()` | ✅ | |
| `PUT /api/dataset/{id}` | `update_dataset_api()` | ✅ | |
| `DELETE /api/dataset/{id}` | `delete_dataset()` | ✅ | |
| `POST /api/dataset/{id}/upload` | `upload_to_dataset()` | ✅ | 已修复 WinError 32 |
| `DELETE /api/dataset/{id}/files/{name}` | `delete_file()` | ✅ | |
| `PUT /api/dataset/{id}/files/{name}/role` | `update_file_role()` | ✅ | |
| `POST /api/dataset/{id}/process` | `process_dataset()` | ✅ | step: cut/split/normalize/pca |
| `GET /api/dataset/{id}/status` | `get_status()` | ✅ | |
| `POST /api/dataset/{id}/auto-detect` | `auto_detect()` | ✅ | |
| `GET /api/dataset/types` | `get_types()` | ✅ | |

**⚠️ 残留问题**：
- `api/data/routes.py` 中 `POST /api/data/upload/raw`、`POST /api/data/execute`、`GET /api/data/processed-status` 三个路由是**遗留代码**，指向旧 `core_algorithms` 目录，前端已不再使用，但仍被 `main.py` 注册。建议保留但不影响功能。

---

### 2.4 模型训练 ⚠️ 大部分对齐，模型仓库未接真实 API

#### 模型训练任务 ✅ 已接入

| 前端调用 | 后端路由 | 状态 | 备注 |
|---------|---------|:----:|------|
| `POST /api/model/train` | `train_model()` | ✅ | 支持 DNN/CNN/RF，后台线程训练 |
| `GET /api/model/train/status/{id}` | `get_train_status()` | ✅ | 实时日志 + 进度 |

训练数据要求：`backend/datasets/{id}/data/trainInput.txt` + `trainOutput.txt` + `testInput.txt` + `testOutput.txt`（split 步骤完成后自动生成）。

#### 模型仓库 ❌ 未对齐

**问题**：`ModelManagement.vue` 的 `fetchModels()` 是 `setTimeout` 模拟，数据完全硬编码（3条假数据），`deployModel()`、`downloadModel()` 均无 API 调用。

**后端现有接口**：
- `GET /api/model/list` → 返回 `t_model` 表中所有训练过的真实模型
- `DELETE /api/model/{id}` → 删除模型文件 + 数据库记录

**需要修复**：`ModelManagement.vue` 的 `fetchModels()` 应调用 `GET /api/model/list`。

#### 训练结果评估页 ⚠️ 部分对齐

`ModelEvaluation.vue` 通过轮询 `/api/model/train/status/{id}` 获取训练指标，但模型ID需从 `ModelTrainingTask.vue` 的训练完成回调中传入，当前通过 `localStorage('last_model_id')` 传递，存在页面跳转后丢失的风险。

---

### 2.5 实时预测 ❌ 核心未对齐

#### 当前状态

```
前端 usePredictionStore.runPredict()
  ↓ POST /api/predict/realtime
predict.py → 随机 gauss 延迟 + 随机生成 fieldValues（5个假值）
  ↓ 返回 { status:"success", fieldValues:[...5个随机float] }
前端 PredictResult.vue 渲染假数据
```

#### 期望状态（全链路预测）

```
前端 PredictSetup.vue（选择模型 + 输入激励值）
  ↓ POST /api/predict/realtime { dataset_id, model_id, inputs }
predict.py
  1. 加载 model_dir/{model_file}.pth（PyTorch）或 .pkl（RF）
  2. Z-Score 归一化输入：(x - mu) / sigma  ← 读 zstrainmuInput.txt / zstrainsigmaInput.txt
  3. 模型推理 → 预测 PCA 分量（output_dim 维）
  4. 逆 PCA：pred_full = pred_pca @ components + mean_pca  ← 读 pca_result/
  5. 返回 { coordinates, fieldValues(N_spatial), stats }
前端 PredictResult.vue 渲染 3D 云图
```

**缺失文件**：
- `predict.py` 没有读取 `DATASETS_DIR`，没有模型加载逻辑，没有 PCA 逆变换

---

## 三、待修复优先级列表

### P0 — 必须修复（影响核心功能）

| # | 问题 | 文件 | 改动量 |
|---|------|------|:------:|
| P0-1 | **实时预测全链路**：`predict.py` 接入真实推理（加载模型 → 推理 → 逆PCA → 返回坐标+场值） | `backend/api/ml/predict.py` | 大 |
| P0-2 | **模型仓库对接真实API**：`ModelManagement.vue` `fetchModels()` 调用 `GET /api/model/list`；`deployModel` 设置激活状态；`downloadModel` 提供下载 | `frontend/views/model/ModelManagement.vue` | 中 |

### P1 — 建议修复（功能完善）

| # | 问题 | 文件 | 改动量 |
|---|------|------|:------:|
| P1-1 | `ModelEvaluation.vue` 训练指标应从 `t_model` 表读取（`GET /api/model/list`），而非仅靠上次训练的 localStorage | `frontend/views/model/ModelEvaluation.vue` | 小 |
| P1-2 | `PredictSetup.vue` 应提供模型选择下拉（调 `GET /api/model/list` 过滤 `status=done`），而不是手填 model_file 字符串 | `frontend/views/prediction/PredictSetup.vue` | 中 |
| P1-3 | `api/data/routes.py` 的遗留路由（`/api/data/upload/raw` 等）与前端脱节，可整体注释掉或删除注册 | `backend/main.py` | 极小 |

### P2 — 技术债务（不影响演示）

| # | 问题 | 说明 |
|---|------|------|
| P2-1 | `datasets.json` 与 PostgreSQL `t_dataset` 双写不同步 | 当前通过 `_sync_dataset_to_pg()` 在训练时按需同步，属于补丁方案；长期应在 `create_dataset` 时同时写入 PG |
| P2-2 | 训练 `_training_jobs` 内存字典在服务重启后丢失 | 应持久化到 `t_training_job` 表；现在重启后训练任务状态不可恢复 |
| P2-3 | `predict.py` 中 `SPLIT_OUTPUT_DIR`、`COORD_FILE`、`PRED_FILE` 指向旧 `core_algorithms` 路径，是遗留死代码 | 全链路接入后可一并清理 |

---

## 四、当前可用的完整功能清单

以下功能**已全部打通**，可正常演示：

- ✅ 登录 / 注册 / 登出 / JWT 鉴权
- ✅ 用户管理（增删改查 + 状态切换）
- ✅ 角色管理（增删改查）
- ✅ 部门管理（增删改查 + 树形结构）
- ✅ 数据集创建 / 删除 / 元数据编辑
- ✅ 文件上传到 MinIO（原始 .txt 数据文件）
- ✅ 文件角色分配（input / output / coordinate）
- ✅ 数据处理四步流水线（cut → split → normalize → pca）
- ✅ 稳态自动检测（auto-detect）
- ✅ 模型训练任务提交（DNN / CNN / RF）+ 实时进度轮询
- ✅ 训练日志解析 + Loss 曲线实时渲染

以下功能**后端已就绪，前端 Mock 中**：

- ⚠️ 模型仓库列表（后端 `GET /api/model/list` 有真实数据，前端未调用）
- ⚠️ 实时预测（后端 `POST /api/predict/realtime` 返回随机值，未接真实推理）

---

## 五、实时预测全链路实现方案（P0-1 详细设计）

```
POST /api/predict/realtime
Request: {
  dataset_id: "ds_xxxxxxxx",
  model_id: 123,           // t_model.id
  inputs: [v1, v2, ..., vN] // 激励值（未归一化）
}

后端步骤：
1. 读 DATASETS_DIR/{dataset_id}/data/zstrainmuInput.txt     → mu (1×n_input)
2. 读 DATASETS_DIR/{dataset_id}/data/zstrainsigmaInput.txt  → sigma (1×n_input)
3. x_norm = (inputs - mu) / sigma
4. 读 t_model WHERE id=model_id → file_path, model_type
5a. [DNN/CNN] torch.load(file_path); model.eval(); pred_pca = model(x_norm_tensor)
5b. [RF]      joblib.load(file_path); pred_pca = model.predict(x_norm)
6. 读 DATASETS_DIR/{dataset_id}/pca_result/mean_pca.txt     → pca_mean (N_spatial,)
7. 读 DATASETS_DIR/{dataset_id}/pca_result/vector_pca.txt   → components (n_pca×N_spatial)
8. pred_full = pred_pca @ components + pca_mean             → (N_spatial,)
9. 读 DATASETS_DIR/{dataset_id}/data/coordinates.txt        → coords (N_spatial×3)
10. 返回 { coordinates: [...], fieldValues: [...], stats: {max,min,mean,std} }

前端：
PredictResult.vue 用 WebGL3DScatter 渲染 coordinates + fieldValues 云图
```

---

*本文档基于 2026-04-18 代码快照手动审计，如代码有变更请重新确认。*

