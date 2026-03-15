---
description: Deploy writing-hub to production
---

# Deploy writing-hub

## Pre-Flight
// turbo
1. Check prod health:
```
MCP: mcp6_docker_manage → container_status(container_id="writing_hub_web", host="88.198.191.108")
```

## Deploy (Server-Build)
2. Build + deploy on server:
```bash
ssh root@88.198.191.108 "GITHUB_TOKEN=\$GITHUB_TOKEN /opt/server-build-hub.sh writing-hub"
```

## Post-Deploy
// turbo
3. Health check:
```
MCP: mcp6_ssh_manage → http_check(url="http://127.0.0.1:8097/healthz/", host="88.198.191.108")
```

## Key Info
- **Server**: 88.198.191.108
- **Port**: 8097 (internal)
- **Domain**: https://writing.iil.pet
- **Container**: writing_hub_web
