<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#0891b2,#06b6d4); box-shadow:0 0 20px rgba(8,145,178,0.4);">
            <el-icon size="20" style="color:white;"><Upload /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#22d3ee,#67e8f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            数据上传
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">将仿真结果文件导入指定数据集</p>
      </div>
    </div>

    <!-- Dataset Selector -->
    <div class="p-4 rounded-xl" style="background:rgba(10,18,36,0.85); border:1px solid rgba(20,184,166,0.2);">
      <DatasetSelector ref="selectorRef" @change="onDatasetChange" />
      <p v-if="!activeDataset" class="text-yellow-500/80 text-xs mt-2">
        ⚠ 请先在「数据集管理」中创建一个数据集，再进行数据上传
      </p>
      <!-- Dataset summary badges -->
      <div v-if="activeDataset" class="flex items-center gap-2 mt-2 flex-wrap">
        <el-tag size="small" type="info">{{ dataOrgLabel }}</el-tag>
        <el-tag size="small">坐标: {{ coordSysLabel }}</el-tag>
        <el-tag size="small" type="warning">坐标列: {{ activeDataset.coordCols }}</el-tag>
        <span v-if="activeDataset.dataOrg === 'perfile'" class="text-purple-300 text-xs ml-2">
          📂 已上传 <b>{{ outputFileCount }}</b> 个工况文件
        </span>
        <span v-else class="text-slate-400 text-xs ml-2">
          已上传 {{ (activeDataset.files || []).length }} 个文件
        </span>
      </div>
    </div>

    <div v-if="activeDataset">
      <!-- ═══════════════════════════════════════════════════
           MODE A: perfile — 多文件逐工况（文件名=工况值）
      ═══════════════════════════════════════════════════ -->
      <template v-if="activeDataset.dataOrg === 'perfile'">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Upload Area -->
          <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.25);">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-bold text-indigo-300">📂 批量工况文件导入</span>
                <el-tag size="small" effect="plain" type="info">逐工况模式</el-tag>
              </div>
            </template>

            <!-- Pattern Rule -->
            <div class="mb-4 p-3 rounded-lg space-y-2"
                 style="background:rgba(2,8,23,0.5); border:1px solid rgba(99,102,241,0.2);">
              <div class="flex items-center gap-2">
                <span class="text-slate-400 text-xs font-semibold flex-shrink-0">工况提取规则：</span>
                <el-input v-model="filenamePattern" size="small" style="width:200px;"
                          placeholder="正则: ^[\d.]+" clearable />
                <el-button size="small" @click="reparseAll" plain>重新解析</el-button>
              </div>
              <div class="text-slate-500 text-xs leading-relaxed">
                匹配文件名中首个数字串为工况值。
                示例：<code class="text-indigo-300 bg-slate-900 px-1 rounded">100[A[.txt</code> → <b class="text-white">100</b>，
                <code class="text-indigo-300 bg-slate-900 px-1 rounded">118.1[A].txt</code> → <b class="text-white">118.1</b>
              </div>
            </div>

            <el-upload
              class="upload-demo"
              drag multiple
              :action="uploadUrl"
              name="file"
              :data="{ role: 'output' }"
              :on-success="handlePerfileSuccess"
              :on-error="handleError"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text text-gray-400">
                批量拖入所有工况文件（.txt），或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip text-gray-500 text-xs">
                  格式：每行一个空间点，前 {{ activeDataset.coordCols }} 列为 ({{ coordSysLabel }}) 坐标，后续列为场值
                </div>
              </template>
            </el-upload>
          </el-card>

          <!-- Parsed Condition Table -->
          <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(99,102,241,0.25);">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-bold text-indigo-300">工况映射表</span>
                <span class="text-slate-500 text-xs font-mono">{{ outputFileCount }} 个文件 · 已排序</span>
              </div>
            </template>
            <div class="max-h-80 overflow-y-auto custom-scrollbar">
              <el-table v-if="outputFileCount > 0" :data="perfileRows" size="small"
                        style="width:100%" class="custom-table">
                <el-table-column label="文件名" min-width="150">
                  <template #default="{ row }">
                    <span class="text-xs font-mono text-slate-300 block truncate"
                          style="max-width:150px;" :title="row.filename">{{ row.filename }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="工况值" width="130">
                  <template #default="{ row }">
                    <el-input-number v-model="row.conditionValue" size="small" :controls="false"
                                     style="width:110px;" @change="updateConditionValue(row)" />
                  </template>
                </el-table-column>
                <el-table-column label="节点" width="70">
                  <template #default="{ row }">
                    <span class="text-xs text-emerald-300 font-mono">{{ row.analysis?.rows ?? '?' }}</span>
                  </template>
                </el-table-column>
                <el-table-column width="55">
                  <template #default="{ row }">
                    <el-button size="small" type="danger" plain @click="handleDeleteFile(row)"
                               :icon="Delete" circle />
                  </template>
                </el-table-column>
              </el-table>
              <div v-else class="text-slate-600 text-xs italic p-4 text-center">
                尚未上传任何工况文件
              </div>
            </div>
          </el-card>
        </div>
      </template>

      <!-- ═══════════════════════════════════════════════════
           MODE B: multicolumn / separated — 常规上传界面
      ═══════════════════════════════════════════════════ -->
      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Upload Section -->
          <el-card class="col-span-2" style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.4);">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-bold text-white">
                  数据导入 — {{ activeDataset.name }}
                </span>
                <el-tag type="info" size="small">{{ dataOrgLabel }}</el-tag>
              </div>
            </template>

            <!-- Role selector -->
            <div class="flex items-center gap-4 mb-4 p-3 rounded-lg"
                 style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.4);">
              <span class="text-slate-400 text-xs font-semibold flex-shrink-0">文件角色：</span>
              <el-radio-group v-model="uploadRole" size="small">
                <el-radio-button value="output">
                  <span class="text-xs">📊 输出场数据</span>
                </el-radio-button>
                <el-radio-button value="input">
                  <span class="text-xs">📈 输入激励量</span>
                </el-radio-button>
                <el-radio-button value="coordinate">
                  <span class="text-xs">📍 坐标文件</span>
                </el-radio-button>
              </el-radio-group>
              <template v-if="uploadRole === 'input' && activeDataset.inputVariables?.length">
                <span class="text-slate-500 text-xs">对应变量：</span>
                <el-select v-model="uploadVarIndex" size="small" style="width:180px;">
                  <el-option v-for="(v, i) in activeDataset.inputVariables" :key="i"
                             :label="`#${i} ${v.name} (${v.unit})`" :value="i" />
                </el-select>
              </template>
            </div>

            <el-upload
              class="upload-demo"
              drag multiple
              :action="uploadUrl"
              name="file"
              :data="uploadFormData"
              :on-success="handleSuccess"
              :on-error="handleError"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text text-gray-400">
                将仿真文件 (.txt) 拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip text-gray-500 text-xs">{{ uploadTip }}</div>
              </template>
            </el-upload>
          </el-card>

          <!-- Summary Panel -->
          <el-card style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.4);">
            <template #header>
              <span class="font-bold text-blue-400">数据集概况</span>
            </template>
            <div class="space-y-3">
              <div v-for="item in summaryItems" :key="item.label"
                   class="flex justify-between items-center bg-gray-900 p-2 rounded">
                <span class="text-xs text-gray-400">{{ item.label }}</span>
                <component :is="item.tag ? 'el-tag' : 'span'" :size="item.tag ? 'small' : ''"
                           :type="item.type" :class="item.cls" class="text-xs font-mono">
                  {{ item.value }}
                </component>
              </div>
            </div>
          </el-card>
        </div>

        <!-- File List Table -->
        <div v-if="activeDataset.files?.length" class="mt-4">
          <h2 class="text-base font-bold text-white mb-3">已上传文件</h2>
          <el-table :data="activeDataset.files" style="width:100%" class="custom-table">
            <el-table-column prop="filename" label="文件名" min-width="200" />
            <el-table-column label="角色" width="165">
              <template #default="{ row }">
                <el-select v-model="row.role" size="small" style="width:140px;"
                           @change="updateFileRole(row)">
                  <el-option label="📊 输出场" value="output" />
                  <el-option label="📈 输入量" value="input" />
                  <el-option label="📍 坐标" value="coordinate" />
                  <el-option label="❓ 未分配" value="unknown" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="变量映射" width="185">
              <template #default="{ row }">
                <el-select v-if="row.role === 'input'" v-model="row.variableIndex" size="small"
                           style="width:165px;" placeholder="选择变量" @change="updateFileRole(row)">
                  <el-option v-for="(v, i) in activeDataset.inputVariables" :key="i"
                             :label="`#${i} ${v.name}`" :value="i" />
                </el-select>
                <span v-else class="text-slate-600 text-xs">—</span>
              </template>
            </el-table-column>
            <el-table-column label="维度 (行×列)" width="130">
              <template #default="{ row }">
                <span class="text-slate-400 text-xs font-mono">
                  {{ row.analysis?.rows || '?' }} × {{ row.analysis?.cols || '?' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="uploadTime" label="上传时间" width="165" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="danger" plain @click="handleDeleteFile(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { UploadFilled, Upload, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import DatasetSelector from '../../components/DatasetSelector.vue';

const API = 'http://127.0.0.1:5000/api/dataset';

const selectorRef     = ref(null);
const activeDataset   = ref(null);
const uploadRole      = ref('output');
const uploadVarIndex  = ref(0);
const filenamePattern = ref('^[\\d.]+');

const DEVICE_MAP = { transformer:'变压器', reactor:'电抗器', motor:'电机', gis:'GIS', cable:'电缆', busbar:'母线', other:'其他' };
const FIELD_MAP  = { magnetic:{l:'磁场',t:''}, temperature:{l:'温度场',t:'warning'}, stress:{l:'应力场',t:'danger'}, electric:{l:'电场',t:'success'}, flow:{l:'流场',t:'info'}, other:{l:'其他',t:'info'} };
const DATA_ORG_LABEL = { multicolumn:'单文件多时步', perfile:'多文件逐工况', separated:'多文件分离式' };
const COORD_SYS_LABEL = { xyz:'x,y,z', rz:'r,z', rphiz:'r,φ,z' };

const dataOrgLabel  = computed(() => DATA_ORG_LABEL[activeDataset.value?.dataOrg] || '—');
const coordSysLabel = computed(() => COORD_SYS_LABEL[activeDataset.value?.coordSystem] || activeDataset.value?.coordSystem || '—');
const isTimeDomain  = computed(() => !!activeDataset.value?.timeStep);

const uploadUrl = computed(() =>
  activeDataset.value ? `${API}/${activeDataset.value.id}/upload` : ''
);
const uploadFormData = computed(() => ({
  role: uploadRole.value,
  variableIndex: uploadRole.value === 'input' ? String(uploadVarIndex.value) : '',
}));

const uploadTip = computed(() => {
  if (!activeDataset.value) return '';
  const ds = activeDataset.value;
  if (uploadRole.value === 'output') {
    return `输出场：前 ${ds.coordCols} 列为 (${coordSysLabel.value}) 坐标，后续列为不同时刻/工况的场量值`;
  } else if (uploadRole.value === 'input') {
    const v = ds.inputVariables?.[uploadVarIndex.value];
    if (!v) return '请先选择对应的输入变量';
    return isTimeDomain.value
      ? `时域：列0=时间(s)，列1=${v.name}(${v.unit}) 的瞬时值`
      : `参数化：每行一个工况下 ${v.name}(${v.unit}) 的稳态幅值`;
  }
  return `坐标文件：每行一个空间点的 (${coordSysLabel.value}) 坐标`;
});

const summaryItems = computed(() => {
  const ds = activeDataset.value;
  if (!ds) return [];
  return [
    { label: '设备类型',   tag: true,  type: '',         value: DEVICE_MAP[ds.deviceType] || ds.deviceType },
    { label: '场类型',     tag: true,  type: FIELD_MAP[ds.fieldType]?.t || 'info', value: FIELD_MAP[ds.fieldType]?.l || ds.fieldType },
    { label: '坐标系',     tag: true,  type: 'info',     value: coordSysLabel.value },
    { label: '坐标列数',   tag: false, cls:'text-blue-300',   value: `${ds.coordCols} 列` },
    { label: '输入变量',   tag: false, cls:'text-blue-300',   value: `${(ds.inputVariables||[]).length} 维` },
    { label: '空间测点',   tag: false, cls:'text-emerald-300', value: ds.outputVariable?.spatialPoints || '待检测' },
    { label: '时间步长',   tag: false, cls:'text-purple-300',  value: ds.timeStep ? `${ds.timeStep} s` : '参数化稳态' },
    { label: '已上传文件', tag: false, cls:'text-yellow-300',  value: `${(ds.files||[]).length} 个` },
  ];
});

// ---- perfile computed ----
const perfileRows = computed(() =>
  [...(activeDataset.value?.files || [])]
    .filter(f => f.role === 'output')
    .sort((a, b) => (a.conditionValue || 0) - (b.conditionValue || 0))
);
const outputFileCount = computed(() => perfileRows.value.length);

function parseConditionFromFilename(filename) {
  try {
    const re = new RegExp(filenamePattern.value);
    const m  = filename.match(re);
    return m ? parseFloat(m[0]) : null;
  } catch {
    const m = filename.match(/^[\d.]+/);
    return m ? parseFloat(m[0]) : null;
  }
}

function reparseAll() {
  if (!activeDataset.value) return;
  const changed = [];
  activeDataset.value.files.forEach(f => {
    if (f.role === 'output') {
      const cv = parseConditionFromFilename(f.filename);
      if (cv !== null && cv !== f.conditionValue) {
        f.conditionValue = cv;
        changed.push(f);
      }
    }
  });
  changed.forEach(f => updateConditionValue(f));
  ElMessage.info(`已重新解析 ${changed.length} 个文件的工况值`);
}

function onDatasetChange(ds) {
  activeDataset.value = ds;
}

async function handlePerfileSuccess(response, file) {
  ElMessage.success(`${file.name} 上传成功`);
  await refreshDataset();
  // auto-patch conditionValue if not set by backend
  const fobj = activeDataset.value?.files?.find(f => f.filename === file.name);
  if (fobj && fobj.conditionValue == null) {
    const cv = parseConditionFromFilename(file.name);
    if (cv !== null) {
      fobj.conditionValue = cv;
      await updateConditionValue(fobj);
    }
  }
}

async function handleSuccess(response, file) {
  ElMessage.success(`${file.name} 上传成功`);
  await refreshDataset();
}

function handleError(err, file) {
  ElMessage.error(`${file.name} 上传失败`);
}

async function refreshDataset() {
  if (!activeDataset.value) return;
  try {
    const r = await fetch(`${API}/${activeDataset.value.id}`);
    const d = await r.json();
    activeDataset.value = d.dataset;
  } catch { /* ignore */ }
}

async function updateFileRole(row) {
  if (!activeDataset.value) return;
  try {
    await fetch(`${API}/${activeDataset.value.id}/files/${encodeURIComponent(row.filename)}/role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: row.role, variableIndex: row.variableIndex, conditionValue: row.conditionValue }),
    });
  } catch { /* ignore */ }
}

async function updateConditionValue(row) {
  await updateFileRole(row);
}

async function handleDeleteFile(row) {
  if (!activeDataset.value) return;
  try {
    await fetch(`${API}/${activeDataset.value.id}/files/${encodeURIComponent(row.filename)}`, { method: 'DELETE' });
    ElMessage.warning(`已删除 ${row.filename}`);
    await refreshDataset();
  } catch { /* ignore */ }
}
</script>

<style scoped>
.custom-table { background-color: #1f2937; color: white; }
:deep(.el-table) {
  --el-table-bg-color: #1f2937;
  --el-table-tr-bg-color: #1f2937;
  --el-table-header-bg-color: #374151;
  --el-table-text-color: #e5e7eb;
  --el-table-header-text-color: #f3f4f6;
  --el-table-border-color: #4b5563;
}
.upload-demo :deep(.el-upload-dragger) { background-color: #1f2937; border-color: #4b5563; }
.upload-demo :deep(.el-upload-dragger:hover) { border-color: #409eff; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
