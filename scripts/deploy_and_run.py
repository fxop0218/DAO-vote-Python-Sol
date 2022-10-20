# Imports
from asyncio.trsock import TransportSocket
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account
from brownie import (
    GovernorContract,
    GovernanceToken,
    GovernanceTimeLocker,
    Box,
    Contract,
    config,
    network,
    accounts,
    chain,
)
from web3 import Web3, constants


# Constants

QUORUM_PERCENTAGE = 4
VOTING_PERIOD = 5
VOTING_DELAY = 1
MIN_DELAY = 1

PROPOSAL_DESCRIPTION = "Proposal #1: Store 1 in the Box!"
NEW_STORE_VALUE = 5


# Functions
# Main function
def deploy_governor():
    account = get_account()  # Get accoutns
    governance_token = (  # Deploy governance token
        GovernanceToken.deploy(
            {"from": account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(GovernanceToken) <= 0  # Check if governance token exists
        else GovernanceToken[-1]
    )
    governance_token.delegate(
        account, {"from": account}
    )  # Delegate the governance token to account
    print(f"CheckPoint {governance_token.numCheckpoints(account)}")
    governance_time_lock = governance_time_lock = (  # Deploy GovernanceTimeLocker
        GovernanceTimeLocker.deploy(
            MIN_DELAY,
            [],
            [],
            {"from": account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(GovernanceTimeLocker) <= 0  # Check if governance timelock exists
        else GovernanceTimeLocker[-1]
    )

    governor = GovernorContract.deploy(  # Deploy governorContract
        governance_token.address,
        governance_time_lock.address,
        VOTING_DELAY,
        VOTING_PERIOD,
        QUORUM_PERCENTAGE,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )

    # Set the roles

    propose_roles = governance_time_lock.PROPOSER_ROLE()
    timelock_admin_roles = governance_time_lock.TIMELOCK_ADMIN_ROLE()
    executor_roles = governance_time_lock.EXECUTOR_ROLE()

    # Grant and revoke the roles
    governance_time_lock.grantRole(propose_roles, governor, {"from": account})
    governance_time_lock.grantRole(
        executor_roles, constants.ADDRESS_ZERO, {"from": account}
    )

    transaction = governance_time_lock.revokeRole(
        timelock_admin_roles, account, {"from": account}
    )
    transaction.wait(1)


# Deploy box function
def deploy_box_to_be_governed():
    account = get_account()
    box = Box.deploy({"from": account})
    boxTransaction = box.transferOwnership(
        GovernanceTimeLocker[-1], {"from": account}
    )  # Transfer ownership to the last governanceTimelock
    boxTransaction.wait(1)
    print("Box deployed")


def propose(store_val):
    account = get_account()  # Get account
    # Store the 1 number
    # With mora args, just add comas and the items
    # Is no arguments, use 'eth_utils.to_bytes(hexstr="0x")
    args = (store_val,)
    # we could do this next line with just the Box object but this is to show it can be any function with any contract
    encoded_function = Contract.from_abi("Box", Box[-1], Box.abi).store.encode_input(
        *args
    )
    print(encoded_function)

    propose_transaction = GovernorContract[-1].propose(
        [Box[-1].address],
        [0],
        [encoded_function],
        PROPOSAL_DESCRIPTION,
        {"from": account},
    )

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        transaction = account.transfer(accounts[0], "0 ether")
        transaction.wait(1)

    propose_transaction.wait(2)  # wait 2 blocks to inclue the voting delay
    # Will return proposal ID
    print(
        f"Proposal state {GovernorContract[-1].state(propose_transaction.return_value)}"
    )
    print(
        f"Proposal snapshot {GovernorContract[-1].proposalSnapshot(propose_transaction.return_value)}"
    )
    print(
        f"Proposal deadline {GovernorContract[-1].proposalDeadline(propose_transaction.return_value)}"
    )
    return propose_transaction.return_value


def move_blocks(amount):
    print("Moving blocks")
    for i in range(0, amount):
        get_account().transfer(get_account(), "0 ether")
    print(chain.height)


def queue_and_execute(store_val):
    account = get_account()
    # We need to explicity give it everything, including the description hash
    # it gets the proposal id like so:
    # uint256 proposalId = hashProposal(targets, value, calldatas, descriptions)
    # It's nearlly exactly the same as the "propose" function, but we hash the description
    args = (store_val,)
    encoded_function = Contract.from_abi("Box", Box[-1], Box.abi).store.encode_input(
        *args
    )

    description_hash = Web3.keccak(text=PROPOSAL_DESCRIPTION).hex
    transaction = GovernorContract[-1].queue(
        [Box[-1].address], [0], [encoded_function], description_hash, {"from": account}
    )
    transaction.wait(1)
    transaction = GovernorContract[-1].execute(
        [Box[-1].address], [0], [encoded_function], description_hash, {"from": account}
    )

    transaction.wait(1)
    print(Box[-1].retrieve())


def vote(proposal_id: int, vote: int):
    # 0 = Against, 1 = for, 2 = Abstain
    # You can all  #COUNTING_MODE() function to see how to vote otherwise
    print(f"Voting yes on {proposal_id}")
    account = get_account()
    transaction = GovernorContract[-1].castVoteWithReason(
        proposal_id, vote, "I want a dolar", {"from": account}
    )
    transaction.wait(1)
    print(transaction.events["VoteCast"])


def main():
    deploy_governor()
    deploy_box_to_be_governed()
    # Get proposal id
    proposal_id = propose(NEW_STORE_VALUE)

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(VOTING_PERIOD)
    vote(proposal_id, 1)

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(VOTING_PERIOD)

    print(f"This proposal is currently {GovernorContract[-1].state(proposal_id)}")
    queue_and_execute(NEW_STORE_VALUE)
