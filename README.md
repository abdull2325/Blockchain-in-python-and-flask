# Blockchain-in-python-and-flask

A comprehensive blockchain implementation using Python and Flask, featuring smart contracts, wallet systems, and various consensus algorithms.

## Features

- Create a new blockchain
- Add new transactions to the blockchain
- Mine new blocks
- Register new nodes
- Resolve conflicts between nodes (Consensus)
- Smart Contracts
- Wallet System
- Interactivity with Real-World Applications
- Multiple Consensus Algorithms (PoW, PoS, DPoS, BFT)
- Peer-to-Peer Network
- Enhanced Security Measures
- Tokenization
- Scalability Solutions

## How to Run

After your Flask SocketIO server starts running, use Postman to interact with the following endpoints:

### 1. Create a New Wallet
- **Endpoint:** `/wallet/new`
- **Method:** GET

### 2. Create a New Transaction
- **Endpoint:** `/transactions/new`
- **Method:** POST
- **Body:**
  ```json
  {
    "sender": "<public_key_of_sender>",
    "recipient": "<public_key_of_recipient>",
    "amount": 10,
    "signature": ""
  }

 ### 3. Sign a Transaction

- **Endpoint:** /transaction/sign
- **Method:** POST
- **Body:**
  ```json

{
  "private_key": "<private_key>",
  "transaction": {
    "sender": "<public_key_of_sender>",
    "recipient": "<public_key_of_recipient>",
    "amount": 10
  }
}
4. Mine a New Block

Endpoint: /mine
Method: GET

5. Get the Full Blockchain

Endpoint: /chain
Method: GET

6. Register a Node

Endpoint: /nodes/register
Method: POST
Body:
jsonCopy{
  "nodes": ["http://localhost:5001"]
}


7. Resolve Conflicts

Endpoint: /nodes/resolve
Method: GET

8. Create a Smart Contract

Endpoint: /smart_contract/new
Method: POST
Body:
jsonCopy{
  "condition": "if temperature > 30",
  "action": "send 10 tokens to recipient"
}


9. Create a Token

Endpoint: /token/create
Method: POST
Body:
jsonCopy{
  "name": "TokenName",
  "total_supply": 1000000
}

