# DeepSeek-R1在阿里云百炼上的调用教程：推理模型API接入完整指南

DeepSeek-R1 是当前国产最强的推理模型之一，在数学、代码和自然语言推理等任务上表现出色。通过阿里云百炼平台，开发者可以零门槛、即刻调用 DeepSeek-R1 满血版，无需自行部署模型基础设施。本文将带你完成从账号准备到代码调用的完整流程。

---

## 一、准备工作

### 1. 注册并开通百炼服务

首先，你需要一个阿里云账号。前往 [阿里云百炼AI大模型](https://www.aliyun.com/benefit/client/cross?userCode=6p8lcsnh)，如果页面顶部提示需要开通服务，点击开通即可。开通后即可获得免费额度。

> 若提示"尚未进行实名认证"，请先完成阿里云账号的实名认证。

### 2. 获取 API Key

登录百炼控制台后，将鼠标悬停在页面右上角的个人头像上，在下拉菜单中点击 **API-KEY**。在左侧导航栏选择"全部 API-KEY"或"我的 API-KEY"，然后点击**创建 API Key**。创建成功后，复制该 Key 备用。

### 3. 安装 OpenAI SDK

百炼平台提供 OpenAI 兼容接口，因此可以直接使用 `openai` Python 包进行调用：

```bash
pip install --upgrade openai
```

---

## 二、基础 API 调用

### 核心参数说明

| 参数  | 说明  | 示例值 |
| --- | --- | --- |
| `base_url` | 百炼 API 基础地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `api_key` | 你的百炼 API Key | `sk-xxx` |
| `model` | 模型名称 | `deepseek-r1` |

### 完整调用示例

以下代码演示了如何调用 DeepSeek-R1 并分别获取**思考过程**和**最终答案**：

```python
import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请直接用百炼 API Key替换下行
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="deepseek-r1",  # 模型名称固定为 deepseek-r1
    messages=[
        {'role': 'user', 'content': '9.9 和 9.11 哪个更大？'}
    ]
)

# DeepSeek-R1 的思考过程通过 reasoning_content 字段返回
print("=" * 20 + " 思考过程 " + "=" * 20)
print(completion.choices[0].message.reasoning_content)

# 最终答案通过 content 字段返回
print("\n" + "=" * 20 + " 最终答案 " + "=" * 20)
print(completion.choices[0].message.content)
```

### 输出结构解析

DeepSeek-R1 作为推理模型，与普通聊天模型的最大区别在于其返回的消息对象包含两个关键字段：

- **`reasoning_content`**：模型的完整思考链（Chain of Thought），展示了它是如何一步步推导问题的。
- **`content`**：经过推理后给出的最终答案。

> 注意：由于 DeepSeek-R1 需要生成较长的思考过程，首次调用可能需要等待数十秒甚至更久，这属于正常现象。

---

## 三、流式输出调用（推荐）

考虑到 DeepSeek-R1 的思考过程可能非常长，为了避免请求超时并提升用户体验，**强烈建议使用流式输出**：

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="deepseek-r1",
    messages=[
        {'role': 'user', 'content': '用 Python 写一个快速排序算法，并解释其时间复杂度'}
    ],
    stream=True,  # 启用流式输出
    # 如需在最后一个 chunk 返回 Token 使用量，可取消下面注释
    # stream_options={"include_usage": True}
)

reasoning_content = ""
answer_content = ""
is_answering = False

print("\n" + "=" * 20 + " 思考过程 " + "=" * 20 + "\n")
for chunk in completion:
    # 处理 include_usage=True 时最后一个空 choices 的 chunk
    if not chunk.choices:
        print("\n" + "=" * 20 + " Token 使用情况 " + "=" * 20)
        print(chunk.usage)
        continue

    delta = chunk.choices[0].delta

    # 获取思考过程片段
    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
        print(delta.reasoning_content, end="", flush=True)
        reasoning_content += delta.reasoning_content

    # 获取最终答案片段（思考结束后开始输出）
    elif delta.content:
        if not is_answering:
            print("\n\n" + "=" * 20 + " 最终答案 " + "=" * 20 + "\n")
            is_answering = True
        print(delta.content, end="", flush=True)
        answer_content += delta.content

print()  # 换行结束
```

**流式输出的优势：**

- 实时看到模型的思考过程，无需等待全部生成完毕
- 显著降低因响应时间过长导致的超时风险
- 适合集成到 Web 应用或聊天界面中

---

## 四、客户端工具接入

除了直接写代码调用，你还可以通过常见的 AI 客户端工具接入百炼 DeepSeek-R1。

### Chatbox 配置

1. 下载并安装 [Chatbox](https://chatboxai.app/)
2. 打开设置，选择"添加自定义提供方"
3. 填写以下信息：

| 配置项 | 值   |
| --- | --- |
| 名称  | 百炼 DeepSeek-R1 |
| API 域名 | `https://dashscope.aliyuncs.com` |
| API 路径 | `/compatible-mode/v1/chat/completions` |
| API 密钥 | 你的百炼 API Key |
| 模型  | `deepseek-r1` |

> 注意：百炼的 API 域名和路径需要**分开填写**，不要填在同一个框里。

### Cherry Studio / Dify 接入

Cherry Studio 和 Dify 的接入方式类似，均选择 **OpenAI 兼容模式**，填入相同的 `base_url`、API Key 和模型名称 `deepseek-r1` 即可。

---

## 五、计费与免费额度

### 免费额度

新用户开通百炼后，DeepSeek-R1 和 DeepSeek-V3 分别赠送 **100 万免费 Token**，额度不重复计算，相当于共 200 万 Token。免费额度自开通起 **180 天内有效**。

### 正式计费标准（华北2 北京）

| 计费项 | 价格  |
| --- | --- |
| 输入 Token | 4 元 / 百万 Tokens |
| 输出 Token | 16 元 / 百万 Tokens |
| 输入（缓存命中） | 0.8 元 / 百万 Tokens |
| 输入（Batch File） | 2 元 / 百万 Tokens |
| 输出（Batch File） | 8 元 / 百万 Tokens |

### 限流策略

| 参数  | 值   |
| --- | --- |
| RPM（每分钟请求数） | 15,000 |
| TPM（每分钟 Tokens） | 1,200,000 |

---

## 六、模型能力与限制

根据阿里云官方文档，DeepSeek-R1 的能力支持情况如下：

| 能力项 | 支持情况 |
| --- | --- |
| 输入模态 | 仅支持文本 |
| 输出模态 | 文本  |
| Function Calling | ✅ 支持 |
| 联网搜索 | ✅ 支持 |
| 结构化输出 | ❌ 不支持 |
| 前缀续写 | ❌ 不支持 |
| 上下文缓存 | ✅ 支持 |
| 批量推理 | ❌ 不支持 |
| 模型调优 | ❌ 不支持 |

**上下文限制：**

- 最大输入长度：98,304 Tokens
- 最大输出长度：16,384 Tokens
- 上下文总长度：131,072 Tokens

---

## 七、常见问题

**Q1：调用时响应很慢，甚至超时？**
A：DeepSeek-R1 是推理模型，生成思考过程需要较长时间。建议使用流式输出（`stream=True`），或增加客户端的请求超时时间。

**Q2：如何只获取最终答案，不输出思考过程？**
A：目前 API 返回中 `reasoning_content` 和 `content` 是分开的，你可以在代码中只读取 `content` 字段。但模型本身仍会生成思考过程，这部分 Token 消耗无法避免。

**Q3：可以上传图片或文档进行提问吗？**
A：DeepSeek-R1 仅支持文本输入。如需图片理解，请使用千问 VL 系列模型；如需长文档处理，请使用 Qwen-Long 模型。

**Q4：免费额度用完了怎么办？**
A：前往阿里云费用与成本中心充值即可。调用 DeepSeek 模型会自动扣费，出账周期为分钟级。

**Q5：如何查看 Token 消耗和调用次数？**
A：模型调用完一小时后，在百炼控制台的"模型观测"页面，选择时间范围并找到 DeepSeek-R1 模型，点击"监控"即可查看统计数据。

---

## 八、总结

通过阿里云百炼调用 DeepSeek-R1 的优势非常明显：

1. **零部署**：无需管理 GPU 服务器，开通即调用
2. **满血版**：直接调用 671B 参数的完整模型，非蒸馏版
3. **OpenAI 兼容**：一行代码替换 `base_url` 和 `model` 即可迁移
4. **成本可控**：百万级免费额度 + 分钟级出账，适合从实验到生产的全阶段

如果你正在寻找一个稳定、低门槛且功能完整的 DeepSeek-R1 接入方案，阿里云百炼无疑是当前国内最优选择之一。[阿里云百炼AI大模型官网](https://www.aliyun.com/benefit/client/cross?userCode=6p8lcsnh)
