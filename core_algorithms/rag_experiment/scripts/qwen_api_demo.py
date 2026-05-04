"""
Qwen3.5 API 调用示例脚本
用于演示如何调用通义千问 API
"""

import os
import json
from typing import Optional
import requests


class QwenAPI:
    """通义千问 API 调用类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 API 客户端
        
        Args:
            api_key: 阿里云 API 密钥，如果未提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "请提供 API 密钥或设置环境变量 DASHSCOPE_API_KEY\n"
                "获取方式：访问 https://dashscope.console.aliyun.com/ 创建 API Key"
            )
        
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(
        self,
        prompt: str,
        model: str = "qwen3.5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> dict:
        """
        发送对话请求
        
        Args:
            prompt: 用户输入的提示词
            model: 模型名称 (qwen3.5, qwen-max, qwen-plus, qwen-turbo 等)
                   qwen3.5: 最新 Qwen 3.5 模型
                   qwen-max: 效果最好的模型
                   qwen-plus: 性能均衡的模型
                   qwen-turbo: 速度最快的模型
            temperature: 温度参数，控制随机性 (0-2)
            max_tokens: 最大生成 token 数
            stream: 是否使用流式输出
            
        Returns:
            API 响应数据 (字典格式)
        """
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个有帮助的 AI 助手。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            },
            "stream": stream
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"请求失败：{str(e)}"}
    
    def simple_ask(self, question: str) -> str:
        """
        简化版问答接口
        
        Args:
            question: 问题
            
        Returns:
            AI 回答文本
        """
        result = self.chat(question)
        
        if "error" in result:
            return f"错误：{result['error']}"
        
        try:
            content = result["output"]["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            return f"解析响应失败：{str(e)}\n原始响应：{json.dumps(result, ensure_ascii=False, indent=2)}"


def main():
    """主函数 - 使用示例"""
    
    print("=" * 60)
    print("Qwen3.5 API 调用示例")
    print("=" * 60)
    
    # 方法 1: 直接从环境变量读取 API Key
    # 请先设置环境变量：set DASHSCOPE_API_KEY=your_api_key
    try:
        qwen = QwenAPI()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\n💡 解决方法:")
        print("   1. 访问 https://dashscope.console.aliyun.com/ 注册并创建 API Key")
        print("   2. 在 PowerShell 中执行：$env:DASHSCOPE_API_KEY='your_api_key'")
        print("   3. 或者直接在代码中传入：QwenAPI(api_key='your_api_key')")
        return
    
    # 方法 2: 直接传入 API Key (取消注释并使用)
    # qwen = QwenAPI(api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxx")
    
    print("\n✅ API 客户端初始化成功!\n")
    
    # 示例 1: 简单问答
    print("-" * 60)
    print("示例 1: 简单问答")
    print("-" * 60)
    question = "Python 中如何实现单例模式？请给出一个简洁的示例代码。"
    print(f"问：{question}\n")
    
    answer = qwen.simple_ask(question)
    print(f"答:\n{answer}\n")
    
    # 示例 2: 带参数的详细调用
    print("-" * 60)
    print("示例 2: 自定义参数调用")
    print("-" * 60)
    prompt = "请用 100 字以内解释什么是机器学习中的过拟合现象"
    print(f"问：{prompt}\n")
    
    result = qwen.chat(
        prompt=prompt,
        model="qwen3.5",  # 可选：qwen3.5(最新), qwen-max, qwen-plus, qwen-turbo
        temperature=0.5,   # 较低温度使输出更确定
        max_tokens=200     # 限制输出长度
    )
    
    if "error" not in result:
        response_text = result["output"]["choices"][0]["message"]["content"]
        print(f"答:\n{response_text}\n")
    else:
        print(f"错误：{result['error']}\n")
    
    # 示例 3: 代码生成
    print("-" * 60)
    print("示例 3: 代码生成")
    print("-" * 60)
    code_prompt = "请用 Python 写一个快速排序算法，要求包含详细的注释"
    print(f"任务：{code_prompt}\n")
    
    code_result = qwen.simple_ask(code_prompt)
    print(f"生成的代码:\n{code_result}\n")
    
    print("=" * 60)
    print("演示完成!")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 更多模型选项请访问：https://help.aliyun.com/zh/dashscope/")
    print("   - 查看 API 文档了解高级功能如流式输出、多模态等")
    print("   - Token 用量可在 DashScope 控制台查看")


if __name__ == "__main__":
    main()
