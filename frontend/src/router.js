import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from './layouts/MainLayout.vue';
import Dashboard from './components/Dashboard.vue';

// 认证页面
import Login from './views/auth/Login.vue';
import Register from './views/auth/Register.vue';

// 用户中心
import UserManagement from './views/user/UserManagement.vue';
import RoleManagement from './views/user/RoleManagement.vue';
import DeptManagement from './views/user/DeptManagement.vue';

// 数据中心
import DatasetManage from './views/data/DatasetManage.vue';
import DataStorage from './views/data/DataStorage.vue';
import DataUpload from './views/data/DataUpload.vue';
import DataProcessing from './views/data/DataProcessing.vue';

// 模型训练
import ModelArchitecture from './views/model/ModelArchitecture.vue';
import ModelTrainingTask from './views/model/ModelTrainingTask.vue';
import ModelEvaluation from './views/model/ModelEvaluation.vue';
import ModelManagement from './views/model/ModelManagement.vue';

// 实时预测
import PredictSetup from './views/prediction/PredictSetup.vue';
import PredictResult from './views/prediction/PredictResult.vue';
import PredictCompare from './views/prediction/PredictCompare.vue';
import PredictHistory from './views/prediction/PredictHistory.vue';

// AI 助手
import AiChat from './views/assistant/AiChat.vue';
import AiKnowledge from './views/assistant/AiKnowledge.vue';
import AiAgent from './views/assistant/AiAgent.vue';

const routes = [
  // 认证路由（独立页面，无侧边栏）
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/register', component: Register, meta: { public: true } },

  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard },
      // 用户中心
      { path: 'user-management', component: UserManagement },
      { path: 'role-management', component: RoleManagement },
      { path: 'dept-management', component: DeptManagement },
      { path: 'user-center', redirect: '/user-management' },
      // 数据中心
      { path: 'data-storage', component: DataStorage },
      { path: 'dataset-manage', component: DatasetManage },
      { path: 'data-upload', redirect: '/dataset-manage' },
      { path: 'data-processing', component: DataProcessing },
      // 模型训练
      { path: 'model-architecture', component: ModelArchitecture },
      { path: 'model-training-task', component: ModelTrainingTask },
      { path: 'model-evaluation', component: ModelEvaluation },
      { path: 'model-management', component: ModelManagement },
      { path: 'model-training', redirect: '/model-architecture' },
      // 实时预测（移除设备场专用云图页）
      { path: 'predict-setup',   component: PredictSetup },
      { path: 'predict-result',  component: PredictResult },
      { path: 'predict-compare', component: PredictCompare },
      { path: 'predict-history', component: PredictHistory },
      { path: 'gaoya-field',       redirect: '/predict-result' },
      { path: 'reactor-field',     redirect: '/predict-result' },
      { path: 'transformer-field', redirect: '/predict-result' },
      { path: 'real-time-prediction', redirect: '/predict-setup' },
      // AI 助手
      { path: 'ai-chat', component: AiChat },
      { path: 'ai-knowledge', component: AiKnowledge },
      { path: 'ai-agent', component: AiAgent },
      { path: 'ai-assistant', redirect: '/ai-chat' },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 全局导航守卫
router.beforeEach((to) => {
  const token = localStorage.getItem('auth_token');
  const isPublic = to.meta?.public === true;
  if (!token && !isPublic) {
    return '/login';
  }
  if (token && (to.path === '/login' || to.path === '/register')) {
    return '/dashboard';
  }
});

export default router;
