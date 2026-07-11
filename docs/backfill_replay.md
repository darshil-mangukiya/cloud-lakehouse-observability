# Backfill and Replay

The platform writes `operations/replay/backfill_manifest.json` after each run. The manifest lists bronze files that can be replayed by source, ingest date, batch ID, and file path.

Replay design:

1. Select a bronze partition from the manifest.
2. Reprocess it through the silver standardizer.
3. Rerun quality checks for affected silver datasets.
4. Rebuild dependent gold marts.
5. Recompute readiness, SLOs, alerts, and incident summary.

CLI:

```bash
python3 -B scripts/platform_cli.py backfill
```

This is the practical recovery story: bronze is immutable, and downstream datasets can be rebuilt from known batch evidence.
