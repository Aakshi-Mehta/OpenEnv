# A11y Engineer Environment

## Problem
96% of websites fail accessibility guidelines. This environment simulates fixing accessibility issues.

## Tasks
- Easy: Missing aria-label
- Medium: Keyboard trap
- Hard: Dynamic updates not announced

## Actions
- SCREEN_READER
- MODIFY
- TAB
- CLICK

## Reward
- Easy: 0.5 detect + 0.5 fix
- Medium: 0.3 detect + 0.7 fix
- Hard: 0.8 setup + 0.2 verify

## Run
```bash
uvicorn server.app:app --reload
python baseline.py