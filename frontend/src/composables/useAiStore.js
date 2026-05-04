/**
 * AI 助手模块 —— 跨页面 / 跨组件共享状态
 * 会话列表、当前会话、消息流、知识库列表、Agent 任务等
 */
import { ref, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { marked } from 'marked';

// ── Markdown 配置 ──
marked.setOptions({ breaks: true, gfm: true });

// ── 双轨路由 Mock 响应库 ──
const MOCK_ROUTES = {
  fault_trace: {
    route: {
      badges: [
        { icon: '🕸️', label: 'KG 图谱轨道', bg: 'rgba(139,92,246,0.18)', color: '#c084fc', border: 'rgba(139,92,246,0.35)' },
        { icon: '3跳', label: 'Reactor→Winding→Fault_Cause', bg: 'rgba(88,28,135,0.12)', color: '#a78bfa', border: 'rgba(139,92,246,0.2)' },
      ],
    },
    sources: {
      kg: [
        { chain: ['铁心电抗器', '中部绕组', '磁场畸变', '匝间短路'], confidence: '91.7%' },
        { chain: ['绕组', '绝缘老化', '局部放电'], confidence: '68.4%' },
        { chain: ['铁芯', '气隙异常', '磁导率下降'], confidence: '54.2%' },
      ],
      vector: [],
    },
    content: `根据**知识图谱故障溯源分析**，已完成三跳路径检索：

**故障链路径（3跳）：** \`Reactor\` → \`Winding\` → \`Fault_Cause\`

| 节点层级 | 实体 | 关系类型 | 置信度 |
|----------|------|----------|--------|
| 设备层 | 铁心电抗器 | 包含组件 | — |
| 组件层 | 中部绕组 | 产生现象 | 96.3% |
| 现象层 | 磁通密度畸变（B↓12%）| 导致故障 | 93.5% |
| 故障层 | **中部匝间短路** | 确认根因 | 91.7% |

**溯源结论：** 当前 280 A 工况下，中部绕组区域 DNN 预测 B 值较正常工况偏低约 12%，知识图谱路径置信度 **91.7%** 指向**中部匝间短路**为最可能故障根因。

**建议处置：**
1. 对中部绕组开展**匝间绝缘电阻测试**（TTR 比值测量）
2. 进行**直流电阻不平衡度检测**，对比三相绕组差异
3. 采用**冲击电压法**或**频率响应分析（FRA）**定位短路匝数
4. 结合 DNN 预测差值图（B 真值 − 预测）标定异常节点位置`,
  },

  tune_debug: {
    route: {
      badges: [
        { icon: '🕸️', label: 'KG 图谱轨道', bg: 'rgba(139,92,246,0.18)', color: '#c084fc', border: 'rgba(139,92,246,0.35)' },
        { icon: '⚡', label: '算法维度路径', bg: 'rgba(251,191,36,0.12)', color: '#fbbf24', border: 'rgba(251,191,36,0.25)' },
      ],
    },
    sources: {
      kg: [
        { chain: ['低电流段误差偏大', '训练样本稀疏', '数据增强/过采样'], confidence: '92.8%' },
        { chain: ['MAPE偏高', 'PCA主成分不足', '增加至8维'], confidence: '85.3%' },
        { chain: ['梯度消失', '学习率过小', '调整至2e-3+Warmup'], confidence: '76.1%' },
      ],
      vector: [],
    },
    content: `基于**知识图谱算法维度路径**，检索到以下参数调优链路：

**调参路径（3跳）：** \`Problem\` → \`Algorithm_Param\` → \`Solution\`

| 问题症状 | 关联参数 | 优化方向 | 置信度 |
|----------|----------|----------|--------|
| 低电流段（100~300A）MAPE偏高 | 训练样本密度 | 对低电流区间做插值增强，样本数 ×3 | 92.8% |
| PCA 重建误差偏大 | 主成分数 \`n=6\` | 提升至 \`n=8\`，解释方差比≥98% | 85.3% |
| 收敛速度慢 | 学习率 \`lr=1e-3\` | 尝试调大学习率，初始 lr=2e-3 | 76.1% |

**调参建议（优先级排序）：**
1. **首先** 在 100~300 A 区间以 9.05 A 步长插值扩充样本 → 新增约 22 组数据
2. **其次** 重新运行 PCA，将主成分从 6 → 8，重训模型
3. **最后** 切换学习率调度为 \`CosineAnnealingWarmRestarts(T_0=50)\`

> 电抗器数据集仅 51 组，低电流段稀疏性是导致误差偏高的核心原因，数据增强优先级高于调参。`,
  },

  regulation_query: {
    route: {
      badges: [
        { icon: '📄', label: 'FAISS 向量轨道', bg: 'rgba(59,130,246,0.18)', color: '#60a5fa', border: 'rgba(59,130,246,0.35)' },
        { icon: '93.6%', label: '余弦相似度', bg: 'rgba(16,185,129,0.1)', color: '#34d399', border: 'rgba(16,185,129,0.2)' },
      ],
    },
    sources: {
      kg: [],
      vector: [
        {
          title: '电抗器运行规程 DL/T 617-2021 §6.4.2',
          excerpt: '铁心电抗器在额定电流下运行时，绕组温升不得超过 65 K，气隙磁密不得超过设计值的 110%。当磁场分布出现局部异常时，应停电进行绕组绝缘试验。',
          similarity: 0.936,
        },
        {
          title: '电力变压器及电抗器绕组匝间绝缘试验 GB/T 4109-2021 §5.2',
          excerpt: '匝间绝缘试验应施加不低于额定电压 1.5 倍的冲击电压，持续时间不少于 30 ms。试验前后应对比直流电阻，差值超过 2% 视为匝间异常。',
          similarity: 0.891,
        },
        {
          title: '频率响应分析法诊断电抗器绕组变形导则  §4.1',
          excerpt: 'FRA 测量结果的相关系数 R 低于 0.98 时，应判定为绕组存在形变或匝间短路，需结合直流电阻不平衡度综合判定。',
          similarity: 0.847,
        },
      ],
    },
    content: `已从 **FAISS 向量知识库**中召回相关规程文档（余弦相似度 **93.6%**）：

根据《电力电抗器运行规程》DL/T 617-2021 第 6.4.2 条：

> 铁心电抗器绕组温升不得超过 **65 K**，气隙磁密不得超过设计值的 **110%**。当磁场分布出现局部异常时，应停电进行绕组绝缘试验。

**匝间短路标准诊断流程：**
1. **直流电阻测量** → 三相不平衡度 > 2% 即判异常
2. **匝间冲击绝缘试验**（GB/T 4109-2021 §5.2）→ 施加 1.5 U_N 冲击电压 ≥ 30 ms
3. **频率响应分析（FRA）**（DL/T 911-2019）→ 相关系数 R < 0.98 判定形变/短路
4. **DNN 磁场差值图辅助定位** → 利用 |B_真值 - B_预测| 热力图标定异常匝位
5. 综合判定后执行 **降额运行或停电检修**`,
  },

  dual_track: {
    route: {
      badges: [
        { icon: '🕸️', label: 'KG 图谱', bg: 'rgba(139,92,246,0.18)', color: '#c084fc', border: 'rgba(139,92,246,0.35)' },
        { icon: '📄', label: 'FAISS 向量', bg: 'rgba(59,130,246,0.18)', color: '#60a5fa', border: 'rgba(59,130,246,0.35)' },
        { icon: '⚡', label: '异步并发', bg: 'rgba(251,191,36,0.12)', color: '#fbbf24', border: 'rgba(251,191,36,0.25)' },
      ],
    },
    sources: {
      kg: [
        { chain: ['中部绕组', '磁场畸变', '匝间短路'], confidence: '91.7%' },
        { chain: ['气隙', '磁导率异常', '硅钢片局部饱和'], confidence: '58.6%' },
      ],
      vector: [
        {
          title: '频率响应分析法诊断电抗器绕组变形导则 DL/T 911-2019',
          excerpt: 'FRA 相关系数 R < 0.98 且直流电阻不平衡度 > 2% 同时满足时，可高置信度判定为中部匝间短路，建议立即停电检修。',
          similarity: 0.921,
        },
        {
          title: '电抗器运行规程 DL/T 617-2021 §6.4.2',
          excerpt: '气隙磁密超过设计值 110% 或绕组磁场局部异常时，应在 24 小时内完成匝间绝缘试验并提交检测报告。',
          similarity: 0.878,
        },
      ],
    },
    content: `已启动**双轨并发检索**（KG 图谱 + FAISS 向量），融合分析结果如下：

---

**🕸️ 知识图谱轨道结论：**

故障因果链：\`中部绕组\` → \`磁场畸变\` → \`匝间短路\`
- 主路径置信度：**91.7%**
- 备选路径：气隙磁导率异常（58.6%）

**📄 向量知识库轨道结论：**

召回规程：《FRA 诊断电抗器绕组变形导则》
- 文档相似度：**92.1%**
- 关键依据：FRA 相关系数 R < 0.98 + 直流电阻不平衡度 > 2%

---

**⚡ 融合诊断结论：**

综合两条检索轨道的证据，当前设备状态判定为 🔴 **高风险 - 建议立即检修**：

| 维度 | 证据来源 | 结论 |
|------|----------|------|
| 故障定位 | KG 图谱（91.7%） | 中部绕组匝间短路高概率 |
| 规程依据 | FAISS 向量（92.1%） | FRA + 直流电阻双判据触达 |
| DNN 辅助 | 磁场差值图 | B 偏低区域与匝间短路位置吻合 |
| 综合判定 | 双轨融合 | **停电检修 + 匝间绝缘试验** |

**建议处置：** 在 **24 小时内**完成 FRA 测量与直流电阻不平衡度检测；若两项均超阈值，执行停电检修并更换受损绕组匝绝缘。`,
  },
};

// ── 单例响应式状态 ──
const API = 'http://127.0.0.1:5000/api/ai';

// 会话
const conversations = ref([]);
const activeConvId = ref('');
const CONV_KEY = 'ai_conversations';

// 消息
const messages = ref([]);
const isStreaming = ref(false);

// 上下文开关
const contextSwitches = ref({
  dataset: true,
  prediction: true,
  model: true,
});

// RAG knowledge base toggle
const ragEnabled = ref(false);

// Dynamic context data
const contextData = ref({
  dataset: null,
  model: null,
  prediction: null,
});

// 知识库
async function loadContextData() {
  const token = localStorage.getItem('auth_token') || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const selectedDatasetId = localStorage.getItem('selected_dataset_id');

  // 1. Dataset context
  try {
    if (selectedDatasetId) {
      const r = await fetch(`/api/dataset/list`, { headers });
      if (r.ok) {
        const data = await r.json();
        const list = data.datasets || data.list || data || [];
        const ds = list.find(d => d.id === selectedDatasetId || String(d.id) === selectedDatasetId);
        if (ds) {
          const inputVars = ds.inputVariables || ds.input_variables || [];
          const trainInfo = ds.trainInfo || ds.train_info || {};
          contextData.value.dataset = {
            id: ds.id,
            name: ds.name,
            deviceType: ds.deviceType || ds.device_type || '',
            fieldType: ds.fieldType || ds.field_type || '',
            inputDim: trainInfo.inputDim || trainInfo.input_dim || (Array.isArray(inputVars) ? inputVars.length : '-'),
            outputNodes: trainInfo.rawOutputDim || trainInfo.raw_output_dim || trainInfo.output_nodes || '-',
            samples: (trainInfo.trainSamples || 0) + (trainInfo.testSamples || 0) || '-',
            trainInfo: trainInfo,
          };
        }
      }
    }
  } catch (e) { console.warn('[Context] Failed to load dataset:', e); }

  // 2. Model context
  try {
    const r = await fetch(`/api/model/list`, { headers });
    if (r.ok) {
      const data = await r.json();
      const list = data.models || data.list || data || [];
      const activeModelId = localStorage.getItem('selected_model_id');
      const model = activeModelId
        ? list.find(m => String(m.id) === String(activeModelId))
        : list.find(m => m.status === 'trained' || m.status === 'completed');
      if (model) {
        const trainParams = model.train_params || model.params || {};
        contextData.value.model = {
          id: model.id,
          name: model.name,
          modelType: model.model_type || model.modelType || 'DNN',
          architecture: model.architecture || '',
          hiddenLayers: model.hidden_layers || model.hiddenLayers || 2,
          pcaDims: trainParams.pca_dims || trainParams.pcaDims || 6,
          optimizer: trainParams.optimizer || 'Adam',
          lr: trainParams.learning_rate || trainParams.lr || 1e-3,
          batch: trainParams.batch_size || trainParams.batch || 32,
          epoch: trainParams.epochs || trainParams.epoch || 100,
          mae: model.mae || null,
        };
      }
    }
  } catch (e) { console.warn('[Context] Failed to load model:', e); }

  // 3. Prediction context
  try {
    const hist = JSON.parse(localStorage.getItem('predict_history') || '[]');
    if (hist.length > 0) {
      const last = hist[0];
      const currentModelType = contextData.value.model?.modelType || '';
      contextData.value.prediction = {
        modelType: last.modelType || '',
        current: last.current || '-',
        bMax: last.bMax || '-',
        bMin: last.bMin || '-',
        bMean: last.bMean || '-',
        bStd: last.bStd || '-',
        timestamp: last.timestamp || '',
        isCurrentModel: !currentModelType || last.modelType === currentModelType,
      };
    }
  } catch (e) { console.warn('[Context] Failed to load prediction:', e); }
}


async function syncConversations() {
  const token = localStorage.getItem('auth_token') || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  try {
    const r = await fetch(`${API}/conversations`, { headers });
    if (r.ok) {
      const data = await r.json();
      conversations.value = (data.conversations || []).map(c => ({
        id: c.id,
        title: c.title || '新对话',
        createdAt: c.created_at || c.createdAt,
        updatedAt: c.updated_at || c.updatedAt,
        messageCount: c.message_count || c.messageCount || 0,
      }));
    }
  } catch (e) {
    console.warn('[AI] syncConversations failed:', e);
  }
}

async function loadMessages(convId) {
  const token = localStorage.getItem('auth_token') || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  try {
    const r = await fetch(`${API}/conversations/${convId}/messages`, { headers });
    if (r.ok) {
      const data = await r.json();
      messages.value = (data.messages || []).map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.created_at ? new Date(m.created_at).toLocaleTimeString() : '',
      }));
    }
  } catch (e) {
    console.warn('[AI] loadMessages failed:', e);
  }
}

const knowledgeDocs = ref([]);

// Agent 任务
const agentTasks = ref([]);

// 抽屉
const drawerVisible = ref(false);
const drawerMessages = ref([]);
const isDrawerStreaming = ref(false);

// ── 启动时恢复 ──
try {
  const saved = localStorage.getItem(CONV_KEY);
  if (saved) {
    const parsed = JSON.parse(saved);
    conversations.value = parsed.conversations || [];
    if (parsed.activeId) activeConvId.value = parsed.activeId;
    // 恢复当前会话的消息
    const active = conversations.value.find(c => c.id === activeConvId.value);
    if (active) messages.value = active.messages || [];
  }
} catch { /* ignore */ }

function _save() {
  // 先把当前消息同步回会话对象
  const active = conversations.value.find(c => c.id === activeConvId.value);
  if (active) active.messages = messages.value;
  const data = { conversations: conversations.value.slice(0, 30), activeId: activeConvId.value };
  try { localStorage.setItem(CONV_KEY, JSON.stringify(data)); } catch { /* quota */ }
}

// ═══════ composable ═══════
export function useAiStore() {
  const router = useRouter();

  // ── 会话管理 ──
  function newConversation() {
    const id = 'conv_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    const conv = {
      id,
      title: '新对话',
      createdAt: new Date().toLocaleString('zh-CN'),
      messages: [],
    };
    conversations.value.unshift(conv);
    activeConvId.value = id;
    messages.value = [];
    _save();
    return id;
  }

  function switchConversation(id) {
    // 保存当前
    const prev = conversations.value.find(c => c.id === activeConvId.value);
    if (prev) prev.messages = [...messages.value];
    // 切换
    activeConvId.value = id;
    const next = conversations.value.find(c => c.id === id);
    messages.value = next ? [...(next.messages || [])] : [];
    _save();
  }

  function deleteConversation(id) {
    conversations.value = conversations.value.filter(c => c.id !== id);
    if (activeConvId.value === id) {
      if (conversations.value.length > 0) {
        switchConversation(conversations.value[0].id);
      } else {
        activeConvId.value = '';
        messages.value = [];
      }
    }
    _save();
  }

  function renameConversation(id, title) {
    const conv = conversations.value.find(c => c.id === id);
    if (conv) conv.title = title;
    _save();
  }

  // ── 构建上下文摘要（注入 system prompt） ──
  function buildContextSummary() {
    const parts = [];
    const cd = contextData.value;

    if (contextSwitches.value.dataset && cd.dataset) {
      const ds = cd.dataset;
      parts.push(`[数据集: ${ds.id} ${ds.name} 设备=${ds.deviceType} 场=${ds.fieldType} 输入${ds.inputDim}维 输出${ds.outputNodes}节点 ${ds.samples}组样本]`);
    } else if (contextSwitches.value.dataset) {
      try {
        const dsRaw = localStorage.getItem('selected_dataset_id');
        if (dsRaw) parts.push(`[当前数据集ID: ${dsRaw}]`);
      } catch {}
    }

    if (contextSwitches.value.model && cd.model) {
      const m = cd.model;
      const modelDesc = m.architecture ? `${m.modelType}${m.architecture}` : m.modelType;
      const maeStr = m.mae != null ? ` MAE=${Number(m.mae).toExponential(2)}` : '';
      let paramStr = '';
      if (m.modelType === 'RF') {
        paramStr = `PCA=${m.pcaDims}维 Epoch=${m.epoch}`;
      } else {
        paramStr = `PCA=${m.pcaDims}维 ${m.optimizer} lr=${m.lr} Batch=${m.batch} Epoch=${m.epoch}`;
      }
      parts.push(`[模型: ${modelDesc} ${paramStr}${maeStr}]`);
    }

    if (contextSwitches.value.prediction) {
      if (cd.prediction) {
        const p = cd.prediction;
        if (p.isCurrentModel) {
          parts.push(`[最近预测: 模型=${p.modelType} I=${p.current}A B_max=${p.bMax}T B_min=${p.bMin}T ${String.fromCharCode(956)}=${p.bMean}T ${String.fromCharCode(963)}=${p.bStd}T]`);
        } else {
          parts.push(`[预测记录: 当前激活的${cd.model?.modelType || '当前模型'}模型暂无预测记录，请前往"实时预测"模块执行预测]`);
        }
      } else {
        parts.push(`[预测记录: ${cd.model?.modelType || '当前模型'}模型暂无预测记录，请前往"实时预测"模块执行预测]`);
      }
    }

    return parts.length > 0 ? '平台上下文: ' + parts.join(' ') : '';
  }

  // ── 发送消息（SSE 流式） ──
  async function sendMessage(content, targetMessages = null, targetStreaming = null, routeKey = null) {
    const msgs = targetMessages || messages;
    const streaming = targetStreaming || isStreaming;

    if (!content.trim()) return;
    if (streaming.value) return;

    // 确保有会话
    if (!activeConvId.value && msgs === messages) {
      newConversation();
    }

    // 追加用户消息
    msgs.value.push({
      id: 'm_' + Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toLocaleTimeString(),
    });

    // 自动更新会话标题（第一条消息时）
    if (msgs === messages && msgs.value.filter(m => m.role === 'user').length === 1) {
      const conv = conversations.value.find(c => c.id === activeConvId.value);
      if (conv && conv.title === '新对话') {
        conv.title = content.trim().slice(0, 30) + (content.length > 30 ? '...' : '');
      }
    }

    // 准备 AI 占位消息
    const aiMsgId = 'm_ai_' + Date.now();
    msgs.value.push({
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      loading: true,
    });

    streaming.value = true;

    // ── 命中预设路由 Key 时使用 Mock 响应 ──
    const mockDef = routeKey ? MOCK_ROUTES[routeKey] : null;
    if (mockDef) {
      await new Promise(r => setTimeout(r, 900)); // 模拟网络延迟
      const aiMsg = msgs.value.find(m => m.id === aiMsgId);
      if (aiMsg) {
        aiMsg.loading = false;
        aiMsg.route = mockDef.route;
        aiMsg.sources = mockDef.sources;
        // 逐字打字效果
        const fullText = mockDef.content;
        const chunkSize = 8;
        for (let i = 0; i < fullText.length; i += chunkSize) {
          aiMsg.content = fullText.slice(0, i + chunkSize);
          await new Promise(r => setTimeout(r, 18));
        }
        aiMsg.content = fullText;
      }
      streaming.value = false;
      _save();
      return;
    }

    try {
      const token = localStorage.getItem('auth_token') || '';
      const contextStr = buildContextSummary();
      const historyForApi = msgs.value
        .filter(m => !m.loading)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }));
      const messagesForApi = contextStr
        ? [{ role: 'system', content: contextStr }, ...historyForApi]
        : historyForApi;

      const res = await fetch(`${API}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          session_id: activeConvId.value || 'default',
          messages: messagesForApi,
          temperature: 0.7,
          max_tokens: 2000,
          stream: true,
          rag_enabled: ragEnabled.value,
          rag_top_k: 5,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const contentType = res.headers.get('content-type') || '';

      if (contentType.includes('text/event-stream')) {
        // SSE 流式（后端返回 JSON Lines 格式）
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const aiMsg = msgs.value.find(m => m.id === aiMsgId);
        if (aiMsg) aiMsg.loading = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const parsed = JSON.parse(line);
              if (parsed.type === 'route' && aiMsg) {
                aiMsg.route = parsed.route || null;
                aiMsg.sources = parsed.sources || { kg: [], vector: [] };
              } else if (parsed.type === 'content' && parsed.content) {
                if (aiMsg) aiMsg.content += parsed.content;
              } else if (parsed.type === 'done') {
                console.log('Stream completed:', parsed.usage);
              } else if (parsed.error) {
                throw new Error(parsed.error);
              }
            } catch {
              // 尝试兼容 data: 前缀 SSE 格式
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data !== '[DONE]') {
                  try {
                    const parsed = JSON.parse(data);
                    const delta = parsed.choices?.[0]?.delta?.content || '';
                    if (delta && aiMsg) aiMsg.content += delta;
                  } catch {}
                }
              }
            }
          }
        }
      } else {
        // 普通 JSON 响应
        const data = await res.json();
        const aiMsg = msgs.value.find(m => m.id === aiMsgId);
        if (aiMsg) {
          aiMsg.content = data.reply || data.content || data.message || JSON.stringify(data);
          aiMsg.loading = false;
        }
      }
    } catch (e) {
      console.error('AI chat error:', e);
      const aiMsg = msgs.value.find(m => m.id === aiMsgId);
      if (aiMsg) {
        aiMsg.content = '⚠️ 连接失败，请检查后端 AI 服务是否已启动。\n\n> 错误详情: ' + e.message;
        aiMsg.loading = false;
        aiMsg.error = true;
      }
    } finally {
      streaming.value = false;
      _save();
    }
  }

  // ── Markdown 渲染 ──
  function renderMarkdown(text) {
    if (!text) return '';
    try { return marked(text); } catch { return text; }
  }

  // ── 抽屉 ──
  function openDrawer() { drawerVisible.value = true; }
  function closeDrawer() { drawerVisible.value = false; }

  async function sendDrawerMessage(content) {
    await sendMessage(content, drawerMessages, isDrawerStreaming);
  }

  function expandDrawerToFull() {
    // 把抽屉消息合并到主对话
    if (drawerMessages.value.length > 0) {
      if (!activeConvId.value) newConversation();
      messages.value.push(...drawerMessages.value);
      drawerMessages.value = [];
      _save();
    }
    drawerVisible.value = false;
    router.push('/ai-chat');
  }

  // ── 知识库 ──
  async function fetchKnowledge() {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/knowledge/list`, { headers });
      const data = await res.json();
      knowledgeDocs.value = data.documents || [];
    } catch {
      knowledgeDocs.value = [];
    }
  }

  async function uploadKnowledge(file, category) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/knowledge/upload`, { method: 'POST', body: formData, headers });
      const data = await res.json();
      ElMessage.success(data.message || '文档上传成功');
      await fetchKnowledge();
      return data;
    } catch (e) {
      ElMessage.error('上传失败: ' + e.message);
    }
  }

  async function deleteKnowledge(docId) {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      await fetch(`${API}/knowledge/${docId}`, { method: 'DELETE', headers });
      knowledgeDocs.value = knowledgeDocs.value.filter(d => d.id !== docId);
      ElMessage.success('文档已删除');
    } catch (e) {
      ElMessage.error('删除失败');
    }
  }

  async function searchKnowledge(query) {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      const res = await fetch(`${API}/knowledge/search`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, top_k: 5 }),
      });
      return await res.json();
    } catch {
      return { results: [] };
    }
  }

  // ── 知识图谱 ──

  async function extractKg(docId) {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const formData = new FormData();
      formData.append('doc_id', docId);
      const res = await fetch(`${API}/knowledge/kg/extract`, {
        method: 'POST', body: formData, headers,
      });
      const data = await res.json();
      if (data.ok) ElMessage.success(data.message || '图谱抽取已提交');
      else ElMessage.warning(data.error || '抽取失败');
      return data;
    } catch (e) {
      ElMessage.error('图谱抽取失败: ' + e.message);
    }
  }

  async function getKgStats() {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/knowledge/kg/stats`, { headers });
      return await res.json();
    } catch {
      return { entities: 0, relations: 0, available: false };
    }
  }

  async function searchKg(query, maxHops = 4, limit = 5) {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      const res = await fetch(`${API}/knowledge/kg/search`, {
        method: 'POST', headers,
        body: JSON.stringify({ query, max_hops: maxHops, limit }),
      });
      return await res.json();
    } catch {
      return { results: [] };
    }
  }

  async function deleteKg(docId) {
    try {
      const token = localStorage.getItem('auth_token') || '';
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      await fetch(`${API}/knowledge/kg/${docId}`, { method: 'DELETE', headers });
      ElMessage.success('文档图谱数据已删除');
    } catch (e) {
      ElMessage.error('删除失败: ' + e.message);
    }
  }

  // ── Agent ──
  async function executeAgent(toolName, params) {
    const taskId = 'task_' + Date.now().toString(36);
    const task = {
      id: taskId,
      tool: toolName,
      params,
      status: 'running',
      startTime: new Date().toLocaleString('zh-CN'),
      steps: [{ type: 'thinking', content: `正在执行 ${toolName}...`, time: new Date().toLocaleTimeString() }],
      result: null,
    };
    agentTasks.value.unshift(task);

    try {
      const res = await fetch(`${API}/agent/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: toolName, params }),
      });
      const data = await res.json();
      task.status = data.status || 'completed';
      task.result = data;
      task.steps.push({ type: 'result', content: data.message || '执行完成', time: new Date().toLocaleTimeString() });
    } catch (e) {
      task.status = 'failed';
      task.steps.push({ type: 'error', content: '执行失败: ' + e.message, time: new Date().toLocaleTimeString() });
    }
    return task;
  }

  return {
    // 会话
    conversations, activeConvId, messages, isStreaming,
    newConversation, switchConversation, deleteConversation, renameConversation,
    // 消息
    sendMessage, renderMarkdown, contextSwitches,
    // Dynamic context
    contextData, loadContextData,
    // RAG
    ragEnabled,
    syncConversations, loadMessages,
    // 抽屉
    drawerVisible, drawerMessages, isDrawerStreaming,
    openDrawer, closeDrawer, sendDrawerMessage, expandDrawerToFull,
    // 知识库
    knowledgeDocs, fetchKnowledge, uploadKnowledge, deleteKnowledge, searchKnowledge,
    // 知识图谱
    extractKg, getKgStats, searchKg, deleteKg,
    // Agent
    agentTasks, executeAgent,
  };
}

