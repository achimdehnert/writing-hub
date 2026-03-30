# 2026-03-30: writing-hub Staging Deploy — Docker live-restore Port-Lock + Django Migration-Konflikt

## Kontext

Beim Deployment der writing-hub Frontend-Optimierungen auf Staging (`staging.writing.iil.pet`) traten zwei kritische Probleme auf, die den CI/CD-Deploy-Job wiederholt zum Scheitern brachten.

---

## Problem 1: Docker Port-Lock durch `live-restore: true`

### Symptom
CI-Deploy-Job schlägt fehl mit:
```
Error response from daemon: failed to set up container networking:
Bind for 127.0.0.1:8098 failed: port is already allocated
```
Port bleibt blockiert auch nach `docker rm`, `docker compose down` und `systemctl restart docker`.

### Root Cause
`live-restore: true` in `/etc/docker/daemon.json` sorgt dafür, dass `dockerd` Container-State (inkl. Port-Bindings) beim Daemon-Start restauriert. Ein Container im Status `Created` (fehlgeschlagener Start) hält den Port intern reserviert — ohne laufenden Prozess.

### Fix
```bash
# 1. live-restore temporär deaktivieren
python3 -c "import json; d=json.load(open('/etc/docker/daemon.json')); d['live-restore']=False; json.dump(d, open('/etc/docker/daemon.json','w'), indent=2)"

# 2. Docker komplett stoppen und neu starten
systemctl stop docker.socket docker && systemctl start docker && sleep 5

# 3. live-restore wieder aktivieren
python3 -c "import json; d=json.load(open('/etc/docker/daemon.json')); d['live-restore']=True; json.dump(d, open('/etc/docker/daemon.json','w'), indent=2)"

# 4. Stack starten
cd /opt/writing-hub-staging && docker compose -f docker-compose.staging.yml up -d
```

### Merksatz
> `live-restore: true` + fehlgeschlagener Container-Start = Port-Zombie. Nur `live-restore: false` + vollständiger Docker-Stop löst das Problem.

---

## Problem 2: Django `InconsistentMigrationHistory` in Staging-DB

### Symptom
Container crasht beim Start:
```
django.db.migrations.exceptions.InconsistentMigrationHistory:
Migration aifw.0007_nl2sql_app_label is applied before its dependency
aifw.0008_nl2sql_example_feedback on database 'default'.
```
CI Exit Code 137 (nicht OOM — SSH-Heredoc-Timeout weil `docker exec migrate` fehlschlägt).

### Root Cause
Migrations wurden in falscher Reihenfolge applied — `0007` ist in `django_migrations` eingetragen, `0008` nicht, obwohl `0007` von `0008` abhängt.

### Fix (direkt in der Staging-DB)
```sql
DELETE FROM django_migrations WHERE app='aifw' AND name='0007_nl2sql_app_label';
-- Container starten → schlägt auf 0008 fehl (Tabelle existiert bereits) → beide manuell eintragen:
INSERT INTO django_migrations (app, name, applied) VALUES ('aifw', '0007_nl2sql_app_label', NOW());
INSERT INTO django_migrations (app, name, applied) VALUES ('aifw', '0008_nl2sql_example_feedback', NOW());
```
Container restart → `Up (healthy)`.

### Merksatz
> Bei `InconsistentMigrationHistory` nie Migration rückgängig machen wenn Tabellen bereits existieren — fehlende Einträge in `django_migrations` manuell nachtragen.

---

## Problem 3: CI/CD YAML-Fixes

Drei Fixes nötig um CI-Pipeline grün zu bekommen:

1. **Doppelter `Sum`-Import** in `apps/projects/views_html.py` → `# noqa: F811` (Zeile 102)
2. **PostgreSQL `services`-Block** in `.github/workflows/ci-cd.yml` fehlte für `test`-Job → ergänzt mit Port 5434
3. **Doppeltes `env:`-Key** im `Run tests`-Step → entfernt (Commit `fb6ac2c`)

---

## Ergebnis

- `main` + `develop` beide auf `fb6ac2c`, CI grün ✅
- `staging.writing.iil.pet` → `{"status": "ok", "service": "writing-hub"}` ✅

## Gilt für
- writing-hub (primär)
- Alle Plattform-Apps mit `live-restore: true` auf Server `88.198.191.108`
- Alle Django-Apps mit inkrementellen Staging-DB-Updates
