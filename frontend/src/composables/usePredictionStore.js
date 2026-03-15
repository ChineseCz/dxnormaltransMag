/**
 * 实时预测模块 —— 跨页面共享状态
 *
 * 所有预测子页面 (Setup / Result / Compare / History) 共用此 store，
 * 通过 Vue 3 的模块级 reactive 实现单例，无需 Pinia / Vuex。
 */
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';

// ═══════ 单例响应式状态 ═══════
const activeDataset  = ref(null);
const isPredicting   = ref(false);
const predictionResult = ref(null);
const predictionHistory = ref([]);

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
  async function runPredict({ modelFile, modelType, inputs, inputArray }) {
    if (!activeDataset.value) {
      ElMessage.warning('请先选择数据集');
      return;
    }
    isPredicting.value = true;
    predictionResult.value = null;

    try {
      const payload = {
        dataset_id: activeDataset.value.id,
        model_file: modelFile,
        model_type: modelType,
        inputs,
      };
      const res = await fetch('http://127.0.0.1:5000/api/predict/realtime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (data.status === 'success' || data.fieldValues) {
        const result = {
          id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
          timestamp: new Date().toLocaleString('zh-CN'),
          datasetName: activeDataset.value.name,
          datasetId: activeDataset.value.id,
          modelFile,
          modelType,
          inputs: { ...inputs },
          fieldValues: data.fieldValues || data.predicted_point || [],
          coordinates: data.coordinates || [],
          stats: data.stats || null,
          pcaDim: data.pcaDim || null,
        };
        predictionResult.value = result;
        predictionHistory.value.unshift(result);
        _saveHistory();

        ElMessage.success('预测完成！已生成物理场分布结果');
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

  function goCompare() {
    router.push('/predict-compare');
  }

  return {
    // state
    activeDataset,
    isPredicting,
    predictionResult,
    predictionHistory,
    // actions
    setDataset,
    runPredict,
    viewRecord,
    deleteRecord,
    clearHistory,
    goCompare,
  };
}

