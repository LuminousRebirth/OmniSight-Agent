/** Chat 对话：Agent 智能体对话窗口（DeepSeek Harness 风格：消息流 + 底部多行输入） */
import { useRef, useState } from "react";
import { Button, Input, Tag, Upload } from "antd";
import { PictureOutlined, SendOutlined } from "@ant-design/icons";
import { agentChat, type Detection } from "../api";

interface Msg {
  role: "user" | "assistant";
  text: string;
  image?: string;
  detections?: Detection[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", text: "你好，我是 OmniSight Agent。可以上传图片让我检测分析，或直接向我提问。" },
  ]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState<{ file: File; url: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const scrollBottom = () =>
    setTimeout(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight }), 60);

  const send = async () => {
    if ((!input.trim() && !pending) || loading) return;
    setMessages((m) => [...m, { role: "user", text: input, image: pending?.url }]);
    setInput("");
    setPending(null);
    setLoading(true);
    try {
      const r = await agentChat(input, pending?.file);
      setMessages((m) => [...m, { role: "assistant", text: r.reply, detections: r.detections }]);
    } finally {
      setLoading(false);
      scrollBottom();
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)" }}>
      {/* 消息流 */}
      <div ref={listRef} style={{ flex: 1, overflowY: "auto", padding: "24px 16px" }}>
        <div style={{ maxWidth: 880, margin: "0 auto" }}>
          {messages.map((m, i) => (
            <div key={i} style={{
              display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start",
              marginBottom: 20,
            }}>
              <div style={{
                maxWidth: "82%", padding: "10px 14px", borderRadius: 12,
                background: m.role === "user" ? "var(--primary)" : "#fff",
                color: m.role === "user" ? "#fff" : "var(--text)",
                border: m.role === "assistant" ? "1px solid var(--border)" : "none",
                boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
                whiteSpace: "pre-wrap", wordBreak: "break-word",
              }}>
                {m.image && (
                  <img src={m.image} alt="附图" style={{
                    maxWidth: 300, maxHeight: 220, borderRadius: 8,
                    display: "block", marginBottom: 8,
                  }} />
                )}
                {m.text}
                {m.detections && m.detections.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    {m.detections.map((d, j) => (
                      <Tag key={j} color="blue" className="mono">
                        {d.class_name} {(d.confidence * 100).toFixed(0)}%
                      </Tag>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: "flex", gap: 4, padding: "6px 2px" }}>
              <span style={dot} /><span style={dot} /><span style={dot} />
            </div>
          )}
        </div>
      </div>

      {/* 底部输入区 */}
      <div style={{ borderTop: "1px solid var(--border)", background: "#fff", padding: "12px 16px" }}>
        <div style={{ maxWidth: 880, margin: "0 auto" }}>
          {pending && (
            <div style={{ marginBottom: 8 }}>
              <Tag icon={<PictureOutlined />} closable onClose={() => setPending(null)}>
                已附图（点击 × 移除）
              </Tag>
            </div>
          )}
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <Upload
              accept="image/*" showUploadList={false}
              beforeUpload={(file) => { setPending({ file, url: URL.createObjectURL(file) }); return false; }}
            >
              <Button icon={<PictureOutlined />} style={{ height: 38 }} />
            </Upload>
            <Input.TextArea
              autoSize={{ minRows: 1, maxRows: 6 }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder="输入消息，Enter 发送，Shift+Enter 换行"
              style={{ flex: 1 }}
            />
            <Button type="primary" icon={<SendOutlined />} onClick={send} loading={loading}
              style={{ height: 38 }}>
              发送
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

const dot: React.CSSProperties = {
  width: 6, height: 6, borderRadius: "50%", background: "var(--text-secondary)",
  animation: "pulse 1s infinite",
};
