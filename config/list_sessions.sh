#!/bin/bash
# List all generation sessions

echo "Blog Generation Sessions"
echo "========================"

for session in generations/*/; do
    if [ -f "$session/metadata.json" ]; then
        echo ""
        echo "📁 $(basename $session)"
        # Use ripgrep to extract key fields
        rg '"topic":|"created_at":|"final_selection":' "$session/metadata.json" | sed 's/^/  /'
    fi
done
