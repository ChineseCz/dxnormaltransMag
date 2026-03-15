<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
    <div class="flex justify-between items-start">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
             style="background:linear-gradient(135deg,#4f46e5,#7c3aed); box-shadow:0 0 20px rgba(99,102,241,0.4);">
          <el-icon size="22" style="color:white;"><OfficeBuilding /></el-icon>
        </div>
        <div>
          <div class="section-badge mb-1.5">
            <span style="width:6px;height:6px;background:#818cf8;border-radius:50%;display:inline-block;"></span>
            Dept Management
          </div>
          <h1 class="text-lg font-bold text-white tracking-tight">部门管理</h1>
          <p class="text-slate-400 text-sm mt-0.5">管理组织架构与部门层级关系</p>
        </div>
      </div>
      <button @click="handleAdd()"
        class="btn-glow flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#4f46e5,#7c3aed); border:1px solid rgba(139,92,246,0.4);">
        <el-icon><Plus /></el-icon>
        新增部门
      </button>
    </div>

    <!-- Search Bar -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
      <el-form :inline="true" :model="searchForm" class="flex items-center flex-wrap gap-2">
        <el-form-item label="部门名称" class="mb-0" style="--el-form-label-color:#94a3b8;">
          <el-input v-model="searchForm.deptName" placeholder="请输入部门名称" clearable style="width:220px;" />
        </el-form-item>
        <el-form-item class="mb-0">
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch" style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
      <el-table
        :data="deptList"
        row-key="deptId"
        default-expand-all
        style="width:100%; background:transparent;"
      >
        <el-table-column prop="deptName" label="部门名称" min-width="220">
          <template #default="scope">
            <div class="flex items-center gap-2">
              <el-icon style="color:#818cf8;" size="14"><OfficeBuilding /></el-icon>
              <span class="text-slate-200 font-medium">{{ scope.row.deptName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="orderNum" label="排序" width="100">
          <template #default="scope">
            <span class="font-mono text-slate-400">{{ scope.row.orderNum }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === '0' ? 'success' : 'danger'" size="small">
              {{ scope.row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="200">
          <template #default="scope">
            <span class="text-slate-400 text-sm">{{ scope.row.createTime }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleUpdate(scope.row)">修改</el-button>
            <el-button link type="success" size="small" :icon="Plus" @click="handleAdd(scope.row)">新增</el-button>
            <el-button link type="danger" size="small" :icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Search, Refresh, Plus, Edit, Delete, OfficeBuilding } from '@element-plus/icons-vue';

const searchForm = ref({ deptName: '' });

const deptList = ref([
  {
    deptId: 100, deptName: '南方电网', orderNum: 0, status: '0', createTime: '2026-01-18 10:58:15',
    children: [
      {
        deptId: 101, deptName: '云南电网', orderNum: 1, status: '0', createTime: '2026-01-18 10:58:15',
        children: [
          { deptId: 103, deptName: '研发部门', orderNum: 1, status: '0', createTime: '2026-01-18 10:58:15' },
          { deptId: 104, deptName: '测试部门', orderNum: 2, status: '0', createTime: '2026-01-18 10:58:15' },
        ]
      },
      { deptId: 102, deptName: '其他电网', orderNum: 2, status: '0', createTime: '2026-01-18 10:58:15' }
    ]
  }
]);

const handleSearch = () => {};
const resetSearch = () => { searchForm.value.deptName = ''; };
const handleAdd = (row) => {};
const handleUpdate = (row) => {};
const handleDelete = (row) => {};
</script>

<style scoped>
/* Add your styles here */
</style>
