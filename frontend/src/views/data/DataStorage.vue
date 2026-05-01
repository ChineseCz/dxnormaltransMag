<template>
  <div class="p-6 space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-cyan-300">数据存储</h1>
        <p class="text-slate-400 text-xs mt-1">按模板组织文件，支持文件夹树形结构和批量上传</p>
      </div>
      <div class="flex items-center gap-2">
        <el-select v-model="activeTemplate" size="small" style="width:200px" @change="onTemplateChange">
          <el-option v-for="t in templates" :key="t.key" :label="t.name" :value="t.key" />
        </el-select>
        <el-button size="small" type="primary" @click="showCreateFolderDialog = true">
          <el-icon><FolderAdd /></el-icon>
          新建文件夹
        </el-button>
        <el-button size="small" @click="loadAll">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-5">
      <!-- 左侧：模板说明 + 文件夹树 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.4);" class="lg:col-span-1">
        <!-- 当前模板说明 -->
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-slate-200 font-semibold">{{ currentTemplateName }}</span>
            <el-tag size="small" type="info">{{ activeTemplate }}</el-tag>
          </div>
        </template>

        <div class="mb-4 p-3 rounded text-xs text-slate-400"
             style="background:rgba(2,8,23,0.5);border:1px solid rgba(51,65,85,0.3);">
          <div class="font-mono text-cyan-300 mb-2">template_storage/{{ activeTemplate }}/</div>
          <div>{{ getTemplateDescription(activeTemplate) }}</div>
        </div>

        <!-- 文件夹树 -->
        <div class="mb-3 text-sm font-semibold text-slate-300 flex items-center justify-between">
          <span>文件夹结构</span>
          <el-tag size="small" type="info">{{ folderCount }}</el-tag>
        </div>

        <el-tree
          :data="folderTree"
          :props="{ label: 'name', children: 'children' }"
          node-key="path"
          highlight-current
          default-expand-all
          @node-click="handleFolderClick"
          class="folder-tree"
        >
          <template #default="{ node, data }">
            <div class="flex items-center justify-between w-full">
              <div class="flex items-center gap-2">
                <el-icon><Folder /></el-icon>
                <span class="text-sm">{{ node.label }}</span>
              </div>
              <div class="flex items-center gap-1 text-xs text-slate-400">
                <span>{{ data.fileCount || 0 }}</span>
                <el-dropdown trigger="click" @command="(cmd) => handleFolderAction(cmd, data)" v-if="data.path !== '/'">
                  <el-icon class="cursor-pointer hover:text-cyan-400"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">重命名</el-dropdown-item>
                      <el-dropdown-item command="delete">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>
        </el-tree>

        <!-- 统计信息 -->
        <div class="mt-4 p-3 rounded" style="background:rgba(2,8,23,0.5);border:1px solid rgba(51,65,85,0.3);">
          <div class="text-xs text-slate-400 space-y-1">
            <div class="flex justify-between">
              <span>文件总数：</span>
              <span class="text-cyan-300">{{ totalFiles }}</span>
            </div>
            <div class="flex justify-between">
              <span>总大小：</span>
              <span class="text-cyan-300">{{ formatBytes(totalSize) }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 右侧：文件列表 -->
      <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.4);" class="lg:col-span-3">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-slate-200 font-semibold">
              文件列表
              <span class="text-slate-400 text-xs ml-2" v-if="currentFolderPath">
                ({{ currentFolderPath }})
              </span>
            </span>
            <div class="flex items-center gap-2">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索文件..."
                size="small"
                style="width:200px"
                clearable
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
          </div>
        </template>

        <!-- 批量上传区域 -->
        <el-upload
          drag
          multiple
          :action="uploadAction"
          name="file"
          :data="uploadData"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          :before-upload="beforeUpload"
          class="mb-4"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip text-xs text-slate-400">
              支持批量上传，文件将保存到 {{ activeTemplate }}/{{ currentFolderPath || '根目录' }}
            </div>
          </template>
        </el-upload>

        <!-- 文件表格 -->
        <el-table
          :data="filteredFiles"
          size="small"
          v-loading="loading"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="filename" label="文件名" min-width="220">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <el-icon><Document /></el-icon>
                <span>{{ row.filename }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="120">
            <template #default="{ row }">{{ formatBytes(row.size) }}</template>
          </el-table-column>
          <el-table-column prop="modified_at" label="修改时间" min-width="170" />
          <el-table-column label="路径" min-width="200">
            <template #default="{ row }">
              <span class="text-slate-400 text-xs font-mono">{{ row.path }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text @click="downloadFile(row)">下载</el-button>
              <el-button size="small" text @click="showRenameDialog(row)">重命名</el-button>
              <el-button size="small" text type="danger" @click="deleteFile(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 批量操作栏 -->
        <div v-if="selectedFiles.length > 0" class="mt-4 p-3 rounded flex items-center justify-between"
             style="background:rgba(14,165,233,0.12);border:1px solid rgba(14,165,233,0.3);">
          <span class="text-sm text-slate-300">已选择 {{ selectedFiles.length }} 个文件</span>
          <div class="flex gap-2">
            <el-button size="small" @click="showMoveDialog = true">移动到...</el-button>
            <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建文件夹对话框 -->
    <el-dialog v-model="showCreateFolderDialog" title="新建文件夹" width="400px">
      <el-form :model="folderForm" label-width="80px">
        <el-form-item label="文件夹名">
          <el-input v-model="folderForm.name" placeholder="请输入文件夹名称" />
        </el-form-item>
        <el-form-item label="父文件夹">
          <el-select v-model="folderForm.parentPath" placeholder="选择父文件夹（留空为根目录）" clearable style="width:100%">
            <el-option
              v-for="folder in flatFolders"
              :key="folder.path"
              :label="folder.path"
              :value="folder.path"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateFolderDialog = false">取消</el-button>
        <el-button type="primary" @click="createFolder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重命名文件对话框 -->
    <el-dialog v-model="showRenameFileDialog" title="重命名文件" width="400px">
      <el-input v-model="renameForm.filename" placeholder="请输入新文件名" />
      <template #footer>
        <el-button @click="showRenameFileDialog = false">取消</el-button>
        <el-button type="primary" @click="renameFile">确定</el-button>
      </template>
    </el-dialog>

    <!-- 移动文件对话框 -->
    <el-dialog v-model="showMoveDialog" title="移动文件" width="400px">
      <el-select v-model="moveTargetPath" placeholder="选择目标文件夹" style="width:100%">
        <el-option
          v-for="folder in flatFolders"
          :key="folder.path"
          :label="folder.path"
          :value="folder.path"
        />
      </el-select>
      <template #footer>
        <el-button @click="showMoveDialog = false">取消</el-button>
        <el-button type="primary" @click="moveFiles">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  FolderAdd, Refresh, Folder, MoreFilled, Search,
  UploadFilled, Document
} from '@element-plus/icons-vue';

// 模板定义
const templates = ref([
  { key: 'multicolumn', name: '单文件多时步模板' },
  { key: 'perfile', name: '逐工况多文件模板' },
  { key: 'separated', name: '输入输出分离模板' },
  { key: 'custom', name: '自定义模板' }
]);

const activeTemplate = ref('multicolumn');
const currentTemplateName = computed(() => {
  const t = templates.value.find(t => t.key === activeTemplate.value);
  return t ? t.name : '';
});

// 状态
const folderTree = ref([]);
const flatFolders = ref([]);
const files = ref([]);
const selectedFiles = ref([]);
const currentFolderPath = ref('/');
const loading = ref(false);
const searchKeyword = ref('');
const totalFiles = ref(0);
const totalSize = ref(0);
const folderCount = ref(0);

// 对话框
const showCreateFolderDialog = ref(false);
const showRenameFileDialog = ref(false);
const showMoveDialog = ref(false);

// 表单
const folderForm = ref({
  name: '',
  parentPath: '/'
});

const renameForm = ref({
  path: '',
  filename: ''
});

const moveTargetPath = ref('/');

// 上传配置
const uploadAction = '/api/dataset/storage/upload';
const uploadData = computed(() => ({
  template: activeTemplate.value,
  folder: currentFolderPath.value
}));

// 工具函数
function formatBytes(n) {
  if (n == null) return '-';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function getTemplateDescription(key) {
  const descriptions = {
    multicolumn: '单个文件包含多个时间步的数据，适用于时序数据',
    perfile: '每个工况一个文件，适用于参数扫描场景',
    separated: '输入和输出数据分别存储，适用于复杂模型',
    custom: '自定义存储格式，灵活组织数据'
  };
  return descriptions[key] || '';
}

// 过滤文件
const filteredFiles = computed(() => {
  if (!searchKeyword.value) return files.value;
  const keyword = searchKeyword.value.toLowerCase();
  return files.value.filter(f =>
    f.filename.toLowerCase().includes(keyword)
  );
});

// 模板切换
function onTemplateChange() {
  currentFolderPath.value = '/';
  loadAll();
}

// 加载所有数据
async function loadAll() {
  await Promise.all([
    loadFolderTree(),
    loadFiles()
  ]);
}

// 加载文件夹树（模拟数据，实际应该从后端获取）
async function loadFolderTree() {
  try {
    // 这里应该调用后端API获取当前模板下的文件夹树
    // 暂时使用模拟数据
    const res = await fetch(`/api/dataset/storage/folders?template=${activeTemplate.value}`);
    if (res.ok) {
      const data = await res.json();
      folderTree.value = data.tree || buildDefaultTree();
      flatFolders.value = flattenTree(folderTree.value);
      folderCount.value = flatFolders.value.length;
    } else {
      // 如果后端还没实现，使用默认树
      folderTree.value = buildDefaultTree();
      flatFolders.value = flattenTree(folderTree.value);
      folderCount.value = flatFolders.value.length;
    }
  } catch (error) {
    // 使用默认树
    folderTree.value = buildDefaultTree();
    flatFolders.value = flattenTree(folderTree.value);
    folderCount.value = flatFolders.value.length;
  }
}

// 构建默认文件夹树
function buildDefaultTree() {
  return [{
    name: '根目录',
    path: '/',
    fileCount: 0,
    children: []
  }];
}

// 展平文件夹树
function flattenTree(nodes, result = []) {
  nodes.forEach(node => {
    result.push({
      name: node.name,
      path: node.path
    });
    if (node.children && node.children.length > 0) {
      flattenTree(node.children, result);
    }
  });
  return result;
}

// 加载文件列表
async function loadFiles() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      template: activeTemplate.value,
      folder: currentFolderPath.value
    });
    const res = await fetch(`/api/dataset/storage/files?${params}`);
    const data = await res.json();
    files.value = data.files || [];

    // 计算统计信息
    totalFiles.value = files.value.length;
    totalSize.value = files.value.reduce((sum, f) => sum + (f.size || 0), 0);
  } catch (error) {
    ElMessage.error('加载文件列表失败');
  } finally {
    loading.value = false;
  }
}

// 文件夹点击
function handleFolderClick(folder) {
  currentFolderPath.value = folder.path;
  loadFiles();
}

// 文件夹操作
function handleFolderAction(command, folder) {
  if (command === 'rename') {
    ElMessageBox.prompt('请输入新文件夹名称', '重命名文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: folder.name
    }).then(async ({ value }) => {
      try {
        const res = await fetch('/api/dataset/storage/folder/rename', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            template: activeTemplate.value,
            oldPath: folder.path,
            newName: value
          })
        });
        if (res.ok) {
          ElMessage.success('重命名成功');
          loadFolderTree();
        } else {
          ElMessage.error('重命名失败');
        }
      } catch (error) {
        ElMessage.error('重命名失败');
      }
    }).catch(() => {});
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定要删除此文件夹吗？将同时删除文件夹内的所有文件。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        const res = await fetch('/api/dataset/storage/folder/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            template: activeTemplate.value,
            path: folder.path
          })
        });
        if (res.ok) {
          ElMessage.success('删除成功');
          if (currentFolderPath.value.startsWith(folder.path)) {
            currentFolderPath.value = '/';
          }
          loadAll();
        } else {
          ElMessage.error('删除失败');
        }
      } catch (error) {
        ElMessage.error('删除失败');
      }
    }).catch(() => {});
  }
}

// 创建文件夹
async function createFolder() {
  if (!folderForm.value.name) {
    ElMessage.warning('请输入文件夹名称');
    return;
  }

  try {
    const res = await fetch('/api/dataset/storage/folder/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template: activeTemplate.value,
        parentPath: folderForm.value.parentPath || '/',
        name: folderForm.value.name
      })
    });
    if (res.ok) {
      ElMessage.success('创建成功');
      showCreateFolderDialog.value = false;
      folderForm.value = { name: '', parentPath: '/' };
      loadFolderTree();
    } else {
      ElMessage.error('创建失败');
    }
  } catch (error) {
    ElMessage.error('创建失败');
  }
}

// 文件选择
function handleSelectionChange(selection) {
  selectedFiles.value = selection;
}

// 上传前检查
function beforeUpload(file) {
  const maxSize = 100 * 1024 * 1024; // 100MB
  if (file.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 超过100MB限制`);
    return false;
  }
  return true;
}

// 上传成功
function onUploadSuccess(response) {
  ElMessage.success('上传成功');
  loadFiles();
}

// 上传失败
function onUploadError() {
  ElMessage.error('上传失败');
}

// 下载文件
async function downloadFile(file) {
  try {
    const url = `/api/dataset/storage/download?path=${encodeURIComponent(file.path)}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = file.filename;
    a.click();
  } catch (error) {
    ElMessage.error('下载失败');
  }
}

// 显示重命名对话框
function showRenameDialog(file) {
  renameForm.value = {
    path: file.path,
    filename: file.filename
  };
  showRenameFileDialog.value = true;
}

// 重命名文件
async function renameFile() {
  if (!renameForm.value.filename) {
    ElMessage.warning('请输入文件名');
    return;
  }

  try {
    const res = await fetch('/api/dataset/storage/file/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        oldPath: renameForm.value.path,
        newFilename: renameForm.value.filename
      })
    });
    if (res.ok) {
      ElMessage.success('重命名成功');
      showRenameFileDialog.value = false;
      loadFiles();
    } else {
      ElMessage.error('重命名失败');
    }
  } catch (error) {
    ElMessage.error('重命名失败');
  }
}

// 删除文件
function deleteFile(file) {
  ElMessageBox.confirm('确定要删除此文件吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await fetch('/api/dataset/storage/file/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: file.path })
      });
      if (res.ok) {
        ElMessage.success('删除成功');
        loadFiles();
      } else {
        ElMessage.error('删除失败');
      }
    } catch (error) {
      ElMessage.error('删除失败');
    }
  }).catch(() => {});
}

// 批量删除
function batchDelete() {
  ElMessageBox.confirm(`确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const promises = selectedFiles.value.map(file =>
        fetch('/api/dataset/storage/file/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: file.path })
        })
      );
      await Promise.all(promises);
      ElMessage.success('批量删除成功');
      loadFiles();
    } catch (error) {
      ElMessage.error('批量删除失败');
    }
  }).catch(() => {});
}

// 移动文件
async function moveFiles() {
  if (!moveTargetPath.value) {
    ElMessage.warning('请选择目标文件夹');
    return;
  }

  try {
    const res = await fetch('/api/dataset/storage/file/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template: activeTemplate.value,
        files: selectedFiles.value.map(f => f.path),
        targetPath: moveTargetPath.value
      })
    });
    if (res.ok) {
      ElMessage.success('移动成功');
      showMoveDialog.value = false;
      loadFiles();
    } else {
      ElMessage.error('移动失败');
    }
  } catch (error) {
    ElMessage.error('移动失败');
  }
}

// 初始化
onMounted(async () => {
  await loadAll();
});
</script>

<style scoped>
.folder-tree {
  background: transparent;
}

:deep(.el-tree) {
  background: transparent;
  color: #cbd5e1;
}

:deep(.el-tree-node__content) {
  background: transparent !important;
  color: #cbd5e1;
  cursor: pointer;
}

:deep(.el-tree-node__content:hover) {
  background: rgba(14, 165, 233, 0.1) !important;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(14, 165, 233, 0.2) !important;
  color: #22d3ee;
}

:deep(.el-tree-node__expand-icon) {
  color: #94a3b8;
}

:deep(.el-upload-dragger) {
  background: rgba(2, 8, 23, 0.5) !important;
  border: 1px dashed rgba(51, 65, 85, 0.5) !important;
}

:deep(.el-upload-dragger:hover) {
  border-color: rgba(14, 165, 233, 0.5) !important;
}

:deep(.el-upload__text) {
  color: #cbd5e1;
}

:deep(.el-upload__tip) {
  color: #94a3b8;
}

:deep(.el-table) {
  background: transparent !important;
  color: #cbd5e1;
}

:deep(.el-table th.el-table__cell) {
  background: rgba(2, 8, 23, 0.5) !important;
  color: #94a3b8;
  border-color: rgba(51, 65, 85, 0.3);
}

:deep(.el-table tr) {
  background: transparent !important;
}

:deep(.el-table td.el-table__cell) {
  background: transparent !important;
  border-color: rgba(51, 65, 85, 0.3);
}

:deep(.el-table tbody tr:hover > td) {
  background: rgba(14, 165, 233, 0.05) !important;
}

:deep(.el-table__empty-block) {
  background: transparent !important;
}

:deep(.el-table__empty-text) {
  color: #94a3b8;
}

/* 对话框样式 */
:deep(.el-dialog) {
  background: rgba(10, 18, 36, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.4);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
}

:deep(.el-dialog__title) {
  color: #cbd5e1;
}

:deep(.el-dialog__body) {
  color: #cbd5e1;
}

:deep(.el-form-item__label) {
  color: #94a3b8;
}

:deep(.el-input__wrapper) {
  background: rgba(2, 8, 23, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.4);
}

:deep(.el-input__inner) {
  color: #cbd5e1;
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(2, 8, 23, 0.5);
}

:deep(.el-textarea__inner) {
  background: rgba(2, 8, 23, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.4);
  color: #cbd5e1;
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu) {
  background: rgba(10, 18, 36, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.4);
}

:deep(.el-dropdown-menu__item) {
  color: #cbd5e1;
}

:deep(.el-dropdown-menu__item:hover) {
  background: rgba(14, 165, 233, 0.1);
  color: #22d3ee;
}

/* 分页样式 */
:deep(.el-pagination) {
  color: #cbd5e1;
}

:deep(.el-pagination button) {
  background: rgba(2, 8, 23, 0.5);
  color: #cbd5e1;
}

:deep(.el-pagination .el-pager li) {
  background: rgba(2, 8, 23, 0.5);
  color: #cbd5e1;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: rgba(14, 165, 233, 0.2);
  color: #22d3ee;
}
</style>
