---
description: Session-Start für writing-hub — Kontext laden
---

# Session Start — writing-hub

## Step 1: Kontext laden
1. Lies `AGENT_HANDOVER.md` (falls vorhanden)
2. Lies Settings + URLs

## Step 2: Prod-Status
// turbo
3. ```
MCP: mcp6_docker_manage → container_status(container_id="writing_hub_web", host="88.198.191.108")
```

## Step 3: Git-Status
// turbo
4. ```bash
git status && git log --oneline -5
```
