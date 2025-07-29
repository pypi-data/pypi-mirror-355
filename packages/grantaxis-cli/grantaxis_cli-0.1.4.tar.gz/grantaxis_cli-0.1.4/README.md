
# ✨ GrantAxis — “git init” for Snowflake RBAC
GrantAxis is a minimal, purpose-built CLI that snapshots the real grants in your Snowflake account and flags anything that drifts from that baseline.

What it does today (MVP)

✅ Captures a deterministic baseline.yml of every meaningful grant (system noise auto-filtered)

✅ Runs an instant diff (locally or in CI) to surface added, removed, changed, or transferred privileges

✅ Fails your pipeline with exit-code 2 when drift is detected

✅ Outputs a clean Markdown report (drift.md) you can read in any code review

Perfect for teams who…

use Terraform/Permifrost but still get “just-this-once” manual GRANTs

haven’t automated RBAC yet and want quick guard-rails without a full platform migration

need a tiny tool they can run anywhere (local, CI, Docker) with zero backend

---

## 🚀 Quick Start — Git-Style Drift Detection for Snowflake RBAC

```bash
pip install grantaxis-cli            #  ⏱ <10 s
export SNOWFLAKE_USER=… SNOWFLAKE_ACCOUNT=… SNOWFLAKE_PASSWORD=…
grantaxis init -o baseline.yml       #  snapshot prod
grantaxis diff -b baseline.yml       #  detect drift any time
```

### 1. Install the CLI

```bash
# one-liner install from PyPI
pip install grantaxis-cli
```

(No root? use `pipx install grantaxis-cli` or a venv.)

---

### 2. Set minimal Snowflake credentials


```bash
export SNOWFLAKE_USER=myservice
export SNOWFLAKE_ACCOUNT=acme-prod
export SNOWFLAKE_PASSWORD=********
export SNOWFLAKE_WAREHOUSE=MONITORING_WH   # optional
```

(OAuth or key-pair auth? set `SNOWFLAKE_AUTHENTICATOR` / `SNOWFLAKE_PRIVATE_KEY_PATH` instead.)
(If you omit env-vars, GrantAxis will prompt for user / password interactively)

---

### 3. git init your RBAC baseline

```bash
# inside your repo
grantaxis init -o baseline.yml
git add baseline.yml
git commit -m "snapshot: initial Snowflake RBAC baseline"
```

`baseline.yml` is a deterministic, human-readable record of every grant that matters (system noise automatically excluded).

---

### 4. (Optional) Detect drift in CI

Add `.github/workflows/grantaxis.yml`:

```yaml
name: Snowflake RBAC drift

on: [push, pull_request]

jobs:
  diff:
    runs-on: ubuntu-latest
    env:
      SNOWFLAKE_USER:      ${{ secrets.SNOWFLAKE_USER }}
      SNOWFLAKE_ACCOUNT:   ${{ secrets.SNOWFLAKE_ACCOUNT }}
      SNOWFLAKE_PASSWORD:  ${{ secrets.SNOWFLAKE_PASSWORD }}
      SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}

    steps:
      - uses: actions/checkout@v4

      - name: Install GrantAxis
        run: pip install grantaxis-cli

      - name: Capture live snapshot
        run: grantaxis init -o live.yml --quiet

      - name: Diff vs. baseline
        run: |
          grantaxis diff -b baseline.yml -s live.yml --report drift.md
          cat drift.md
```

🚨 If any new, removed, or modified grants are found, the job fails (exit 2).
Review `drift.md`, commit intentional changes, or revoke rogue privileges.

---

### 5. What a drift report looks like

```markdown
# Grant Drift Report

Summary: 3 changes detected (➕1 ➖1 🔄1)

| Type | Grantee               | Object                 | Priv | GrantOpt |
|------|-----------------------|------------------------|------|----------|
| ➕ Added   | dev_order_protected | SALES_DB.STAGING (SCHEMA) | USAGE | ❌ |
| ➖ Removed | dev_order_protected | ROLE data_engineer        | USAGE | ❌ |
| 🔄 Transfer| dev_order_protected | ROLE data_analyst         | USAGE | ❌ |
```

Push the fix or merge the PR to keep prod and Git in perfect sync.

---

**That's it.**

From now on any "just-this-once" manual GRANT shows up in the diff before it becomes tomorrow's incident. Enjoy the peace of mind.

---

## 🔒 Security
✅ No data leaves your environment
✅ CLI runs locally, no backend

