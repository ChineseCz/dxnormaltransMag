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
            数据集管理
          </h1>
        </div>
        <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理不同电力设备与物理场的仿真数据集</p>
      </div>
      <button @click="showCreate = true"
        class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-105"
        style="background:linear-gradient(135deg,#0891b2,#0ea5e9); border:1px solid rgba(14,165,233,0.4); box-shadow:0 0 16px rgba(8,145,178,0.35);">
        <el-icon><Plus /></el-icon>
        新建数据集
      </button>
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
            <div class="text-[10px] text-slate-500">输入维度</div>
            <div class="text-xs text-blue-300 font-mono font-bold mt-0.5">{{ (ds.inputVariables || []).length }}</div>
          </div>
          <div class="p-2 rounded-lg text-center" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] text-slate-500">空间节点</div>
            <div class="text-xs text-emerald-300 font-mono font-bold mt-0.5">{{ ds.outputVariable?.spatialPoints || '—' }}</div>
          </div>
          <div class="p-2 rounded-lg text-center" style="background:rgba(2,8,23,0.5); border:1px solid rgba(51,65,85,0.3);">
            <div class="text-[10px] text-slate-500">文件数</div>
            <div class="text-xs text-purple-300 font-mono font-bold mt-0.5">{{ (ds.files || []).length }}</div>
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
          <span class="text-[10px] font-mono px-2 py-0.5 rounded"
                style="background:rgba(51,65,85,0.3); color:#64748b;">{{ ds.id }}</span>
        </div>
      </div>
    </div>

    <!-- ===== Create Dialog ===== -->
    <el-dialog v-model="showCreate" title="新建数据集" width="640px" top="6vh"
               style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;"
               :close-on-click-modal="false">
      <el-form :model="form" label-position="top" size="default" class="space-y-1">
        <!-- 基本信息 -->
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="数据集名称" required>
            <el-input v-model="form.name" placeholder="例：单相变压器-额定工况-磁场" />
          </el-form-item>
          <el-form-item label="时间步长 (s)">
            <el-input v-model.number="form.timeStep" placeholder="0.0005" />
          </el-form-item>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="设备类型" required>
            <el-select v-model="form.deviceType" class="w-full" placeholder="选择设备">
              <el-option v-for="t in deviceTypes" :key="t.value" :label="t.icon + ' ' + t.label" :value="t.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="物理场类型" required>
            <el-select v-model="form.fieldType" class="w-full" placeholder="选择物理场">
              <el-option v-for="t in fieldTypes" :key="t.value" :label="t.label + ' (' + t.unit + ')'" :value="t.value" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选：关于本数据集的说明" />
        </el-form-item>

        <!-- 输入变量 -->
        <div class="pt-2">
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

        <!-- 输出变量 -->
        <div class="pt-2">
          <span class="text-sm font-semibold text-slate-200 block mb-2">输出物理场</span>
          <div class="grid grid-cols-3 gap-3">
            <el-form-item label="场量名称" class="mb-0">
              <el-input v-model="form.outputVariable.name" placeholder="如 磁通密度" size="small" />
            </el-form-item>
            <el-form-item label="单位" class="mb-0">
              <el-input v-model="form.outputVariable.unit" :placeholder="autoUnit" size="small" />
            </el-form-item>
            <el-form-item label="坐标列数" class="mb-0">
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { Plus, Delete, Check, FolderOpened } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const API = 'http://127.0.0.1:5000/api/dataset';

const datasets = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const creating = ref(false);

const deviceTypes = ref([]);
const fieldTypes = ref([]);

const pipelineOrder = [
  { key: 'cut', label: '截取' },
  { key: 'split', label: '划分' },
  { key: 'zscore', label: '归一化' },
  { key: 'pca', label: 'PCA' },
];

const form = reactive({
  name: '',
  deviceType: 'transformer',
  fieldType: 'magnetic',
  description: '',
  timeStep: 0.0005,
  coordCols: 3,
  inputVariables: [
    { name: '一次侧电压', unit: 'V' },
    { name: '二次侧电压', unit: 'V' },
    { name: '一次侧电流', unit: 'A' },
    { name: '二次侧电流', unit: 'A' },
  ],
  outputVariable: { name: '磁通密度', unit: 'T' },
});

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
    const res = await fetch(`${API}/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (data.dataset) {
      datasets.value.push(data.dataset);
      showCreate.value = false;
      ElMessage.success('数据集创建成功');
      // 重置表单
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

