# 架构与消息协议

## 这套东西在做什么

Claude Code 会把一轮会话持续写入本机 JSONL transcript。这个仓库从 transcript 尾部增量读取两类事件：

- `thinking`：内部过程文本；
- `tool_use`：工具动作，只保留安全的人话摘要，不转发工具参数和工具返回值。

正式回复不从 transcript 自动抓取。模型显式调用 MCP 的 `reply` 工具，一次调用就是一个稳定的消息边界。这样可以避免：

- 一条长回复被误拆成多条；
- 多个气泡被合成一条；
- transcript 与 MCP 双路径造成重复发送。

默认数据流：

```text
Claude Code transcript
  └─ watcher.py
      ├─ thinking ─────────┐
      └─ action ───────────┤
                           ├─ Relay / Telegram
Claude Code reply MCP ─────┘
```

## 统一事件

```json
{
  "event_id": "uuid",
  "ts": "2026-01-01T00:00:00+00:00",
  "conversation_id": "main",
  "kind": "thinking | action | reply",
  "text": "...",
  "meta": {}
}
```

`event_id` 是去重键，也是正式气泡的通知 ID。

## 自述块协议

正式回复可以用下面的机器可读边界携带一段自述：

```text
[[自我状态]]
这里是安装者自己的自述内容
[[/自我状态]]
——
这里是正式回复
```

Relay 原样保存全文。不同消费者做不同处理：

- 网页：自述块显示为“心里话”，正式回复显示成气泡；
- 通知：先删除整个自述块，只使用正式回复；
- Telegram：自述块作为静默可展开引用，正式回复作为正常消息。

如果一条消息只有自述块，没有正式回复，则不发系统通知。

## 回合分组

前端把一个正式回复前积累的 `thinking` / `action` 附着到该回复。连续多个 `reply` 事件保持多个气泡。超过五分钟的孤立过程会单独显示，避免错误归到下一轮。

## 失败边界

- transcript 读取使用字节 offset，只消费换行结束的完整 JSON 记录；
- 切换到新 transcript 时默认从文件尾开始，不补发旧历史；
- Relay 以 `event_id` 唯一约束实现幂等；
- 推送失败不影响消息入库和 SSE；
- Telegram / Relay 任一输出失败会记录错误，不把另一个输出伪装成成功。
