# Windows + VPS 网页版安装

这一页给出从 Claude Code 电脑到手机网页的完整安装路径。

## 1. 前提

- 运行 Claude Code 的 Windows / Linux 电脑；
- Python 3.10+；
- 一台能运行 Python 的小型 VPS；
- 一个已配置 HTTPS 的域名；
- 防火墙只公开 80/443，Relay 的 8787 端口仅监听本机或由防火墙拦住。

## 2. 在 Claude Code 电脑安装 watcher

```powershell
cd D:\claude\thinking_pipeline
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
```

编辑 `.env`：

```dotenv
BRIDGE_SINKS=relay
CLAUDE_TRANSCRIPT_GLOB=C:/Users/你的用户名/.claude/projects/**/*.jsonl
RELAY_URL=https://你的域名
RELAY_AGENT_TOKEN=一条长随机值
RELAY_USER_TOKEN=另一条不同的长随机值
```

同一个 `.env` 的 `RELAY_AGENT_TOKEN` 要复制到 VPS；不要发到聊天，不要写进命令行参数，不要提交到 Git。

检查：

```powershell
.\.venv\Scripts\thought-bridge.exe doctor
```

前台试跑：

```powershell
.\.venv\Scripts\thought-bridge-watcher.exe
```

稳定后可运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\install-windows.ps1 -InstallWatcherTask
```

脚本只创建 watcher 的当前用户登录任务，不修改代理、防火墙或系统网络设置。

## 3. 安装“看清自己”风格

Claude Code 用户 output style 的位置：

```text
Windows: C:\Users\你的用户名\.claude\output-styles\看清自己.md
Linux:   ~/.claude/output-styles/看清自己.md
```

仓库的 `templates/看清自己.md` 包含通用的第一人称公开自述 prompt，以及 Relay 识别心里话和正式正文所需的程序封装协议。它不会读取或覆盖机器上已有的同名文件。

```powershell
Copy-Item .\templates\看清自己.md "$env:USERPROFILE\.claude\output-styles\看清自己.md"
```

然后在 `~/.claude/settings.json` 选择：

```json
{
  "outputStyle": "看清自己"
}
```

模板已经要求成品回复遵守 `[[自我状态]]...[[/自我状态]]` 协议，并通过 `reply` 工具发送。如果要改自述规则，可以替换 `## [给user的公开自述]` 部分，但应保留末尾的 `## [程序封装协议]`。

## 4. 注册正式回复 MCP

```powershell
claude mcp add thought-bridge -- D:\claude\thinking_pipeline\.venv\Scripts\python.exe -m thought_bridge.mcp_server
```

重开 Claude Code 后确认能看到 `mcp__thought-bridge__reply`。每调用一次就是一个独立气泡；要三个气泡就调用三次，不要在一次调用里用空行假装分泡。

## 5. 在 VPS 部署 Relay

把仓库复制到例如 `/opt/claude-thought-bridge`，不要复制电脑上的 `.env` 和 `state/`：

```bash
cd /opt/claude-thought-bridge
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env
nano .env
```

VPS `.env` 至少填写：

```dotenv
RELAY_BIND_HOST=127.0.0.1
RELAY_BIND_PORT=8787
RELAY_AGENT_TOKEN=与电脑一致
RELAY_USER_TOKEN=与手机登录一致
RELAY_DB=/var/lib/thought-bridge/relay.sqlite3
VAPID_SUBJECT=mailto:你的邮箱
```

生成 Web Push 密钥：

```bash
.venv/bin/thought-bridge vapid
```

把命令给出的 `VAPID_PRIVATE_KEY` 和 `VAPID_PUBLIC_KEY` 写入 VPS `.env`，私钥文件权限设为 `600`。

安装 systemd：

```bash
sudo useradd --system --home /opt/claude-thought-bridge --shell /usr/sbin/nologin thoughtbridge
sudo install -d -o thoughtbridge -g thoughtbridge /var/lib/thought-bridge /opt/claude-thought-bridge/state
sudo chown -R thoughtbridge:thoughtbridge /opt/claude-thought-bridge
sudo cp deploy/thought-bridge-relay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now thought-bridge-relay
sudo systemctl status thought-bridge-relay
```

## 6. Nginx 与 HTTPS

参考 `deploy/nginx.conf.example`，把域名和证书路径换成自己的。Nginx 反代到 `127.0.0.1:8787`，SSE 路径必须关闭缓冲并延长读取超时。

## 7. 手机首次打开

1. 打开 `https://你的域名/`；
2. 输入 `RELAY_USER_TOKEN`；
3. 确认历史和实时消息正常；
4. 点“开启通知”，允许系统通知；
5. 把页面切到后台后，用 `thought-bridge send --kind reply "测试正文"` 测试。

通知的服务器规则：

- 只处理 `kind=reply`；
- 删除 `[[自我状态]]...[[/自我状态]]`；
- 只有自述而没有正文时不通知；
- `tag=reply-{event_id}`，每个气泡独立，不互相替换。

## 8. 验收

- `thinking`：网页出现折叠过程，但系统没有通知；
- `action`：网页出现动作行，但系统没有通知；
- 一条含自述的 `reply`：网页有心里话+气泡，通知只有正文；
- 连续三次 `reply`：网页三气泡，后台三条独立通知；
- 心里话展开后双击：切到原始过程；
- 原始过程单击：复制并收起。
