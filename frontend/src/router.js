import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from './layouts/MainLayout.vue';
import Dashboard from './components/Dashboard.vue'; // A placeholder component
import UserManagement from './views/UserManagement.vue';
import RoleManagement from './views/RoleManagement.vue';
import DeptManagement from './views/DeptManagement.vue';
import DataProcessing from './views/DataProcessing.vue';
import DataUpload from './views/DataUpload.vue';

// 导入模型训练相关的组件
import ModelArchitecture from './views/ModelArchitecture.vue';
import ModelTrainingTask from './views/ModelTrainingTask.vue';
import ModelEvaluation from './views/ModelEvaluation.vue';
import ModelManagement from './views/ModelManagement.vue';

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard },
      { path: 'user-management', component: UserManagement },
      { path: 'role-management', component: RoleManagement },
      { path: 'dept-management', component: DeptManagement },
      { path: 'user-center', component: Dashboard }, // Replace with actual components
      { path: 'data-upload', component: DataUpload },
      { path: 'data-processing', component: DataProcessing },
      // 模型训练子路由
      { path: 'model-architecture', component: ModelArchitecture },
      { path: 'model-training-task', component: ModelTrainingTask },
      { path: 'model-evaluation', component: ModelEvaluation },
      { path: 'model-management', component: ModelManagement },
      { path: 'model-training', redirect: '/model-architecture' },
      { path: 'real-time-prediction', component: Dashboard },
      { path: 'ai-assistant', component: Dashboard },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
