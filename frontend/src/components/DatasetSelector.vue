<template>
  <div class="flex items-center gap-3 flex-wrap">
    <div class="flex items-center gap-2">
      <div class="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
           style="background:rgba(20,184,166,0.2);">
        <el-icon style="color:#2dd4bf;" size="14"><Folder /></el-icon>
      </div>
      <span class="text-slate-400 text-xs font-semibold whitespace-nowrap">当前数据集</span>
    </div>
    <el-select v-model="selectedId" placeholder="请选择数据集..." size="small"
               @change="onSelect" filterable style="min-width:240px;"
               :class="{'no-dataset': !selectedId}">
      <el-option v-for="ds in datasets" :key="ds.id" :label="ds.name" :value="ds.id">
        <div class="flex items-center gap-2 py-0.5">
          <span class="text-sm">{{ deviceIcon(ds.deviceType) }}</span>
          <span class="text-slate-200 text-xs">{{ ds.name }}</span>
          <el-tag size="small" effect="plain" round
                  :type="fieldTag(ds.fieldType)">{{ fieldLabel(ds.fieldType) }}</el-tag>
        </div>
      </el-option>
    </el-select>
    <!-- 快捷信息徽标 -->
    <template v-if="current">
      <el-tag size="small" effect="plain" round style="border-color:rgba(59,130,246,0.3); color:#93c5fd; background:rgba(59,130,246,0.08);">
        {{ deviceLabel(current.deviceType) }}
      </el-tag>
      <el-tag size="small" effect="plain" round :type="fieldTag(current.fieldType)">
        {{ fieldLabel(current.fieldType) }}
      </el-tag>
      <span class="text-slate-500 text-[11px] font-mono" v-if="current.trainInfo">
        {{ current.trainInfo.inputDim }}D → {{ current.trainInfo.rawOutputDim || '?' }}D
        <template v-if="current.trainInfo.outputDim !== current.trainInfo.rawOutputDim">
          (PCA {{ current.trainInfo.outputDim }}D)
        </template>
      </span>
    </template>
    <slot name="actions" :dataset="current" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { Folder } from '@element-plus/icons-vue';

const API = 'http://127.0.0.1:5000/api/dataset';
const STORAGE_KEY = 'selected_dataset_id';

const emit = defineEmits(['change']);
const props = defineProps({ modelValue: { type: String, default: '' } });

const datasets = ref([]);
const selectedId = ref('');
const current = ref(null);

const FIELD_MAP = {
  magnetic: { label: '磁场', tag: '' },
  temperature: { label: '温度场', tag: 'warning' },
  stress: { label: '应力场', tag: 'danger' },
  electric: { label: '电场', tag: 'success' },
  flow: { label: '流场', tag: 'info' },
  other: { label: '其他', tag: 'info' },
};
const DEVICE_MAP = {
  transformer: { label: '变压器', icon: '⚡' },
  reactor: { label: '电抗器', icon: '🔌' },
  motor: { label: '电机', icon: '⚙️' },
  gis: { label: 'GIS', icon: '🏗️' },
  cable: { label: '电缆', icon: '🔗' },
  busbar: { label: '母线', icon: '📏' },
  other: { label: '其他', icon: '📦' },
};

const fieldLabel = (t) => FIELD_MAP[t]?.label || t;
const fieldTag = (t) => FIELD_MAP[t]?.tag || 'info';
const deviceLabel = (t) => DEVICE_MAP[t]?.label || t;
const deviceIcon = (t) => DEVICE_MAP[t]?.icon || '📦';

async function fetchDatasets() {
  try {
    const r = await fetch(`${API}/list`);
    const d = await r.json();
    datasets.value = d.datasets || [];
  } catch {
    datasets.value = [];
  }
}

function onSelect(id) {
  current.value = datasets.value.find(d => d.id === id) || null;
  localStorage.setItem(STORAGE_KEY, id);
  emit('change', current.value);
}

// 公开方法：外部调用刷新
async function refresh() {
  await fetchDatasets();
  if (selectedId.value) {
    current.value = datasets.value.find(d => d.id === selectedId.value) || null;
    emit('change', current.value);
  }
}

defineExpose({ refresh, datasets, current });

onMounted(async () => {
  await fetchDatasets();
  // 恢复上次选择
  const saved = props.modelValue || localStorage.getItem(STORAGE_KEY);
  if (saved && datasets.value.find(d => d.id === saved)) {
    selectedId.value = saved;
    onSelect(saved);
  } else if (datasets.value.length > 0) {
    selectedId.value = datasets.value[0].id;
    onSelect(datasets.value[0].id);
  }
});

watch(() => props.modelValue, (v) => {
  if (v && v !== selectedId.value) {
    selectedId.value = v;
    onSelect(v);
  }
});
</script>

<style scoped>
.no-dataset :deep(.el-input__inner) { color: #f59e0b !important; }
</style>

