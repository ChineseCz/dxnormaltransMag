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

// ═══════ 单例响应式状态 ═══════
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

// 知识库
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
    if (contextSwitches.value.dataset) {
      try {
        const dsRaw = localStorage.getItem('selected_dataset_id');
        if (dsRaw) parts.push(`[当前数据集ID: ${dsRaw}]`);
      } catch {}
    }
    if (contextSwitches.value.prediction) {
      try {
        const hist = JSON.parse(localStorage.getItem('predict_history') || '[]');
        if (hist.length > 0) {
          const last = hist[0];
          parts.push(`[最近预测: ${last.modelType} 模型, ${(last.fieldValues||[]).length}个场点, ${last.timestamp}]`);
        }
      } catch {}
    }
    return parts.length > 0 ? '平台上下文: ' + parts.join(' ') : '';
  }

  // ── 发送消息（SSE 流式） ──
  async function sendMessage(content, targetMessages = null, targetStreaming = null) {
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

    try {
      const contextStr = buildContextSummary();
      const historyForApi = msgs.value
        .filter(m => !m.loading)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }));

      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: historyForApi,
          context: contextStr,
          conversation_id: activeConvId.value,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const contentType = res.headers.get('content-type') || '';

      if (contentType.includes('text/event-stream')) {
        // SSE 流式
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
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') break;
              try {
                const parsed = JSON.parse(data);
                const delta = parsed.choices?.[0]?.delta?.content || parsed.content || parsed.text || '';
                if (delta && aiMsg) {
                  aiMsg.content += delta;
                }
              } catch {
                // 纯文本 delta
                if (data && aiMsg) aiMsg.content += data;
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
      const res = await fetch(`${API}/knowledge/list`);
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
      const res = await fetch(`${API}/knowledge/upload`, { method: 'POST', body: formData });
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
      await fetch(`${API}/knowledge/${docId}`, { method: 'DELETE' });
      knowledgeDocs.value = knowledgeDocs.value.filter(d => d.id !== docId);
      ElMessage.success('文档已删除');
    } catch (e) {
      ElMessage.error('删除失败');
    }
  }

  async function searchKnowledge(query) {
    try {
      const res = await fetch(`${API}/knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      });
      return await res.json();
    } catch {
      return { results: [] };
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
    // 抽屉
    drawerVisible, drawerMessages, isDrawerStreaming,
    openDrawer, closeDrawer, sendDrawerMessage, expandDrawerToFull,
    // 知识库
    knowledgeDocs, fetchKnowledge, uploadKnowledge, deleteKnowledge, searchKnowledge,
    // Agent
    agentTasks, executeAgent,
  };
}

