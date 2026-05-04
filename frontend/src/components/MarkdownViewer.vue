<template>
  <div class="markdown-viewer">
    <div class="prose prose-invert max-w-none">
      <div v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  filePath: {
    type: String,
    required: true
  }
})

const renderedContent = ref('')

onMounted(async () => {
  try {
    const response = await fetch(props.filePath)
    const markdown = await response.text()
    renderedContent.value = marked.parse(markdown)
  } catch (error) {
    renderedContent.value = '<p class="text-red-400">无法加载文档内容</p>'
    console.error('Failed to load markdown:', error)
  }
})
</script>

<style scoped>
.markdown-viewer {
  @apply text-slate-200;
}

/* 自定义 Prose 样式以适配暗色主题 */
.markdown-viewer :deep(h1) {
  @apply text-2xl font-bold mb-4 mt-6 text-cyan-400 border-b border-slate-700 pb-2;
}

.markdown-viewer :deep(h2) {
  @apply text-xl font-semibold mb-3 mt-5 text-blue-400;
}

.markdown-viewer :deep(h3) {
  @apply text-lg font-semibold mb-2 mt-4 text-purple-400;
}

.markdown-viewer :deep(h4) {
  @apply text-base font-semibold mb-2 mt-3 text-slate-300;
}

.markdown-viewer :deep(p) {
  @apply mb-3 leading-relaxed text-slate-300;
}

.markdown-viewer :deep(ul),
.markdown-viewer :deep(ol) {
  @apply mb-3 ml-6 space-y-1;
}

.markdown-viewer :deep(li) {
  @apply text-slate-300;
}

.markdown-viewer :deep(code) {
  @apply bg-slate-800 text-green-400 px-1.5 py-0.5 rounded text-sm font-mono;
}

.markdown-viewer :deep(pre) {
  @apply bg-slate-900 p-4 rounded-lg overflow-x-auto mb-4 border border-slate-700;
}

.markdown-viewer :deep(pre code) {
  @apply bg-transparent p-0 text-green-300;
}

.markdown-viewer :deep(table) {
  @apply w-full mb-4 border-collapse;
}

.markdown-viewer :deep(th) {
  @apply bg-slate-800 text-cyan-300 font-semibold p-2 border border-slate-700 text-left;
}

.markdown-viewer :deep(td) {
  @apply p-2 border border-slate-700 text-slate-300;
}

.markdown-viewer :deep(blockquote) {
  @apply border-l-4 border-blue-500 pl-4 italic text-slate-400 my-4;
}

.markdown-viewer :deep(a) {
  @apply text-blue-400 hover:text-blue-300 underline;
}

.markdown-viewer :deep(strong) {
  @apply font-bold text-white;
}

.markdown-viewer :deep(hr) {
  @apply my-6 border-slate-700;
}
</style>

