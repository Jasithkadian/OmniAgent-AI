import { WebSocketEvent } from '@/types/workflow';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/workflows/ws';

export class WorkflowSocket {
  private socket: WebSocket | null = null;
  private onEvent: (event: WebSocketEvent) => void;

  constructor(onEvent: (event: WebSocketEvent) => void) {
    this.onEvent = onEvent;
  }

  connect() {
    this.socket = new WebSocket(WS_URL);

    this.socket.onopen = () => {
      console.log('Connected to Workflow WebSocket');
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onEvent(data);
    };

    this.socket.onclose = () => {
      console.log('Disconnected from Workflow WebSocket');
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  }

  send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not open');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}
