<template>
  <div class="p-6 space-y-6 min-h-full">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <div class="flex items-center gap-3">
          <div class="rounded-xl flex items-center justify-center flex-shrink-0"
               style="width:36px;height:36px;background:linear-gradient(135deg,#0891b2,#0ea5e9); box-shadow:0 0 20px rgba(8,145,178,0.4);">
            <el-icon size="20" style="color:white;"><FolderOpened /></el-icon>
          </div>
          <h1 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#2dd4bf,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            模板构建
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">构建模板项目并管理上传/导入文件</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="showGuide = true"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all hover:scale-105"
          style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3); color:#a5b4fc;">
          <el-icon><QuestionFilled /></el-icon>
          数据规范
        </button>
        <button @click="showCreate = true"
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
          style="background:linear-gradient(135deg,#0891b2,#0ea5e9); border:1px solid rgba(14,165,233,0.4); box-shadow:0 0 16px rgba(8,145,178,0.35);">
          <el-icon><Plus /></el-icon>
          新建数据集
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="datasets.length === 0 && !loading"
         class="flex flex-col items-center justify-center py-20 rounded-2xl"
         style="background:rgba(10,18,36,0.6); border:1px dashed rgba(51,65,85,0.5);">
      <el-icon size="48" style="color:#334155;"><FolderOpened /></el-icon>
      <p class="text-slate-500 text-sm mt-4">暂无数据集，请新建一个开始使用</p>
      <button @click="showCreate = true"
        class="mt-4 px-6 py-2 rounded-xl text-sm font-semibold text-white"
        style="background:linear-gradient(135deg,#0891b2,#0ea5e9);">
        <el-icon class="mr-1"><Plus /></el-icon>创建第一个数据集
      </button>
    </div>

    <!-- Dataset Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <div v-for="ds in datasets" :key="ds.id"
           class="rounded-2xl p-5 transition-all duration-200 hover:scale-[1.01] group relative"
           style="background:rgba(10,18,36,0.85); border:1px solid rgba(51,65,85,0.4);">
        <!-- Header -->
        <div class="flex items-start gap-3 mb-4">
          <div class="w-11 h-11 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
               :style="`background:${deviceBg(ds.deviceType)};`">
            {{ deviceIcon(ds.deviceType) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-white font-bold text-sm truncate">{{ ds.name }}</div>
            <div class="flex items-center gap-1.5 mt-1">
              <el-tag size="small" effect="plain" round style="border-color:rgba(59,130,246,0.3); color:#93c5fd; background:rgba(59,130,246,0.08);">
                {{ deviceLabel(ds.deviceType) }}
              </el-tag>
              <el-tag size="small" effect="plain" round :type="fieldTag(ds.fieldType)">
                {{ fieldLabel(ds.fieldType) }}
              </el-tag>
              <el-tag size="small" effect="plain" round style="border-color:rgba(99,102,241,0.3); color:#c4b5fd; background:rgba(99,102,241,0.07); font-size:10px;">
                {{ dataOrgLabel(ds.dataOrg) }}
              </el-tag>
            </div>
          </div>
          <!-- Delete -->
          <button @click="confirmDelete(ds)"
            class="opacity-0 group-hover:opacity-100 transition-all w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
            style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.25); color:#f87171;">
            <el-icon size="13"><Delete /></el-icon>
          </button>
        </div>

        <!-- Description -->
        <p class="text-slate-500 text-xs leading-relaxed mb-4 line-clamp-2 min-h-[32px]">
          {{ ds.description || '暂无描述' }}
        </p>

        <!-- Stats Row -->
        <div class="grid grid-cols-3 gap-2 mb-4">
          <div class="p-2 rounded-lg text-center" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] text-slate-500">{{ ds.dataOrg === 'perfile' ? '工况文件数' : '输入维度' }}</div>
            <div class="text-xs text-blue-300 font-mono font-bold mt-0.5">
              {{ ds.dataOrg === 'perfile' ? ((ds.outputVariable?.conditionCount || ds.files?.filter(f=>f.role==='output').length) + ' 个') : ((ds.inputVariables || []).length) }}
            </div>
          </div>
          <div class="p-2 rounded-lg text-center" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] text-slate-500">空间节点</div>
            <div class="text-xs text-emerald-300 font-mono font-bold mt-0.5">{{ ds.outputVariable?.spatialPoints || '—' }}</div>
          </div>
          <div class="p-2 rounded-lg text-center" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] text-slate-500">坐标系</div>
            <div class="text-xs text-purple-300 font-mono font-bold mt-0.5">{{ coordSysLabel(ds.coordSystem) }}</div>
          </div>
        </div>

        <!-- Pipeline Progress -->
        <div class="flex items-center gap-1.5 mb-3">
          <span class="text-[10px] text-slate-500 flex-shrink-0">处理进度</span>
          <div class="flex-1 flex items-center gap-1">
            <div v-for="(s, key) in pipelineOrder" :key="key"
                 class="flex-1 h-1.5 rounded-full transition-all"
                 :style="ds.pipelineStatus?.[s.key]
                   ? 'background:linear-gradient(90deg,#059669,#10b981);'
                   : 'background:rgba(51,65,85,0.4);'"
                 :title="s.label" />
          </div>
          <span class="text-[10px] font-mono" :class="pipelineDoneCount(ds) === 4 ? 'text-emerald-400' : 'text-slate-600'">
            {{ pipelineDoneCount(ds) }}/4
          </span>
        </div>

        <!-- Footer -->
        <div class="flex justify-between items-center pt-3" style="border-top:1px solid rgba(51,65,85,0.3);">
          <span class="text-[10px] text-slate-600">创建于 {{ ds.createdAt }}</span>
          <div class="flex items-center gap-2">
            <button
              @click="openImport(ds)"
              class="px-2 py-1 rounded text-[10px]"
              style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.3); color:#c4b5fd;"
            >
              从数据存储导入
            </button>
            <button
              @click="openExplorer(ds)"
              class="px-2 py-1 rounded text-[10px]"
              style="background:rgba(14,165,233,0.12); border:1px solid rgba(14,165,233,0.3); color:#7dd3fc;"
            >
              资源管理器
            </button>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded"
                  style="background:rgba(51,65,85,0.3); color:#64748b;">{{ ds.id }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Create Dialog ===== -->
    <el-dialog v-model="showCreate" title="新建数据集" width="640px" top="6vh"
               style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;"
               :close-on-click-modal="false">
      <el-form :model="form" label-position="top" size="default" class="space-y-1">
        <!-- Row 1: 名称 + 数据组织方式 -->
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="数据集名称" required>
            <el-input v-model="form.name" placeholder="例：单相变压器-额定工况-磁场" />
          </el-form-item>
          <el-form-item label="数据组织方式" required>
            <el-select v-model="form.dataOrg" class="w-full" @change="onDataOrgChange">
              <el-option value="multicolumn" label="📑 单文件多时步 (时域/参数化)" />
              <el-option value="perfile"     label="📂 多文件逐工况 (文件名=工况)" />
              <!-- <el-option value="separated"   label="🗂 多文件分离式 (输入/输出分离)" /> -->
              <!-- ⚠️ v1.1支持。当前请使用解交织工具+multicolumn模式 -->
            </el-select>
          </el-form-item>
        </div>

        <!-- 数据组织方式说明 -->
        <div class="px-3 py-2 rounded-lg text-xs leading-relaxed mb-1"
             :style="dataOrgHints[form.dataOrg].style">
          <span class="font-bold">{{ dataOrgHints[form.dataOrg].icon }} </span>
          {{ dataOrgHints[form.dataOrg].desc }}
        </div>

        <!-- Row 2: 设备 + 场类型 -->
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="设备类型" required>
            <el-select v-model="form.deviceType" class="w-full" placeholder="选择设备">
              <el-option v-for="t in deviceTypes" :key="t.value" :label="t.icon + ' ' + t.label" :value="t.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="电磁场类型" required>
            <el-select v-model="form.fieldType" class="w-full" placeholder="选择电磁场">
              <el-option v-for="t in fieldTypes" :key="t.value" :label="t.label + ' (' + t.unit + ')'" :value="t.value" />
            </el-select>
          </el-form-item>
        </div>

        <!-- Row 3: 坐标系 + 时间步长 (仅非perfile) -->
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="坐标系统" required>
            <el-select v-model="form.coordSystem" class="w-full" @change="onCoordSystemChange">
              <el-option value="xyz"   label="直角坐标 (x, y, z)  — 3列" />
              <el-option value="rz"    label="柱坐标 2D (r, z)      — 2列" />
              <el-option value="rphiz" label="柱坐标 3D (r, φ, z) — 3列" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.dataOrg !== 'perfile'" label="时间步长 Δt (s)">
            <el-input v-model.number="form.timeStep" placeholder="如 0.0005，参数化数据集填 0" />
          </el-form-item>
          <el-form-item v-else label="工况输入变量名称">
            <el-input v-model="form.conditionVarName" placeholder="如 电流 (A)" />
          </el-form-item>
        </div>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选：关于本数据集的说明" />
        </el-form-item>

        <!-- 输入变量 (仅 multicolumn / separated) -->
        <div v-if="form.dataOrg !== 'perfile'" class="pt-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold text-slate-200">输入变量（电气激励量）</span>
            <el-button size="small" type="primary" plain @click="addInputVar">
              <el-icon class="mr-1"><Plus /></el-icon>添加
            </el-button>
          </div>
          <div v-for="(v, i) in form.inputVariables" :key="i"
               class="flex items-center gap-2 mb-2 p-2 rounded-lg"
               style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.4);">
            <span class="text-slate-500 text-xs w-6 text-center flex-shrink-0">#{{ i }}</span>
            <el-input v-model="v.name" placeholder="变量名，如 一次侧电压" size="small" class="flex-1" />
            <el-input v-model="v.unit" placeholder="单位" size="small" style="width:80px;" />
            <el-button size="small" type="danger" plain circle @click="form.inputVariables.splice(i, 1)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <div v-if="form.inputVariables.length === 0" class="text-slate-600 text-xs italic p-2">
            点击「添加」定义输入变量（每个变量对应一个上传文件）
          </div>
        </div>

        <!-- 逐工况输入变量说明 + 工况变量名 (perfile) -->
        <div v-else class="pt-2 space-y-2">
          <div class="px-3 py-2 rounded-lg text-xs"
               style="background:rgba(8,145,178,0.07); border:1px solid rgba(8,145,178,0.2); color:#7dd3fc;">
            📂 逐工况模式：平台将自动从文件名中提取激励量数值作为输入。
            请填写工况变量名称与单位，用于预测时的参数标注。
          </div>
          <div class="flex items-center gap-2 p-2 rounded-lg"
               style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.4);">
            <span class="text-slate-400 text-xs flex-shrink-0">工况变量</span>
            <el-input
              v-model="form.inputVariables[0].name"
              placeholder="如 激励电流"
              size="small" class="flex-1"
            />
            <el-input
              v-model="form.inputVariables[0].unit"
              placeholder="单位，如 A"
              size="small" style="width:90px;"
            />
          </div>
        </div>

        <!-- 输出变量 -->
        <div class="pt-2">
          <span class="text-sm font-semibold text-slate-200 block mb-2">输出电磁场</span>
          <div class="grid grid-cols-3 gap-3">
            <el-form-item label="场量名称" class="mb-0">
              <el-input v-model="form.outputVariable.name" placeholder="如 磁通密度" size="small" />
            </el-form-item>
            <el-form-item label="单位" class="mb-0">
              <el-input v-model="form.outputVariable.unit" :placeholder="autoUnit" size="small" />
            </el-form-item>
            <el-form-item label="坐标列数（自动）" class="mb-0">
              <el-input-number v-model="form.coordCols" :min="0" :max="10" size="small" controls-position="right" class="w-full" />
            </el-form-item>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="doCreate" :loading="creating">
          <el-icon class="mr-1"><Check /></el-icon>创建数据集
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== Data Spec Guide Dialog ===== -->
    <el-dialog v-model="showGuide" title="📋 数据格式规范与上传指南" width="90%" top="3vh"
               style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px; max-width:1200px;"
               :close-on-click-modal="false">
      <DataSpecGuide />
      <template #footer>
        <el-button @click="showGuide = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showExplorer"
      :title="`数据集资源管理器 · ${explorerDataset?.name || ''}`"
      width="92%"
      top="4vh"
      style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px; max-width:1400px;"
    >
      <DatasetStorageExplorer
        v-if="showExplorer && explorerDataset?.id"
        :dataset-id="explorerDataset.id"
        @changed="fetchAll"
      />
    </el-dialog>

    <el-dialog
      v-model="showImport"
      :title="`导入文件到模板 · ${importDataset?.name || ''}`"
      width="900px"
      top="6vh"
      style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;"
    >
      <div class="flex items-center gap-2 mb-3">
        <el-select v-model="importTemplate" size="small" style="width:220px" @change="loadStorageFiles">
          <el-option v-for="t in storageTemplates" :key="t.key" :label="t.name" :value="t.key" />
        </el-select>
        <el-button size="small" @click="loadStorageFiles">刷新</el-button>
      </div>
      <el-table :data="storageFiles" size="small" max-height="460">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="template" label="模板" width="120" />
        <el-table-column label="文件角色" width="150">
          <template #default="{ row }">
            <el-select v-model="row.role" size="small" placeholder="选择角色">
              <el-option label="📊 输出场" value="output" />
              <el-option label="📈 输入激励" value="input" />
              <el-option label="📍 坐标文件" value="coordinate" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="modified_at" label="修改时间" width="150" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="doImport(row)" :disabled="!row.role">
              导入
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { Plus, Delete, Check, FolderOpened, QuestionFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import DataSpecGuide from '@/components/DataSpecGuide.vue';
import DatasetStorageExplorer from '@/components/DatasetStorageExplorer.vue';

const API = 'http://127.0.0.1:5000/api/dataset';

const datasets = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const showGuide = ref(false);
const showExplorer = ref(false);
const showImport = ref(false);
const creating = ref(false);
const explorerDataset = ref(null);
const importDataset = ref(null);
const storageTemplates = ref([]);
const storageFiles = ref([]);
const importTemplate = ref('multicolumn');

const deviceTypes = ref([]);
const fieldTypes = ref([]);

const pipelineOrder = [
  { key: 'cut',   label: '矩阵构建' },
  { key: 'split', label: '划分' },
  { key: 'zscore', label: '归一化' },
  { key: 'pca',   label: 'PCA' },
];

const form = reactive({
  name: '',
  deviceType: 'transformer',
  fieldType: 'magnetic',
  description: '',
  timeStep: 0.0005,
  coordCols: 3,
  coordSystem: 'xyz',
  dataOrg: 'multicolumn',
  conditionVarName: '激励电流 (A)',
  inputVariables: [
    { name: '初级绕组电压', unit: 'V' },
    { name: '次级绕组电压', unit: 'V' },
    { name: '初级绕组电流', unit: 'A' },
    { name: '次级绕组电流', unit: 'A' },
  ],
  outputVariable: { name: '磁通密度', unit: 'T' },
});

const dataOrgHints = {
  multicolumn: {
    icon: '📑', style: 'background:rgba(8,145,178,0.06);border:1px solid rgba(8,145,178,0.2);color:#7dd3fc;',
    desc: '单个输出文件包含所有时间步（COMSOL 多参数导出格式）。前几列为坐标，后续列为不同时刻/工况的场值。同时需上传各激励量的时间序列文件。'
  },
  perfile: {
    icon: '📂', style: 'background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);color:#a5b4fc;',
    desc: '每个工况对应一个独立的仿真结果文件，文件名中包含激励量数值（如 "100[A].txt"）。平台自动从文件名提取工况值，无需单独上传输入文件。'
  },
  // separated: {  // ⚠️ v1.1支持
  //   icon: '🗂', style: 'background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.2);color:#6ee7b7;',
  //   desc: '输入激励量与输出场分布分别存储于独立文件，每个输入变量一个文件，与单个输出场文件对应。适合多相/多通道输入的复杂场景（如三相变压器）。'
  // },
};

function onDataOrgChange(val) {
  if (val === 'perfile') {
    form.coordSystem = 'rz';
    form.coordCols = 2;
    form.timeStep = 0;
    // 保证 perfile 模式下至少有一个工况变量条目
    if (!form.inputVariables.length) {
      form.inputVariables.push({ name: '激励电流', unit: 'A' });
    }
  } else {
    form.coordSystem = 'xyz';
    form.coordCols = 3;
  }
}

function onCoordSystemChange(val) {
  form.coordCols = val === 'rz' ? 2 : 3;
}

const autoUnit = computed(() => {
  const ft = fieldTypes.value.find(f => f.value === form.fieldType);
  return ft?.unit || '';
});

const DEVICE_MAP = {
  transformer: { label: '变压器', icon: '⚡', bg: 'rgba(59,130,246,0.15)' },
  reactor: { label: '电抗器', icon: '🔌', bg: 'rgba(99,102,241,0.15)' },
  motor: { label: '电机', icon: '⚙️', bg: 'rgba(168,85,247,0.15)' },
  gis: { label: 'GIS', icon: '🏗️', bg: 'rgba(245,158,11,0.15)' },
  cable: { label: '电缆', icon: '🔗', bg: 'rgba(16,185,129,0.15)' },
  busbar: { label: '母线', icon: '📏', bg: 'rgba(236,72,153,0.15)' },
  other: { label: '其他', icon: '📦', bg: 'rgba(71,85,105,0.15)' },
};
const FIELD_MAP = {
  magnetic: { label: '磁场', tag: '' },
  temperature: { label: '温度场', tag: 'warning' },
  stress: { label: '应力场', tag: 'danger' },
  electric: { label: '电场', tag: 'success' },
  flow: { label: '流场', tag: 'info' },
  other: { label: '其他', tag: 'info' },
};

const deviceLabel = (t) => DEVICE_MAP[t]?.label || t;
const deviceIcon = (t) => DEVICE_MAP[t]?.icon || '📦';
const deviceBg = (t) => DEVICE_MAP[t]?.bg || 'rgba(71,85,105,0.15)';
const fieldLabel = (t) => FIELD_MAP[t]?.label || t;
const fieldTag = (t) => FIELD_MAP[t]?.tag || 'info';
const pipelineDoneCount = (ds) =>
  Object.values(ds.pipelineStatus || {}).filter(Boolean).length;

const DATA_ORG_MAP = {
  multicolumn: '单文件多时步',
  perfile:     '多文件逐工况',
  // separated:   '多文件分离式',  // ⚠️ v1.1支持
};
const COORD_SYS_MAP = { xyz: 'xyz', rz: 'r,z', rphiz: 'r,φ,z' };
const dataOrgLabel  = (t) => DATA_ORG_MAP[t] || t || '—';
const coordSysLabel = (t) => COORD_SYS_MAP[t] || t || '—';

const addInputVar = () => form.inputVariables.push({ name: '', unit: '' });

async function fetchAll() {
  loading.value = true;
  try {
    const [dsRes, typeRes] = await Promise.all([
      fetch(`${API}/list`),
      fetch(`${API}/types`),
    ]);
    datasets.value = (await dsRes.json()).datasets || [];
    const types = await typeRes.json();
    deviceTypes.value = types.deviceTypes || [];
    fieldTypes.value = types.fieldTypes || [];
  } catch {
    ElMessage.warning('无法连接后端服务');
  } finally {
    loading.value = false;
  }
}

async function doCreate() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入数据集名称');
    return;
  }
  creating.value = true;
  try {
    const payload = { ...form };
    // For perfile, add conditionVarName as a single inputVariable placeholder
    if (form.dataOrg === 'perfile') {
      payload.inputVariables = [{ name: form.conditionVarName || '激励量', unit: '' }];
      payload.timeStep = 0;
    }
    const res = await fetch(`${API}/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.dataset) {
      datasets.value.push(data.dataset);
      showCreate.value = false;
      ElMessage.success('数据集创建成功');
      form.name = '';
      form.description = '';
    }
  } catch (e) {
    ElMessage.error('创建失败: ' + e.message);
  } finally {
    creating.value = false;
  }
}

async function confirmDelete(ds) {
  try {
    await ElMessageBox.confirm(
      `确定删除数据集「${ds.name}」？关联的所有数据文件将被永久移除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
    );
    await fetch(`${API}/${ds.id}`, { method: 'DELETE' });
    datasets.value = datasets.value.filter(d => d.id !== ds.id);
    ElMessage.success('数据集已删除');
  } catch { /* cancelled */ }
}

function openExplorer(ds) {
  explorerDataset.value = ds;
  showExplorer.value = true;
}

async function loadStorageTemplates() {
  const res = await fetch('/api/dataset/storage/templates');
  const data = await res.json();
  storageTemplates.value = data.templates || [];
}

async function loadStorageFiles() {
  const q = new URLSearchParams({ template: importTemplate.value }).toString();
  const res = await fetch(`/api/dataset/storage/files?${q}`);
  const data = await res.json();
  // 为每个文件添加默认角色
  storageFiles.value = (data.files || []).map(f => ({
    ...f,
    role: 'output' // 默认为输出场
  }));
}

async function openImport(ds) {
  importDataset.value = ds;
  showImport.value = true;
  if (!storageTemplates.value.length) await loadStorageTemplates();
  await loadStorageFiles();
}

async function doImport(row) {
  if (!importDataset.value?.id) return;
  if (!row.role) {
    ElMessage.warning('请先选择文件角色');
    return;
  }
  try {
    const res = await fetch(`/api/dataset/${importDataset.value.id}/import-storage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: row.path, role: row.role }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || '导入失败');
    ElMessage.success(`已导入: ${row.filename} (${row.role})`);
    fetchAll();
  } catch (e) {
    ElMessage.error(e.message || '导入失败');
  }
}

onMounted(fetchAll);
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

