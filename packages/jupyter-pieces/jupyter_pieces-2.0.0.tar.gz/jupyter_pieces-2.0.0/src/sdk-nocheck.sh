#!/bin/bash

add_ts_nocheck() {
    for i in "$1"/*; do
        if [ -d "$i" ]; then
            add_ts_nocheck "$i"
        elif [ -f "$i" ]; then
            local ext="${i##*.}"
            if [[ $ext == "ts" ]]; then
                echo "Processing $i"
                sed -i '' '1s/^/\/\/@ts-nocheck\n/' "$i"
            fi
        fi
    done
}

dir="PiecesSDK"

if [ -d "$dir" ]; then
    add_ts_nocheck "$dir"
else
    echo "Directory $dir does not exist."
fi
