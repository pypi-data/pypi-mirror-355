#!/bin/bash
# Script to create a new Architecture Decision Record

set -e

# Check if title is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Title of the ADR\""
    echo "Example: $0 \"Use Async Throughout the Codebase\""
    exit 1
fi

TITLE="$1"
ADR_DIR="docs/adr"

# Create ADR directory if it doesn't exist
mkdir -p "$ADR_DIR"

# Find the next ADR number
NEXT_NUM=1
for file in "$ADR_DIR"/*.md; do
    if [[ -f "$file" && "$file" =~ ([0-9]+)- ]]; then
        NUM="${BASH_REMATCH[1]}"
        if [[ $NUM =~ ^[0-9]+$ ]] && [ "$NUM" -ge "$NEXT_NUM" ]; then
            NEXT_NUM=$((NUM + 1))
        fi
    fi
done

# Format number with leading zeros
PADDED_NUM=$(printf "%03d" $NEXT_NUM)

# Create filename
FILENAME="$ADR_DIR/${PADDED_NUM}-${TITLE,,}.md"
FILENAME="${FILENAME// /-}"

# Create ADR from template
cat > "$FILENAME" << EOF
# ADR-${PADDED_NUM}: ${TITLE}

## Status
Proposed

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Lessons Learned
What errors did we make previously that led to this decision?

## Code Examples
\`\`\`python
# Before (what didn't work)
# ...

# After (what works better)
# ...
\`\`\`
EOF

echo "Created: $FILENAME"
echo "Next steps:"
echo "  1. Edit the ADR to fill in the details"
echo "  2. Change status to 'Accepted' when approved"
echo "  3. Reference in code comments: 'See ADR-${PADDED_NUM}'"
