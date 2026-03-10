// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DocumentTimestamp {

    address public owner;
    bool public paused;

    struct Record {
        bytes32 documentHash;
        address sender;
        uint256 timestamp;
    }

    mapping(bytes32 => Record) private records;

    event DocumentStored(
        bytes32 indexed documentHash,
        address indexed sender,
        uint256 timestamp
    );

    event Paused();
    event Unpaused();

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    constructor() {
        owner = msg.sender;
        paused = false;
    }

    function storeDocument(bytes32 _hash) external whenNotPaused {
        require(records[_hash].timestamp == 0, "Document already stored");

        records[_hash] = Record({
            documentHash: _hash,
            sender: msg.sender,
            timestamp: block.timestamp
        });

        emit DocumentStored(_hash, msg.sender, block.timestamp);
    }

    function verifyDocument(bytes32 _hash) external view returns (bool exists, uint256 timestamp, address sender) {
        Record memory record = records[_hash];

        if (record.timestamp == 0) {
            return (false, 0, address(0));
        }

        return (true, record.timestamp, record.sender);
    }

    function pause() external onlyOwner {
        paused = true;
        emit Paused();
    }

    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused();
    }
}
