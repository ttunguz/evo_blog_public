#!/bin/bash
# Search through all blog generations using ripgrep

if [ $# -eq 0 ]; then
    echo "Usage: ./search.sh <search_term>"
    exit 1
fi

echo "Searching for: $1"
echo "=================="

# Search in all markdown files
rg "$1" --type md generations/

# Search in metadata
echo -e "\nMetadata matches:"
rg "$1" --type json generations/*/metadata.json
