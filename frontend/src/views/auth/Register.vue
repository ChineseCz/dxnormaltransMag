<template>
  <div class="auth-bg flex items-center justify-center min-h-screen">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div class="glow-orb glow-orb-1"></div>
      <div class="glow-orb glow-orb-2"></div>
    </div>

    <div class="auth-card relative z-10">
      <!-- Logo & 标题 -->
      <div class="flex flex-col items-center mb-8">
        <div class="relative mb-4">
          <svg width="52" height="52" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#reg-grad)"/>
            <path d="M8 22 L14 10 L16 16 L19 12 L24 22" stroke="white" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <circle cx="25" cy="9" r="2.5" fill="#60a5fa"/>
            <defs>
              <linearGradient id="reg-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#1d4ed8"/>
                <stop offset="100%" stop-color="#4f46e5"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-400 border-2 border-[#0b1528]"
                style="box-shadow:0 0 8px rgba(74,222,128,0.9);"></span>
        </div>
        <h1 class="text-2xl font-extrabold tracking-tight"
            style="background:linear-gradient(90deg,#93c5fd,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          创建新账户
        </h1>
        <p class="text-slate-500 text-sm mt-1 tracking-wider uppercase">Physical Field AI · Register</p>
      </div>

      <!-- 注册表单 -->
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item prop="username" label="用户名">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名（3~20位字母数字）"
            size="large"
            :prefix-icon="User"
            class="auth-input"
            clearable
          />
        </el-form-item>

        <el-form-item prop="email" label="邮箱（选填）">
          <el-input
            v-model="form.email"
            placeholder="请输入邮箱地址"
            size="large"
            :prefix-icon="Message"
            class="auth-input"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password" label="密码">
          <el-input
            v-model="form.password"
            placeholder="请设置密码（至少6位）"
            size="large"
            :prefix-icon="Lock"
            type="password"
            show-password
            class="auth-input"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword" label="确认密码">
          <el-input
            v-model="form.confirmPassword"
            placeholder="请再次输入密码"
            size="large"
            :prefix-icon="Lock"
            type="password"
            show-password
            class="auth-input"
          />
        </el-form-item>

        <!-- 密码强度指示 -->
        <div v-if="form.password" class="mb-5 -mt-1">
          <div class="flex gap-1 mb-1">
            <div v-for="i in 4" :key="i"
                 class="h-1 flex-1 rounded-full transition-all duration-300"
                 :class="getStrengthClass(i)"></div>
          </div>
          <p class="text-xs text-slate-500">密码强度：<span :class="strengthLabelClass">{{ strengthLabel }}</span></p>
        </div>

        <el-form-item prop="agree">
          <el-checkbox v-model="form.agree">
            <span class="text-slate-400 text-sm">
              我已阅读并同意
              <span class="text-blue-400 cursor-pointer hover:text-blue-300">《用户服务协议》</span>
            </span>
          </el-checkbox>
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="w-full auth-btn"
          @click="handleRegister"
          round
        >
          <span class="font-semibold tracking-widest">注 册</span>
        </el-button>
      </el-form>

      <!-- 底部登录引导 -->
      <div class="text-center mt-6 text-slate-500 text-sm">
        已有账户？
        <router-link to="/login" class="text-blue-400 hover:text-blue-300 font-medium transition-colors ml-1">
          返回登录 →
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock, Message } from '@element-plus/icons-vue';
import { useAuthStore } from '../../composables/useAuthStore.js';

const router = useRouter();
const authStore = useAuthStore();

const formRef = ref(null);
const loading = ref(false);

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agree: false,
});

// 密码强度计算
const passwordStrength = computed(() => {
  const p = form.password;
  if (!p) return 0;
  let score = 0;
  if (p.length >= 6) score++;
  if (p.length >= 10) score++;
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
  if (/\d/.test(p) && /[^A-Za-z0-9]/.test(p)) score++;
  return score;
});

const strengthLabel = computed(() => ['弱', '一般', '较强', '强'][passwordStrength.value - 1] || '弱');
const strengthLabelClass = computed(() =>
  ['text-red-400', 'text-orange-400', 'text-yellow-400', 'text-green-400'][passwordStrength.value - 1] || 'text-red-400'
);

function getStrengthClass(i) {
  if (i > passwordStrength.value) return 'bg-slate-700';
  const colors = ['bg-red-500', 'bg-orange-400', 'bg-yellow-400', 'bg-green-400'];
  return colors[passwordStrength.value - 1] || 'bg-red-500';
}

const validatePass2 = (_, value, callback) => {
  if (value !== form.password) callback(new Error('两次输入的密码不一致'));
  else callback();
};

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3~20位', trigger: 'blur' },
  ],
  email: [
    { type: 'email', message: '请输入合法的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' },
  ],
  agree: [
    {
      validator: (_, val, cb) => val ? cb() : cb(new Error('请阅读并同意用户服务协议')),
      trigger: 'change',
    },
  ],
};

async function handleRegister() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await authStore.register(form.username, form.password, form.email);
    ElMessage.success('注册成功，欢迎加入！');
    router.push('/dashboard');
  } catch (err) {
    ElMessage.error(err.message || '注册失败，请重试');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-bg {
  background-color: #060d1a;
  background-image:
    radial-gradient(ellipse 80% 50% at 80% 10%, rgba(139,92,246,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 20% 80%, rgba(59,130,246,0.07) 0%, transparent 60%);
  position: relative;
}

.auth-card {
  width: 420px;
  max-width: calc(100vw - 48px);
  margin: 0 auto;
  background: rgba(11, 21, 40, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(59,130,246,0.05);
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 8s ease-in-out infinite;
}
.glow-orb-1 {
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(139,92,246,0.3), transparent);
  top: -80px; right: -80px;
}
.glow-orb-2 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(59,130,246,0.25), transparent);
  bottom: -60px; left: -60px;
  animation-delay: -4s;
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

:deep(.el-form-item__label) {
  color: #94a3b8 !important;
  font-size: 13px;
  font-weight: 500;
}
:deep(.el-input__wrapper) {
  background-color: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(59,130,246,0.25) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
  transition: border-color 0.2s;
}
:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  border-color: rgba(59,130,246,0.6) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.1) !important;
}
:deep(.el-input__inner) {
  color: #e2e8f0 !important;
  background: transparent !important;
}
:deep(.el-input__prefix-inner .el-icon),
:deep(.el-input__suffix-inner .el-icon) {
  color: #64748b !important;
}
:deep(.el-checkbox__label) {
  color: #64748b !important;
}
:deep(.el-checkbox__inner) {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(59,130,246,0.3) !important;
}

.auth-btn {
  background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
  border: none !important;
  height: 46px !important;
  font-size: 15px !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.35) !important;
  transition: opacity 0.2s, transform 0.15s !important;
}
.auth-btn:hover {
  opacity: 0.92 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(59,130,246,0.5) !important;
}
</style>

