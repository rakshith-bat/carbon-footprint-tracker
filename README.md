# GitHub Codespaces ♥️ Flask
DISCLAIMER:
## Scope & Intent

This project is an academic / experimental prototype.
The goal is to demonstrate:
- carbon footprint computation logic
- blockchain-inspired ledger mechanics
- UI + backend integration

It is NOT intended for:
- production deployment
- real financial transactions
- security-critical usage

PROJECT DEVELOPMENT:
project starting date (v3_different from prototypes):  13-jan-2026 

Note this is not official project start date, but , it is completely new , concept , with clear working interface


first commit 15-jan, finsihed templates, and app.py



jan 17 - v3.1 , works but can be better, so , hoping to reconfigure


jan 19- asked help form teammate, so work on blockchain end

jan 20- teammate agreed to help ,and gave , blockchian netwrok v0.01 , crude and doenst work, so advised to change


jan 24 - added blockchain part, somewhat works,but needs more improvement, currently , cannot mine blocks , and results are not clean


jan 25 - added authenticatorkeys


jan 27 to feb 2 - fixed all minor errors , and all laoding issues, 

## Contribution Breakdown

Rakshith:
- Frontend implementation (HTML templates, CSS, JavaScript)
- Application logic and integration
- Emissions calculation module (`emissions.py`)
- Configuration management (`config.py`)
- Authentication mechanism (`authkey.txt`)
- UI assets and models (WallE)
- Overall system integration and debugging and testing

Shared Contribution:
- Core blockchain flow and integration
  (`core/block.py`, `core/state.py`, `blockchain.py`, `miner/miner.py`,`users.py`,)

Ashutosh:
- Supporting backend modules
  (`core/transaction.py`, `consensus/pow.py`, `network/node.py`,`network/peer.py`,`network/protocol.py`,`storage/disk.py`)

SUMMARY:
## Contribution Breakdown (High-Level)

Rakshith:
- System architecture & overall design direction
- Complete frontend implementation
- Core business logic (emissions, scoring, rewards)
- App orchestration, authentication layer, and integration
- Debugging, refactoring, and final stabilization

Ashutosh:
- Initial blockchain-related modules and experimentation
- Supporting backend components used as reference and extended


## Versioning Note

All versions prior to v3 were experimental prototypes.
v3 is a clean reimplementation and should be treated as the
first coherent version of the project.


## Primary Author

Primary author and maintainer: Rakshith K  
Secondary contributor: Ashutosh (specific modules only)
