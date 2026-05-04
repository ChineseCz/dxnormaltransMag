<template>
  <div class="h-[68vh] flex gap-4">
    <div class="w-[280px] rounded-xl p-3 overflow-auto"
         style="background:rgba(2,8,23,0.55); border:1px solid rgba(51,65,85,0.4);">
      <div class="text-xs text-slate-400 mb-2">目录树</div>
      <el-tree
        :data="treeData"
        node-key="id"
        :expand-on-click-node="false"
        :default-expanded-keys="defaultExpanded"
        @node-click="onNodeClick"
      >
        <template #default="{ data }">
          <span class="text-xs" :class="data.type === 'dir' ? 'text-cyan-300' : 'text-slate-300'">
            {{ data.type === 'dir' ? '📁' : '📄' }} {{ data.label }}
          </span>
        </template>
      </el-tree>
    </div>

    <div class="flex-1 rounded-xl p-4 overflow-auto"
         style="background:rgba(2,8,23,0.55); border:1px solid rgba(51,65,85,0.4);">
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="text-slate-300 text-sm font-semibold">路径：{{ selectedPath || '/' }}</div>
          <div class="text-slate-500 text-xs mt-1">{{ folderHint }}</div>
        </div>
        <div class="flex items-center gap-2">
          <el-button size="small" @click="refreshTree">刷新</el-button>
          <el-button v-if="selectedPath === 'raw/'" size="small" type="primary" @click="showUpload = true">上传文件</el-button>
        </div>
      </div>

      <el-table :data="currentList" size="small" style="width:100%">
        <el-table-column label="名称" min-width="220">
          <template #default="{ row }">
            <span class="text-xs">{{ row.type === 'dir' ? '📁' : '📄' }} {{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }"><span class="text-xs text-slate-400">{{ row.type }}</span></template>
        </el-table-column>
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.role" size="small">{{ row.role }}</el-tag>
            <span v-else class="text-slate-600 text-xs">-</span>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="120">
          <template #default="{ row }"><span class="text-xs text-slate-400">{{ formatBytes(row.size) }}</span></template>
        </el-table-column>
        <el-table-column label="修改时间" min-width="160">
          <template #default="{ row }"><span class="text-xs text-slate-500">{{ row.modified_at || '-' }}</span></template>
        </el-table-column>
      </el-table>
    </div>
  </div>

  <el-dialog v-model="showUpload" title="上传到 raw 目录" width="520px">
    <el-form label-position="top" size="small">
      <el-form-item label="文件角色">
        <el-select v-model="uploadRole" style="width:100%">
          <el-option value="output" label="输出场 (output)" />
          <el-option value="input" label="输入激励 (input)" />
          <el-option value="coordinate" label="坐标 (coordinate)" />
          <el-option value="unknown" label="未分类 (unknown)" />
        </el-select>
      </el-form-item>
      <el-form-item label="文件上传">
        <el-upload
          drag
          multiple
          :action="uploadAction"
          name="file"
          :headers="uploadHeaders"
          :data="{ role: uploadRole }"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
        >
          <div class="text-slate-300 text-xs">拖拽文件到这里或点击上传</div>
        </el-upload>
      </el-form-item>
    </el-form>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  datasetId: { type: String, required: true },
});

const emit = defineEmits(['changed']);

const items = ref([]);
const selectedPath = ref('raw/');
const treeData = ref([]);
const defaultExpanded = ref(['raw/', 'data/', 'pca_result/', 'model/', 'result/']);
const showUpload = ref(false);
const uploadRole = ref('output');

const uploadAction = computed(() => `/api/dataset/${props.datasetId}/upload`);
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('auth_token') || '';
  return token ? { Authorization: `Bearer ${token}` } : {};
});

const folderHint = computed(() => {
  const m = {
    'raw/': '原始上传文件目录：用户应上传的文件都在这里',
    'data/': '处理后中间文件目录：cut/split/normalize 产物',
    'pca_result/': 'PCA结果目录：mean/vector 与降维结果',
    'model/': '模型文件目录：训练输出的模型权重',
    'result/': '预测结果目录：推理结果与导出文件',
  };
  return m[selectedPath.value] || '浏览文件';
});

const currentList = computed(() => {
  const prefix = selectedPath.value || '';
  return items.value
    .filter(i => i.path !== prefix && i.path.startsWith(prefix))
    .filter(i => {
      const rest = i.path.slice(prefix.length);
      const normalized = i.type === 'dir' ? rest.replace(/\/$/, '') : rest;
      return normalized && !normalized.includes('/');
    });
});

function formatBytes(n) {
  if (n === null || n === undefined) return '-';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function buildTree() {
  const root = [];
  const map = new Map();
  const dirs = items.value.filter(i => i.type === 'dir').sort((a, b) => a.path.localeCompare(b.path));
  for (const dir of dirs) {
    const node = { id: dir.path, label: dir.name, type: 'dir', children: [] };
    map.set(dir.path, node);
    const parent = dir.path.split('/').slice(0, -2).join('/');
    if (!parent) root.push(node);
    else {
      const pkey = `${parent}/`;
      if (map.has(pkey)) map.get(pkey).children.push(node);
      else root.push(node);
    }
  }
  treeData.value = root;
}

function onNodeClick(node) {
  selectedPath.value = node.id;
}

async function refreshTree() {
  try {
    const res = await fetch(`/api/dataset/${props.datasetId}/storage/tree`);
    const data = await res.json();
    items.value = data.items || [];
    buildTree();
  } catch {
    ElMessage.error('加载目录树失败');
  }
}

function onUploadSuccess() {
  ElMessage.success('上传成功');
  emit('changed');
  refreshTree();
}

function onUploadError() {
  ElMessage.error('上传失败');
}

onMounted(refreshTree);
watch(() => props.datasetId, () => {
  selectedPath.value = 'raw/';
  refreshTree();
});
</script>
