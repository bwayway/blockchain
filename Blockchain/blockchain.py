import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask,jsonify,request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        #An empty list of dictionaries (blocks) that hold the sender address, recipient address, and the amount of the transaction
        self.current_transactions = []

        #Used keyword arguments to help visualize
        #Genesis block
        self.new_block(proof = 1, previous_hash = 1000)
    
    def new_block(self, proof, previous_hash):
        #Creates a new Block and adds it to our chain. returns a dictionary of a new block
        """
        proof <int> - Value assigned from the Proof Of Work algorithm
        previous_hash <str> - Hash from the previous block in the chain
        """
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof" : proof,
            "previous_hash" : previous_hash or self.hash(self.chain[-1])
        }
        #reset the current transactions so they don't duplicate
        self.current_transactions = []

        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        #creates a hash of the block
        #json.dumps converts the block into a json format. sort_keys sorts the block (dictionary) so that it's the same order each time/Keeps the blockchain from altering.
        block_string = json.dumps(block,sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest

    @property
    def last_block(self):
        #Gets the last block of the chain
        return self.chain[-1]

    def new_transaction(self, sender, receiver, amount):
        """
        Creates a new transaction to go into a new block, and returns the index of the block
        sender - <str> Address of the sender of the transaction
        receiver - <str> Address of the receiver of the transaction 
        amount - <float> Amount of the transaction
        """

        self.current_transactions.append({
            "sender" : sender,
            "receiver" : receiver,
            "amount" : amount
        })
        return self.last_block["index"] + 1


    #PROOF OF WORK ALGORITHMS
    """
    PoW is essentially how blockchains are "mined". A complex equation must be solved, typically with a solution/number that is difficult to solve, but easy to verify. 
    """
    def proof_of_work(self, last_proof):

        """
        Find a number y such that hash(xy) has 4 leading zeros where x is the previous proof and y is the new proof

        last_proof <int> - The value that solves the last proof of work algorithm
        """
        
        proof = 0
        while self.valid_proof(last_proof,proof) is False:
            proof +=1
        return proof
    
    @staticmethod
    def valid_proof(last_proof,proof):
        """
        Hash the combination of last_proof and the current proof (hash(last_proof,proof) and return True if the hash contains 4 leading zeros
        last_proof <int> - value that solved the proof of the last block
        proof <int> - value that is used to attempt to solve the current proof
        """
        #Combine the proofs and convert it to a hash value (in this case sha256)
        
        combined_hash_value = f'{last_proof}{proof}'.encode()
        hash_value_guess = hashlib.sha256(combined_hash_value).hexdigest()
        if hash_value_guess[:4] == "0430":
            return True
        else:
            return False


#API 
"""
Because API's and Flask are all relatively new to me, I commented in some stream of conciousness to help me understand what's going on when I come back later. Might be a bit messy...
"""


#Instantiate the node
#Flask(__name__) is used to tell Flask where the current module is defined

app = Flask(__name__)

#Generate a GUID as an address for the node
#GUID is a unique identifier with a specific structure (check out guid.one for more info)

node_identifier = str(uuid4()).replace("-","")

#Instantiate the block chain

blockchain = Blockchain()



#app.route tells us that whenever a user visits the app.domain (myapp.com), the following function will be called. In this case, myapp.com/mine
@app.route("/mine", methods = ["GET"])
def mine():

    #calculate the proof of the new block, by solving the proof of work for the last block of the chain
    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    #Add a new block to the chain, with the sender as 0 to signify that the transaction was mined

    #Create a new transaction and add it to the list of transactions on the blockcain object
    blockchain.new_transaction(0,node_identifier, 1)

    #Now tht the transactions are updated, we can create a new block and add it to the blockchain
    previous_hash = blockchain.hash(last_block)
    new_block = blockchain.new_block(proof,previous_hash)

    response = {
        'message': 'New Block Forged',
        'index': new_block['index'],
        'transactions': new_block['transactions'],
        'proof': new_block['proof'],
        'previous_hash': new_block['previous_hash'],
    }


    return jsonify(response), 200





#Eendpoint for adding a new transaction
@app.route("/transactions/new", methods = ["POST"])
def new_transaction():
    #First get all the values from the request. Request class if from the Flask module
    values = request.get_json()

    #Check that all the fields for the request are filled out
    required = ["sender","receiver", "amount"]

    if not all(k in values for k in required):
        return "Missing values in request" , 400

    
    index = blockchain.new_transaction(values["sender"], values["receiver"], values["amount"])
    response = {"message": "New transaction will be added to block "+ index}


    #Jsonify takes in a dictionary and returns a json file/format
    return jsonify(response), 201





#Endpoint for getting the entire chain as a response. Returns as a JSON
@app.route("/chain", methods = ["GET"])
def get_chain():
    response = { 
        "chain" : blockchain.chain,
        "length" : len(blockchain.chain)
    }

    return jsonify(response), 200



# __name__ returns the name of the current process. Essentially, if __name___ == __main__ Then we are running in the current module, not from an imported one
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
