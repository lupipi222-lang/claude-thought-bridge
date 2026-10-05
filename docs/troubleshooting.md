# 排错手册

## watcher 没有任何消息

1. 运行 `thought-bridge doctor`；
2. 检查 `CLAUDE_TRANSCRIPT_GLOB` 是否匹配当前项目；
3. watcher 第一次看见一个 transcript 时会从文件尾开始，不补推历史；再发一条新消息测试；
4. 看 `state/watcher.log`，正文不会写进日志。

## 过程有，正式回复没有

正式回复默认不从 transcript 自动抓取。确认 Claude Code 已注册 `thought-bridge` MCP，并且模型调用了 `reply`。

临时调试可以设置 `AUTO_REPLY_FROM_TRANSCRIPT=true`，但可能与 MCP 路径重复，生产不建议打开。

## 正式回复重复

- 关闭 `AUTO_REPLY_FROM_TRANSCRIPT`；
- 确认没有同时运行两个 watcher；
- Relay 会按 `event_id` 去重，但两个独立进程会生成不同 ID。

## 心里话进入了通知

确认边界完全匹配：

```text
[[自我状态]]
...
[[/自我状态]]
```

服务端只对 `reply` 调用 `notification_body()`；不要在 service worker 里用原始事件文本重新组通知。

## 多个气泡只剩一条通知

检查 service worker 的 `tag`。必须使用 `event_id` 派生的唯一值，不能写成固定的 `home-message`。

## iPhone 看不到通知

- HTTPS 必须有效；
- iOS 需要把网页添加到主屏幕后再授权 Web Push；
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` 必须成对；
- 页面在前台时 Relay 默认不推通知；切到后台再测；
- 检查浏览器通知权限和专注模式。

## SSE 一会儿就断

Nginx 的 SSE 路径需要：

```nginx
proxy_buffering off;
proxy_read_timeout 1h;
```

## Telegram 400

常见原因是 Bot Token / chat_id 错误，或消息超过限制。本项目会切长消息并转义 HTML；仍失败时查看 watcher 日志中的 HTTP 状态，但不要打印 Token。
