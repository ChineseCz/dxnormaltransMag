<template>
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useAuthStore } from './composables/useAuthStore.js';

const auth = useAuthStore();

// 启动时检查 token 是否过期或即将过期
onMounted(() => { auth.checkExpiry(); });

// 每 4 分钟轮询一次，确保长时间使用时自动续签
const _timer = setInterval(() => { auth.checkExpiry(); }, 4 * 60 * 1000);
onUnmounted(() => clearInterval(_timer));
</script>
