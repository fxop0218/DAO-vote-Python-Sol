// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Box is Ownable {
    uint256 private value;
    // emit a event when the value changes
    event ValueChanged(uint256 newValue);

    // Store the value
    function store(uint256 newValue) public onlyOwner {
        value = newValue;
        emit ValueChanged(newValue);
    }

    // Read the last value
    function retrieve() public view returns (uint256) {
        return value;
    }
}
