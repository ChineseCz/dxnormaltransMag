/**
 * 实时预测模块 —— 跨页面共享状态
 *
 * 所有预测子页面 (Setup / Result / Compare / History) 共用此 store，
 * 通过 Vue 3 的模块级 reactive 实现单例，无需 Pinia / Vuex。
 */
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

// ═══════ 单例响应式状态 ═══════
const activeDataset  = ref(null);
const isPredicting   = ref(false);
const predictionResult = ref(null);
const predictionHistory = ref([]);
const compareTargetId = ref(null);   // 预选到对比页的记录 id

const HISTORY_KEY = 'predict_history';

// 启动时从 localStorage 恢复历史
try {
  const saved = localStorage.getItem(HISTORY_KEY);
  if (saved) predictionHistory.value = JSON.parse(saved);
} catch { /* ignore */ }

function _saveHistory() {
  const trimmed = predictionHistory.value.slice(0, 50);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
}

// ═══════ composable ═══════
export function usePredictionStore() {
  const router = useRouter();

  // ── 数据集 ──
  function setDataset(ds) {
    activeDataset.value = ds;
  }

  // ── 执行预测 ──
  // modelInfo: { id, type, file_path, dataset_id, metrics }
  async function runPredict({ modelInfo, inputArray, inputLabels }) {
    if (!modelInfo || !modelInfo.id) {
      ElMessage.warning('请先在「模型管理」中激活一个模型');
      return;
    }
    isPredicting.value = true;
    predictionResult.value = null;

    try {
      const token = localStorage.getItem('auth_token');
      const payload = {
        model_id:    modelInfo.id,
        input_array: inputArray,
        dataset_id:  modelInfo.dataset_id,
      };
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000); // 60s 超时
      const res = await fetch('http://127.0.0.1:5000/api/predict/realtime', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      // 统一处理 401
      if (res.status === 401) {
        ['auth_token', 'user_info', 'auth_expires'].forEach(k => localStorage.removeItem(k));
        ElMessage.error('登录已过期，请重新登录');
        setTimeout(() => { window.location.href = '/login'; }, 800);
        return;
      }

      let data;
      try {
        const raw = await res.text();
        data = JSON.parse(raw);
      } catch (jsonErr) {
        console.error('[predict] JSON 解析失败:', jsonErr);
        ElMessage.error('响应解析失败（后端返回了非法 JSON，可能含 NaN 值），请联系开发者');
        return;
      }

      if (data.status === 'success' || data.fieldValues) {
        // 构建可读的 inputs map
        const inputs = {};
        (inputLabels || []).forEach((lbl, i) => { inputs[lbl] = inputArray[i]; });

        // 尝试从 modelInfo 或后端补充输出场元信息
        const outputUnit  = modelInfo.outputUnit  || modelInfo.output_unit  || 'T';
        const outputLabel = modelInfo.outputLabel || modelInfo.output_label || 'B';
        const deviceType  = modelInfo.deviceType  || modelInfo.device_type  || '';
        const fieldType   = modelInfo.fieldType   || modelInfo.field_type   || '';
        const coordSystem = modelInfo.coordSystem || modelInfo.coord_system || 'xyz';

        const result = {
          id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
          timestamp: new Date().toLocaleString('zh-CN'),
          datasetId:    data.dataset_id || modelInfo.dataset_id,
          datasetName:  modelInfo.dataset_name || modelInfo.dataset_id || '—',
          modelId:      modelInfo.id,
          modelType:    data.model_type || modelInfo.type,
          modelFile:    (modelInfo.file_path || '').split('/').pop(),
          inputs,
          inputArray:   [...inputArray],
          fieldValues:  data.fieldValues || [],
          coordinates:  data.coordinates || [],
          stats:        data.stats || null,
          used_pca:     data.used_pca,
          latency_s:    data.latency_s,
          outputUnit,
          outputLabel,
          deviceType,
          fieldType,
          coordSystem,
        };
        predictionResult.value = result;
        predictionHistory.value.unshift(result);
        _saveHistory();

        ElMessage.success(data.msg || '预测完成！');
        router.push('/predict-result');
      } else {
        ElMessage.error(data.error || data.msg || '预测失败');
      }
    } catch (e) {
      console.error(e);
      ElMessage.error('网络请求失败，请检查后端服务');
    } finally {
      isPredicting.value = false;
    }
  }

  // ── 历史操作 ──
  function viewRecord(record) {
    predictionResult.value = record;
    router.push('/predict-result');
  }

  function deleteRecord(recordId) {
    predictionHistory.value = predictionHistory.value.filter(r => r.id !== recordId);
    _saveHistory();
  }

  function clearHistory() {
    predictionHistory.value = [];
    localStorage.removeItem(HISTORY_KEY);
  }

  function goCompare(recordId) {
    if (recordId) compareTargetId.value = recordId;
    router.push('/predict-compare');
  }

  return {
    // state
    activeDataset,
    isPredicting,
    predictionResult,
    predictionHistory,
    compareTargetId,
    // actions
    setDataset,
    runPredict,
    viewRecord,
    deleteRecord,
    clearHistory,
    goCompare,
  };
}

