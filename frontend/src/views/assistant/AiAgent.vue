<template>
  <div class="min-h-full" style="background:#060d1a;">
    <!-- 页面标题 -->
    <div class="px-6 pt-6 pb-4">
      <div class="flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3">
            <div class="rounded-xl flex items-center justify-center flex-shrink-0"
                 style="width:36px;height:36px;background:linear-gradient(135deg,#f59e0b,#d97706); box-shadow:0 0 20px rgba(245,158,11,0.4);">
              <el-icon size="20" style="color:#fff;"><SetUp /></el-icon>
            </div>
            <h1 class="text-2xl font-extrabold tracking-tight"
                style="background:linear-gradient(90deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              Agent 工作台
            </h1>
          </div>
          <p class="text-slate-500 text-xs mt-1.5 ml-[48px]">AI Agent 自动执行平台操作 · Tool Calling · 可控可审计</p>
        </div>
      </div>
    </div>

    <div class="px-6 pb-6 space-y-5">
      <!-- ═══════ 可用工具列表 ═══════ -->
      <div class="agent-card">
        <div class="card-header">
          <div class="flex items-center gap-2">
            <el-icon size="15" style="color:#fbbf24;"><Briefcase /></el-icon>
            <span class="text-white font-bold text-sm">可用 Agent 工具</span>
          </div>
          <span class="text-slate-500 text-[11px]">{{ tools.length }} 个工具已注册</span>
        </div>
        <div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="tool in tools" :key="tool.id" class="tool-card group" @click="openToolDialog(tool)">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                   :style="`background:${tool.color}15;`">
                <span class="text-lg">{{ tool.icon }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-bold text-slate-200 group-hover:text-white transition-colors">{{ tool.name }}</div>
                <div class="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{{ tool.desc }}</div>
                <div class="flex items-center gap-2 mt-2">
                  <el-tag v-for="tag in tool.tags" :key="tag" size="small" effect="plain" round
                          style="border-color:rgba(51,65,85,0.3); color:#64748b; background:transparent; font-size:10px;">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              <el-icon size="14" class="text-slate-600 group-hover:text-amber-400 transition-colors mt-1"><Right /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ 任务执行时间线 ═══════ -->
      <div class="agent-card">
        <div class="card-header">
          <div class="flex items-center gap-2">
            <el-icon size="15" style="color:#60a5fa;"><Timer /></el-icon>
            <span class="text-white font-bold text-sm">任务执行记录</span>
          </div>
          <span class="text-slate-500 text-[11px]">{{ agentTasks.length }} 个任务</span>
        </div>
        <div class="p-5">
          <div v-if="agentTasks.length > 0" class="space-y-4">
            <div v-for="task in agentTasks" :key="task.id" class="task-item">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                     :style="`background:${taskStatusBg(task.status)};`">
                  <el-icon v-if="task.status === 'running'" class="is-loading" size="14" style="color:#fbbf24;"><Loading /></el-icon>
                  <el-icon v-else-if="task.status === 'completed'" size="14" style="color:#34d399;"><CircleCheck /></el-icon>
                  <el-icon v-else size="14" style="color:#f87171;"><CircleClose /></el-icon>
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-white text-sm font-bold">{{ getToolName(task.tool) }}</span>
                    <el-tag size="small" effect="dark" round
                            :type="task.status === 'completed' ? 'success' : task.status === 'running' ? 'warning' : 'danger'">
                      {{ task.status === 'completed' ? '已完成' : task.status === 'running' ? '执行中' : '失败' }}
                    </el-tag>
                  </div>
                  <span class="text-slate-500 text-[10px]">{{ task.startTime }}</span>
                </div>
              </div>
              <!-- 步骤时间线 -->
              <div class="ml-4 pl-6 border-l space-y-2" style="border-color:rgba(51,65,85,0.3);">
                <div v-for="(step, si) in task.steps" :key="si" class="flex items-start gap-2 relative">
                  <div class="absolute -left-[25px] w-2 h-2 rounded-full mt-1.5"
                       :class="step.type === 'error' ? 'bg-red-400' : step.type === 'result' ? 'bg-green-400' : 'bg-slate-600'"></div>
                  <div class="flex-1">
                    <span class="text-xs" :class="step.type === 'error' ? 'text-red-400' : step.type === 'result' ? 'text-green-400' : 'text-slate-400'">
                      {{ step.content }}
                    </span>
                    <span class="text-[10px] text-slate-600 ml-2">{{ step.time }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="flex flex-col items-center py-16">
            <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                 style="background:rgba(245,158,11,0.05); border:1px solid rgba(245,158,11,0.1);">
              <el-icon size="32" style="color:#292524;"><SetUp /></el-icon>
            </div>
            <p class="text-slate-600 text-sm">暂无 Agent 任务记录</p>
            <p class="text-slate-700 text-xs mt-1">点击上方工具卡片或在对话中触发 Agent 操作</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 工具执行弹窗 ═══════ -->
    <el-dialog v-model="toolDialogVisible" :title="`执行工具: ${activeTool?.name}`" width="500px"
               style="--el-dialog-bg-color:#0f172a; --el-dialog-border-radius:16px;">
      <div v-if="activeTool" class="space-y-4">
        <div class="p-3 rounded-lg" style="background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.15);">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg">{{ activeTool.icon }}</span>
            <span class="text-amber-300 text-sm font-bold">{{ activeTool.name }}</span>
          </div>
          <p class="text-slate-500 text-xs">{{ activeTool.desc }}</p>
        </div>

        <!-- 动态参数表单 -->
        <div v-for="param in activeTool.params" :key="param.key" class="space-y-1">
          <label class="text-slate-400 text-xs font-semibold">{{ param.label }}</label>
          <el-input v-if="param.type === 'text'" v-model="toolParams[param.key]" :placeholder="param.placeholder" />
          <el-input-number v-else-if="param.type === 'number'" v-model="toolParams[param.key]" class="w-full" />
          <el-select v-else-if="param.type === 'select'" v-model="toolParams[param.key]" class="w-full" :placeholder="param.placeholder">
            <el-option v-for="o in param.options" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </div>

        <div class="p-3 rounded-lg flex items-start gap-2"
             style="background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.15);">
          <el-icon size="14" style="color:#f87171; margin-top:2px;"><Warning /></el-icon>
          <span class="text-red-300/70 text-[11px] leading-relaxed">
            此操作将由 AI Agent 代为执行，请确认参数无误后再提交。
          </span>
        </div>
      </div>
      <template #footer>
        <el-button @click="toolDialogVisible = false">取消</el-button>
        <el-button type="warning" @click="handleExecuteTool" :loading="executing"
                   style="font-weight:600;">
          <el-icon class="mr-1"><Promotion /></el-icon>确认执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import {
  SetUp, Briefcase, Right, Timer, Loading, CircleCheck, CircleClose,
  Warning, Promotion,
} from '@element-plus/icons-vue';
import { useAiStore } from '../../composables/useAiStore.js';

const { agentTasks, executeAgent } = useAiStore();

const toolDialogVisible = ref(false);
const activeTool = ref(null);
const toolParams = reactive({});
const executing = ref(false);

const tools = [
  {
    id: 'create_dataset', name: '创建数据集', icon: '📂', color: '#60a5fa',
    desc: '根据描述自动创建数据集并配置输入/输出变量、物理场类型等参数',
    tags: ['数据管理', '自动化'],
    params: [
      { key: 'name', label: '数据集名称', type: 'text', placeholder: '如：220kV 变压器漏磁场' },
      { key: 'deviceType', label: '设备类型', type: 'select', options: [
        { value: 'transformer', label: '变压器' }, { value: 'reactor', label: '电抗器' },
        { value: 'motor', label: '电机' }, { value: 'other', label: '其他' },
      ]},
      { key: 'fieldType', label: '物理场类型', type: 'select', options: [
        { value: 'magnetic', label: '磁场' }, { value: 'temperature', label: '温度场' },
        { value: 'stress', label: '应力场' }, { value: 'electric', label: '电场' },
      ]},
    ],
  },
  {
    id: 'run_prediction', name: '执行预测', icon: '🎯', color: '#f59e0b',
    desc: '指定模型和输入参数，自动调用预测 API 获取物理场分布结果',
    tags: ['预测', '推理'],
    params: [
      { key: 'model_file', label: '模型文件', type: 'text', placeholder: '如：DNN_2023-03-13.pth' },
      { key: 'description', label: '工况描述', type: 'text', placeholder: '如：额定负载条件下' },
    ],
  },
  {
    id: 'suggest_hyperparams', name: '超参数推荐', icon: '🧠', color: '#c084fc',
    desc: '分析当前数据集特征，智能推荐合适的模型架构和训练超参数',
    tags: ['智能推荐', '模型优化'],
    params: [
      { key: 'model_type', label: '模型类型', type: 'select', options: [
        { value: 'dnn', label: 'DNN' }, { value: 'cnn', label: 'CNN' },
        { value: 'lstm', label: 'LSTM' }, { value: 'auto', label: '自动选择' },
      ]},
    ],
  },
  {
    id: 'analyze_result', name: '结果分析', icon: '📊', color: '#34d399',
    desc: '对最近的预测结果进行深度统计分析并生成可视化报告',
    tags: ['分析', '报告'],
    params: [],
  },
  {
    id: 'export_report', name: '导出报告', icon: '📄', color: '#f472b6',
    desc: '将分析结果和预测数据导出为 PDF 或 Markdown 格式的专业报告',
    tags: ['导出', '文档'],
    params: [
      { key: 'format', label: '报告格式', type: 'select', options: [
        { value: 'markdown', label: 'Markdown' }, { value: 'pdf', label: 'PDF' },
      ]},
    ],
  },
  {
    id: 'query_status', name: '系统状态查询', icon: '🔍', color: '#38bdf8',
    desc: '查询当前平台的数据集、模型、训练任务等整体运行状态',
    tags: ['查询', '监控'],
    params: [],
  },
];

function getToolName(toolId) { return tools.find(t => t.id === toolId)?.name || toolId; }
function taskStatusBg(status) {
  const map = { running: 'rgba(245,158,11,0.15)', completed: 'rgba(16,185,129,0.15)', failed: 'rgba(239,68,68,0.15)' };
  return map[status] || 'rgba(51,65,85,0.2)';
}

function openToolDialog(tool) {
  activeTool.value = tool;
  // 清空参数
  Object.keys(toolParams).forEach(k => delete toolParams[k]);
  tool.params.forEach(p => { toolParams[p.key] = ''; });
  toolDialogVisible.value = true;
}

async function handleExecuteTool() {
  if (!activeTool.value) return;
  executing.value = true;
  await executeAgent(activeTool.value.id, { ...toolParams });
  executing.value = false;
  toolDialogVisible.value = false;
  ElMessage.success(`Agent 任务「${activeTool.value.name}」已提交`);
}
</script>

<style scoped>
.agent-card {
  border-radius: 16px;
  border: 1px solid rgba(51,65,85,0.4);
  background: linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.3) 100%);
  overflow: hidden;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid rgba(51,65,85,0.3); background: rgba(15,23,42,0.4);
}
.tool-card {
  padding: 14px; border-radius: 12px;
  border: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.4);
  cursor: pointer; transition: all 0.2s;
}
.tool-card:hover {
  border-color: rgba(245,158,11,0.3);
  background: rgba(15,23,42,0.7);
  transform: translateY(-1px);
}
.task-item {
  padding: 16px; border-radius: 12px;
  border: 1px solid rgba(51,65,85,0.3);
  background: rgba(15,23,42,0.3);
}
</style>

