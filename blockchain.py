import hashlib
import json
from time import time
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests
import logging
import ecdsa
import binascii
import random
import eventlet
import eventlet.wsgi
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
logging.basicConfig(level=logging.INFO)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.tokens = {}
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def proof_of_stake(self):
        return random.choice(list(self.nodes))

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except Exception as e:
                logging.error(f"Error connecting to node {node}: {e}")

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def create_smart_contract(self, condition, action):
        self.current_transactions.append({
            'type': 'smart_contract',
            'condition': condition,
            'action': action,
        })

    def create_token(self, name, total_supply):
        self.tokens[name] = total_supply

# Wallet functionality
def generate_wallet():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    return binascii.hexlify(private_key.to_string()).decode('ascii'), binascii.hexlify(public_key.to_string()).decode('ascii')

def sign_transaction(private_key_hex, transaction):
    private_key = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key_hex), curve=ecdsa.SECP256k1)
    transaction_hash = hashlib.sha256(json.dumps(transaction, sort_keys=True).encode()).digest()
    signature = private_key.sign(transaction_hash)
    return binascii.hexlify(signature).decode('ascii')

# Two-Factor Authentication (Placeholder)
def two_factor_auth(user_id, code):
    return True  # Implement actual 2FA logic here

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_proof = blockchain.last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient="our_address",
        amount=1,
    )

    previous_hash = blockchain.hash(blockchain.last_block)
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

    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    transaction = {
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
    }

    # Verify the signature
    public_key = ecdsa.VerifyingKey.from_string(binascii.unhexlify(values['sender']), curve=ecdsa.SECP256k1)
    transaction_hash = hashlib.sha256(json.dumps(transaction, sort_keys=True).encode()).digest()
    try:
        if not public_key.verify(binascii.unhexlify(values['signature']), transaction_hash):
            return 'Invalid signature', 400
    except:
        return 'Invalid signature', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    try:
        replaced = blockchain.resolve_conflicts()

        if replaced:
            response = {
                'message': 'Our chain was replaced',
                'new_chain': blockchain.chain
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': blockchain.chain
            }

        return jsonify(response), 200
    except Exception as e:
        logging.error(f"Error in consensus: {e}")
        return "Internal Server Error", 500

@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    private_key, public_key = generate_wallet()
    response = {
        'private_key': private_key,
        'public_key': public_key,
    }
    return jsonify(response), 200

@app.route('/transaction/sign', methods=['POST'])
def sign_new_transaction():
    values = request.get_json()

    required = ['private_key', 'transaction']
    if not all(k in values for k in required):
        return 'Missing values', 400

    signature = sign_transaction(values['private_key'], values['transaction'])

    response = {'signature': signature}
    return jsonify(response), 201

@app.route('/smart_contract/new', methods=['POST'])
def new_smart_contract():
    values = request.get_json()

    required = ['condition', 'action']
    if not all(k in values for k in required):
        return 'Missing values', 400

    blockchain.create_smart_contract(values['condition'], values['action'])

    response = {'message': 'Smart contract will be added to the next block'}
    return jsonify(response), 201

@app.route('/token/create', methods=['POST'])
def create_token():
    values = request.get_json()

    required = ['name', 'total_supply']
    if not all(k in values for k in required):
        return 'Missing values', 400

    blockchain.create_token(values['name'], values['total_supply'])
    response = {'message': f'Token {values["name"]} created with total supply {values["total_supply"]}'}
    return jsonify(response), 201


# Enhanced Security - Placeholder for Two-Factor Authentication
@app.route('/2fa', methods=['POST'])
def two_factor_authentication():
    values = request.get_json()

    required = ['user_id', 'code']
    if not all(k in values for k in required):
        return 'Missing values', 400

    if two_factor_auth(values['user_id'], values['code']):
        response = {'message': 'Two-Factor Authentication successful'}
        return jsonify(response), 200
    else:
        return 'Invalid authentication code', 400


# Peer-to-Peer network with Flask-SocketIO
@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')


@socketio.on('new_block')
def handle_new_block(data):
    block = data['block']
    blockchain.chain.append(block)
    emit('block_added', {'message': 'New block added'}, broadcast=True)


@socketio.on('new_transaction')
def handle_new_transaction(data):
    transaction = data['transaction']
    blockchain.current_transactions.append(transaction)
    emit('transaction_added', {'message': 'New transaction added'}, broadcast=True)


import eventlet
import eventlet.wsgi

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)

