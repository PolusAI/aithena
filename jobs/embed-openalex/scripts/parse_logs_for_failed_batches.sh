#!/bin/bash
# Parse embed logs for failed batches

# Default file names
default_input_file="embed.out"
default_output_file="failed_embed.txt"

# Input and output file names from command-line arguments or default values
input_file="${1:-$default_input_file}"
output_file="${2:-$default_output_file}"

# Grep lines containing "ERROR" and extract numbers in brackets, then dump to output file
grep "ERROR" "$input_file" | awk -F'[][]' '{print $2}' > "$output_file"

echo "Failed embed batches saved to $output_file"