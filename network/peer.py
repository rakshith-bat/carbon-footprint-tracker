class PeerManager:
    def __init__(self, initial_peers=None):
        # Store peers as a set of strings like "127.0.0.1:5001"
        self.peers = set(initial_peers) if initial_peers else set()

    def add_peer(self, peer_address):
        self.peers.add(peer_address)

    def get_all_peers(self):
        return list(self.peers)