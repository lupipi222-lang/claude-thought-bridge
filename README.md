# Claude Code 内在过程桥接器

这是一套把 Claude Code 终端里的三类内容送到手机端的自托管模板：

1. **内部过程**：transcript 中实时出现的 `thinking` 片段；
2. **动作轨迹**：读文件、改文件、检索、执行命令等工具动作的人话摘要；
3. **正式回复**：Claude Code 主动调用 `reply` 工具发出的成品消息。

它不修改模型，也不替你写人格。它只是观察 Claude Code 已经写入本机的 JSONL transcript，把事件转换成统一协议，再送往：

- 一个自制的“小家”网页；或
- Telegram Bot（不需要自制前端）。

仓库不包含任何私人现用 prompt、聊天记录、域名、头像、令牌或现用配置。`templates/看清自己.md` 使用一份可公开复用的第一人称自述 prompt，并附有网页分区需要的程序封装协议。

## 最终效果

网页端：

- 内部过程与动作会收在正式回复上方的折叠区；
- `[[自我状态]]...[[/自我状态]]` 显示为“心里话”；
- 单击标题展开／收起心里话；
- 在心里话文字区域双击，切换到原始过程；
- 在原始过程区域单击，自动复制全文并收起；
- 每次 `reply` 调用生成一个独立气泡；
- 系统通知只显示正式回复，绝不带心里话、内部过程或动作；
- 每个正式气泡使用独立通知 ID，连续气泡不会互相覆盖。

Telegram 端：

- 内部过程、自述块和动作轨迹均静默发送；
- 内部过程和自述块使用 Telegram 的可展开引用；
- 正式回复正常提醒；
- 每次 `reply` 调用对应一条独立 Telegram 消息。

Telegram Bot 无法接管客户端的双击、自动复制和自动关闭手势，因此只能近似网页体验。完整手势请使用网页端。

## 仓库结构

```text
src/thought_bridge/
  watcher.py        # 实时跟随 Claude Code transcript
  transcript.py     # JSONL 增量读取与事件抽取
  action_labels.py  # 工具调用转为安全的人话摘要
  sinks.py          # Relay / Telegram 输出
  mcp_server.py     # Claude Code 的 reply MCP 工具
  server.py         # FastAPI + SQLite + SSE + Web Push
  web/              # 可直接部署的手机网页
templates/
  看清自己.md        # 通用 output style + 程序封装协议
examples/
  claude-settings.json
deploy/
docs/
tests/
```

## 五分钟本地试跑

Windows PowerShell：

```powershell
cd D:\claude\thinking_pipeline
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
notepad .env
.\.venv\Scripts\thought-bridge.exe doctor
```

开两个终端：

```powershell
.\.venv\Scripts\thought-bridge-relay.exe
.\.venv\Scripts\thought-bridge-watcher.exe
```

浏览器打开 `http://127.0.0.1:8787`，输入 `.env` 中的 `RELAY_USER_TOKEN`。

给 Claude Code 注册正式回复工具：

```powershell
claude mcp add thought-bridge -- D:\claude\thinking_pipeline\.venv\Scripts\python.exe -m thought_bridge.mcp_server
```

之后模型每调用一次 `mcp__thought-bridge__reply`，手机端就得到一个独立正式气泡。

## 安装路线

- [架构与消息协议](docs/architecture.md)
- [Windows + VPS 网页版安装](docs/web.md)
- [Telegram 版安装](docs/telegram.md)
- [安全与隐私](docs/security.md)
- [排错手册](docs/troubleshooting.md)

`deploy/install-windows.ps1` 和 `deploy/install-linux.sh` 是辅助脚本。先通读并填写 `.env`；不要把真实令牌提交到 Git。

## 边界

- transcript 结构属于 Claude Code 的实现细节，版本升级后可能变化；测试覆盖了常见的 `assistant.content[].thinking/tool_use/text` 结构。
- 不自动读取或发布安装者现有的 output style；仓库只提供这份通用模板。
- 默认对常见密钥格式做遮盖，但这不是数据防泄漏的绝对保证。公开服务器前必须使用 HTTPS、长随机令牌和防火墙。
- 正式回复默认要求模型显式调用 `reply` 工具，避免 transcript 自动抓取造成重复气泡。
