<template>
  <div class="ai-chat-page flex h-full" style="background:#060d1a;">
    <!-- ═══════ 左栏：会话列表 ═══════ -->
    <div class="w-[260px] flex-shrink-0 flex flex-col border-r" style="border-color:rgba(51,65,85,0.4); background:rgba(8,14,29,0.95);">
      <!-- 新建按钮 -->
      <div class="p-3">
        <el-button class="w-full" @click="newConversation"
                   style="background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(168,85,247,0.15)); border:1px solid rgba(236,72,153,0.3); color:#f472b6; font-weight:600;">
          <el-icon class="mr-1"><Plus /></el-icon>新建对话
        </el-button>
      </div>

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto px-2 pb-2 space-y-1">
        <div v-for="conv in conversations" :key="conv.id"
             class="conv-item group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
             :class="conv.id === activeConvId ? 'conv-active' : ''"
             @click="switchConversation(conv.id)">
          <el-icon size="14" :style="`color:${conv.id === activeConvId ? '#f472b6' : '#475569'}`"><ChatDotRound /></el-icon>
          <span class="flex-1 text-xs truncate" :class="conv.id === activeConvId ? 'text-slate-200' : 'text-slate-400'">
            {{ conv.title }}
          </span>
          <el-icon size="12" class="text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-400"
                   @click.stop="deleteConversation(conv.id)"><Close /></el-icon>
        </div>
        <div v-if="conversations.length === 0" class="text-center py-10">
          <el-icon size="32" style="color:#1e293b;"><ChatDotRound /></el-icon>
          <p class="text-slate-700 text-xs mt-2">暂无对话记录</p>
        </div>
      </div>
    </div>

    <!-- ═══════ 右栏：主对话区 ═══════ -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 顶栏：标题行 + 可展开上下文面板 -->
      <div class="flex-shrink-0 border-b" style="border-color:rgba(51,65,85,0.3); background:rgba(10,18,36,0.85);">

        <!-- ── 主标题行 ── -->
        <div class="px-5 py-3 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                 style="background:linear-gradient(135deg,#ec4899,#8b5cf6); box-shadow:0 0 12px rgba(236,72,153,0.3);">
              <el-icon size="16" style="color:#fff;"><MagicStick /></el-icon>
            </div>
            <div>
              <span class="text-white font-bold text-sm">AI 智能助手</span>
<!--              <span class="text-slate-500 text-[10px] ml-2">电磁场分析专家 · RAG 增强</span>-->
            </div>
          </div>

          <div class="flex items-center gap-2">
            <!-- 模块注入开关 —— pill 按钮 -->
            <button v-for="(cfg, key) in ctxModules" :key="key"
                    class="ctx-module-btn flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium select-none transition-all"
                    :class="contextSwitches[key] ? 'ctx-module-on' : 'ctx-module-off'"
                    @click="contextSwitches[key] = !contextSwitches[key]">
              <span class="text-sm leading-none">{{ cfg.icon }}</span>
              {{ cfg.label }}
              <span class="w-1.5 h-1.5 rounded-full ml-0.5"
                    :class="contextSwitches[key] ? 'bg-green-400' : 'bg-slate-600'"></span>
            </button>

            <!-- RAG 知识库增强开关 -->
            <div class="w-px h-4 mx-1" style="background:rgba(51,65,85,0.6);"></div>
            <button class="ctx-module-btn flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium select-none transition-all"
                    :class="ragEnabled ? 'ctx-module-on' : 'ctx-module-off'"
                    @click="ragEnabled = !ragEnabled">
              <span class="text-sm leading-none">📚</span>
              RAG 知识增强
              <span class="w-1.5 h-1.5 rounded-full ml-0.5"
                    :class="ragEnabled ? 'bg-purple-400' : 'bg-slate-600'"></span>
            </button>

            <!-- 分隔线 -->
            <div class="w-px h-4 mx-1" style="background:rgba(51,65,85,0.6);"></div>

            <!-- 上下文已注入 绿色徽章（点击展开面板） -->
            <button class="ctx-badge-btn flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold select-none"
                    :class="contextPanelVisible ? 'ctx-badge-open' : ''"
                    @click="contextPanelVisible = !contextPanelVisible">
              <span class="w-2 h-2 rounded-full bg-green-400 ctx-dot"></span>
              上下文已注入
              <span class="ctx-chevron text-[9px]" :class="contextPanelVisible ? 'ctx-chevron-open' : ''">▼</span>
            </button>
          </div>
        </div>

        <!-- ── 上下文展开面板 ── -->
        <div v-if="contextPanelVisible" class="ctx-expand-panel border-t"
             style="border-color:rgba(51,65,85,0.3); background:rgba(6,12,24,0.95);">

          <!-- 面板标题栏 -->
          <div class="px-6 pt-4 pb-2 flex items-center gap-2">
            <span class="text-sm font-bold tracking-wider uppercase" style="color:#475569;">动态上下文注入模块</span>
            <span class="text-xs" style="color:#334155;">· 勾选模块后其内容将作为 System Prompt 注入 LLM</span>
          </div>

          <!-- 三列数据卡 -->
          <div class="grid grid-cols-3 gap-4 px-6 pb-4">

              <!-- 📊 数据集元数据 -->
            <div class="ctx-card rounded-xl p-4 cursor-pointer"
                 :class="!contextSwitches.dataset ? 'ctx-card-off' : 'ctx-card-on'"
                 @click="contextSwitches.dataset = !contextSwitches.dataset">
              <div class="flex items-center gap-2 mb-3">
                <span class="text-xl leading-none">📊</span>
                <span class="text-sm font-bold" style="color:#60a5fa;">数据集元数据</span>
                <div class="ml-auto flex items-center gap-1.5">
                  <!-- toggle pill -->
                  <div class="ctx-toggle-pill" :class="contextSwitches.dataset ? 'ctx-toggle-on' : 'ctx-toggle-off'">
                    <span class="ctx-toggle-thumb" :class="contextSwitches.dataset ? 'ctx-toggle-thumb-on' : ''"></span>
                  </div>
                  <span class="text-xs" :style="contextSwitches.dataset ? 'color:#34d399' : 'color:#475569'">
                    {{ contextSwitches.dataset ? '注入中' : '已关闭' }}
                  </span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="ctx-row">
                  <span class="ctx-key">Dataset ID</span>
                  <span class="ctx-val font-mono" style="color:#93c5fd; font-size:12px;">
                    {{ contextData.dataset?.id || localStorage?.getItem?.('selected_dataset_id') || '未选择' }}
                  </span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">数据集名称</span>
                  <span class="ctx-val" style="color:#a78bfa;">{{ contextData.dataset?.name || '-' }}</span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">设备类型</span>
                  <span class="ctx-val">{{ contextData.dataset?.deviceType || '-' }}</span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">场类型</span>
                  <span class="ctx-val">{{ contextData.dataset?.fieldType || '-' }}</span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">输出节点</span>
                  <span class="ctx-val" style="color:#34d399;">{{ contextData.dataset?.outputNodes || '-' }}</span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">样本总量</span>
                  <span class="ctx-val">{{ contextData.dataset?.samples || '-' }} 组</span>
                </div>
              </div>
            </div>

            <!-- ⚙️ 模型配置快照 -->
            <div class="ctx-card rounded-xl p-4 cursor-pointer"
                 :class="!contextSwitches.model ? 'ctx-card-off' : 'ctx-card-on'"
                 @click="contextSwitches.model = !contextSwitches.model">
              <div class="flex items-center gap-2 mb-3">
                <span class="text-xl leading-none">⚙️</span>
                <span class="text-sm font-bold" style="color:#fbbf24;">模型配置快照</span>
                <div class="ml-auto flex items-center gap-1.5">
                  <div class="ctx-toggle-pill" :class="contextSwitches.model ? 'ctx-toggle-on' : 'ctx-toggle-off'">
                    <span class="ctx-toggle-thumb" :class="contextSwitches.model ? 'ctx-toggle-thumb-on' : ''"></span>
                  </div>
                  <span class="text-xs" :style="contextSwitches.model ? 'color:#34d399' : 'color:#475569'">
                    {{ contextSwitches.model ? '注入中' : '已关闭' }}
                  </span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="ctx-row">
                  <span class="ctx-key">架构</span>
                  <span class="ctx-val font-mono" style="font-size:12px;">
                    {{ contextData.model ? `${contextData.model.modelType}${contextData.model.architecture || ''}` : '-' }}
                  </span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">PCA 主成分</span>
                  <span class="ctx-val" style="color:#fbbf24;">{{ contextData.model?.pcaDims || '-' }} 维</span>
                </div>
                <div v-if="contextData.model?.modelType !== 'RF'" class="ctx-row">
                  <span class="ctx-key">优化器</span>
                  <span class="ctx-val">{{ contextData.model ? `${contextData.model.optimizer} · lr=${contextData.model.lr}` : '-' }}</span>
                </div>
                <div class="ctx-row">
                  <span class="ctx-key">Batch / Epoch</span>
                  <span class="ctx-val">{{ contextData.model ? `${contextData.model.batch} / ${contextData.model.epoch}` : '-' }}</span>
                </div>
                <div v-if="contextData.model?.mae != null" class="ctx-row">
                  <span class="ctx-key">MAE</span>
                  <span class="ctx-val" style="color:#34d399;">{{ Number(contextData.model.mae).toExponential(2) }}</span>
                </div>
              </div>
            </div>

            <!-- 📈 最近预测结果 -->
            <div class="ctx-card rounded-xl p-4 cursor-pointer"
                 :class="!contextSwitches.prediction ? 'ctx-card-off' : 'ctx-card-on'"
                 @click="contextSwitches.prediction = !contextSwitches.prediction">
              <div class="flex items-center gap-2 mb-3">
                <span class="text-xl leading-none">📈</span>
                <span class="text-sm font-bold" style="color:#34d399;">最近预测结果</span>
                <div class="ml-auto flex items-center gap-1.5">
                  <div class="ctx-toggle-pill" :class="contextSwitches.prediction ? 'ctx-toggle-on' : 'ctx-toggle-off'">
                    <span class="ctx-toggle-thumb" :class="contextSwitches.prediction ? 'ctx-toggle-thumb-on' : ''"></span>
                  </div>
                  <span class="text-xs" :style="contextSwitches.prediction ? 'color:#34d399' : 'color:#475569'">
                    {{ contextSwitches.prediction ? '注入中' : '已关闭' }}
                  </span>
                </div>
              </div>
              <div class="space-y-2">
                <!-- 当前模型有预测记录 -->
                <template v-if="contextData.prediction && contextData.prediction.isCurrentModel">
                  <div class="ctx-row">
                    <span class="ctx-key">模型类型</span>
                    <span class="ctx-val" style="color:#fbbf24;">{{ contextData.prediction.modelType || '-' }}</span>
                  </div>
                  <div class="ctx-row">
                    <span class="ctx-key">激励电流</span>
                    <span class="ctx-val" style="color:#fbbf24;">{{ contextData.prediction.current != null ? contextData.prediction.current + ' A' : '-' }}</span>
                  </div>
                  <div class="ctx-row">
                    <span class="ctx-key">B_max</span>
                    <span class="ctx-val" style="color:#f87171;">{{ contextData.prediction.bMax != null ? contextData.prediction.bMax + ' T' : '-' }}</span>
                  </div>
                  <div class="ctx-row">
                    <span class="ctx-key">B_min</span>
                    <span class="ctx-val">{{ contextData.prediction.bMin != null ? contextData.prediction.bMin + ' T' : '-' }}</span>
                  </div>
                  <div class="ctx-row">
                    <span class="ctx-key">均值 μ</span>
                    <span class="ctx-val">{{ contextData.prediction.bMean != null ? contextData.prediction.bMean + ' T' : '-' }}</span>
                  </div>
                  <div class="ctx-row">
                    <span class="ctx-key">标准差 σ</span>
                    <span class="ctx-val">{{ contextData.prediction.bStd != null ? contextData.prediction.bStd + ' T' : '-' }}</span>
                  </div>
                  <div v-if="contextData.prediction.timestamp" class="ctx-row">
                    <span class="ctx-key">时间</span>
                    <span class="ctx-val" style="font-size:11px; color:#475569;">{{ contextData.prediction.timestamp }}</span>
                  </div>
                </template>

                <!-- 当前模型无预测记录 -->
                <template v-else>
                  <div class="flex flex-col items-center justify-center py-6 px-4 text-center">
                    <div class="text-4xl mb-3">🔮</div>
                    <div class="text-sm font-medium mb-2" style="color:#94a3b8;">
                      当前激活的 {{ contextData.model?.modelType || '模型' }} 暂无预测记录
                    </div>
                    <div class="text-xs mb-3" style="color:#64748b;">
                      请前往"实时预测"模块执行预测操作
                    </div>
                    <button
                      @click.stop="$router.push('/predict/setup')"
                      class="px-4 py-2 rounded-lg text-xs font-medium transition-all"
                      style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);"
                      @mouseenter="$event.target.style.background='rgba(16,185,129,0.25)'"
                      @mouseleave="$event.target.style.background='rgba(16,185,129,0.15)'">
                      前往预测模块 →
                    </button>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- System Prompt 注入片段预览 -->
          <div class="mx-6 mb-4 rounded-xl overflow-hidden"
               style="border:1px solid rgba(51,65,85,0.5); background:rgba(0,0,0,0.5);">
            <div class="px-4 py-2 flex items-center gap-2 border-b"
                 style="border-color:rgba(51,65,85,0.4); background:rgba(15,23,42,0.6);">
              <span class="w-2 h-2 rounded-full bg-yellow-400" style="animation:ctxPulse 2s ease-in-out infinite;"></span>
              <span class="text-xs font-bold tracking-wide" style="color:#94a3b8;">System Prompt 注入片段预览</span>
              <span class="text-[11px]" style="color:#334155;">— 切换上方模块开关，文本实时变化</span>
              <!-- 注入数量徽章 -->
              <span class="ml-auto px-2 py-0.5 rounded-full text-xs font-bold"
                    style="background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.25);">
                {{ [contextSwitches.dataset, contextSwitches.model, contextSwitches.prediction, ragEnabled].filter(Boolean).length }} / 4 模块已注入
              </span>
            </div>
            <div class="px-4 py-3">
              <p class="text-xs leading-relaxed break-all whitespace-pre-wrap"
                 style="font-family:'JetBrains Mono',ui-monospace,monospace; color:#64748b; line-height:1.8;">{{ systemPromptText }}</p>
            </div>
          </div>

        </div>

      </div>

      <!-- 消息列表 -->
      <div ref="messageListRef" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <!-- 欢迎屏幕 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
               style="background:linear-gradient(135deg,rgba(236,72,153,0.1),rgba(139,92,246,0.1)); border:1px solid rgba(236,72,153,0.15);">
            <el-icon size="32" style="color:#f472b6;"><MagicStick /></el-icon>
          </div>
          <h2 class="text-xl font-bold mb-2"
              style="background:linear-gradient(90deg,#f472b6,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            你好，我是电磁场预测平台AI助手
          </h2>
          <p class="text-slate-500 text-sm mb-8 text-center max-w-md">
            我可以帮你分析预测结果、解答电气设备电磁场相关问题、推荐模型参数等。
          </p>

          <!-- 预设 Prompt 快捷卡片 -->
          <div class="grid grid-cols-2 gap-3 w-full max-w-lg">
            <div v-for="(p, idx) in presetPrompts" :key="idx"
                 class="prompt-card p-3 rounded-xl cursor-pointer group"
                 @click="handlePreset(p.content, p.routeKey)">
              <div class="flex items-center gap-2 mb-1.5">
                <span class="text-base">{{ p.icon }}</span>
                <span class="text-xs font-bold" :style="`color:${p.color}`">{{ p.title }}</span>
              </div>
              <!-- 轨道标记小标签 -->
              <div class="flex gap-1 mb-1">
                <span v-for="badge in p.badges" :key="badge.label"
                      class="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold"
                      :style="`background:${badge.bg}; color:${badge.color}; border:1px solid ${badge.border};`">
                  {{ badge.icon }} {{ badge.label }}
                </span>
              </div>
              <p class="text-[11px] text-slate-500 leading-relaxed group-hover:text-slate-400 transition-colors">{{ p.desc }}</p>
            </div>
          </div>
        </div>

        <!-- 消息气泡 -->
        <template v-for="msg in messages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="flex justify-end gap-3">
            <div class="max-w-[70%]">
              <div class="px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed"
                   style="background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(139,92,246,0.15)); border:1px solid rgba(236,72,153,0.2); color:#e2e8f0;">
                {{ msg.content }}
              </div>
              <div class="text-[10px] text-slate-600 mt-1 text-right">{{ msg.timestamp }}</div>
            </div>
            <div class="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-[10px] font-bold"
                 style="background:linear-gradient(135deg,#3b82f6,#8b5cf6); color:white;">U</div>
          </div>

          <!-- AI 消息 -->
          <div v-else class="flex gap-3">
            <div class="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center"
                 style="background:linear-gradient(135deg,#ec4899,#8b5cf6);">
              <el-icon size="13" style="color:#fff;"><MagicStick /></el-icon>
            </div>
            <div class="max-w-[75%] min-w-[200px]">
              <!-- 加载状态 -->
              <div v-if="msg.loading" class="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-bl-md"
                   style="background:rgba(15,23,42,0.6); border:1px solid rgba(51,65,85,0.3);">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                <span class="text-slate-500 text-xs">思考中...</span>
              </div>
              <!-- 正常内容 -->
              <div v-else class="px-4 py-3 rounded-2xl rounded-bl-md ai-msg-bubble"
                   :class="msg.error ? 'ai-msg-error' : ''">
                <!-- ── 路由徽章栏 ── -->
                <div v-if="msg.route && msg.route.badges && msg.route.badges.length"
                     class="flex flex-wrap gap-1.5 mb-2.5">
                  <span v-for="badge in msg.route.badges" :key="badge.label"
                        class="route-badge inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                        :style="`background:${badge.bg}; color:${badge.color}; border:1px solid ${badge.border};`">
                    {{ badge.icon }} {{ badge.label }}
                  </span>
                </div>
                <div class="ai-markdown text-sm leading-relaxed" v-html="renderMarkdown(msg.content)"></div>
              </div>

              <!-- ── 展开检索来源 折叠面板 ── -->
              <div v-if="!msg.loading && msg.sources && (msg.sources.kg?.length || msg.sources.vector?.length)"
                   class="mt-1.5">
                <button class="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
                        @click="toggleSources(msg.id)">
                  <span class="source-arrow" :class="expandedSources.has(msg.id) ? 'expanded' : ''">▶</span>
                  展开检索来源
                  <span v-if="msg.sources.kg?.length" class="ml-1 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px]"
                        style="background:rgba(139,92,246,0.15);color:#a78bfa;border:1px solid rgba(139,92,246,0.25);">
                    🕸️ KG {{ msg.sources.kg.length }}条
                  </span>
                  <span v-if="msg.sources.vector?.length" class="ml-0.5 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px]"
                        style="background:rgba(59,130,246,0.15);color:#60a5fa;border:1px solid rgba(59,130,246,0.25);">
                    📄 向量 {{ msg.sources.vector.length }}段
                  </span>
                </button>

                <!-- 展开内容 -->
                <div v-if="expandedSources.has(msg.id)" class="sources-panel mt-1.5 rounded-xl overflow-hidden"
                     style="border:1px solid rgba(51,65,85,0.4);">
                  <!-- KG 来源 -->
                  <div v-if="msg.sources.kg?.length" class="p-3"
                       style="background:rgba(88,28,135,0.08); border-bottom:1px solid rgba(139,92,246,0.15);">
                    <div class="flex items-center gap-1.5 mb-2">
                      <span class="text-[10px] font-bold" style="color:#a78bfa;">🕸️ 知识图谱轨道 · 因果链三元组</span>
                    </div>
                    <div v-for="(triple, ti) in msg.sources.kg" :key="ti"
                         class="kg-triple flex items-center gap-1 text-[11px] mb-1 last:mb-0">
                      <template v-for="(node, ni) in triple.chain" :key="ni">
                        <span class="kg-node px-1.5 py-0.5 rounded"
                              :style="ni === 0 ? 'background:rgba(139,92,246,0.2);color:#c084fc;border:1px solid rgba(139,92,246,0.3);'
                                    : ni === triple.chain.length-1 ? 'background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25);'
                                    : 'background:rgba(251,191,36,0.1);color:#fbbf24;border:1px solid rgba(251,191,36,0.2);'">
                          {{ node }}
                        </span>
                        <span v-if="ni < triple.chain.length-1" class="text-slate-600">→</span>
                      </template>
                      <span v-if="triple.confidence" class="ml-auto text-[9px]" style="color:#64748b;">
                        置信度 {{ triple.confidence }}
                      </span>
                    </div>
                  </div>
                  <!-- 向量来源 -->
                  <div v-if="msg.sources.vector?.length" class="p-3"
                       style="background:rgba(30,58,138,0.08);">
                    <div class="flex items-center gap-1.5 mb-2">
                      <span class="text-[10px] font-bold" style="color:#60a5fa;">📄 FAISS 向量轨道 · 召回文档</span>
                    </div>
                    <div v-for="(doc, di) in msg.sources.vector" :key="di"
                         class="vector-doc mb-2 last:mb-0 p-2 rounded-lg"
                         style="background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.12);">
                      <div class="flex items-center justify-between mb-1">
                        <span class="text-[10px] font-semibold" style="color:#93c5fd;">{{ doc.title }}</span>
                        <div class="flex items-center gap-1">
                          <div class="similarity-bar" :style="`width:${Math.round(doc.similarity*50)}px`"></div>
                          <span class="text-[9px]" style="color:#64748b;">余弦相似度 {{ (doc.similarity*100).toFixed(1) }}%</span>
                        </div>
                      </div>
                      <p class="text-[10px] leading-relaxed" style="color:#94a3b8;">{{ doc.excerpt }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="text-[10px] text-slate-600 mt-1">{{ msg.timestamp }}</div>
            </div>
          </div>
        </template>

        <!-- 流式输出时的滚动锚点 -->
        <div ref="scrollAnchorRef"></div>
      </div>

      <!-- 输入区 -->
      <div class="flex-shrink-0 px-5 pb-4 pt-2">
        <!-- 快捷 Prompt 条（已隐藏）-->
        <!-- <div v-if="messages.length > 0" class="flex gap-2 mb-2 overflow-x-auto pb-1">
          <span v-for="(q, i) in quickActions" :key="i"
                class="quick-chip flex-shrink-0 px-2.5 py-1 rounded-full text-[10px] cursor-pointer"
                @click="handlePreset(q.content)">
            {{ q.icon }} {{ q.label }}
          </span>
        </div> -->

        <div class="flex items-end gap-3">
          <div class="flex-1 relative">
            <el-input v-model="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 5 }"
                      placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
                      @keydown="handleKeydown" resize="none"
                      class="chat-input" />
          </div>
          <el-button :loading="isStreaming" :disabled="!inputText.trim() || isStreaming"
                     @click="handleSend" circle size="large"
                     style="background:linear-gradient(135deg,#ec4899,#8b5cf6); border:none; width:44px; height:44px;">
            <el-icon size="18" style="color:white;"><Promotion /></el-icon>
          </el-button>
        </div>
        <div class="text-center mt-2">
          <span class="text-[10px] text-slate-700">AI 回答可能存在误差，重要决策请结合专业判断</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import {
  Plus, Close, ChatDotRound, MagicStick, Promotion,
} from '@element-plus/icons-vue';
import { useAiStore } from '../../composables/useAiStore.js';

const {
  conversations, activeConvId, messages, isStreaming,
  newConversation, switchConversation, deleteConversation,
  syncConversations, loadMessages,
  sendMessage, renderMarkdown, contextSwitches,
  contextData, loadContextData,
  ragEnabled,
} = useAiStore();

const inputText = ref('');
const messageListRef = ref(null);
const scrollAnchorRef = ref(null);

// 展开检索来源的消息 id 集合
const expandedSources = ref(new Set());
function toggleSources(msgId) {
  const s = new Set(expandedSources.value);
  s.has(msgId) ? s.delete(msgId) : s.add(msgId);
  expandedSources.value = s;
}

// ── 上下文面板 ──
const contextPanelVisible = ref(false);

// 模块配置（用于标题栏 pill 按钮）
const ctxModules = {
  dataset:    { icon: '📊', label: '数据集' },
  model:      { icon: '⚙️', label: '模型'   },
  prediction: { icon: '📈', label: '预测'   },
};

// System Prompt 注入预览（随开关动态变化）
const systemPromptText = computed(() => {
  const sw = contextSwitches.value;
  const cd = contextData.value;
  const parts = [];

  if (sw.dataset) {
    if (cd.dataset) {
      const ds = cd.dataset;
      parts.push(`[数据集: ${ds.id} · ${ds.name} · 设备=${ds.deviceType} · 场=${ds.fieldType} · 输出${ds.outputNodes}节点 · ${ds.samples}组样本]`);
    } else {
      const dsId = localStorage.getItem?.('selected_dataset_id');
      if (dsId) parts.push(`[数据集ID: ${dsId}]`);
    }
  }
  if (sw.model) {
    if (cd.model) {
      const m = cd.model;
      const arch = m.hiddenLayers?.length ? `[${m.hiddenLayers.join(',')}]` : m.modelType;
      parts.push(`[模型: ${m.modelType}${arch} · PCA=${m.pcaDims}维 · ${m.optimizer} lr=${m.lr} · Batch=${m.batch} · Epoch=${m.epoch}]`);
    }
  }
  if (sw.prediction) {
    if (cd.prediction) {
      const p = cd.prediction;
      parts.push(`[最近预测: I=${p.current}A · B_max=${p.bMax}T · B_min=${p.bMin}T · μ=${p.bMean}T · σ=${p.bStd}T]`);
    }
  }

  if (parts.length === 0) {
    return '# 所有上下文模块已关闭 — 当前为纯文本对话模式，无平台上下文注入';
  }
  return '平台上下文: ' + parts.join(' ');
});

// 预设 Prompt 快捷卡片（双轨路由演示）
const presetPrompts = [
  {
    icon: '🔍', title: '故障溯源', color: '#a78bfa',
    routeKey: 'fault_trace',
    badges: [
      { icon: '🕸️', label: 'KG 图谱', bg: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
    ],
    desc: 'Reactor→Winding→Fault_Cause 三跳因果路径检索',
    content: '电抗器在 280 A 工况下中部绕组区域磁通密度 B 值较正常工况偏低约 12%，请帮我进行匝间短路故障溯源分析。',
  },
  {
    icon: '⚡', title: '调参排错', color: '#fbbf24',
    routeKey: 'tune_debug',
    badges: [
      { icon: '🕸️', label: 'KG 图谱', bg: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
    ],
    desc: 'Problem→Algorithm_Param→Solution 算法维度路径',
    content: '电抗器 DNN 模型在低电流区间（100~300 A）的 MAPE 偏高，请通过知识图谱帮我排查参数配置问题并给出优化建议。',
  },
  {
    icon: '📖', title: '规程查询', color: '#60a5fa',
    routeKey: 'regulation_query',
    badges: [
      { icon: '📄', label: 'FAISS 向量', bg: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: 'rgba(59,130,246,0.3)' },
    ],
    desc: '相似度 93.6% · 向量知识库召回匝间短路诊断规程',
    content: '请查询铁心电抗器匝间短路的标准诊断规程与绕组绝缘检测方法。',
  },
  {
    icon: '🔄', title: '综合诊断（双轨并发）', color: '#34d399',
    routeKey: 'dual_track',
    badges: [
      { icon: '🕸️', label: 'KG', bg: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
      { icon: '📄', label: '向量', bg: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: 'rgba(59,130,246,0.3)' },
      { icon: '⚡', label: '并发', bg: 'rgba(251,191,36,0.12)', color: '#fbbf24', border: 'rgba(251,191,36,0.25)' },
    ],
    desc: '异步并发双轨检索 + 结果融合输出',
    content: '请对当前电抗器设备进行综合智能诊断，结合 DNN 磁场预测结果与知识库，同时调用知识图谱和向量知识库双轨检索。',
  },
];

const quickActions = [
  { icon: '📊', label: '分析损失曲线', content: '当前模型的训练损失曲线是否正常？有没有过拟合或欠拟合的迹象？' },
  { icon: '🔧', label: '调参建议', content: '训练效果不太好，请给我一些超参数调优的建议。' },
  { icon: '📈', label: '对比模型', content: '帮我对比 DNN 和 CNN 在当前电磁场预测任务中的优劣。' },
  { icon: '❓', label: '平台使用', content: '请介绍一下这个平台的主要功能模块和使用流程。' },
];

function handlePreset(content, routeKey) {
  inputText.value = content;
  sendMessageWithRoute(content, routeKey);
}

function sendMessageWithRoute(text, routeKey) {
  if (!text.trim() || isStreaming.value) return;
  inputText.value = '';
  sendMessage(text, null, null, routeKey);
}

function handleSend() {
  if (!inputText.value.trim() || isStreaming.value) return;
  const text = inputText.value;
  inputText.value = '';
  sendMessage(text);
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

// 自动滚动
watch(
  () => messages.value.length > 0 ? messages.value[messages.value.length - 1]?.content : '',
  () => {
    nextTick(() => {
      scrollAnchorRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  },
  { flush: 'post' }
);

// 如果没有会话则自动创建
onMounted(async () => {
  // 先从后端同步会话列表
  await syncConversations();

  if (conversations.value.length === 0) {
    newConversation();
  } else if (!activeConvId.value) {
    await switchConversation(conversations.value[0].id);
  } else if (messages.value.length === 0) {
    // 当前会话消息为空时，从后端拉取
    await loadMessages(activeConvId.value);
  }

  await loadContextData();
});
</script>

<style scoped>
.ai-chat-page { height: calc(100vh - 56px); }

/* 会话列表 */
.conv-item:hover { background: rgba(236,72,153,0.05); }
.conv-active { background: rgba(236,72,153,0.1) !important; border-left: 2px solid #ec4899; }

/* ── 模块切换 pill 按钮（标题栏） ── */
.ctx-module-btn { cursor: pointer; }
.ctx-module-on {
  background: rgba(16,185,129,0.12);
  color: #a7f3d0;
  border: 1px solid rgba(16,185,129,0.3);
}
.ctx-module-on:hover { background: rgba(16,185,129,0.2); }
.ctx-module-off {
  background: rgba(30,41,59,0.6);
  color: #475569;
  border: 1px solid rgba(51,65,85,0.3);
}
.ctx-module-off:hover { color: #64748b; border-color: rgba(71,85,105,0.5); }

/* ── 上下文已注入徽章 ── */
.ctx-badge-btn {
  background: rgba(16,185,129,0.12);
  color: #34d399;
  border: 1px solid rgba(16,185,129,0.3);
  transition: all 0.2s ease;
  cursor: pointer;
}
.ctx-badge-btn:hover { background: rgba(16,185,129,0.2); border-color: rgba(16,185,129,0.45); }
.ctx-badge-open {
  background: rgba(16,185,129,0.22) !important;
  border-color: rgba(16,185,129,0.5) !important;
  box-shadow: 0 0 10px rgba(16,185,129,0.15);
}
.ctx-dot { animation: ctxPulse 2s ease-in-out infinite; }
@keyframes ctxPulse {
  0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(52,211,153,0.4); }
  50%      { opacity:0.7; box-shadow:0 0 0 4px rgba(52,211,153,0); }
}
.ctx-chevron { display:inline-block; font-size:8px; transition:transform 0.25s ease; }
.ctx-chevron-open { transform: rotate(180deg); }

/* ── 展开面板 ── */
.ctx-expand-panel { animation: ctxSlideDown 0.22s ease; }
@keyframes ctxSlideDown {
  from { opacity:0; transform:translateY(-6px); }
  to   { opacity:1; transform:translateY(0); }
}

/* ── 数据卡 ── */
.ctx-card {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.4);
  transition: all 0.2s ease;
}
.ctx-card-on  { border-color: rgba(71,85,105,0.5); }
.ctx-card-off { opacity: 0.35; filter: grayscale(0.5); pointer-events: none; }
.ctx-card:not(.ctx-card-off):hover { border-color: rgba(100,116,139,0.6); background: rgba(15,23,42,0.75); }

/* ── Toggle pill（卡片内） ── */
.ctx-toggle-pill {
  width: 28px; height: 15px;
  border-radius: 999px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}
.ctx-toggle-on  { background: rgba(16,185,129,0.4); border:1px solid rgba(16,185,129,0.5); }
.ctx-toggle-off { background: rgba(51,65,85,0.5);   border:1px solid rgba(71,85,105,0.3); }
.ctx-toggle-thumb {
  position: absolute; top: 2px; left: 2px;
  width: 9px; height: 9px;
  border-radius: 50%;
  background: #475569;
  transition: all 0.2s ease;
}
.ctx-toggle-thumb-on { left: 15px; background: #34d399; }

/* ── 卡片行 ── */
.ctx-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}
.ctx-key {
  font-size: 12px;
  color: #475569;
  flex-shrink: 0;
  white-space: nowrap;
}
.ctx-val {
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
}

/* Prompt 卡片 */
.prompt-card {
  background: rgba(15,23,42,0.5);
  border: 1px solid rgba(51,65,85,0.3);
  transition: all 0.2s ease;
}
.prompt-card:hover {
  border-color: rgba(236,72,153,0.3);
  background: rgba(15,23,42,0.7);
  transform: translateY(-2px);
}

/* AI 消息气泡 */
.ai-msg-bubble {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.3);
}
.ai-msg-error {
  border-color: rgba(239,68,68,0.3) !important;
  background: rgba(239,68,68,0.06) !important;
}

/* Markdown 样式 */
.ai-markdown :deep(p) { margin: 0.4em 0; color: #cbd5e1; }
.ai-markdown :deep(strong) { color: #f1f5f9; font-weight: 700; }
.ai-markdown :deep(code) {
  background: rgba(59,130,246,0.1); color: #93c5fd; padding: 1px 5px;
  border-radius: 4px; font-size: 0.85em; font-family: 'JetBrains Mono', monospace;
}
.ai-markdown :deep(pre) {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(51,65,85,0.4);
  border-radius: 8px; padding: 12px; margin: 8px 0; overflow-x: auto;
}
.ai-markdown :deep(pre code) { background: none; padding: 0; color: #e2e8f0; }
.ai-markdown :deep(ul), .ai-markdown :deep(ol) { padding-left: 1.2em; margin: 0.4em 0; color: #94a3b8; }
.ai-markdown :deep(li) { margin: 2px 0; }
.ai-markdown :deep(blockquote) {
  border-left: 3px solid rgba(236,72,153,0.4); padding-left: 12px;
  margin: 8px 0; color: #64748b; font-style: italic;
}
.ai-markdown :deep(h1), .ai-markdown :deep(h2), .ai-markdown :deep(h3) {
  color: #e2e8f0; margin: 0.6em 0 0.3em; font-weight: 700;
}
.ai-markdown :deep(table) { border-collapse: collapse; margin: 8px 0; width: 100%; }
.ai-markdown :deep(th), .ai-markdown :deep(td) {
  border: 1px solid rgba(51,65,85,0.4); padding: 6px 10px; font-size: 0.85em;
}
.ai-markdown :deep(th) { background: rgba(15,23,42,0.6); color: #94a3b8; }
.ai-markdown :deep(td) { color: #cbd5e1; }

/* 打字动画 */
.typing-dots { display: flex; gap: 4px; }
.typing-dots span {
  width: 6px; height: 6px; border-radius: 50%;
  background: #64748b; animation: blink 1.4s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

/* 快捷标签 */
.quick-chip {
  background: rgba(15,23,42,0.6);
  border: 1px solid rgba(51,65,85,0.3);
  color: #94a3b8;
  transition: all 0.15s;
}
.quick-chip:hover {
  border-color: rgba(236,72,153,0.3);
  color: #f472b6;
  background: rgba(236,72,153,0.06);
}

/* 路由徽章 */
.route-badge {
  letter-spacing: 0.02em;
  backdrop-filter: blur(4px);
}

/* 展开检索来源 */
.source-arrow {
  display: inline-block;
  transition: transform 0.2s ease;
  font-size: 8px;
}
.source-arrow.expanded { transform: rotate(90deg); }

.sources-panel {
  background: rgba(8,14,29,0.8);
  animation: slideDown 0.2s ease;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* KG 节点 */
.kg-triple { flex-wrap: wrap; }
.kg-node { font-size: 10px; font-weight: 600; }

/* 相似度进度条 */
.similarity-bar {
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  min-width: 8px;
}

/* 输入框暗色 */
.chat-input :deep(.el-textarea__inner) {
  background: rgba(15,23,42,0.6) !important;
  border: 1px solid rgba(51,65,85,0.4) !important;
  color: #e2e8f0 !important;
  border-radius: 16px !important;
  padding: 10px 16px !important;
  box-shadow: none !important;
  font-size: 14px;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: rgba(236,72,153,0.4) !important;
}
</style>

