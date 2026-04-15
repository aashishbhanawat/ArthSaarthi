#!/bin/bash

# This script reads markdown files from the docs/issues directory,
# parses the title and labels from the YAML frontmatter, and creates
# GitHub issues using the gh CLI.

set -e # Exit immediately if a command exits with a non-zero status.

ISSUE_DIR="1"

# Check if gh is installed
if ! command -v gh &> /dev/null
then
    echo "GitHub CLI (gh) could not be found. Please install it first."
    echo "See: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null
then
    echo "You are not logged into GitHub. Please run 'gh auth login' first."
    exit 1
fi

echo "Starting issue creation process..."

for file in "$ISSUE_DIR"/*.md; do
  if [ -f "$file" ]; then
    echo "--------------------------------------------------"
    echo "Processing file: $file"

    # Extract title from YAML frontmatter using grep and sed.
    title=$(grep '^title:' "$file" | sed "s/title: '\(.*\)'/\1/")

    # Extract labels and format them for the gh command.
    labels_str=$(grep '^labels:' "$file" | sed "s/labels: '\(.*\)'/\1/")
    label_flags=""
    if [ -n "$labels_str" ]; then
      # Use tr to replace commas with newlines, then read into an array
      while IFS= read -r label; do
        # Trim leading/trailing whitespace that might exist
        trimmed_label=$(echo "$label" | xargs)
        if [ -n "$trimmed_label" ]; then
          label_flags+=" --label \"$trimmed_label\""
        fi
      done < <(echo "$labels_str" | tr ',' '\n')
    fi

    # Extract the body of the issue (everything after the second '---').
    body=$(sed '1,/---/d' "$file")

    if [ -z "$title" ]; then
      echo "WARNING: Could not extract title from $file. Skipping."
      continue
    fi

    echo "  Title: $title"
    echo "  Labels: $labels_str"

    # Create the issue using the gh CLI.
    # The body is passed via stdin for safety with special characters.
    echo "$body" | gh issue create --title "$title" --body-file - $label_flags

    echo "  Successfully created issue for $file"
    # Sleep for a second to avoid hitting API rate limits.
    sleep 1
  fi
done

echo "--------------------------------------------------"
echo "✅ All issues have been processed and created on GitHub."
