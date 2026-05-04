<template>
  <div class="common-layout h-screen text-white" style="background-color:#060d1a;">
    <el-container class="h-full">
      <!-- Sidebar -->
      <el-aside :width="asideWidth"
        class="flex flex-col transition-all duration-300 overflow-hidden flex-shrink-0"
        style="background:linear-gradient(180deg,#080e1d 0%,#0b1528 60%,#0a1020 100%); border-right:1px solid rgba(59,130,246,0.15);">

        <!-- Logo Brand Area -->
        <div class="flex items-center h-20 flex-shrink-0 sidebar-brand"
             :class="isCollapsed ? 'justify-center px-0' : 'gap-4 px-5'">
          <div class="flex-shrink-0 relative cursor-pointer" @click="isCollapsed && toggleCollapse()">
            <svg width="38" height="38" viewBox="0 0 32 32" fill="none" class="sidebar-logo-glow">
              <rect width="32" height="32" rx="8" fill="url(#brand-grad)"/>
              <path d="M8 22 L14 10 L16 16 L19 12 L24 22" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <circle cx="25" cy="9" r="2.5" fill="#60a5fa"/>
              <defs>
                <linearGradient id="brand-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#1d4ed8"/>
                  <stop offset="100%" stop-color="#4f46e5"/>
                </linearGradient>
              </defs>
            </svg>
            <span class="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-green-400"
                  style="box-shadow:0 0 6px rgba(74,222,128,0.9);"></span>
          </div>
          <div v-if="!isCollapsed" class="overflow-hidden">
            <div class="font-extrabold leading-tight tracking-tight"
              style="font-size:20px; background:linear-gradient(90deg,#93c5fd,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; white-space:nowrap;">
              电气设备电磁场预测平台
            </div>
            <div class="text-[11px] text-slate-500 tracking-wider uppercase mt-1">Physical Field AI</div>
          </div>
        </div>

        <!-- Navigation Menu — hidden when collapsed -->
        <div v-if="!isCollapsed" class="flex-grow overflow-y-auto overflow-x-hidden">
          <el-menu
            active-text-color="#60a5fa"
            background-color="transparent"
            class="border-r-0"
            :default-active="route.path"
            router
            text-color="#94a3b8"
            style="--el-menu-hover-bg-color:rgba(59,130,246,0.08);">

            <!-- 用户中心 -->
            <el-sub-menu index="1">
              <template #title>
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style="background:rgba(99,102,241,0.2);">
                    <el-icon style="color:#818cf8;" size="17"><User /></el-icon>
                  </div>
                  <span class="text-slate-100 font-semibold" style="font-size:17px;">用户中心</span>
                </div>
              </template>
              <el-menu-item index="/user-management">
                <el-icon size="15"><User /></el-icon><span class="ml-1" style="font-size:15px;">用户管理</span>
              </el-menu-item>
              <el-menu-item index="/role-management">
                <el-icon size="15"><UserFilled /></el-icon><span class="ml-1" style="font-size:15px;">角色管理</span>
              </el-menu-item>
              <el-menu-item index="/dept-management">
                <el-icon size="15"><OfficeBuilding /></el-icon><span class="ml-1" style="font-size:15px;">部门管理</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- 数据中心 -->
            <el-sub-menu index="2">
              <template #title>
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style="background:rgba(20,184,166,0.2);">
                    <el-icon style="color:#2dd4bf;" size="17"><DataAnalysis /></el-icon>
                  </div>
                  <span class="text-slate-100 font-semibold" style="font-size:17px;">数据中心</span>
                </div>
              </template>
              <el-menu-item index="/data-storage">
                <el-icon size="15"><FolderOpened /></el-icon><span class="ml-1" style="font-size:15px;">数据存储</span>
              </el-menu-item>
              <el-menu-item index="/dataset-manage">
                <el-icon size="15"><Upload /></el-icon><span class="ml-1" style="font-size:15px;">模板构建</span>
              </el-menu-item>
              <el-menu-item index="/data-processing">
                <el-icon size="15"><Cpu /></el-icon><span class="ml-1" style="font-size:15px;">数据处理</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- 模型训练 -->
            <el-sub-menu index="3">
              <template #title>
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style="background:rgba(59,130,246,0.2);">
                    <el-icon style="color:#60a5fa;" size="17"><Cpu /></el-icon>
                  </div>
                  <span class="text-slate-100 font-semibold" style="font-size:17px;">模型训练</span>
                </div>
              </template>
              <el-menu-item index="/model-architecture">
                <el-icon size="15"><Operation /></el-icon><span class="ml-1" style="font-size:15px;">架构设计</span>
              </el-menu-item>
              <el-menu-item index="/model-training-task">
                <el-icon size="15"><VideoPlay /></el-icon><span class="ml-1" style="font-size:15px;">训练任务</span>
              </el-menu-item>
              <el-menu-item index="/model-evaluation">
                <el-icon size="15"><TrendCharts /></el-icon><span class="ml-1" style="font-size:15px;">训练结果</span>
              </el-menu-item>
              <el-menu-item index="/model-management">
                <el-icon size="15"><Box /></el-icon><span class="ml-1" style="font-size:15px;">模型中心</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- 实时预测 -->
            <el-sub-menu index="4">
              <template #title>
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style="background:rgba(245,158,11,0.2);">
                    <el-icon style="color:#fbbf24;" size="17"><Odometer /></el-icon>
                  </div>
                  <span class="text-slate-100 font-semibold" style="font-size:17px;">实时预测</span>
                </div>
              </template>
              <el-menu-item index="/predict-setup">
                <el-icon size="15"><Setting /></el-icon><span class="ml-1" style="font-size:15px;">预测配置</span>
              </el-menu-item>
              <el-menu-item index="/predict-result">
                <el-icon size="15"><DataLine /></el-icon><span class="ml-1" style="font-size:15px;">结果可视化</span>
              </el-menu-item>
              <el-menu-item index="/predict-compare">
                <el-icon size="15"><Switch /></el-icon><span class="ml-1" style="font-size:15px;">多次对比</span>
              </el-menu-item>
              <el-menu-item index="/predict-history">
                <el-icon size="15"><Clock /></el-icon><span class="ml-1" style="font-size:15px;">预测记录</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- AI 助手 -->
            <el-sub-menu index="5">
              <template #title>
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style="background:rgba(236,72,153,0.2);">
                    <el-icon style="color:#f472b6;" size="17"><MagicStick /></el-icon>
                  </div>
                  <span class="text-slate-100 font-semibold" style="font-size:17px;">AI 助手</span>
                </div>
              </template>
              <el-menu-item index="/ai-chat">
                <el-icon size="15"><ChatDotRound /></el-icon><span class="ml-1" style="font-size:15px;">智能对话</span>
              </el-menu-item>
              <el-menu-item index="/ai-knowledge">
                <el-icon size="15"><Collection /></el-icon><span class="ml-1" style="font-size:15px;">知识库</span>
              </el-menu-item>
              <!-- Agent 工作台（未完成，暂时隐藏）
              <el-menu-item index="/ai-agent">
                <el-icon size="15"><SetUp /></el-icon><span class="ml-1" style="font-size:15px;">Agent 工作台</span>
              </el-menu-item>
              -->
            </el-sub-menu>
          </el-menu>
        </div>

        <!-- Sidebar Footer -->
        <div class="p-3 flex-shrink-0 border-t" style="border-color:rgba(51,65,85,0.4);">
          <div class="flex items-center gap-3 px-2 py-2 rounded-lg"
               :class="isCollapsed ? 'justify-center' : ''"
               style="background:rgba(59,130,246,0.06);">
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                 style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);">A</div>
            <template v-if="!isCollapsed">
              <div class="flex-1 min-w-0">
                <div class="text-xs font-medium text-slate-300 truncate">Admin</div>
                <div class="text-[10px] text-slate-500 truncate">admin@dxnormal.com</div>
              </div>
              <el-icon class="text-slate-500 flex-shrink-0" size="14"><Setting /></el-icon>
            </template>
          </div>
        </div>
      </el-aside>

      <el-container>
        <!-- Header -->
        <el-header class="flex justify-between items-center px-6 flex-shrink-0"
          style="height:56px; background:rgba(6,13,26,0.9); backdrop-filter:blur(12px); border-bottom:1px solid rgba(51,65,85,0.4);">
          <div class="flex items-center gap-4">
            <el-button @click="toggleCollapse" text circle style="color:#94a3b8;">
              <el-icon size="18"><Expand v-if="isCollapsed" /><Fold v-else /></el-icon>
            </el-button>
            <!-- Breadcrumb -->
            <div class="hidden md:flex items-center gap-2 text-xs text-slate-500">
              <el-icon size="12"><HomeFilled /></el-icon>
              <span>/</span>
              <span class="text-slate-300">{{ breadcrumbGroup }}</span>
              <span>/</span>
              <span class="text-blue-400 font-medium">{{ breadcrumbPage }}</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <!-- Status Dot -->
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
                 style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25); color:#34d399;">
              <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse inline-block"></span>
              系统运行正常
            </div>
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold cursor-pointer"
                 style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);">A</div>
          </div>
        </el-header>

        <!-- Main Content -->
        <el-main class="main-bg overflow-y-auto" style="padding:0;">
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>

    <!-- 全局 AI 浮窗对话 -->
    <ChatDrawer />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  User, DataAnalysis, Cpu, Odometer, MagicStick, ChatDotRound,
  Operation, VideoPlay, TrendCharts, Box,
  Setting, Expand, Fold, HomeFilled, Switch, Clock, DataLine,
  Collection, UserFilled, OfficeBuilding, FolderOpened, Upload,
} from '@element-plus/icons-vue';
import ChatDrawer from '../components/ChatDrawer.vue';

const isCollapsed = ref(false);
const asideWidth = computed(() => (isCollapsed.value ? '64px' : '280px'));
const toggleCollapse = () => { isCollapsed.value = !isCollapsed.value; };
const route = useRoute();

const ROUTE_META = {
  '/user-management':   ['用户中心', '用户管理'],
  '/role-management':   ['用户中心', '角色管理'],
  '/dept-management':   ['用户中心', '部门管理'],
  '/data-storage':      ['数据中心', '数据存储'],
  '/dataset-manage':    ['数据中心', '模板构建'],
  '/data-upload':       ['数据中心', '模板构建'],
  '/data-processing':   ['数据中心', '数据处理'],
  '/model-architecture':['模型训练', '架构设计'],
  '/model-training-task':['模型训练', '训练任务'],
  '/model-evaluation':  ['模型训练', '训练结果'],
  '/model-management':  ['模型训练', '模型中心'],
  '/predict-setup':     ['实时预测', '预测配置'],
  '/predict-result':    ['实时预测', '结果可视化'],
  '/predict-compare':   ['实时预测', '多次对比'],
  '/predict-history':   ['实时预测', '预测记录'],
  '/ai-chat':           ['AI 助手', '智能对话'],
  '/ai-knowledge':      ['AI 助手', '知识库'],
};
const breadcrumbGroup = computed(() => ROUTE_META[route.path]?.[0] ?? '首页');
const breadcrumbPage  = computed(() => ROUTE_META[route.path]?.[1] ?? route.path);
</script>

<style scoped>
:deep(.el-menu-item) {
  border-radius: 8px !important;
  margin: 3px 10px !important;
  height: 48px !important;
  line-height: 48px !important;
  font-size: 15px !important;
}
:deep(.el-sub-menu__title) {
  border-radius: 8px !important;
  margin: 3px 10px !important;
  height: 48px !important;
  line-height: 48px !important;
  font-size: 15px !important;
}
:deep(.el-sub-menu__title:hover) {
  background-color: rgba(59,130,246,0.08) !important;
}
:deep(.el-menu-item:hover) {
  background-color: rgba(59,130,246,0.08) !important;
}
:deep(.el-menu-item.is-active) {
  background: rgba(59,130,246,0.15) !important;
  border-left: 2px solid #3b82f6 !important;
  color: #60a5fa !important;
}
</style>
