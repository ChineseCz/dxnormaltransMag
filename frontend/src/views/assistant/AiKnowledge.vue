<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- 页面标题 -->
    <div class="px-6 pt-6 pb-4">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="flex items-center gap-3">
            <div class="rounded-xl flex items-center justify-center flex-shrink-0"
                 style="width:36px;height:36px;background:linear-gradient(135deg,#8b5cf6,#6d28d9); box-shadow:0 0 20px rgba(139,92,246,0.4);">
              <el-icon size="20" style="color:#fff;"><Collection /></el-icon>
            </div>
            <h1 class="text-2xl font-extrabold tracking-tight"
                style="background:linear-gradient(90deg,#c084fc,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              知识库管理
            </h1>
          </div>
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">管理 RAG 文档库，为 AI 助手提供领域知识增强</p>
        </div>
        <el-button type="primary" @click="showUpload = true"
                   style="background:linear-gradient(135deg,#8b5cf6,#6d28d9); border:none;">
          <el-icon class="mr-1"><Upload /></el-icon>上传文档
        </el-button>
      </div>
    </div>

    <div class="px-6 pb-6 space-y-5">
      <!-- ═══════ 统计概览 ═══════ -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="(s, i) in statsCards" :key="i" class="p-4 rounded-xl" :style="s.style">
          <div class="text-[10px] font-bold uppercase tracking-widest mb-1" :style="`color:${s.labelColor}`">{{ s.label }}</div>
          <div class="text-2xl font-extrabold font-mono" :style="`color:${s.valueColor}`">{{ s.value }}</div>
        </div>
      </div>

      <!-- ═══════ 分类标签页 ═══════ -->
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
          <!-- 文档卡片网格 -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="doc in filteredDocs" :key="doc.id" class="doc-card group">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                     :style="`background:${getCategoryColor(doc.category)}15;`">
                  <span class="text-lg">{{ getCategoryIcon(doc.category) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-semibold text-slate-200 truncate">{{ doc.name }}</div>
                  <div class="flex items-center gap-2 mt-1">
                    <el-tag size="small" effect="plain" round
                            :style="`border-color:${getCategoryColor(doc.category)}40; color:${getCategoryColor(doc.category)}; background:${getCategoryColor(doc.category)}10;`">
                      {{ getCategoryLabel(doc.category) }}
                    </el-tag>
                    <span class="text-[10px] text-slate-600">{{ doc.size || '—' }}</span>
                  </div>
                  <div class="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
                    <span>{{ doc.chunks || 0 }} 文档块</span>
                    <span>·</span>
                    <span>{{ doc.uploadTime || '—' }}</span>
                  </div>
                  <!-- 向量化状态 -->
                  <div class="flex items-center gap-1.5 mt-2">
                    <span class="w-1.5 h-1.5 rounded-full"
                          :class="doc.vectorized ? 'bg-green-400' : 'bg-amber-400 animate-pulse'"></span>
                    <span class="text-[10px]" :class="doc.vectorized ? 'text-green-400' : 'text-amber-400'">
                      {{ doc.vectorized ? '已向量化' : '处理中...' }}
                    </span>
                  </div>
                </div>
                <!-- 操作 -->
                <el-dropdown trigger="click" @command="(cmd) => handleDocAction(cmd, doc)">
                  <el-button size="small" text circle class="opacity-0 group-hover:opacity-100 transition-opacity"
                             style="color:#64748b;">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="preview"><el-icon><View /></el-icon>预览</el-dropdown-item>
                      <el-dropdown-item command="reindex"><el-icon><Refresh /></el-icon>重新索引</el-dropdown-item>
                      <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-if="filteredDocs.length === 0" class="col-span-full flex flex-col items-center py-16">
              <el-icon size="48" style="color:#1e293b;"><FolderOpened /></el-icon>
              <p class="text-slate-600 text-sm mt-3">暂无文档</p>
              <p class="text-slate-700 text-xs mt-1">点击右上角「上传文档」添加知识库内容</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ 检索测试面板 ═══════ -->
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
            <el-button type="primary" size="large" :loading="searching" @click="handleSearch"
                       style="background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.3); color:#60a5fa;">
              <el-icon class="mr-1"><Search /></el-icon>检索
            </el-button>
          </div>
          <!-- 检索结果 -->
          <div v-if="searchResults.length > 0" class="space-y-3">
            <div v-for="(r, idx) in searchResults" :key="idx"
                 class="p-3 rounded-lg" style="background:rgba(15,23,42,0.5); border:1px solid rgba(51,65,85,0.3);">
              <div class="flex items-center justify-between mb-2">
                <span class="text-blue-400 text-xs font-bold">Top {{ idx + 1 }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 text-[10px]">{{ r.source || '—' }}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-mono"
                        style="background:rgba(16,185,129,0.1); color:#34d399;">
                    {{ (r.score * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
              <p class="text-slate-400 text-xs leading-relaxed">{{ r.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 上传弹窗 ═══════ -->
    <el-dialog v-model="showUpload" title="上传知识文档" width="500px"
               style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;">
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
          <el-upload ref="uploadRef" drag action="#" :auto-upload="false"
                     :on-change="onFileChange" :limit="5" accept=".pdf,.txt,.md,.docx"
                     class="dark-upload">
            <el-icon size="40" style="color:#475569;"><UploadFilled /></el-icon>
            <div class="text-slate-400 text-sm mt-2">拖拽文件到此处，或 <em class="text-purple-400">点击选择</em></div>
            <div class="text-slate-600 text-[10px] mt-1">支持 PDF / TXT / Markdown / DOCX，单文件 ≤ 20MB</div>
          </el-upload>
        </div>
      </div>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading"
                   style="background:linear-gradient(135deg,#8b5cf6,#6d28d9); border:none;">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Collection, Upload, UploadFilled, FolderOpened, Search, View,
  Delete, Refresh, MoreFilled,
} from '@element-plus/icons-vue';
import { useAiStore } from '../../composables/useAiStore.js';

const { knowledgeDocs, fetchKnowledge, uploadKnowledge, deleteKnowledge, searchKnowledge } = useAiStore();

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

const categories = [
  { value: 'help',    label: '平台帮助', icon: '📋' },
  { value: 'domain',  label: '领域知识', icon: '📚' },
  { value: 'log',     label: '操作日志', icon: '📝' },
  { value: 'faq',     label: 'FAQ',     icon: '❓' },
];

function getCategoryLabel(v) { return categories.find(c => c.value === v)?.label || v; }
function getCategoryIcon(v) { return categories.find(c => c.value === v)?.icon || '📄'; }
function getCategoryColor(v) {
  const map = { help: '#60a5fa', domain: '#c084fc', log: '#34d399', faq: '#fbbf24' };
  return map[v] || '#94a3b8';
}

// 演示数据（后端未接入时）
const demoDocs = [
  { id: 'd1', name: '平台使用指南.md', category: 'help', size: '24KB', chunks: 15, uploadTime: '2026-03-15', vectorized: true },
  { id: 'd2', name: '变压器漏磁场计算原理.pdf', category: 'domain', size: '2.3MB', chunks: 48, uploadTime: '2026-03-14', vectorized: true },
  { id: 'd3', name: 'PCA 主成分分析详解.pdf', category: 'domain', size: '1.1MB', chunks: 32, uploadTime: '2026-03-14', vectorized: true },
  { id: 'd4', name: '常见问题解答.txt', category: 'faq', size: '8KB', chunks: 10, uploadTime: '2026-03-13', vectorized: true },
  { id: 'd5', name: 'DNN 模型调参经验总结.md', category: 'domain', size: '16KB', chunks: 12, uploadTime: '2026-03-12', vectorized: false },
];

const allDocs = computed(() => knowledgeDocs.value.length > 0 ? knowledgeDocs.value : demoDocs);

const filteredDocs = computed(() => {
  let list = allDocs.value;
  if (filterCategory.value) list = list.filter(d => d.category === filterCategory.value);
  if (searchText.value) {
    const q = searchText.value.toLowerCase();
    list = list.filter(d => d.name.toLowerCase().includes(q));
  }
  return list;
});

const statsCards = computed(() => [
  { label: '总文档数', value: allDocs.value.length, labelColor: '#60a5fa', valueColor: '#93c5fd',
    style: 'background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.15);' },
  { label: '已向量化', value: allDocs.value.filter(d => d.vectorized).length, labelColor: '#34d399', valueColor: '#6ee7b7',
    style: 'background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);' },
  { label: '文档块总数', value: allDocs.value.reduce((s, d) => s + (d.chunks || 0), 0), labelColor: '#c084fc', valueColor: '#d8b4fe',
    style: 'background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.15);' },
  { label: '分类数', value: new Set(allDocs.value.map(d => d.category)).size, labelColor: '#fbbf24', valueColor: '#fde68a',
    style: 'background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15);' },
]);

function onFileChange(file) { uploadFiles.value.push(file); }

async function handleUpload() {
  if (uploadFiles.value.length === 0) { ElMessage.warning('请选择文件'); return; }
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
    searchResults.value = res.results || [
      // 演示数据
      { content: 'PCA 通过对协方差矩阵进行特征值分解，将高维数据投影到方差最大的方向上，实现降维...', source: 'PCA 主成分分析详解.pdf', score: 0.92 },
      { content: '变压器漏磁场主要分布在铁心窗口区域，磁通密度沿绕组高度方向呈近似梯形分布...', source: '变压器漏磁场计算原理.pdf', score: 0.85 },
      { content: '建议首先检查数据预处理是否正确，特别是 Z-Score 标准化的均值和方差是否使用训练集统计量...', source: '常见问题解答.txt', score: 0.78 },
    ];
  } finally { searching.value = false; }
}

function handleDocAction(cmd, doc) {
  if (cmd === 'delete') {
    ElMessageBox.confirm(`确定删除文档「${doc.name}」？`, '删除确认', { type: 'warning' })
      .then(() => { deleteKnowledge(doc.id); })
      .catch(() => {});
  } else if (cmd === 'preview') {
    ElMessage.info(`预览文档: ${doc.name}`);
  } else if (cmd === 'reindex') {
    ElMessage.success(`已提交重新索引: ${doc.name}`);
  }
}

onMounted(fetchKnowledge);
</script>

<style scoped>
.kb-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid rgba(51,65,85,0.3); background: rgba(15,23,42,0.4);
}
.doc-card {
  padding: 14px 16px; border-radius: 12px;
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

