<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#4f46e5,#818cf8); box-shadow:0 0 20px rgba(99,102,241,0.4);">
            <el-icon size="20" style="color:white;"><User /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#818cf8,#a5b4fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            用户管理
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理系统用户账号与权限分配</p>
      </div>
      <button @click="handleAdd"
        class="btn-glow flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#4f46e5,#818cf8); border:1px solid rgba(129,140,248,0.4);">
        <el-icon><Plus /></el-icon>新增用户
      </button>
    </div>

    <el-row :gutter="16">
      <!-- 左：部门树 -->
      <el-col :span="5">
        <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <el-icon style="color:#818cf8;" size="14"><OfficeBuilding /></el-icon>
              <span class="text-slate-300 text-sm font-semibold">部门列表</span>
            </div>
          </template>
          <el-input v-model="filterText" placeholder="搜索部门" size="small" class="mb-3" />
          <el-tree ref="treeRef" :data="deptTree" :props="{ children:'children', label:'deptName' }"
            :filter-node-method="filterNode" default-expand-all highlight-current
            node-key="deptId" @node-click="handleDeptClick" class="dark-tree" />
        </el-card>
      </el-col>

      <!-- 右：搜索+表格 -->
      <el-col :span="19">
        <el-card class="mb-4" style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <el-form :inline="true" class="flex flex-wrap gap-2">
            <el-form-item label="用户名称" class="mb-0">
              <el-input v-model="search.username" placeholder="搜索用户" clearable style="width:200px;" @keyup.enter="loadList" />
            </el-form-item>
            <el-form-item class="mb-0">
              <el-button type="primary" :icon="Search" @click="loadList">搜索</el-button>
              <el-button :icon="Refresh" @click="resetSearch"
                style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <el-table :data="tableData" v-loading="loading" style="width:100%;">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="userId" label="编号" width="80">
              <template #default="s"><span class="font-mono text-slate-400 text-sm">{{ s.row.userId }}</span></template>
            </el-table-column>
            <el-table-column prop="userName" label="用户名">
              <template #default="s"><span class="text-slate-200 font-medium">{{ s.row.userName }}</span></template>
            </el-table-column>
            <el-table-column prop="nickName" label="昵称">
              <template #default="s"><span class="text-slate-300">{{ s.row.nickName }}</span></template>
            </el-table-column>
            <el-table-column prop="dept" label="部门">
              <template #default="s">
                <el-tag size="small" style="background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.3); color:#a5b4fc;">
                  {{ s.row.dept }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="phoneNumber" label="手机" width="130">
              <template #default="s"><span class="font-mono text-slate-400 text-sm">{{ s.row.phoneNumber || '-' }}</span></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="s">
                <el-switch v-model="s.row.status"
                  style="--el-switch-on-color:#3b82f6; --el-switch-off-color:#374151;"
                  @change="(v) => handleStatusChange(s.row, v)" />
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="175">
              <template #default="s"><span class="text-slate-500 text-xs">{{ s.row.createTime }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="s">
                <el-button link type="primary" size="small" @click="handleEdit(s.row)">
                  <el-icon class="mr-0.5"><Edit /></el-icon>修改
                </el-button>
                <el-divider direction="vertical" style="border-color:rgba(51,65,85,0.6);" />
                <el-button link type="danger" size="small" @click="handleDelete(s.row)">
                  <el-icon class="mr-0.5"><Delete /></el-icon>删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="mt-5 flex justify-end">
            <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
              :page-sizes="[10,20,30,50]" layout="total, sizes, prev, pager, next, jumper"
              :total="total" @size-change="loadList" @current-change="loadList"
              style="--el-pagination-bg-color:transparent; --el-pagination-text-color:#94a3b8; --el-pagination-button-color:#94a3b8;" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '修改用户' : '新增用户'" width="520px"
      :close-on-click-modal="false"
      style="--el-dialog-bg-color:rgba(10,18,36,0.97); --el-dialog-border-radius:12px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" class="pr-4">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="3~20位字符" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="选填" />
        </el-form-item>
        <el-form-item :label="isEdit ? '新密码' : '密码'" :prop="isEdit ? '' : 'password'">
          <el-input v-model="form.password" type="password" :placeholder="isEdit ? '不填则不修改' : '至少6位'" show-password />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="选填" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="form.role_id" style="width:100%;">
            <el-option v-for="r in roleOptions" :key="r.roleId" :label="r.roleName" :value="r.roleId" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-tree-select v-model="form.dept_id" :data="deptTree"
            :props="{ label:'deptName', value:'deptId', children:'children' }"
            placeholder="选择部门（选填）" clearable check-strictly style="width:100%;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, Plus, Edit, Delete, User, OfficeBuilding } from '@element-plus/icons-vue';
import { getUserList, createUser, updateUser, deleteUser, toggleUserStatus, getRoleList, getDeptTree } from '../../utils/userApi.js';

// ── 状态 ──────────────────────────────────────────────────
const loading    = ref(false);
const submitting = ref(false);
const tableData  = ref([]);
const total      = ref(0);
const page       = ref(1);
const pageSize   = ref(10);
const search     = ref({ username: '', dept_id: null });
const filterText = ref('');
const treeRef    = ref();
const deptTree   = ref([]);
const roleOptions= ref([]);

// ── 对话框 ────────────────────────────────────────────────
const dialogVisible = ref(false);
const isEdit        = ref(false);
const editId        = ref(null);
const formRef       = ref();
const form          = ref({ username:'', nickname:'', password:'', phone:'', email:'', role_id:2, dept_id:null, status:1 });
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min:3, max:20, message:'3~20位', trigger:'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min:6, message:'至少6位', trigger:'blur' }],
  role_id:  [{ required: true, message: '请选择角色', trigger: 'change' }],
};

// ── 初始化 ────────────────────────────────────────────────
onMounted(() => { loadList(); loadDeptTree(); loadRoles(); });

async function loadList() {
  loading.value = true;
  try {
    const res = await getUserList({ page: page.value, size: pageSize.value, username: search.value.username, dept_id: search.value.dept_id });
    tableData.value = res.list || [];
    total.value     = res.total || 0;
  } catch (e) { ElMessage.error(e.message || '加载失败'); }
  finally { loading.value = false; }
}

async function loadDeptTree() {
  try { const res = await getDeptTree(); deptTree.value = res.list || []; } catch {}
}

async function loadRoles() {
  try { const res = await getRoleList(); roleOptions.value = res.list || []; } catch {}
}

// ── 部门树过滤 ────────────────────────────────────────────
watch(filterText, (v) => treeRef.value?.filter(v));
const filterNode = (val, data) => !val || data.deptName.includes(val);
const handleDeptClick = (data) => {
  search.value.dept_id = data.deptId;
  page.value = 1;
  loadList();
};

// ── CRUD ──────────────────────────────────────────────────
function resetSearch() { search.value = { username:'', dept_id:null }; page.value=1; loadList(); }

function handleAdd() {
  isEdit.value = false; editId.value = null;
  form.value = { username:'', nickname:'', password:'', phone:'', email:'', role_id:2, dept_id:null, status:1 };
  dialogVisible.value = true;
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.userId;
  form.value = { username: row.userName, nickname: row.nickName === row.userName ? '' : row.nickName,
    password:'', phone: row.phoneNumber, email: row.email, role_id: row.roleId,
    dept_id: row.deptId, status: row.status ? 1 : 0 };
  dialogVisible.value = true;
}

async function handleSubmit() {
  await formRef.value.validate();
  submitting.value = true;
  try {
    const payload = { ...form.value };
    if (isEdit.value && !payload.password) delete payload.password;
    if (isEdit.value) {
      await updateUser(editId.value, payload);
      ElMessage.success('更新成功');
    } else {
      await createUser(payload);
      ElMessage.success('创建成功');
    }
    dialogVisible.value = false;
    loadList();
  } catch (e) { ElMessage.error(e.message || '操作失败'); }
  finally { submitting.value = false; }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.userName}」？`, '警告', { type:'warning' });
  try { await deleteUser(row.userId); ElMessage.success('删除成功'); loadList(); }
  catch (e) { ElMessage.error(e.message || '删除失败'); }
}

async function handleStatusChange(row, val) {
  try { await toggleUserStatus(row.userId, val); }
  catch (e) { row.status = !val; ElMessage.error(e.message || '操作失败'); }
}
</script>

<style scoped>
:deep(.dark-tree) { background:transparent !important; color:#cbd5e1; }
:deep(.dark-tree .el-tree-node__content) { border-radius:6px !important; height:34px !important; font-size:13px !important; color:#cbd5e1 !important; }
:deep(.dark-tree .el-tree-node__content:hover) { background-color:rgba(59,130,246,0.1) !important; color:#93c5fd !important; }
:deep(.dark-tree .el-tree-node.is-current > .el-tree-node__content) { background-color:rgba(59,130,246,0.15) !important; color:#60a5fa !important; border-left:2px solid #3b82f6; }
:deep(.dark-tree .el-tree-node__expand-icon) { color:#475569 !important; }
:deep(.dark-tree .el-tree-node__expand-icon.is-leaf) { color:transparent !important; }
</style>
