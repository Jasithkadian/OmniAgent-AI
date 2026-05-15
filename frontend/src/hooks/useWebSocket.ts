import { useState, useEffect, useCallback, useRef } from 'react';

interface WebSocketOptions {
  url: string;
  token?: string;
  workflowId?: string;
  onMessage?: (data: any) => void;
  autoConnect?: boolean;
}

export const useWebSocket = ({
  url,
  token,
  workflowId,
  onMessage,
  autoConnect = true,
}: WebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const lastMessageIdRef = useRef<string | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectDelay = 30000; // 30 seconds

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    // Append auth and recovery params to URL
    const queryParams = new URLSearchParams();
    if (token) queryParams.append('token', token);
    if (workflowId) queryParams.append('workflow_id', workflowId);
    if (lastMessageIdRef.current) {
      queryParams.append('last_message_id', lastMessageIdRef.current);
    }

    const fullUrl = `${url}?${queryParams.toString()}`;
    const ws = new WebSocket(fullUrl);

    ws.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Track last message ID for recovery
      if (data.message_id) {
        lastMessageIdRef.current = data.message_id;
      }

      if (onMessage) {
        onMessage(data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      
      // Exponential Backoff Reconnect
      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttemptsRef.current),
        maxReconnectDelay
      );
      
      console.log(`WebSocket closed. Reconnecting in ${delay}ms...`);
      setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connect();
      }, delay);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      setError(new Error('WebSocket connection failed'));
      ws.close();
    };

    socketRef.current = ws;
  }, [url, token, workflowId, onMessage]);

  const sendMessage = useCallback((data: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected. Message not sent.');
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      socketRef.current?.close();
    };
  }, [autoConnect, connect]);

  return { isConnected, error, sendMessage, lastMessageId: lastMessageIdRef.current };
};
