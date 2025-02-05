import { Injectable, OnDestroy } from '@angular/core';
import { io, Socket } from 'socket.io-client'; // Import socket.io-client
import { Subject } from 'rxjs'; // Import Subject to create observables for event listening
import { HOST } from '../../../../environment';

@Injectable({
  providedIn: 'root',
})
export class SocketService implements OnDestroy {
  private socket: Socket | undefined;
  private messageSubject = new Subject<any>(); // Subject to emit messages to subscribers

  constructor() {
    // Connect to the WebSocket server
    this.socket = io(`http://${HOST}:5001`, {
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
    });

    // Listen for messages from the server and emit them to the messageSubject
    this.socket.on('message', (data: any) => {
      console.log('Message received from BE:', data);
      this.messageSubject.next(data); // Emit the message to the subscribers
    });
  }

  // Emit messages to the server
  sendMessage(message: string) {
    if (this.socket) {
      this.socket.emit('whatsapp_chat', message);
    }
  }

  // Return the observable of the messageSubject to subscribe to messages
  getMessages() {
    return this.messageSubject.asObservable();
  }

  // Clean up the socket connection on service destroy
  ngOnDestroy() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}
