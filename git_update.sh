#!/bin/bash

git status
git add .
git commit -m "更新"
git pull --rebase origin main
git push
