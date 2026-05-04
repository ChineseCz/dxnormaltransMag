<template>
  <div class="min-h-full" style="background:#060d1a;">
    <div class="px-6 pt-6 pb-4">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="flex items-center gap-3">
            <div
              class="rounded-xl flex items-center justify-center flex-shrink-0"
              style="width:36px;height:36px;background:linear-gradient(135deg,#8b5cf6,#6d28d9); box-shadow:0 0 20px rgba(139,92,246,0.4);"
            >
              <el-icon size="20" style="color:#fff;"><Collection /></el-icon>
            </div>
            <h1
              class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#c084fc,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            >
              知识库管理
            </h1>
          </div>
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理 RAG 文档库，为 AI 助手提供领域知识增强</p>
        </div>
        <el-button
          type="primary"
          @click="showUpload = true"
          style="background:linear-gradient(135deg,#8b5cf6,#6d28d9); border:none;"
        >
          <el-icon class="mr-1"><Upload /></el-icon>上传文档
        </el-button>
      </div>
    </div>

    <div class="px-6 pb-6 space-y-5">
      <div
        class="flex items-center gap-1 p-1 rounded-xl"
        style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3); width:fit-content;"
      >
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="px-4 py-2 rounded-lg text-xs font-bold transition-all"
          :class="activeTab === tab.key ? 'tab-active' : 'tab-inactive'"
          @click="activeTab = tab.key"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <template v-if="activeTab === 'docs'">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(s, i) in statsCards" :key="i" class="p-4 rounded-xl" :style="s.style">
            <div class="text-[10px] font-bold uppercase tracking-widest mb-1" :style="`color:${s.labelColor}`">{{ s.label }}</div>
            <div class="text-2xl font-extrabold font-mono" :style="`color:${s.valueColor}`">{{ s.value }}</div>
          </div>
        </div>

        <div class="kb-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <el-icon size="15" style="color:#c084fc;"><FolderOpened /></el-icon>
              <span class="text-white font-bold text-sm">文档列表</span>
            </div>
            <div class="flex items-center gap-2">
              <el-input v-model="searchText" size="small" placeholder="搜索文档..." clearable style="width:180px;" />
              <el-select v-model="filterCategory" size="small" placeholder="分类" clearable style="width:120px;">
                <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </div>
          </div>

          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div v-for="doc in filteredDocs" :key="doc.id || doc.doc_id" class="doc-card group">
                <div class="flex items-start gap-3">
                  <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" :style="`background:${getCategoryColor(doc.category)}15;`">
                    <span class="text-lg">{{ getCategoryIcon(doc.category) }}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-slate-200 truncate">{{ doc.name }}</div>
                    <div class="flex items-center gap-2 mt-1">
                      <el-tag
                        size="small"
                        effect="plain"
                        round
                        :style="`border-color:${getCategoryColor(doc.category)}40; color:${getCategoryColor(doc.category)}; background:${getCategoryColor(doc.category)}10;`"
                      >
                        {{ getCategoryLabel(doc.category) }}
                      </el-tag>
                      <span class="text-[10px] text-slate-600">{{ doc.size || '--' }}</span>
                    </div>
                    <div class="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
                      <span>{{ doc.chunks || 0 }} 文档块</span>
                      <span>·</span>
                      <span>{{ doc.uploadTime || '--' }}</span>
                    </div>
                    <div class="flex items-center gap-1.5 mt-2">
                      <span class="w-1.5 h-1.5 rounded-full" :class="doc.vectorized ? 'bg-green-400' : 'bg-amber-400 animate-pulse'"></span>
                      <span class="text-[10px]" :class="doc.vectorized ? 'text-green-400' : 'text-amber-400'">
                        {{ doc.vectorized ? '已向量化' : '处理中...' }}
                      </span>
                    </div>
                  </div>

                  <el-dropdown trigger="click" @command="(cmd) => handleDocAction(cmd, doc)">
                    <el-button size="small" text circle class="opacity-0 group-hover:opacity-100 transition-opacity" style="color:#64748b;">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="preview"><el-icon><View /></el-icon>预览</el-dropdown-item>
                        <el-dropdown-item command="reindex"><el-icon><Refresh /></el-icon>重新索引</el-dropdown-item>
                        <el-dropdown-item command="extract_kg"><el-icon><Connection /></el-icon>抽取图谱</el-dropdown-item>
                        <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>

              <div v-if="filteredDocs.length === 0" class="col-span-full flex flex-col items-center py-16">
                <el-icon size="48" style="color:#1e293b;"><FolderOpened /></el-icon>
                <p class="text-slate-600 text-sm mt-3">暂无文档。</p>
                <p class="text-slate-700 text-xs mt-1">点击右上角“上传文档”添加知识库内容</p>
              </div>
            </div>
          </div>
        </div>

        <div class="kb-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <el-icon size="15" style="color:#60a5fa;"><Search /></el-icon>
              <span class="text-white font-bold text-sm">检索测试</span>
            </div>
            <span class="text-slate-500 text-[11px]">输入问题，测试知识库召回效果</span>
          </div>
          <div class="p-4 space-y-4">
            <div class="flex gap-3">
              <el-input v-model="testQuery" placeholder="输入测试问题..." size="large" class="flex-1" />
              <el-button
                type="primary"
                size="large"
                :loading="searching"
                @click="handleSearch"
                style="background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.3); color:#60a5fa;"
              >
                <el-icon class="mr-1"><Search /></el-icon>检索
              </el-button>
            </div>
            <div v-if="searchResults.length > 0" class="space-y-3">
              <div v-for="(r, idx) in searchResults" :key="idx" class="p-3 rounded-lg" style="background:rgba(15,23,42,0.5); border:1px solid rgba(51,65,85,0.3);">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-blue-400 text-xs font-bold">Top {{ idx + 1 }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-slate-500 text-[10px]">{{ r.source || '--' }}</span>
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-mono" style="background:rgba(16,185,129,0.1); color:#34d399;">
                      {{ (r.score * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
                <p class="text-slate-400 text-xs leading-relaxed">{{ r.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-if="activeTab === 'kg'">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div class="p-4 rounded-xl" style="background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.15);">
            <div class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color:#c084fc;">实体数</div>
            <div class="text-2xl font-extrabold font-mono" style="color:#d8b4fe;">{{ kgStats.entities || 0 }}</div>
          </div>
          <div class="p-4 rounded-xl" style="background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.15);">
            <div class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color:#60a5fa;">关系数</div>
            <div class="text-2xl font-extrabold font-mono" style="color:#93c5fd;">{{ kgStats.relations || 0 }}</div>
          </div>
          <div class="p-4 rounded-xl" style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);">
            <div class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color:#34d399;">Neo4j 状态</div>
            <div class="text-lg font-bold" :style="kgStats.available ? 'color:#6ee7b7' : 'color:#f87171'">
              {{ kgStats.available ? '已连接' : '未连接' }}
            </div>
          </div>
        </div>

        <div class="kb-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <span class="text-base">🕸️</span>
              <span class="text-white font-bold text-sm">文档图谱抽取</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-slate-500 text-[11px]">选择文档执行三元组抽取，构建知识图谱</span>
              <span v-if="busyMessage" class="text-amber-300 text-[11px]">{{ busyMessage }}</span>
            </div>
          </div>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              <div
                v-for="doc in allDocs"
                :key="doc.id || doc.doc_id"
                class="flex items-center gap-3 p-3 rounded-lg"
                style="background:rgba(15,23,42,0.4); border:1px solid rgba(51,65,85,0.3);"
              >
                <span class="text-lg">{{ getCategoryIcon(doc.category) }}</span>
                <div class="flex-1 min-w-0">
                  <div class="text-xs font-semibold text-slate-300 truncate">{{ doc.name }}</div>
                  <div class="text-[10px] text-slate-600">{{ doc.chunks || 0 }} 块</div>
                </div>
                <el-button
                  size="small"
                  :loading="isDocProcessing(doc.id || doc.doc_id, 'kg')"
                  :disabled="isDocProcessing(doc.id || doc.doc_id, 'kg')"
                  @click="handleExtractKg(doc)"
                  style="background:rgba(139,92,246,0.15); border:1px solid rgba(139,92,246,0.3); color:#c084fc; font-size:11px;"
                >
                  抽取图谱
                </el-button>
              </div>
              <div v-if="allDocs.length === 0" class="col-span-full text-center py-8">
                <p class="text-slate-600 text-sm">暂无文档，请先上传文档</p>
              </div>
            </div>
          </div>
        </div>

        <div class="kb-card">
          <div class="card-header">
            <div class="flex items-center gap-2">
              <el-icon size="15" style="color:#c084fc;"><Search /></el-icon>
              <span class="text-white font-bold text-sm">图谱路径检索</span>
            </div>
            <span class="text-slate-500 text-[11px]">输入关键词，测试多跳路径检索</span>
          </div>
          <div class="p-4 space-y-4">
            <div class="flex gap-3">
              <el-input v-model="kgQuery" placeholder="输入关键词（如：绕组 短路）..." size="large" class="flex-1" />
              <el-button
                type="primary"
                size="large"
                :loading="kgSearching"
                @click="handleKgSearch"
                style="background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.3); color:#c084fc;"
              >
                <el-icon class="mr-1"><Search /></el-icon>检索
              </el-button>
            </div>
            <div v-if="kgSearchResults.length > 0" class="space-y-3">
              <div v-for="(r, idx) in kgSearchResults" :key="idx" class="p-3 rounded-lg" style="background:rgba(88,28,135,0.08); border:1px solid rgba(139,92,246,0.2);">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-purple-400 text-xs font-bold">路径 {{ idx + 1 }}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-mono" style="background:rgba(139,92,246,0.1); color:#c084fc;">
                    置信度 {{ r.confidence }}
                  </span>
                </div>
                <div class="flex items-center gap-1 flex-wrap">
                  <template v-for="(node, ni) in r.chain" :key="ni">
                    <span
                      class="px-2 py-0.5 rounded text-[11px] font-medium"
                      :style="ni === 0 ? 'background:rgba(139,92,246,0.2);color:#c084fc;border:1px solid rgba(139,92,246,0.3);'
                            : ni === r.chain.length-1 ? 'background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25);'
                            : 'background:rgba(251,191,36,0.1);color:#fbbf24;border:1px solid rgba(251,191,36,0.2);'"
                    >
                      {{ node }}
                    </span>
                    <span v-if="ni < r.chain.length - 1" class="text-slate-600 text-xs">→</span>
                  </template>
                </div>
              </div>
            </div>
            <div v-else-if="kgSearched && kgSearchResults.length === 0" class="text-center py-6 text-slate-600 text-sm">
              未找到相关路径
            </div>
          </div>
        </div>
      </template>
    </div>

    <el-dialog v-model="showUpload" title="上传知识文档" width="500px" style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;">
      <div class="space-y-4">
        <div>
          <label class="block text-slate-400 text-xs font-semibold mb-2">文档分类</label>
          <el-radio-group v-model="uploadCategory" size="default">
            <el-radio-button v-for="c in categories" :key="c.value" :value="c.value">
              {{ c.icon }} {{ c.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
        <div>
          <label class="block text-slate-400 text-xs font-semibold mb-2">选择文件</label>
          <el-upload
            ref="uploadRef"
            drag
            action="#"
            :auto-upload="false"
            :on-change="onFileChange"
            :limit="5"
            accept=".pdf,.txt,.md,.docx"
            class="dark-upload"
          >
            <el-icon size="40" style="color:#475569;"><UploadFilled /></el-icon>
            <div class="text-slate-400 text-sm mt-2">拖拽文件到此处，或 <em class="text-purple-400">点击选择</em></div>
            <div class="text-slate-600 text-[10px] mt-1">支持 PDF / TXT / Markdown / DOCX，单文件 ≤ 20MB</div>
          </el-upload>
        </div>
      </div>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9); border:none;">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Collection, Connection, Delete, FolderOpened, MoreFilled, Refresh, Search, Upload, UploadFilled, View } from '@element-plus/icons-vue';
import { useAiStore } from '../../composables/useAiStore.js';

const { knowledgeDocs, fetchKnowledge, uploadKnowledge, deleteKnowledge, searchKnowledge, extractKg, getKgStats, searchKg } = useAiStore();

const activeTab = ref('docs');
const tabs = [
  { key: 'docs', icon: '📚', label: '文档管理' },
  { key: 'kg', icon: '🕸️', label: '知识图谱' },
];

const searchText = ref('');
const filterCategory = ref('');
const showUpload = ref(false);
const uploadCategory = ref('help');
const uploadRef = ref(null);
const uploadFiles = ref([]);
const uploading = ref(false);
const testQuery = ref('');
const searching = ref(false);
const searchResults = ref([]);

const kgStats = ref({ entities: 0, relations: 0, available: false });
const kgQuery = ref('');
const kgSearching = ref(false);
const kgSearchResults = ref([]);
const kgSearched = ref(false);
const processingDocs = ref({});
const busyMessage = ref('');

const categories = [
  { value: 'help', label: '平台帮助', icon: '📘' },
  { value: 'domain', label: '领域知识', icon: '📗' },
  { value: 'log', label: '操作日志', icon: '📙' },
  { value: 'faq', label: 'FAQ', icon: '❓' },
];

function getCategoryLabel(v) {
  return categories.find((c) => c.value === v)?.label || v;
}

function getCategoryIcon(v) {
  return categories.find((c) => c.value === v)?.icon || '📚';
}

function getCategoryColor(v) {
  const map = { help: '#60a5fa', domain: '#c084fc', log: '#34d399', faq: '#fbbf24' };
  return map[v] || '#94a3b8';
}

const allDocs = computed(() => knowledgeDocs.value || []);

const filteredDocs = computed(() => {
  let list = allDocs.value;
  if (filterCategory.value) list = list.filter((d) => d.category === filterCategory.value);
  if (searchText.value) {
    const q = searchText.value.toLowerCase();
    list = list.filter((d) => (d.name || '').toLowerCase().includes(q));
  }
  return list;
});

const statsCards = computed(() => [
  {
    label: '总文档数',
    value: allDocs.value.length,
    labelColor: '#60a5fa',
    valueColor: '#93c5fd',
    style: 'background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.15);',
  },
  {
    label: '已向量化',
    value: allDocs.value.filter((d) => d.vectorized).length,
    labelColor: '#34d399',
    valueColor: '#6ee7b7',
    style: 'background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);',
  },
  {
    label: '文档块总数',
    value: allDocs.value.reduce((s, d) => s + (d.chunks || 0), 0),
    labelColor: '#c084fc',
    valueColor: '#d8b4fe',
    style: 'background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.15);',
  },
  {
    label: '分类数',
    value: new Set(allDocs.value.map((d) => d.category)).size,
    labelColor: '#fbbf24',
    valueColor: '#fde68a',
    style: 'background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15);',
  },
]);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function setDocProcessing(docId, type, on) {
  if (!docId) return;
  if (!processingDocs.value[docId]) processingDocs.value[docId] = { reindex: false, kg: false };
  processingDocs.value[docId][type] = on;
}

function isDocProcessing(docId, type) {
  return !!processingDocs.value?.[docId]?.[type];
}

async function pollAfterLongTask(docId, type, baseline = null) {
  const maxRounds = 30;
  for (let i = 0; i < maxRounds; i += 1) {
    await sleep(3000);
    await fetchKnowledge();
    await loadKgStats();
    const hit = knowledgeDocs.value.find((d) => (d.id || d.doc_id) === docId);
    if (type === 'reindex' && hit?.vectorized) return true;
    if (type === 'kg') {
      if (baseline && (Number(kgStats.value.entities || 0) > Number(baseline.entities || 0)
        || Number(kgStats.value.relations || 0) > Number(baseline.relations || 0))) {
        return true;
      }
    }
  }
  return false;
}

function onFileChange(file) {
  uploadFiles.value.push(file);
}

async function handleUpload() {
  if (uploadFiles.value.length === 0) {
    ElMessage.warning('请选择文件');
    return;
  }
  uploading.value = true;
  for (const f of uploadFiles.value) {
    await uploadKnowledge(f.raw || f, uploadCategory.value);
  }
  uploading.value = false;
  uploadFiles.value = [];
  showUpload.value = false;
}

async function handleSearch() {
  if (!testQuery.value.trim()) return;
  searching.value = true;
  try {
    const res = await searchKnowledge(testQuery.value);
    searchResults.value = res.results || [];
  } finally {
    searching.value = false;
  }
}

async function handleDocAction(cmd, doc) {
  const docId = doc.id || doc.doc_id;
  if (cmd === 'delete') {
    ElMessageBox.confirm(`确定删除文档「${doc.name}」？`, '删除确认', { type: 'warning' })
      .then(() => deleteKnowledge(docId))
      .catch(() => {});
    return;
  }

  if (cmd === 'preview') {
    ElMessage.info(`预览文档: ${doc.name}`);
    return;
  }

  if (cmd === 'reindex') {
    if (isDocProcessing(docId, 'reindex')) return;
    try {
      setDocProcessing(docId, 'reindex', true);
      busyMessage.value = `正在重新索引：${doc.name}`;
      ElMessage.info('已提交重新索引，后台处理中...');

      const token = localStorage.getItem('auth_token') || '';
      const headers = { Authorization: `Bearer ${token}` };
      const res = await fetch(`/api/ai/knowledge/${docId}/reindex`, { method: 'POST', headers });
      const data = await res.json();
      if (res.ok) {
        const done = await pollAfterLongTask(docId, 'reindex');
        ElMessage.success(done ? `重新索引完成：${doc.name}` : (data.message || `已提交重新索引：${doc.name}`));
      } else {
        ElMessage.error(data.error || '重新索引失败');
      }
    } catch (e) {
      ElMessage.error(`重新索引失败: ${e.message}`);
    } finally {
      setDocProcessing(docId, 'reindex', false);
      busyMessage.value = '';
    }
    return;
  }

  if (cmd === 'extract_kg') {
    await handleExtractKg(doc);
  }
}

async function handleExtractKg(doc) {
  const docId = doc.id || doc.doc_id;
  if (isDocProcessing(docId, 'kg')) return;

  try {
    setDocProcessing(docId, 'kg', true);
    busyMessage.value = `正在抽取图谱：${doc.name}`;
    ElMessage.info('已提交图谱抽取，后台处理中...');
    const beforeEntities = Number(kgStats.value.entities || 0);
    const beforeRelations = Number(kgStats.value.relations || 0);

    const data = await extractKg(docId);
    if (data?.skipped) {
      ElMessage.success(data.message || '已跳过重复抽取');
      await loadKgStats();
      return;
    }

    await pollAfterLongTask(docId, 'kg', { entities: beforeEntities, relations: beforeRelations });
    await loadKgStats();
    const afterEntities = Number(kgStats.value.entities || 0);
    const afterRelations = Number(kgStats.value.relations || 0);
    if (afterEntities > beforeEntities || afterRelations > beforeRelations) {
      ElMessage.success(`图谱抽取已完成：${doc.name}`);
    } else {
      ElMessage.info(`图谱任务已提交，仍在处理中：${doc.name}`);
    }
  } finally {
    setDocProcessing(docId, 'kg', false);
    busyMessage.value = '';
  }
}

async function handleKgSearch() {
  if (!kgQuery.value.trim()) return;
  kgSearching.value = true;
  kgSearched.value = false;
  try {
    const res = await searchKg(kgQuery.value);
    kgSearchResults.value = res.results || [];
    kgSearched.value = true;
  } finally {
    kgSearching.value = false;
  }
}

async function loadKgStats() {
  kgStats.value = await getKgStats();
}

onMounted(async () => {
  await fetchKnowledge();
  await loadKgStats();
});
</script>

<style scoped>
.tab-active {
  background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(99,102,241,0.2));
  color: #c084fc;
  border: 1px solid rgba(139,92,246,0.3);
}

.tab-inactive {
  background: transparent;
  color: #64748b;
  border: 1px solid transparent;
}

.tab-inactive:hover {
  color: #94a3b8;
  background: rgba(51,65,85,0.2);
}

.kb-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.4);
}

.doc-card {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.4);
  transition: all 0.2s;
}

.doc-card:hover {
  border-color: rgba(139,92,246,0.3);
  background: rgba(15,23,42,0.6);
}

.dark-upload :deep(.el-upload-dragger) {
  background: rgba(15,23,42,0.5) !important;
  border: 1px dashed rgba(51,65,85,0.4) !important;
  border-radius: 12px !important;
}

.dark-upload :deep(.el-upload-dragger:hover) {
  border-color: rgba(139,92,246,0.4) !important;
}
</style>
