<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
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

    <!-- Search Bar -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(14,165,233,0.15);">
      <el-form :inline="true" :model="searchForm" class="flex items-center flex-wrap gap-2">
        <el-form-item label="角色名称" class="mb-0">
          <el-input v-model="searchForm.roleName" placeholder="请输入角色名称" clearable style="width:200px;" />
        </el-form-item>
        <el-form-item class="mb-0">
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch"
            style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(14,165,233,0.15);">
      <el-table :data="roleList" style="width:100%;" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column label="角色编号" prop="roleId" width="100">
          <template #default="scope">
            <span class="font-mono text-slate-400 text-sm">{{ scope.row.roleId }}</span>
          </template>
        </el-table-column>
        <el-table-column label="角色名称" prop="roleName">
          <template #default="scope">
            <span class="text-slate-200 font-medium">{{ scope.row.roleName }}</span>
          </template>
        </el-table-column>
        <el-table-column label="权限字符" prop="roleKey">
          <template #default="scope">
            <el-tag size="small"
              style="background:rgba(14,165,233,0.12); border-color:rgba(14,165,233,0.3); color:#7dd3fc; font-family:monospace;">
              {{ scope.row.roleKey }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="显示顺序" prop="roleSort" width="100" align="center">
          <template #default="scope">
            <span class="font-mono text-slate-400 text-sm">{{ scope.row.roleSort }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" align="center" width="90">
          <template #default="scope">
            <el-switch v-model="scope.row.status" active-value="0" inactive-value="1"
              style="--el-switch-on-color:#3b82f6; --el-switch-off-color:#374151;"
              @change="handleStatusChange(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="createTime" width="175">
          <template #default="scope">
            <span class="text-slate-500 text-xs">{{ scope.row.createTime }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="180" fixed="right">
          <template #default="scope">
            <div class="flex items-center justify-center gap-1">
              <el-button link type="primary" size="small" @click="handleUpdate(scope.row)">
                <el-icon class="mr-0.5"><Edit /></el-icon>修改
              </el-button>
              <el-divider direction="vertical" style="border-color:rgba(51,65,85,0.6);" />
              <el-button link type="danger" size="small" @click="handleDelete(scope.row)">
                <el-icon class="mr-0.5"><Delete /></el-icon>删除
              </el-button>
              <el-divider direction="vertical" style="border-color:rgba(51,65,85,0.6);" />
              <el-button link type="primary" size="small" @click="handleDataScope(scope.row)">更多</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="mt-5 flex justify-end">
        <el-pagination
          v-model:current-page="queryParams.pageNum"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 30, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          style="--el-pagination-bg-color:transparent; --el-pagination-text-color:#94a3b8; --el-pagination-button-color:#94a3b8;"
          @size-change="getList" @current-change="getList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Search, Refresh, Plus, Edit, Delete, UserFilled } from '@element-plus/icons-vue';

const roleList = ref([
  { roleId: 1, roleName: '超级管理员', roleKey: 'admin',  roleSort: 1, status: '0', createTime: '2026-01-18 10:58:15' },
  { roleId: 2, roleName: '普通角色',   roleKey: 'common', roleSort: 2, status: '0', createTime: '2026-01-18 10:58:15' },
]);

const total = ref(2);
const ids = ref([]);
const searchForm = ref({ roleName: '', roleKey: '', status: '', dateRange: [] });
const queryParams = ref({ pageNum: 1, pageSize: 10 });

const getList = () => {};
const handleSearch = () => { queryParams.value.pageNum = 1; getList(); };
const resetSearch = () => { searchForm.value = { roleName: '', roleKey: '', status: '', dateRange: [] }; handleSearch(); };
const handleSelectionChange = (sel) => { ids.value = sel.map(i => i.roleId); };
const handleStatusChange = (row) => {};
const handleAdd = () => {};
const handleUpdate = (row) => {};
const handleDelete = (row) => {};
const handleDataScope = (row) => {};
</script>

<style scoped>
/* Add your custom styles here */
</style>
