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
    cd /tmp/
    git clone https://github.com/ashish-gehani/SPADE.git
    cp -r /tmp/SPADE/* /SPADE/

    ./configure
    ./make -j 8
fi

$spade_executable_path stop
$spade_executable_path start

$spade_executable_path control <<< "remove storage Neo4j"
$spade_executable_path control <<< "add storage Neo4j"
$spade_executable_path control <<< "set storage Neo4j"
$spade_executable_path control <<< "add analyzer CommandLine"

tail -f  /dev/null