# Aggregator app

Minimal RSS/Atom aggregator for Django.

## Usage

1. Add a feed source via Django admin (`Source` model).
2. Run migrations and fetch items:

```bash
python backend/manage.py migrate
python backend/manage.py pull_feeds --dry-run
```

The management command supports `--source=<id-or-url>`, `--limit=N` and
`--dry-run` options.

