import hashlib
import json
import time
from datetime import datetime


# ===========================
#   BLOCK CLASS
# ===========================
class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0, hash_val=None):
        # Unique ID of the block in the chain
        self.index = index

        # When the block was created (string timestamp)
        self.timestamp = timestamp

        # Block content (transaction, message, etc.)
        self.data = data

        # Hash of the previous block → ensures chain continuity
        self.previous_hash = previous_hash

        # Value used for proof-of-work
        self.nonce = nonce

        # Final hash of this block (computed at creation or after mining)
        self.hash = hash_val or self.compute_hash()

    def compute_hash(self):
        """
        Computes the SHA-256 hash of the block.
        This converts the block into a stable JSON string before hashing.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True, separators=(',', ':'))  # ensures consistent ordering

        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self):
        # When printing a block, display a short version of its hash for readability
        return (f"Block(index={self.index}, timestamp={self.timestamp}, nonce={self.nonce}, "
                f"hash={self.hash[:12]}..., prev={self.previous_hash[:12]}...)")


# ===========================
#   BLOCKCHAIN CLASS
# ===========================
class Blockchain:
    def __init__(self, difficulty=2):
        """
        difficulty: how many leading zeros are required in the block hash.
        Higher difficulty = longer mining time.
        """
        self.difficulty = difficulty
        self.chain = []

        # Lists to store mining statistics (for the report)
        self.mining_times = []   # seconds spent mining each block
        self.nonce_counts = []   # nonce used for each block

        # Create the first block
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Creates the first block of the blockchain ("Genesis block").
        """
        ts = datetime.utcnow().isoformat()
        genesis = Block(index=0, timestamp=ts, data="Genesis Block", previous_hash="0")

        # The genesis block is also mined (optional but educational)
        mined_genesis, t, nonce = self.proof_of_work(genesis)

        # Add to chain + save mining stats
        self.chain.append(mined_genesis)
        self.mining_times.append(t)
        self.nonce_counts.append(nonce)

    def latest_block(self):
        """
        Returns the last block in the chain.
        """
        return self.chain[-1]

    def add_block(self, data):
        """
        Creates and mines a new block, then adds it to the chain.
        """
        prev = self.latest_block()
        index = prev.index + 1
        ts = datetime.utcnow().isoformat()

        new_block = Block(index=index, timestamp=ts, data=data, previous_hash=prev.hash)

        # Mine it (proof-of-work)
        mined_block, t, nonce = self.proof_of_work(new_block)

        # Add to chain and save mining data
        self.chain.append(mined_block)
        self.mining_times.append(t)
        self.nonce_counts.append(nonce)

        return mined_block

    def proof_of_work(self, block):
        """
        The mining algorithm.
        We increase the nonce until the hash starts with 'difficulty' number of zeros.
        """
        start = time.time()  # start timing

        prefix = '0' * self.difficulty
        nonce = 0

        while True:
            block.nonce = nonce
            computed_hash = block.compute_hash()

            # Check if hash meets difficulty requirement
            if computed_hash.startswith(prefix):
                block.hash = computed_hash
                elapsed = time.time() - start
                return block, elapsed, nonce

            # Otherwise increase nonce and try again
            nonce += 1

    def is_chain_valid(self):
        """
        Verifies:
        1. Previous hash links
        2. Block hash consistency
        3. Difficulty rule compliance
        """
        prefix = '0' * self.difficulty

        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            # 1) The "previous_hash" must match the real hash of the previous block
            if curr.previous_hash != prev.hash:
                return False, f"Block {i}: previous_hash does not match (chain broken)."

            # 2) Recompute the hash and compare
            recomputed = curr.compute_hash()
            if recomputed != curr.hash:
                return False, f"Block {i}: Hash tampering detected."

            # 3) Hash must satisfy the difficulty (e.g. start with "000")
            if not curr.hash.startswith(prefix):
                return False, f"Block {i}: Difficulty rule violated."

        # Validate genesis block too
        genesis = self.chain[0]
        if not genesis.hash.startswith(prefix):
            return False, "Genesis block does not meet difficulty."
        if genesis.compute_hash() != genesis.hash:
            return False, "Genesis block hash mismatch."

        return True, "Chain is valid."

    def print_chain(self):
        """
        Prints the entire blockchain with all details.
        """
        print("Blockchain (length = {}):".format(len(self.chain)))
        for block in self.chain:
            print("-" * 80)
            print(f"Index       : {block.index}")
            print(f"Timestamp   : {block.timestamp}")
            print(f"Data        : {block.data}")
            print(f"PreviousHash: {block.previous_hash}")
            print(f"Nonce       : {block.nonce}")
            print(f"Hash        : {block.hash}")
        print("-" * 80)

    def tamper_block(self, index, new_data):
        """
        Modify a block’s data without re-mining it → simulates hacking.
        Validation should then fail.
        """
        if index < 0 or index >= len(self.chain):
            raise IndexError("Block index out of range")

        self.chain[index].data = new_data
        # We DO NOT recompute the hash → this breaks the chain on purpose

    # ---------------------------------------
    # BONUS: mining statistics
    # ---------------------------------------
    def average_mining_time(self):
        return sum(self.mining_times) / len(self.mining_times) if self.mining_times else 0

    def average_nonce(self):
        return sum(self.nonce_counts) / len(self.nonce_counts) if self.nonce_counts else 0


# ===========================
#   MAIN PROGRAM (DEMO)
# ===========================
if __name__ == "__main__":
    # You can change difficulty for testing
    difficulty = 3
    bc = Blockchain(difficulty=difficulty)

    print(f"Genesis mined in {bc.mining_times[0]:.4f}s with nonce {bc.nonce_counts[0]} (difficulty={difficulty})\n")

    # Example data for new blocks
    blocks_to_add = [
        "Alice pays 5 BTC to Bob",
        "Bob pays 2 BTC to Charlie",
        {"from": "Charlie", "to": "Dave", "amount": 1.234},
        "Final block with text"
    ]

    # Add and mine blocks
    for data in blocks_to_add:
        mined = bc.add_block(data)
        print(f"Mined Block {mined.index} in {bc.mining_times[-1]:.4f}s (nonce={bc.nonce_counts[-1]}) hash={mined.hash[:20]}...")

    print("\nFull chain:")
    bc.print_chain()

    # Validate chain
    valid, msg = bc.is_chain_valid()
    print("\nValidation:", valid, "-", msg)

    # Bonus statistics
    print(f"\nAverage mining time: {bc.average_mining_time():.4f}s")
    print(f"Average nonce      : {bc.average_nonce():.1f}")

    # Tamper demonstration
    print("\n-- Tampering with block 2 data --")
    bc.tamper_block(2, "This was hacked!")

    valid, msg = bc.is_chain_valid()
    print("After tampering, validation:", valid, "-", msg)

    # Display broken chain
    bc.print_chain()
