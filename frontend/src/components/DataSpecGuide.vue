<template>
  <div class="max-w-6xl mx-auto">
    <!-- 快速选择器 -->
    <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">📋 数据格式快速选择</h2>
      <p class="text-gray-600 mb-4">选择您的数据场景，查看对应的上传指南：</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          v-for="scenario in scenarios"
          :key="scenario.id"
          @click="selectedScenario = scenario.id"
          :class="[
            'p-4 rounded-lg border-2 transition-all text-left',
            selectedScenario === scenario.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300'
          ]"
        >
          <div class="text-2xl mb-2">{{ scenario.icon }}</div>
          <div class="font-semibold text-gray-800">{{ scenario.title }}</div>
          <div class="text-sm text-gray-500 mt-1">{{ scenario.desc }}</div>
          <div class="text-xs text-blue-600 mt-2">
            模式：<span class="font-mono">{{ scenario.mode }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- 详细说明 -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <div v-if="selectedScenario === 'reactor'">
        <h3 class="text-lg font-semibold mb-3 flex items-center">
          <span class="text-2xl mr-2">🔌</span>
          场景一：电抗器参数化数据（最简单）
        </h3>

        <div class="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <div class="font-semibold text-yellow-800 mb-1">✅ 推荐用于</div>
          <div class="text-sm text-yellow-700">
            COMSOL 参数化扫描、每个工况单独导出一个文件的场景
          </div>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">数据文件结构：</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>电抗器/
  ├─ 100[A].txt     ← 电流100A时的磁场分布
  ├─ 200[A].txt     ← 电流200A时的磁场分布
  ├─ 300[A].txt
  └─ ...</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">单文件内容示例：</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>% Dimension: 2
% Nodes: 91462
% r         z         Color
0.1        0.5       0.025
0.15       0.5       0.032
...</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">创建数据集设置：</h4>
          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">坐标系</div>
              <div class="font-mono font-semibold">rz</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">数据组织方式</div>
              <div class="font-mono font-semibold">perfile</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">坐标列数</div>
              <div class="font-mono font-semibold">2</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">输入变量</div>
              <div class="font-mono font-semibold">1个（电流I）</div>
            </div>
          </div>
        </div>

        <div class="p-4 bg-green-50 border border-green-200 rounded">
          <h4 class="font-semibold text-green-800 mb-2">⚡ 关键操作</h4>
          <ul class="text-sm text-green-700 space-y-1">
            <li>• 上传时系统自动从文件名提取工况值（100, 200, ...）</li>
            <li>• 所有文件角色设为 <code class="bg-white px-1 rounded">output</code></li>
            <li>• 处理时选择"装配"（无需设置时间参数）</li>
          </ul>
        </div>
      </div>

      <div v-else-if="selectedScenario === 'transformer'">
        <h3 class="text-lg font-semibold mb-3 flex items-center">
          <span class="text-2xl mr-2">⚡</span>
          场景二：单相变压器时域数据
        </h3>

        <div class="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <div class="font-semibold text-yellow-800 mb-1">✅ 推荐用于</div>
          <div class="text-sm text-yellow-700">
            COMSOL 时域仿真、单个工况包含多个时间步的数据
          </div>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">数据文件结构：</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>单相变压器磁场/raw data/
  ├─ mag-100-10k-50-0.2-0.0005.txt      ← 磁场（1241点 × 400时间步）
  ├─ primcur-100-10k-50-0.2-0.0005.txt  ← 初级电流
  └─ seccur-100-10k-50-0.2-0.0005.txt   ← 次级电流</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">磁场文件示例（列头显示时间）：</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>% Dimension: 3
% Nodes: 1241
% x    y    z    mf.normB@t=0  mf.normB@t=0.0005  ...  mf.normB@t=0.2
0.1   0.2  0.0  0.035         0.042              ...  0.038</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">创建数据集设置：</h4>
          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">坐标系</div>
              <div class="font-mono font-semibold">xyz</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">数据组织方式</div>
              <div class="font-mono font-semibold">multicolumn</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">坐标列数</div>
              <div class="font-mono font-semibold">3</div>
            </div>
            <div class="p-3 bg-blue-50 rounded">
              <div class="text-xs text-gray-600">时间步长</div>
              <div class="font-mono font-semibold">0.0005 s</div>
            </div>
          </div>
        </div>

        <div class="p-4 bg-green-50 border border-green-200 rounded">
          <h4 class="font-semibold text-green-800 mb-2">⚡ 关键操作</h4>
          <ul class="text-sm text-green-700 space-y-1">
            <li>• 上传顺序：先上传 output（磁场），再上传 input（电流）</li>
            <li>• 输入文件需指定 <code class="bg-white px-1 rounded">variableIndex</code>（0, 1, ...）</li>
            <li>• 处理时设置稳态截取区间（t0 → tEnd）</li>
            <li>• 可使用"自动检测稳态"功能</li>
          </ul>
        </div>
      </div>

      <div v-else-if="selectedScenario === 'temperature'">
        <h3 class="text-lg font-semibold mb-3 flex items-center">
          <span class="text-2xl mr-2">🌡️</span>
          场景三：变压器温升数据（多参数文件名）
        </h3>

        <div class="mb-4 p-4 bg-orange-50 border border-orange-200 rounded">
          <div class="font-semibold text-orange-800 mb-1">⚠️ 特殊处理</div>
          <div class="text-sm text-orange-700">
            文件名包含多个参数时，需要预处理或手动设置工况值
          </div>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">数据文件结构：</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>变压器温升计算/导出数据/
  ├─ 1158.6_865.8.txt   ← P1=1158.6W, P2=865.8W
  ├─ 1190.7_889.85.txt
  └─ ...</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">解决方案 A：批量重命名（推荐）</h4>
          <pre class="bg-gray-900 text-green-400 p-3 rounded text-sm overflow-x-auto"><code>Python 脚本：
import os, re
for fname in os.listdir("path/to/data"):
    m = re.search(r'^([\d.]+)_[\d.]+\.txt', fname)
    if m:
        os.rename(fname, f"{m.group(1)}[W].txt")
# 结果：1158.6_865.8.txt → 1158.6[W].txt</code></pre>
        </div>

        <div class="mb-4">
          <h4 class="font-semibold mb-2">解决方案 B：手动设置工况值</h4>
          <ol class="text-sm text-gray-700 space-y-1 list-decimal list-inside">
            <li>先批量上传原始文件</li>
            <li>在文件列表中逐个点击"编辑"</li>
            <li>手动填写"工况值"（如 1158.6）</li>
          </ol>
        </div>

        <div class="p-4 bg-blue-50 border border-blue-200 rounded">
          <h4 class="font-semibold text-blue-800 mb-2">📌 未来版本支持</h4>
          <div class="text-sm text-blue-700">
            v1.1 将支持多参数文件名自动解析（如 P1_P2.txt）
          </div>
        </div>
      </div>
    </div>

    <!-- 通用注意事项 -->
    <div class="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
      <h3 class="text-lg font-semibold mb-3">💡 通用注意事项</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 class="font-semibold text-sm mb-2">✅ 必须满足</h4>
          <ul class="text-sm text-gray-700 space-y-1">
            <li>• 文件是 COMSOL 标准导出格式（含 % 元数据）</li>
            <li>• 文件编码为 UTF-8 或 ASCII</li>
            <li>• perfile 模式：所有文件空间节点数一致</li>
            <li>• multicolumn 模式：时间步长准确</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold text-sm mb-2">❌ 常见错误</h4>
          <ul class="text-sm text-gray-700 space-y-1">
            <li>• 坐标系选择错误（2D用rz，3D用xyz）</li>
            <li>• 坐标列数设置错误</li>
            <li>• perfile 文件名不以数字开头</li>
            <li>• 输入文件未指定 variableIndex</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 快速链接 -->
    <div class="mt-6 flex gap-4">
      <button
        @click="openDocs('full')"
        class="flex-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 transition-all cursor-pointer"
      >
        <div class="font-semibold mb-1">📖 完整规范文档</div>
        <div class="text-xs text-gray-500">查看所有数据格式、坐标系定义、FAQ</div>
      </button>
      <button
        @click="openDocs('quick')"
        class="flex-1 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 transition-all cursor-pointer"
      >
        <div class="font-semibold mb-1">🚀 快速上手指南</div>
        <div class="text-xs text-gray-500">分步操作教程、错误排查</div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const scenarios = [
  {
    id: 'reactor',
    icon: '🔌',
    title: '电抗器参数化',
    desc: '每个工况一个文件',
    mode: 'perfile'
  },
  {
    id: 'transformer',
    icon: '⚡',
    title: '变压器时域',
    desc: '单文件多时间步',
    mode: 'multicolumn'
  },
  {
    id: 'temperature',
    icon: '🌡️',
    title: '温升多参数',
    desc: '文件名包含多参数',
    mode: 'perfile'
  }
]

const selectedScenario = ref('reactor')

const emit = defineEmits(['openDoc'])

function openDocs(type) {
  const docMap = {
    full: 'DATA_SPECIFICATION.md',
    quick: 'QUICK_START_DATA_UPLOAD.md'
  }

  // 尝试在新窗口打开 markdown 文件
  const path = `/docs/${docMap[type]}`

  // 如果父组件监听了事件，则触发
  if (emit) {
    emit('openDoc', docMap[type])
  } else {
    // 否则提示用户
    ElMessage.info({
      message: `请在项目 docs/ 目录下查看：${docMap[type]}`,
      duration: 3000
    })
  }
}
</script>

<style scoped>
code {
  background-color: #1f2937;
  color: #34d399;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

pre code {
  background-color: transparent;
  padding: 0;
}
</style>





