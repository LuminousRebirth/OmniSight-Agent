/** WebSocket hook：连接实时检测流，接收帧/结果/状态消息 */
import { useEffect, useRef, useState } from "react";

export function useSocket(url: string | null, onMessage: (msg: Record<string, unknown>) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!url) return;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onmessage = (e) => onMessageRef.current(JSON.parse(e.data));
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [url]);

  return { connected };
}
