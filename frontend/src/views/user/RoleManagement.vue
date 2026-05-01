<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#0ea5e9,#6366f1); box-shadow:0 0 20px rgba(14,165,233,0.35);">
            <el-icon size="20" style="color:white;"><UserFilled /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            角色管理
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理系统角色与权限字符分配</p>
      </div>
      <button @click="handleAdd"
        class="btn-glow flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#0ea5e9,#6366f1); border:1px solid rgba(56,189,248,0.35);">
        <el-icon><Plus /></el-icon>新增角色
      </button>
    </div>

    <!-- 搜索 -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(14,165,233,0.15);">
      <el-form :inline="true" class="flex flex-wrap gap-2">
        <el-form-item label="角色名称" class="mb-0">
          <el-input v-model="search.roleName" placeholder="搜索角色名称" clearable style="width:200px;" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item class="mb-0">
          <el-button type="primary" :icon="Search" @click="loadList">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch"
            style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(14,165,233,0.15);">
      <el-table :data="filteredList" v-loading="loading" style="width:100%;" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column label="编号" prop="roleId" width="90">
          <template #default="s"><span class="font-mono text-slate-400 text-sm">{{ s.row.roleId }}</span></template>
        </el-table-column>
        <el-table-column label="角色名称" prop="roleName">
          <template #default="s"><span class="text-slate-200 font-medium">{{ s.row.roleName }}</span></template>
        </el-table-column>
        <el-table-column label="权限字符" prop="roleKey">
          <template #default="s">
            <el-tag size="small" style="background:rgba(14,165,233,0.12); border-color:rgba(14,165,233,0.3); color:#7dd3fc; font-family:monospace;">
              {{ s.row.roleKey }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="排序" prop="roleSort" width="90" align="center">
          <template #default="s"><span class="font-mono text-slate-400">{{ s.row.roleSort }}</span></template>
        </el-table-column>
        <el-table-column label="状态" align="center" width="90">
          <template #default="s">
            <el-switch v-model="s.row.status" active-value="0" inactive-value="1"
              style="--el-switch-on-color:#3b82f6; --el-switch-off-color:#374151;" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="createTime" width="175">
          <template #default="s"><span class="text-slate-500 text-xs">{{ s.row.createTime }}</span></template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="160" fixed="right">
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
          :total="total"
          style="--el-pagination-bg-color:transparent; --el-pagination-text-color:#94a3b8; --el-pagination-button-color:#94a3b8;" />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '修改角色' : '新增角色'" width="480px"
      :close-on-click-modal="false"
      style="--el-dialog-bg-color:rgba(10,18,36,0.97); --el-dialog-border-radius:12px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="pr-4">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="form.role_name" placeholder="如：普通用户" />
        </el-form-item>
        <el-form-item label="权限字符" prop="role_key">
          <el-input v-model="form.role_key" placeholder="如：engineer" />
        </el-form-item>
        <el-form-item label="显示顺序" prop="role_sort">
          <el-input-number v-model="form.role_sort" :min="1" :max="999" style="width:100%;" />
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
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, Plus, Edit, Delete, UserFilled } from '@element-plus/icons-vue';
import { getRoleList, createRole, updateRole, deleteRole } from '../../utils/userApi.js';

const loading    = ref(false);
const submitting = ref(false);
const roleList   = ref([]);
const total      = ref(0);
const page       = ref(1);
const pageSize   = ref(10);
const search     = ref({ roleName: '' });
const ids        = ref([]);

const dialogVisible = ref(false);
const isEdit        = ref(false);
const editId        = ref(null);
const formRef       = ref();
const form          = ref({ role_name: '', role_key: '', role_sort: 1, status: 1 });
const rules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  role_key:  [{ required: true, message: '请输入权限字符', trigger: 'blur' }],
};

const filteredList = computed(() => {
  const kw = search.value.roleName.trim().toLowerCase();
  const list = kw ? roleList.value.filter(r => r.roleName.toLowerCase().includes(kw)) : roleList.value;
  total.value = list.length;
  const start = (page.value - 1) * pageSize.value;
  return list.slice(start, start + pageSize.value);
});

onMounted(loadList);

async function loadList() {
  loading.value = true;
  try {
    const res = await getRoleList();
    roleList.value = res.list || [];
    total.value = roleList.value.length;
  } catch (e) { ElMessage.error(e.message || '加载失败'); }
  finally { loading.value = false; }
}

function resetSearch() { search.value.roleName = ''; page.value = 1; }
const handleSelectionChange = (sel) => { ids.value = sel.map(i => i.roleId); };

function handleAdd() {
  isEdit.value = false; editId.value = null;
  form.value = { role_name:'', role_key:'', role_sort:1, status:1 };
  dialogVisible.value = true;
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.roleId;
  form.value = { role_name: row.roleName, role_key: row.roleKey, role_sort: row.roleSort,
    status: row.status === '0' ? 1 : 0 };
  dialogVisible.value = true;
}

async function handleSubmit() {
  await formRef.value.validate();
  submitting.value = true;
  try {
    if (isEdit.value) { await updateRole(editId.value, form.value); ElMessage.success('更新成功'); }
    else              { await createRole(form.value);                ElMessage.success('创建成功'); }
    dialogVisible.value = false;
    loadList();
  } catch (e) { ElMessage.error(e.message || '操作失败'); }
  finally { submitting.value = false; }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除角色「${row.roleName}」？`, '警告', { type:'warning' });
  try { await deleteRole(row.roleId); ElMessage.success('删除成功'); loadList(); }
  catch (e) { ElMessage.error(e.message || '删除失败'); }
}
</script>

<style scoped>
/* Add your custom styles here */
</style>
