#!/usr/bin/env bash
git diff --name-only master --output=diff_file.log
cat diff_file.log