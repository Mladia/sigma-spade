# sigma-spade

Collections of bash scripts, a docker container and rules for detection of cyberattacks

---

fill out the variables ./scripts/args and run either record a session with
```
cd ./scripts
bash record
```
or perform a detection
```
cd ./scripts
bash detect some_audit_log.log
```

On the initial execution, the script will build and start the docker container. The script creates and uses the folder `~/.sigma-spade/` for intermediary storage.

This repository contains:
- scripts for recording a session and performing a detection based on 
- detection rules translated from SIGMA into queries for
- containerized SPADE instance for performing detection using provenance analysis
%TODO: Add scripts for translation of sigma rules

Requirements:
- bash
- docker


###  Recording a session: 
%TODO:
A virtual machine with root access is needed.
Audit rules used for the log recording in ```audit/audit.rules```
