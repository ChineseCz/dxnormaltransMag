<template>
  <el-dialog
    v-model="visible"
    title="从数据存储导入"
    width="900px"
    :close-on-click-modal="false"
  >
    <div class="grid grid-cols-3 gap-4" style="height: 500px;">
      <!-- 左侧：模板和文件夹树 -->
      <div class="col-span-1 flex flex-col gap-3">
        <!-- 模板选择 -->
        <el-select v-model="selectedTemplate" size="small" @change="onTemplateChange">
          <el-option
            v-for="t in templates"
            :key="t.key"
            :label="t.name"
            :value="t.key"
          />
        </el-select>

        <!-- 文件夹树 -->
        <div class="flex-1 overflow-auto p-3 rounded"
             style="background:rgba(2,8,23,0.5);border:1px solid rgba(51,65,85,0.3);">
          <el-tree
            :data="folderTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="path"
            highlight-current
            default-expand-all
            @node-click="handleFolderClick"
          >
            <template #default="{ node, data }">
              <div class="flex items-center gap-2 text-sm">
                <el-icon><Folder /></el-icon>
                <span>{{ node.label }}</span>
                <span class="text-xs text-slate-400">({{ data.fileCount || 0 }})</span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右侧：文件列表 -->
      <div class="col-span-2 flex flex-col gap-3">
        <!-- 搜索 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文件..."
          size="small"
          clearable
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <!-- 文件表格 -->
        <div class="flex-1 overflow-auto">
          <el-table
            :data="filteredFiles"
            size="small"
            @selection-change="handleSelectionChange"
            height="100%"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="filename" label="文件名" min-width="180">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <el-icon><Document /></el-icon>
                  <span class="text-sm">{{ row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="100">
              <template #default="{ row }">{{ formatBytes(row.size) }}</template>
            </el-table-column>
            <el-table-column prop="modified_at" label="修改时间" width="150" />
          </el-table>
        </div>

        <!-- 已选择文件 -->
        <div v-if="selectedFiles.length > 0"
             class="p-3 rounded"
             style="background:rgba(14,165,233,0.12);border:1px solid rgba(14,165,233,0.3);">
          <div class="text-sm text-slate-300 mb-2">
            已选择 {{ selectedFiles.length }} 个文件
          </div>
          <div class="flex flex-wrap gap-2">
            <el-tag
              v-for="file in selectedFiles"
              :key="file.path"
              size="small"
              closable
              @close="removeFile(file)"
            >
              {{ file.filename }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between">
        <div class="text-sm text-slate-400">
          将导入 {{ selectedFiles.length }} 个文件
        </div>
        <div class="flex gap-2">
          <el-button @click="visible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleImport"
            :disabled="selectedFiles.length === 0"
          >
            导入
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Folder, Search, Document } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: Boolean
});

const emit = defineEmits(['update:modelValue', 'import']);

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

// 模板定义
const templates = ref([
  { key: 'multicolumn', name: '单文件多时步模板' },
  { key: 'perfile', name: '逐工况多文件模板' },
  { key: 'separated', name: '输入输出分离模板' },
  { key: 'custom', name: '自定义模板' }
]);

const selectedTemplate = ref('multicolumn');
const folderTree = ref([]);
const files = ref([]);
const currentFolderPath = ref('/');
const searchKeyword = ref('');
const selectedFiles = ref([]);

// 过滤文件
const filteredFiles = computed(() => {
  if (!searchKeyword.value) return files.value;
  const keyword = searchKeyword.value.toLowerCase();
  return files.value.filter(f =>
    f.filename.toLowerCase().includes(keyword)
  );
});

// 工具函数
function formatBytes(n) {
  if (n == null) return '-';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

// 模板切换
function onTemplateChange() {
  currentFolderPath.value = '/';
  loadFolderTree();
  loadFiles();
}

// 加载文件夹树
async function loadFolderTree() {
  try {
    const res = await fetch(`/api/dataset/storage/folders?template=${selectedTemplate.value}`);
    if (res.ok) {
      const data = await res.json();
      folderTree.value = data.tree || [{ name: '根目录', path: '/', fileCount: 0, children: [] }];
    }
  } catch (error) {
    console.error('加载文件夹树失败', error);
  }
}

// 加载文件列表
async function loadFiles() {
  try {
    const params = new URLSearchParams({
      template: selectedTemplate.value,
      folder: currentFolderPath.value
    });
    const res = await fetch(`/api/dataset/storage/files?${params}`);
    const data = await res.json();
    files.value = data.files || [];
  } catch (error) {
    console.error('加载文件列表失败', error);
  }
}

// 文件夹点击
function handleFolderClick(folder) {
  currentFolderPath.value = folder.path;
  loadFiles();
}

// 文件选择
function handleSelectionChange(selection) {
  selectedFiles.value = selection;
}

// 移除文件
function removeFile(file) {
  const index = selectedFiles.value.findIndex(f => f.path === file.path);
  if (index > -1) {
    selectedFiles.value.splice(index, 1);
  }
}

// 导入文件
function handleImport() {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请选择要导入的文件');
    return;
  }

  emit('import', {
    template: selectedTemplate.value,
    files: selectedFiles.value.map(f => ({
      filename: f.filename,
      path: f.path,
      size: f.size
    }))
  });

  visible.value = false;
  selectedFiles.value = [];
}

// 监听对话框打开
watch(visible, (val) => {
  if (val) {
    loadFolderTree();
    loadFiles();
  }
});
</script>

<style scoped>
:deep(.el-tree) {
  background: transparent;
  color: #cbd5e1;
}

:deep(.el-tree-node__content) {
  background: transparent;
  color: #cbd5e1;
}

:deep(.el-tree-node__content:hover) {
  background: rgba(14, 165, 233, 0.1);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(14, 165, 233, 0.2);
  color: #22d3ee;
}

:deep(.el-table) {
  background: transparent;
  color: #cbd5e1;
}

:deep(.el-table th.el-table__cell) {
  background: rgba(2, 8, 23, 0.5);
  color: #94a3b8;
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table tbody tr:hover > td) {
  background: rgba(14, 165, 233, 0.05);
}
</style>
