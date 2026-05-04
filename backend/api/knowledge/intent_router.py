"""api/knowledge/intent_router.py  ──  问题意图路由分类器"""
import os
import re
import json
from typing import Optional

import httpx


FAULT_KEYWORDS = [
    "故障", "溯源", "短路", "异常", "畸变", "偏低", "偏高", "损坏",
    "老化", "放电", "过热", "漏磁", "饱和", "变形", "诊断", "检修",
    "绝缘", "击穿", "烧毁", "断裂", "腐蚀", "磨损",
]
TUNING_KEYWORDS = [
    "调参", "优化", "学习率", "过拟合", "欠拟合", "MAPE", "MAE", "损失",
    "收敛", "梯度", "PCA", "主成分", "batch", "epoch", "超参",
    "训练", "模型精度", "误差", "数据增强", "正则化", "dropout",
]
GENERAL_KEYWORDS = [
    "规程", "标准", "规范", "查询", "介绍", "说明", "什么是", "如何",
]

CLASSIFY_PROMPT = """你是一个问题意图分类器。根据用户问题判断其类型。

分类规则：
- fault_diagnosis: 设备故障诊断、异常溯源、故障原因分析
- param_tuning: 模型调参、算法优化、训练问题排查
- general: 规程查询、知识咨询、综合问题

只输出 JSON：{"intent": "fault_diagnosis|param_tuning|general"}

用户问题："""


class IntentRouter:
    """意图路由：关键词规则优先，LLM 兜底"""

    def __init__(self):
        self.relay_api_key = os.getenv("RELAY_API_KEY", "")
        self.relay_url = os.getenv("RELAY_API_URL", "https://www.openclaudecode.cn")
        self.relay_model = os.getenv("RELAY_MODEL", "gpt-4o-mini")
        self.qwen_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.default_service = os.getenv("CHAT_SERVICE", "relay")

    def _keyword_classify(self, query: str) -> Optional[str]:
        q = query.lower()
        fault_score = sum(1 for kw in FAULT_KEYWORDS if kw in q)
        tuning_score = sum(1 for kw in TUNING_KEYWORDS if kw in q)
        general_score = sum(1 for kw in GENERAL_KEYWORDS if kw in q)

        if fault_score >= 2 and fault_score > tuning_score:
            return "fault_diagnosis"
        if tuning_score >= 2 and tuning_score > fault_score:
            return "param_tuning"
        if fault_score >= 1 and tuning_score == 0:
            return "fault_diagnosis"
        if tuning_score >= 1 and fault_score == 0:
            return "param_tuning"
        if general_score >= 1 and fault_score == 0 and tuning_score == 0:
            return "general"
        return None

    async def _llm_classify(self, query: str) -> str:
        try:
            if self.default_service == "qwen" and self.qwen_api_key:
                return await self._classify_qwen(query)
            elif self.relay_api_key:
                return await self._classify_relay(query)
            elif self.qwen_api_key:
                return await self._classify_qwen(query)
        except Exception as e:
            print(f"[IntentRouter] LLM 分类失败: {e}")
        return "general"

    async def _classify_relay(self, query: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.relay_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.relay_model,
            "messages": [{"role": "user", "content": CLASSIFY_PROMPT + query}],
            "temperature": 0.0,
            "max_tokens": 50,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.relay_url}/v1/chat/completions", headers=headers, json=payload
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            return self._parse_intent(text)

    async def _classify_qwen(self, query: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.qwen_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "qwen-turbo",
            "input": {"messages": [{"role": "user", "content": CLASSIFY_PROMPT + query}]},
            "parameters": {"temperature": 0.0, "max_tokens": 50, "result_format": "message"},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers, json=payload,
            )
            resp.raise_for_status()
            text = resp.json()["output"]["choices"][0]["message"]["content"].strip()
            return self._parse_intent(text)

    def _parse_intent(self, text: str) -> str:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(text[start:end + 1])
                intent = data.get("intent", "general")
                if intent in ("fault_diagnosis", "param_tuning", "general"):
                    return intent
        except (json.JSONDecodeError, KeyError):
            pass
        if "fault" in text.lower():
            return "fault_diagnosis"
        if "tuning" in text.lower() or "param" in text.lower():
            return "param_tuning"
        return "general"

    async def classify(self, query: str) -> dict:
        """分类用户问题并返回路由决策"""
        intent = self._keyword_classify(query)
        used_llm = False

        if intent is None:
            intent = await self._llm_classify(query)
            used_llm = True

        track_map = {
            "fault_diagnosis": ["kg", "vector"],
            "param_tuning": ["kg", "vector"],
            "general": ["kg", "vector"],
        }
        tracks = track_map.get(intent, ["vector"])

        return {
            "intent": intent,
            "tracks": tracks,
            "used_llm": used_llm,
        }


intent_router = IntentRouter()
