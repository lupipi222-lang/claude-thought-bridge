# Telegram 版教程

Telegram 版适合不想维护网页前端的人。它复用同一个 watcher 和 MCP `reply` 工具，只把输出目的地改成 Bot API。

## 能做到什么

| 内容 | Telegram 表现 | 是否响铃 |
|---|---|---|
| 内部过程 | expandable blockquote | 否 |
| 动作轨迹 | 等宽小消息 | 否 |
| 自述块 | expandable blockquote | 否 |
| 正式回复 | 普通 Bot 消息 | 是 |
| 多个正式气泡 | 多条独立消息 | 每条独立 |

Telegram 客户端不允许 Bot 接管“双击切换、点击自动复制、点击后自动关闭”，因此这三个手势无法原样复刻。可展开引用是最接近、也最稳定的原生控件。

## 1. 创建 Bot

在 Telegram 里通过官方 Bot 管理入口创建 Bot，拿到 Bot Token。令牌只写进机器的 `.env`；不要粘贴到公开聊天、Issue、截图或仓库。

给 Bot 发一条消息，然后用 Bot API 的 `getUpdates` 查看自己的 `chat_id`。完成后可以删除浏览器历史中的含 Token URL，最好使用本机脚本查询而不是把 Token 放进地址栏。

## 2. 配置

```dotenv
BRIDGE_SINKS=telegram
CLAUDE_TRANSCRIPT_GLOB=C:/Users/你的用户名/.claude/projects/**/*.jsonl
TELEGRAM_BOT_TOKEN=你的BotToken
TELEGRAM_CHAT_ID=你的chat_id
```

同时发网页和 Telegram：

```dotenv
BRIDGE_SINKS=relay,telegram
```

## 3. 启动

```powershell
.\.venv\Scripts\thought-bridge.exe doctor
.\.venv\Scripts\thought-bridge-watcher.exe
```

注册同一个 MCP：

```powershell
claude mcp add thought-bridge -- D:\claude\thinking_pipeline\.venv\Scripts\python.exe -m thought_bridge.mcp_server
```

模型每调用一次 `reply`，Telegram 就收到一条正式消息。回复内如果有自述块，发送顺序是：

1. 静默的可展开自述；
2. 正常提醒的正式回复。

内部过程与动作均使用 `disable_notification=true`，不会把手机震个不停。

## 4. 远程和 Claude Code 对话

本仓库负责“Claude Code → Telegram”的展示。若还要“Telegram → Claude Code”自动注入当前终端，需要额外的会话适配器，因为 Claude Code CLI 没有一个通用、稳定的远程输入端口。

有三种选择：

1. 继续在电脑终端输入，Telegram 只做随身查看；
2. 安装你信任的 Telegram ↔ Claude Code MCP/插件处理入站；
3. 自己维护 tmux/PTY 适配器，并为每条入站消息实现身份校验、会话锁和重放保护。

不要把一个公开 Telegram Bot 直接接到 shell；至少限制允许的 `chat_id`，并且不要允许消息文本直接拼接成命令。

## 5. 验收

```powershell
.\.venv\Scripts\thought-bridge.exe send --kind thinking "过程测试"
.\.venv\Scripts\thought-bridge.exe send --kind action "动作测试"
.\.venv\Scripts\thought-bridge.exe send --kind reply "正式回复测试"
```

前两条应该静默，最后一条正常提醒。测试自述：

```powershell
.\.venv\Scripts\thought-bridge.exe send --kind reply "[[自我状态]]自述测试[[/自我状态]]`n——`n正式正文"
```

Telegram 应收到一条静默可展开自述和一条正常提醒正文。
