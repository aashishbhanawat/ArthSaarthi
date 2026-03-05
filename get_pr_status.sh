#!/bin/bash
for pr in $(gh pr list --limit 40 --json number --jq '.[].number'); do
  echo "Fetching PR #$pr"
  gh pr view $pr --json number,title,mergeable,reviews,comments,statusCheckRollup,url | jq '{number: .number, title: .title, mergeable: .mergeable, checks: .statusCheckRollup}'
done
