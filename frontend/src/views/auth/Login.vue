<template>
  <div class="auth-bg flex min-h-screen">
    <!-- 背景光晕 -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div class="glow-orb glow-orb-1"></div>
      <div class="glow-orb glow-orb-2"></div>
    </div>

    <!-- ===== 左侧：科技可视化面板 ===== -->
    <div class="left-panel hidden lg:flex flex-col relative overflow-hidden">
      <!-- 顶部品牌标识 -->
      <div class="flex items-center gap-3 px-10 pt-10">
        <svg width="30" height="30" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#lp-logo-grad)"/>
          <path d="M8 22 L14 10 L16 16 L19 12 L24 22" stroke="white" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <circle cx="25" cy="9" r="2.5" fill="#60a5fa"/>
          <defs>
            <linearGradient id="lp-logo-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#1d4ed8"/>
              <stop offset="100%" stop-color="#4f46e5"/>
            </linearGradient>
          </defs>
        </svg>
        <span class="text-slate-400 text-xs tracking-widest uppercase font-medium">Physical Field AI</span>
      </div>

      <!-- 可视化画布 -->
      <div class="flex-1 flex items-center justify-center px-10">
        <canvas ref="visCanvas" class="field-canvas"></canvas>
      </div>

      <!-- 底部平台信息 -->
      <div class="px-10 pb-12">
        <h1 class="text-3xl font-extrabold mb-2 whitespace-nowrap"
            style="background:linear-gradient(90deg,#93c5fd,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          电气设备电磁场预测平台
        </h1>
        <p class="text-slate-500 text-sm mb-7">基于深度学习的多电磁场智能预测引擎</p>
        <div class="flex items-center gap-8">
          <div class="text-center">
            <div class="text-xl font-bold text-blue-400">10K+</div>
            <div class="text-slate-500 text-xs mt-1">空间网格节点</div>
          </div>
          <div class="w-px h-8 bg-slate-700"></div>
          <div class="text-center">
            <div class="text-xl font-bold text-purple-400">ms 级</div>
            <div class="text-slate-500 text-xs mt-1">实时场预测</div>
          </div>
          <div class="w-px h-8 bg-slate-700"></div>
          <div class="text-center">
            <div class="text-xl font-bold text-cyan-400">RAG</div>
            <div class="text-slate-500 text-xs mt-1">智能知识问答</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 右侧：登录面板 ===== -->
    <div class="right-panel flex items-center justify-center">
      <div class="auth-card relative z-10">
        <!-- Logo & 标题 -->
        <div class="flex flex-col items-center mb-8">
          <div class="relative mb-4">
            <svg width="52" height="52" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#login-grad)"/>
              <path d="M8 22 L14 10 L16 16 L19 12 L24 22" stroke="white" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <circle cx="25" cy="9" r="2.5" fill="#60a5fa"/>
              <defs>
                <linearGradient id="login-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#1d4ed8"/>
                  <stop offset="100%" stop-color="#4f46e5"/>
                </linearGradient>
              </defs>
            </svg>
            <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-400 border-2 border-[#0b1528]"
                  style="box-shadow:0 0 8px rgba(74,222,128,0.9);"></span>
          </div>
          <h2 class="text-2xl font-extrabold tracking-tight"
              style="background:linear-gradient(90deg,#93c5fd,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            电气设备电磁场预测平台
          </h2>
          <!-- 仅在移动端显示平台名 -->
<!--          <p class="lg:hidden text-xs text-slate-500 mt-1 whitespace-nowrap">电气设备电磁场预测平台</p-->
          <p class="text-slate-500 text-sm mt-1 tracking-wider uppercase">Physical Field AI · Sign In</p>
        </div>

        <!-- 登录表单 -->
        <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @keyup.enter="handleLogin">
          <el-form-item prop="username" label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large"
                      :prefix-icon="User" class="auth-input" clearable/>
          </el-form-item>
          <el-form-item prop="password" label="密码">
            <el-input v-model="form.password" placeholder="请输入密码" size="large"
                      :prefix-icon="Lock" type="password" show-password class="auth-input"/>
          </el-form-item>
          <div class="flex justify-between items-center mb-5 text-sm">
            <el-checkbox v-model="rememberMe" label="记住我" class="text-slate-400"/>
            <span class="text-blue-400 cursor-pointer hover:text-blue-300 transition-colors">忘记密码？</span>
          </div>
          <el-button type="primary" size="large" :loading="loading"
                     class="w-full auth-btn" @click="handleLogin" round>
            <span class="font-semibold tracking-widest">登 录</span>
          </el-button>
        </el-form>

        <div class="text-center mt-6 text-slate-500 text-sm">
          还没有账户？
          <router-link to="/register" class="text-blue-400 hover:text-blue-300 font-medium transition-colors ml-1">
            立即注册 →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import { useAuthStore } from '../../composables/useAuthStore.js';

const router = useRouter();
const authStore = useAuthStore();
const formRef = ref(null);
const loading = ref(false);
const rememberMe = ref(false);
const visCanvas = ref(null);
const form = reactive({ username: '', password: '' });

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

async function handleLogin() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  try {
    await authStore.login(form.username, form.password);
    ElMessage.success('登录成功，欢迎回来！');
    router.push('/dashboard');
  } catch (err) {
    ElMessage.error(err.message || '登录失败，请重试');
  } finally {
    loading.value = false;
  }
}

// ===== 磁场可视化 Canvas =====
let animFrameId = null;

// Jet colormap: t ∈ [0,1] → [r,g,b]
function jetColor(t) {
  t = Math.max(0, Math.min(1, t));
  let r, g, b;
  if      (t < 0.25) { r = 0;              g = t * 4;               b = 1; }
  else if (t < 0.5)  { r = 0;              g = 1;                   b = 1 - (t - 0.25) * 4; }
  else if (t < 0.75) { r = (t - 0.5) * 4; g = 1;                   b = 0; }
  else               { r = 1;              g = 1 - (t - 0.75) * 4; b = 0; }
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

// 磁偶极子场强（点偶极子，偶极矩沿 +y 方向）
function dipoleB(px, py, cx, cy) {
  const dx = px - cx, dy = py - cy;
  const r = Math.sqrt(dx * dx + dy * dy);
  if (r < 8) return 0;
  const cosT = (cy - py) / r; // 正上方为极轴
  return Math.sqrt(3 * cosT * cosT + 1) / (r * r * r);
}

// 磁力线方程：r = a·sin²θ，θ∈(0,π)，右侧场线
function computeFieldLine(a, cx, cy, nPts = 200) {
  const pts = [];
  for (let i = 1; i < nPts; i++) {
    const theta = (i / nPts) * Math.PI;
    const r = a * Math.sin(theta) * Math.sin(theta);
    pts.push({
      x: cx + r * Math.sin(theta),
      y: cy - r * Math.cos(theta), // canvas y 轴翻转
    });
  }
  return pts;
}

function initVisualization() {
  const canvas = visCanvas.value;
  if (!canvas) return;

  const S = 420;
  canvas.width = S;
  canvas.height = S;
  const ctx = canvas.getContext('2d');
  const cx = S / 2, cy = S / 2;

  // 离屏 canvas 绘制静态元素（只画一次）
  const offscreen = document.createElement('canvas');
  offscreen.width = S; offscreen.height = S;
  const oc = offscreen.getContext('2d');

  // 背景径向渐变
  const bg = oc.createRadialGradient(cx, cy, 0, cx, cy, S * 0.75);
  bg.addColorStop(0, '#0d2244');
  bg.addColorStop(1, '#060d1a');
  oc.fillStyle = bg;
  oc.fillRect(0, 0, S, S);

  // 网格
  oc.strokeStyle = 'rgba(59,130,246,0.07)';
  oc.lineWidth = 0.5;
  for (let v = 0; v <= S; v += 20) {
    oc.beginPath(); oc.moveTo(v, 0); oc.lineTo(v, S); oc.stroke();
    oc.beginPath(); oc.moveTo(0, v); oc.lineTo(S, v); oc.stroke();
  }

  // 散点（场强着色）
  const step = 14, margin = 45;
  const dots = [];
  let maxB = 0;
  for (let px = margin; px <= S - margin; px += step) {
    for (let py = margin; py <= S - margin; py += step) {
      const B = dipoleB(px, py, cx, cy);
      if (B > maxB) maxB = B;
      dots.push({ x: px, y: py, B });
    }
  }
  const sat = maxB * 0.06;
  for (const d of dots) {
    const t = Math.min(d.B / sat, 1);
    const [r, g, b] = jetColor(t);
    oc.globalAlpha = 0.42 + t * 0.52;
    oc.fillStyle = `rgb(${r},${g},${b})`;
    oc.beginPath();
    oc.arc(d.x, d.y, 3.2, 0, Math.PI * 2);
    oc.fill();
  }
  oc.globalAlpha = 1;

  // 磁力线（左右对称）
  const fieldLines = [];
  for (const a of [45, 82, 124, 168, 205]) {
    const right = computeFieldLine(a, cx, cy).filter(
      p => p.x >= 5 && p.x <= S - 5 && p.y >= 5 && p.y <= S - 5
    );
    if (right.length > 4) {
      fieldLines.push(right);
      fieldLines.push(right.map(p => ({ x: cx - (p.x - cx), y: p.y }))); // 左侧镜像
    }
  }
  for (const line of fieldLines) {
    oc.beginPath();
    oc.moveTo(line[0].x, line[0].y);
    for (let i = 1; i < line.length; i++) oc.lineTo(line[i].x, line[i].y);
    oc.strokeStyle = 'rgba(255,255,255,0.15)';
    oc.lineWidth = 1;
    oc.stroke();
  }

  // Colorbar
  const cbX = S - 28, cbY = 55, cbH = 200, cbW = 11;
  const cbGrad = oc.createLinearGradient(0, cbY, 0, cbY + cbH);
  cbGrad.addColorStop(0,    'rgb(255,0,0)');
  cbGrad.addColorStop(0.25, 'rgb(255,255,0)');
  cbGrad.addColorStop(0.5,  'rgb(0,220,120)');
  cbGrad.addColorStop(0.75, 'rgb(0,220,255)');
  cbGrad.addColorStop(1,    'rgb(0,0,255)');
  oc.fillStyle = cbGrad;
  oc.fillRect(cbX, cbY, cbW, cbH);
  oc.strokeStyle = 'rgba(255,255,255,0.15)';
  oc.lineWidth = 0.5;
  oc.strokeRect(cbX, cbY, cbW, cbH);
  oc.fillStyle = 'rgba(200,220,255,0.55)';
  oc.font = '9px monospace';
  oc.fillText('High', cbX - 3, cbY - 5);
  oc.fillText('B/T',  cbX + 1, cbY + cbH + 14);
  oc.fillText('Low',  cbX - 3, cbY + cbH + 4);

  // 坐标轴
  oc.strokeStyle = 'rgba(148,163,184,0.22)';
  oc.lineWidth = 1;
  oc.beginPath(); oc.moveTo(margin, cy); oc.lineTo(S - 40, cy); oc.stroke();
  oc.beginPath(); oc.moveTo(cx, S - margin); oc.lineTo(cx, 14); oc.stroke();
  oc.fillStyle = 'rgba(148,163,184,0.45)';
  oc.font = '10px monospace';
  oc.fillText('x/mm', S - 46, cy + 16);
  oc.fillText('y/mm', cx + 6, 22);

  // 偶极子中心辉光
  const cg = oc.createRadialGradient(cx, cy, 0, cx, cy, 24);
  cg.addColorStop(0,   'rgba(255,210,80,0.9)');
  cg.addColorStop(0.4, 'rgba(255,140,40,0.35)');
  cg.addColorStop(1,   'transparent');
  oc.fillStyle = cg;
  oc.beginPath(); oc.arc(cx, cy, 24, 0, Math.PI * 2); oc.fill();
  oc.fillStyle = 'rgba(255,235,120,0.95)';
  oc.beginPath(); oc.arc(cx, cy, 3, 0, Math.PI * 2); oc.fill();

  // 粒子初始化（每条场线 3 个，均匀错开）
  const particles = fieldLines.flatMap((line, li) =>
    [0, 0.34, 0.67].map(offset => ({
      li,
      progress: (offset + Math.random() * 0.08) % 1,
      speed: 0.0017 + Math.random() * 0.0012,
    }))
  );

  // 动画循环
  function animate() {
    ctx.clearRect(0, 0, S, S);
    ctx.drawImage(offscreen, 0, 0);
    for (const pt of particles) {
      pt.progress = (pt.progress + pt.speed) % 1;
      const line = fieldLines[pt.li];
      const { x, y } = line[Math.min(Math.floor(pt.progress * line.length), line.length - 1)];
      // 光晕
      const pg = ctx.createRadialGradient(x, y, 0, x, y, 5.5);
      pg.addColorStop(0, 'rgba(147,197,253,0.85)');
      pg.addColorStop(1, 'transparent');
      ctx.fillStyle = pg;
      ctx.beginPath(); ctx.arc(x, y, 5.5, 0, Math.PI * 2); ctx.fill();
      // 核心亮点
      ctx.fillStyle = 'rgba(255,255,255,0.92)';
      ctx.beginPath(); ctx.arc(x, y, 1.5, 0, Math.PI * 2); ctx.fill();
    }
    animFrameId = requestAnimationFrame(animate);
  }
  animate();
}

onMounted(() => { initVisualization(); });
onUnmounted(() => { if (animFrameId) cancelAnimationFrame(animFrameId); });
</script>

<style scoped>
.auth-bg {
  background-color: #060d1a;
  position: relative;
  overflow: hidden;
}

/* 左侧面板 */
.left-panel {
  width: 55%;
  background: linear-gradient(160deg, #080f20 0%, #0b1a35 55%, #060d1a 100%);
  border-right: 1px solid rgba(59, 130, 246, 0.1);
  flex-direction: column;
}

.field-canvas {
  width: 100%;
  max-width: 420px;
  height: auto;
  border-radius: 12px;
  border: 1px solid rgba(59, 130, 246, 0.18);
  box-shadow: 0 0 48px rgba(59, 130, 246, 0.14), 0 0 100px rgba(139, 92, 246, 0.07);
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  background-color: #060d1a;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 10%, rgba(59,130,246,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(139,92,246,0.05) 0%, transparent 60%);
}

.auth-card {
  width: 420px;
  max-width: calc(100vw - 48px);
  background: rgba(11, 21, 40, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.05);
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 8s ease-in-out infinite;
}
.glow-orb-1 {
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.3), transparent);
  top: -80px; right: 8%;
}
.glow-orb-2 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.25), transparent);
  bottom: -60px; right: 4%;
  animation-delay: -4s;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-20px); }
}

/* Element Plus 深色覆写 */
:deep(.el-form-item__label) {
  color: #94a3b8 !important;
  font-size: 13px;
  font-weight: 500;
}
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(59, 130, 246, 0.25) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
  transition: border-color 0.2s;
}
:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.6) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
}
:deep(.el-input__inner) {
  color: #e2e8f0 !important;
  background: transparent !important;
}
:deep(.el-input__prefix-inner .el-icon),
:deep(.el-input__suffix-inner .el-icon) {
  color: #64748b !important;
}
:deep(.el-checkbox__label) { color: #64748b !important; }
:deep(.el-checkbox__inner) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

.auth-btn {
  background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
  border: none !important;
  height: 46px !important;
  font-size: 15px !important;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.35) !important;
  transition: opacity 0.2s, transform 0.15s !important;
}
.auth-btn:hover {
  opacity: 0.92 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(59, 130, 246, 0.5) !important;
}
</style>

