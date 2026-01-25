import socket
import threading
import json
from network.protocol import Protocol

class Node:
    def __init__(self, host, port, blockchain):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = [] # List of (host, port) tuples
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        """Start the node server in a background thread"""
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        while True:
            client, addr = self.socket.accept()
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def handle_client(self, client):
        try:
            data = client.recv(1024 * 10).decode('utf-8')
            if data:
                message = json.loads(data)
                self.process_message(message)
        except Exception as e:
            print(f"Network error: {e}")
        finally:
            client.close()

    def process_message(self, message):
        msg_type = message.get("type")
        
        if msg_type == Protocol.NEW_BLOCK:
            print(f"📩 Node {self.port} received a new block from peer!")
            # Logic to validate and add to blockchain goes here
            
        elif msg_type == Protocol.SYNC_CHAIN:
            # Send our chain to the requesting peer
            pass

    def broadcast(self, message_type, data):
        """Send data to all known peers"""
        message = {"type": message_type, "data": data}
        for peer in self.peers:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                s.send(json.dumps(message).encode('utf-8'))
                s.close()
            except ConnectionRefusedError:
                print(f"Peer {peer} is offline")