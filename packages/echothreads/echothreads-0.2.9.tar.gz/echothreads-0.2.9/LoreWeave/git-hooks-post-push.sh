#!/bin/bash

# Post-push hook script to run LoreWeave parser after each push

# Ensure the script is executable
chmod +x .git/hooks/post-push

# Run the LoreWeave parser
python3 LoreWeave/parser.py --post-push

# Check if the parser ran successfully
if [ $? -eq 0 ]; then
  echo "LoreWeave parser ran successfully."
else
  echo "LoreWeave parser encountered an error."
  exit 1
fi
