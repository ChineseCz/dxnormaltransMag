<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#4f46e5,#7c3aed); box-shadow:0 0 20px rgba(99,102,241,0.4);">
            <el-icon size="20" style="color:white;"><OfficeBuilding /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            部门管理
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理组织架构与部门层级关系</p>
      </div>
      <button @click="handleAdd(null)"
        class="btn-glow flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#4f46e5,#7c3aed); border:1px solid rgba(139,92,246,0.4);">
        <el-icon><Plus /></el-icon>新增部门
      </button>
    </div>

    <!-- 搜索 -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
      <el-form :inline="true" class="flex flex-wrap gap-2">
        <el-form-item label="部门名称" class="mb-0">
          <el-input v-model="search.name" placeholder="搜索部门名称" clearable style="width:220px;" @keyup.enter="loadTree" />
        </el-form-item>
        <el-form-item class="mb-0">
          <el-button type="primary" :icon="Search" @click="loadTree">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch" style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
      <el-table :data="deptList" v-loading="loading" row-key="deptId" default-expand-all style="width:100%;">
        <el-table-column prop="deptName" label="部门名称" min-width="220">
          <template #default="s">
            <div class="flex items-center gap-2">
              <el-icon style="color:#818cf8;" size="14"><OfficeBuilding /></el-icon>
              <span class="text-slate-200 font-medium">{{ s.row.deptName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="orderNum" label="排序" width="90">
          <template #default="s"><span class="font-mono text-slate-400">{{ s.row.orderNum }}</span></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="s">
            <el-tag :type="s.row.status === '0' ? 'success' : 'danger'" size="small">
              {{ s.row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180">
          <template #default="s"><span class="text-slate-400 text-sm">{{ s.row.createTime }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="s">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleEdit(s.row)">修改</el-button>
            <el-button link type="success" size="small" :icon="Plus"  @click="handleAdd(s.row)">新增</el-button>
            <el-button link type="danger"  size="small" :icon="Delete" @click="handleDelete(s.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '修改部门' : '新增部门'" width="480px"
      :close-on-click-modal="false"
      style="--el-dialog-bg-color:rgba(10,18,36,0.97); --el-dialog-border-radius:12px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="pr-4">
        <el-form-item label="上级部门">
          <el-tree-select v-model="form.parent_id" :data="deptList"
            :props="{ label:'deptName', value:'deptId', children:'children' }"
            placeholder="顶级部门" clearable check-strictly style="width:100%;" />
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="显示排序" prop="order_num">
          <el-input-number v-model="form.order_num" :min="0" :max="999" style="width:100%;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
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
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, Plus, Edit, Delete, OfficeBuilding } from '@element-plus/icons-vue';
import { getDeptTree, createDept, updateDept, deleteDept } from '../../utils/userApi.js';

const loading    = ref(false);
const submitting = ref(false);
const deptList   = ref([]);
const search     = ref({ name: '' });

const dialogVisible = ref(false);
const isEdit        = ref(false);
const editId        = ref(null);
const formRef       = ref();
const form          = ref({ name: '', parent_id: null, order_num: 0, status: 1 });
const rules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
};

onMounted(loadTree);

async function loadTree() {
  loading.value = true;
  try {
    const res = await getDeptTree(search.value.name);
    deptList.value = res.list || [];
  } catch (e) { ElMessage.error(e.message || '加载失败'); }
  finally { loading.value = false; }
}

function resetSearch() { search.value.name = ''; loadTree(); }

function handleAdd(parentRow) {
  isEdit.value = false; editId.value = null;
  form.value = { name: '', parent_id: parentRow ? parentRow.deptId : null, order_num: 0, status: 1 };
  dialogVisible.value = true;
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.deptId;
  form.value = { name: row.deptName, parent_id: row.parentId || null,
    order_num: row.orderNum, status: row.status === '0' ? 1 : 0 };
  dialogVisible.value = true;
}

async function handleSubmit() {
  await formRef.value.validate();
  submitting.value = true;
  try {
    const payload = { ...form.value, parent_id: form.value.parent_id || 0 };
    if (isEdit.value) { await updateDept(editId.value, payload); ElMessage.success('更新成功'); }
    else              { await createDept(payload);               ElMessage.success('创建成功'); }
    dialogVisible.value = false;
    loadTree();
  } catch (e) { ElMessage.error(e.message || '操作失败'); }
  finally { submitting.value = false; }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除部门「${row.deptName}」？`, '警告', { type:'warning' });
  try { await deleteDept(row.deptId); ElMessage.success('删除成功'); loadTree(); }
  catch (e) { ElMessage.error(e.message || '删除失败'); }
}
</script>

<style scoped>
/* Add your styles here */
</style>
