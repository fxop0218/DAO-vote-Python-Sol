# Imports
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account
from brownie import (
    GovernorContract,
    GovernanceToken,
    GovernanceTimeLock,
    Box,
    Contract,
    config,
    network,
    accounts,
    chain,
)
from web3 import Web3, constants
import time

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
    governance_time_lock = governance_time_lock = (  # Deploy governanceTimelock
        GovernanceTimeLock.deploy(
            MIN_DELAY,
            [],
            [],
            {"from": account},
            publish_source=config["network"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(GovernanceTimeLock) <= 0  # Check if governance timelock exists
        else GovernanceTimeLock[-1]
    )

    governorContract = GovernorContract.deploy(  # Deploy governorContract
        governance_token.address,
        governance_time_lock.address,
        VOTING_DELAY,
        VOTING_PERIOD,
        QUORUM_PERCENTAGE,
        {"from": account},
        publish_source=config["network"][network.show_active()].get("verify", False),
    )

    # Set the roles

    propose_roles = governance_time_lock.PROPOSER_ROLE()
    timelock_admin_roles = governance_time_lock.TIMELOCK_ADMIN_ROLE()
    executor_roles = governance_time_lock.EXECUTOR_ROLE()

    # Grant and revoke the roles
    governance_time_lock.grantRole(propose_roles, governorContract, {"from": account})
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
        GovernanceTimeLock[-1], {"from": account}
    )  # Transfer ownership to the last governanceTimelock
    boxTransaction.wait(1)
    print("Box deployed")
