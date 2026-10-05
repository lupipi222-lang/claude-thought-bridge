# 安全与隐私

这套程序处理的是高敏感数据。内部过程可能出现文件名、代码片段、命令、上下文摘要和临时凭据。默认遮盖只是一层兜底，不是绝对的数据防泄漏方案。

## 必做

- `.env`、数据库、日志、VAPID 私钥永远不提交；
- Relay 的 agent token 与 user token 必须不同；
- 使用至少 32 字节随机值；
- VPS 只公开 HTTPS；
- Telegram Bot 只允许自己的 `chat_id`；
- 定期轮换 Token；
- watcher 的运行账号只给需要的文件权限；
- 日志只记录事件类型和 ID，不记录正文；
- 发布仓库前执行 `git status --ignored` 和密钥扫描。

生成随机值示例：

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
```

```bash
openssl rand -hex 32
```

## 默认遮盖

`BRIDGE_REDACT=common` 会遮盖常见 GitHub / API Token、Bearer 值和 `token=...` / `password=...` 形式。它可能漏掉非标准格式，也可能误伤正常文本。

如果内容不能离开电脑，就不要把 watcher 指向它，而不是依赖正则表达式。

## 不要做

- 不要把 Token 放进 URL；网页实时流通过 HttpOnly 会话 Cookie 鉴权，代理日志不会记录 Token；
- 不要在截图里展示 `.env`；
- 不要让 Bot 的消息直接进入 shell；
- 不要把整个生产目录直接 `git add -A`；
- 不要给过程消息开启系统提醒；
- 不要用一个恒定 notification tag，否则连续正式气泡会互相覆盖。
