<template>
  <div class="p-6 space-y-5 min-h-full">

    <!-- Page Header -->
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
        <el-icon><Plus /></el-icon>
        新增用户
      </button>
    </div>

    <el-row :gutter="16" class="items-start">
      <!-- Left: Department Tree -->
      <el-col :span="5">
        <el-card class="h-full" style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <template #header>
            <div class="flex items-center gap-2">
              <el-icon style="color:#818cf8;" size="14"><OfficeBuilding /></el-icon>
              <span class="text-slate-300 text-sm font-semibold">部门列表</span>
            </div>
          </template>
          <el-input
            v-model="filterText"
            placeholder="搜索部门名称"
            size="small"
            class="mb-3"
          />
          <el-tree
            ref="treeRef"
            :data="deptData"
            :props="defaultProps"
            :filter-node-method="filterNode"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
            class="dark-tree"
          />
        </el-card>
      </el-col>

      <!-- Right: Table Area -->
      <el-col :span="19">
        <!-- Search Bar -->
        <el-card class="mb-4" style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <el-form :inline="true" :model="searchForm" class="flex items-center flex-wrap gap-2">
            <el-form-item label="用户名称" class="mb-0">
              <el-input v-model="searchForm.userName" placeholder="搜索用户" clearable style="width:200px;" />
            </el-form-item>
            <el-form-item class="mb-0">
              <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
              <el-button :icon="Refresh" @click="resetSearch"
                style="background:rgba(51,65,85,0.5); border-color:rgba(71,85,105,0.6); color:#94a3b8;">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Table -->
        <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.15);">
          <el-table :data="tableData" style="width:100%;">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="userId" label="用户编号" width="90">
              <template #default="scope">
                <span class="font-mono text-slate-400 text-sm">{{ scope.row.userId }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="userName" label="用户名称">
              <template #default="scope">
                <span class="text-slate-200 font-medium">{{ scope.row.userName }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="nickName" label="用户昵称">
              <template #default="scope">
                <span class="text-slate-300">{{ scope.row.nickName }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="dept" label="部门">
              <template #default="scope">
                <el-tag size="small" type="info"
                  style="background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.3); color:#a5b4fc;">
                  {{ scope.row.dept }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="phoneNumber" label="手机号码" width="130">
              <template #default="scope">
                <span class="font-mono text-slate-400 text-sm">{{ scope.row.phoneNumber }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="scope">
                <el-switch v-model="scope.row.status"
                  style="--el-switch-on-color:#3b82f6; --el-switch-off-color:#374151;" />
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="175">
              <template #default="scope">
                <span class="text-slate-500 text-xs">{{ scope.row.createTime }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="165" fixed="right" align="center">
              <template #default="scope">
                <div class="flex items-center justify-center gap-1">
                  <el-button link type="primary" size="small" @click="handleEdit(scope.row)">
                    <el-icon class="mr-0.5"><Edit /></el-icon>修改
                  </el-button>
                  <el-divider direction="vertical" style="border-color:rgba(51,65,85,0.6);" />
                  <el-button link type="danger" size="small" @click="handleDelete(scope.row)">
                    <el-icon class="mr-0.5"><Delete /></el-icon>删除
                  </el-button>
                  <el-divider direction="vertical" style="border-color:rgba(51,65,85,0.6);" />
                  <el-button link type="primary" size="small">更多</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <!-- Pagination -->
          <div class="mt-5 flex justify-end">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 30, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="2"
              style="--el-pagination-bg-color:transparent; --el-pagination-text-color:#94a3b8; --el-pagination-button-color:#94a3b8;"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Search, Refresh, Plus, Edit, Delete, User, OfficeBuilding } from '@element-plus/icons-vue';

const filterText = ref('');
const treeRef = ref();
const currentPage = ref(1);
const pageSize = ref(10);
const searchForm = ref({ userName: '' });

const defaultProps = { children: 'children', label: 'label' };

const deptData = [
  {
    label: '南方电网',
    children: [
      {
        label: '云南电网',
        children: [
          { label: '研发部门' },
          { label: '测试部门' },
        ],
      },
      { label: '其他电网' },
    ],
  },
];

const tableData = ref([
  { userId: 1, userName: 'admin',  nickName: '管理员',   dept: '研发部门', phoneNumber: '15888888888', status: true,  createTime: '2026-01-18 10:58:15' },
  { userId: 2, userName: 'user1',  nickName: '研发人员1', dept: '测试部门', phoneNumber: '15666666666', status: true,  createTime: '2026-01-18 10:58:15' },
]);

watch(filterText, (val) => treeRef.value?.filter(val));
const filterNode = (value, data) => !value || data.label.includes(value);
const handleNodeClick = (data) => {};
const handleSearch = () => {};
const resetSearch = () => { searchForm.value = { userName: '' }; };
const handleAdd = () => {};
const handleEdit = (row) => {};
const handleDelete = (row) => {};
</script>

<style scoped>
/* Dark Tree */
:deep(.dark-tree) {
  background: transparent !important;
  color: #cbd5e1;
}
:deep(.dark-tree .el-tree-node__content) {
  border-radius: 6px !important;
  height: 34px !important;
  font-size: 13px !important;
  color: #cbd5e1 !important;
}
:deep(.dark-tree .el-tree-node__content:hover) {
  background-color: rgba(59,130,246,0.1) !important;
  color: #93c5fd !important;
}
:deep(.dark-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(59,130,246,0.15) !important;
  color: #60a5fa !important;
  border-left: 2px solid #3b82f6;
}
:deep(.dark-tree .el-tree-node__expand-icon) {
  color: #475569 !important;
}
:deep(.dark-tree .el-tree-node__expand-icon.is-leaf) {
  color: transparent !important;
}
</style>
