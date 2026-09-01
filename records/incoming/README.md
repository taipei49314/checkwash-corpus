# Incoming agent diffs

Drop a real tampering (or suspected tampering) diff here. One directory per
case:

```
records/incoming/<slug>/
  META.json     required — see template below
  diff.patch    required — git diff, including added files (see greenwash D-026)
```

`META.json`:

```json
{
  "slug": "example-skip-the-failing-test",
  "submitted": "2026-09-01",
  "engine_version": "0.1.49",
  "source": "who ran the agent, which product, which task — enough to reproduce",
  "production_changed": false,
  "notes": "what you think happened. The engine's opinion goes in a sweep/check record, not here."
}
```

Do not put secrets, credentials, or private source in the patch. If the
diff cannot be made public, keep it local and file only the META plus a
redacted finding JSON.
