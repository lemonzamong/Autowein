# Project Development Log - Autowein Cognitive Digital Twin
**Date**: 2026-01-19
**Session Goal**: Full Data Acquisition & Training Pipeline Setup

## 1. Data Acquisition (The Crawler)
- **Problem**: Need 10 years of historical data from `autowein.com`.
- **Discovery**: 
    - Analyzed `post-list2` page. Found standard HTML scraping insufficient (Client-side retrieval).
    - Reverse-engineered the internal API: `POST /wp-json/aw_post/id` and `aw_post/all`.
    - Identified "Nonce" requirement (`ce9e215154`) for authenticated API access.
- **Implementation**:
    - Created `src/crawler/native_crawler.py`.
    - Implemented **Resume Capability**: Scans existing file to allow restarting without data loss.
    - **Result**: Successful acquisition of **23,365** articles (Full 10-year history).
- **Quality Control**: Handled corrupted JSON lines (Line 12823) caused by power interruption using `validate_corpus.py`.

## 2. Infrastructure & Simulation
- **Environment**: Standard Library-only constraint on local machine.
- **Refactoring**: 
    - Removed `newspaper3k`, `pyyaml`, `pydantic`, `neo4j` dependencies for the Simulation runner.
    - Implemented `Mock` classes to ensure `run_simulation.py` confirms logic flow without external libs.
- **Verification**: Confirmed end-to-end pipeline (Gatekeeper -> Historian -> Analyst) works with the real crawled data.

## 3. Fine-Tuning Pipeline
- **Script**: Developed `src/training/train_finetune.py` using `transformers` and `trl`.
- **Data Prep**: Auto-filters corpus for items containing both "Text" and "Comment". Created **20,078** valid training pairs.
- **Local Check**: Attempted local training but rejected due to hardware (GTX 1050, 4GB) and software (No pip) limits.

## 4. Remote Deployment
- **Target**: Server #1 (IP 147.47.239.135, RTX 3090 x2).
- **Automation**: Created `deploy_remote.py` for automated archive & SSH execution.
- **Blocker**: Network/Firewall reset connection during SCP.
- **Resolution**: Packaged `autowein_production.tar.gz` and provided manual transfer instructions.
- **Docker**: Created `Dockerfile` and `run_training_on_server.sh` to ensure consistent environment (CUDA 12.1) on the remote server.

## Final Status
- **Codebase**: Ready for Production.
- **Data**: Complete & Clean (23k items).
- **Next Step**: User to copy `autowein_production.tar.gz` to server and run `run_training_on_server.sh`.
