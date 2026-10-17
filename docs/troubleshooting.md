# 排错手册

## watcher 没有任何消息

1. 运行 `thought-bridge doctor`；
2. 检查 `CLAUDE_TRANSCRIPT_GLOB` 是否匹配当前项目；
3. watcher 第一次看见一个 transcript 时会从文件尾开始，不补推历史；再发一条新消息测试；
4. 看 `state/watcher.log`，正文不会写进日志。

## 过程有，正式回复没有

正式回复默认不从 transcript 自动抓取。确认 Claude Code 已注册 `thought-bridge` MCP，并且模型调用了 `reply`。

临时调试可以设置 `AUTO_REPLY_FROM_TRANSCRIPT=true`，但可能与 MCP 路径重复，生产不建议打开。

## 出现 `reasoning_extraction` 或开窗后第一条就被拒绝

先查看该轮 transcript。如果同时出现 `stop_reason: refusal` 和 `stop_details.category: reasoning_extraction`，这是该轮候选输出触发了“推理提取”分类；不能据此判断是 NSFW、思考等级或账号被永久标记。

按下面顺序排查：

1. 新开一个干净窗口，不要在同一窗口反复重试相同结构；
2. 暂时关闭心里话封装做一次 A/B 测试，记录开启与关闭时的 `stop_reason`；
3. 检查开窗时最终拼接的全部 system prompt、output style、`CLAUDE.md` 和 runtime prompt，不要只检查其中一个文件；
4. 如果使用自建前端且不需要 `reply`，删除额外拼入的 `reply` 封装协议，但保留原本已经验证可用的心里话模板；
5. `thinking` 和行动轨迹由 watcher 从 transcript 外部读取。不要在提示词里要求模型主动“输出、还原、解释或推送原生思考链”；
6. 不要靠切换中／高／x高思考等级解决结构问题。

完整上下文也会影响分类结果。一次 A/B 只能定位可疑层，不能证明某个账号被标记，也不能保证任何提示在所有上下文中都不会被拒绝。

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
