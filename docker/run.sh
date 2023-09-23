#!/bin/bash


spade_executable_path="/SPADE/bin/spade"
spade_dir="/SPADE"

if ! [ -d "$spade_dir" ]
then
    echo Mount $spade_dir to continue
    exit
fi

if ! [ -f "$spade_executable_path" ]
then
    echo "$spade_executable_path does not exist."
    echo Performing initial SPADE configuration...
    
    cd /SPADE && git clone https://github.com/ashish-gehani/SPADE.git

    echo Starting the build
    cd /SPADE && ./configure
    echo Building SPADE
    make -C /SPADE
    sudo chown root /SPADE/bin/spadeAuditBridge
    sudo chmod ug+s /SPADE/bin/spadeAuditBridge
fi

$spade_executable_path stop
$spade_executable_path start

$spade_executable_path control <<< "remove storage Neo4j"
$spade_executable_path control <<< "add storage Neo4j"
$spade_executable_path control <<< "set storage Neo4j"
$spade_executable_path control <<< "add analyzer CommandLine"

tail -f  /dev/null