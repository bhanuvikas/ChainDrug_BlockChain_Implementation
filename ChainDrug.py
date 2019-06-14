import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import random

import requests
from flask import Flask, jsonify, request

"""
A conceptual blockchain track drug sales.
The idea is to have a way to ensure that at every trasaction is tracked and accounted.
"""
PEERS = [
    'http://localhost:5000/',
    'http://localhost:5001/',
    'http://localhost:5002/',
    'http://localhost:5003/',
    ]

info = [(350, 2618, 17189), (490, 20109, 52691), (640, 18099, 54787), (720, 17066, 25657)]


class ChainDrug:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = PEERS
        # Create the first block - Let there be light
        self.new_block(previous_hash='1', proof=100)


    def valid_chain(self, chain):
        """
        Blockchain validation is done here
        chain: A blockchain
        return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our network consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        Our logic here is that the longest chain is the most valid chain.
        return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # Look only for chains longer than current
        max_length = len(self.chain)

        # Find and verify the chains from all the nodes in network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check to see if length is longer than current and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new block in the blockchain.
        We use the hash of the previous block as part of the immutability of the blockchain
        proof: The proof given by the proof of work algorithm
        previous_hash: Hash of previous block
        return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, owner, receiver, amount, drug_id):
        """
        Creates a new transaction thats queued for the next mined Block
        owner: ID of the current drug owner
        receiver: ID of the drug buyer 
        amount: Amount paid in the transaction
        drug_id: Unique drug id for the drug that's being transacted
        return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'owner': owner,
            'receiver': receiver,
            'amount': amount,
            'drug_id': drug_id
            
        })

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Every block in the network needs a signature -> Reinforces uniqueness and immutability
        We can do that by hashing our block dictionary with SHA-256 hash.
        Creates a SHA-256 hash of a Block
        block: block dictionary
        return: hashed string
        """
        
        """
        The entire dictionary will be hashed.
        We must make sure that the information in the Dictionary is ordered, 
        or we'll have inconsistent hashes across different transactions.
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        last_block: last Block
        return: proof as an integer number
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        last_proof: Previous Proof
        proof: Current Proof
        last_hash: The hash of the Previous Block
        return: True if correct, False if not.
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = ChainDrug()


@app.route('/mineBroadcast', methods=['GET'])
def mineBroadcast():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # Reward transactions have drug_id as 0 to distinguish them.

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200



@app.route('/mine', methods=['GET'])
def mine():
    for PEER in PEERS:
        if PEER[-2] != request.host[-1]:
            try:
                requests.get(PEER + 'mineBroadcast')
            except requests.exceptions.ConnectionError:
                print("Peer " + PEER + " not connected")
                continue
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # Reward transactions have drug_id as 0 to distinguish them.
    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['owner', 'receiver', 'amount', 'drug_id', 'x']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    
    response = {'message': 'Transaction broadcasted to all nodes for verification.'}

    #add h and s to the transaction before broadcasting

    Transaction = dict()

    Transaction['owner'] = values['owner']
    Transaction['receiver'] = values['receiver']
    Transaction['amount'] = values['amount']
    Transaction['drug_id'] = values['drug_id']

    print(request.host)
    A, B, p = info[int(request.host[-1])]

    r = random.randint(0, p-2)

    Transaction['h'] = (A ** r) % p
    Transaction['s0'] = r % (p-1)
    Transaction['s1'] = (r + values['x']) % (p-1)

    print(A, B, p, r, Transaction['h'], Transaction['s0'], Transaction['s1'])

    for PEER in PEERS:
        try:
            r = requests.post(PEER +'broadcast', json = Transaction)
        except requests.exceptions.ConnectionError:
            print("Peer " + PEER + " not connected")
            continue
        

    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


#add arguement
@app.route('/viewUser/<string:port>', methods = ['GET'])
def viewUser(port):
    answer = []
    port = int(port)
    for block in blockchain.chain:
        for transaction in block['transactions']:
            if transaction['owner'] == port or transaction['receiver'] == port:
                answer.append(transaction)
    return jsonify(answer), 200



@app.route('/broadcast', methods = ['POST'])
def verifyTransaction():
    Transaction = request.get_json()
    h, s0, s1 = Transaction['h'], Transaction['s0'], Transaction['s1']
    A, B, p = info[Transaction['owner']-5000]
    print(A, B, p, h, s0, s1)
    if (A**s0) % p == h % p and (A**s1) % p == (h*B) % p:
        blockchain.new_transaction(Transaction['owner'], Transaction['receiver'], Transaction['amount'], Transaction['drug_id'])
        response = {'message': 'Transaction is added to the block.'}
        print("Transaction is added to the block.")
    else:
        response = {'message': 'Fraudulent Transaction discarded.'}
        print("Fraudulent Transaction discarded.")
    return jsonify(response), 201
    


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    # If replaced display message
    if replaced:
        response = {
            'message': 'Current chain was replaced',
            'new_chain': blockchain.chain
        }
    # Else maintain authority of current chain
    else:
        response = {
            'message': 'Current chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200



if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    """
    Change the port number in the parameter: default - to fire up different nodes in the same system.
    The default port number is 5000
    """
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='localhost', port=port, debug=True)