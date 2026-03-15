---
description: Schneller Produktions-Fix für writing-hub
---

# Hotfix — writing-hub

## 1. Logs prüfen
// turbo
```
MCP: mcp6_docker_manage → container_logs(container_id="writing_hub_web", host="88.198.191.108", lines=50)
```

## 2. Fix + Test
```bash
pytest tests/ -x -q --tb=short
```

## 3. Deploy
```bash
git add -A && git commit -m "fix: [BESCHREIBUNG]" && git push origin main
ssh root@88.198.191.108 "GITHUB_TOKEN=\$GITHUB_TOKEN /opt/server-build-hub.sh writing-hub"
```

## 4. Verify
// turbo
```
MCP: mcp6_ssh_manage → http_check(url="http://127.0.0.1:8097/healthz/", host="88.198.191.108")
```
