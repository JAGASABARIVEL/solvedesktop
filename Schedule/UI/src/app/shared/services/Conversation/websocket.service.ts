import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class WebSocketService {
  private socket: WebSocket | null = null;

  /**
   * Connects to the given WebSocket URL.
   * @param url The WebSocket endpoint to connect to.
   */
  connect(url: string): WebSocket {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.close(); // Close any existing connection before reconnecting
    }

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log('WebSocket connected:', url);
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket closed:', event);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return this.socket;
  }

  /**
   * Sends a message through the WebSocket connection.
   * @param message The message to send.
   */
  sendMessage(message: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not open. Cannot send message.');
    }
  }

  /**
   * Subscribes to incoming messages from the WebSocket connection.
   * @param callback A function to handle incoming messages.
   */
  onMessage(callback: (data: any) => void): void {
    if (!this.socket) {
      console.error('WebSocket is not initialized.');
      return;
    }

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };
  }

  /**
   * Disconnects the WebSocket connection.
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
