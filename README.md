# Blockchain Document Timestamp

Implementation of a blockchain-based timestamping system for digital documents using Ethereum smart contracts and a Python client.

This project was developed as part of a bachelor thesis and demonstrates how blockchain technology can be used to create trusted timestamps and verify the integrity of digital documents.

## Project Structure

python-client/  
Python application that interacts with the smart contract and allows storing and verifying document timestamps.

smart-contract/  
Solidity smart contract used to store document hashes and timestamps on the Ethereum blockchain.

text_example/  
Example file used for demonstrating timestamp verification.

## Requirements

Python 3.9 or newer.

Install dependencies:

pip install -r python-client/requirements.txt

## Usage

Navigate to the python-client directory and run the commands below.

Generate a hash of a document:

python document_timestamp_client.py hash <file>

Store the document hash on the blockchain:

python document_timestamp_client.py anchor <file>

Verify the document timestamp and integrity:

python document_timestamp_client.py verify <file>

Check contract status:

python document_timestamp_client.py status

## Bachelor Thesis

This repository contains the source code developed as part of the bachelor thesis focused on analyzing blockchain technology and implementing a prototype system for document timestamping using Ethereum smart contracts and a Python client.

## Author

Mykyta Poznyshev  
Czech University of Life Sciences Prague  
Faculty of Economics and Management
Department of Information Technologies
Bachelor Thesis Project
