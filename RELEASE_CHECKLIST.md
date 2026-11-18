# Release Checklist

## Before GitHub push

- [x] Exclude `.venv` from the Git payload
- [x] Exclude generated temporary files/databases/logs from the Git payload
- [x] Check source/config/sample files for secrets
- [x] Check `.gitignore`
- [x] Run tests (89 passed)
- [x] Run lint/format checks
- [x] Seed database from scratch (full demo and isolated clean-copy demo)
- [x] Generate reports from scratch
- [x] Verify live API and API tests
- [x] Verify dashboard with AppTest and browser
- [x] Review README
- [x] Review screenshots
- [x] Confirm synthetic-data disclaimer
- [x] Confirm no unsupported claims

Docker startup and hosted CI remain unexecuted. Git is initialized on main; no commit, push or external publication has been made. Run the configured CI/Docker checks on a capable host before claiming those environments are verified. Local artifacts are retained for demonstration, while .gitignore keeps generated working files out of a future commit.

## Suggested Git workflow

```bash
git init
git add .
git commit -m "Build financial operations analytics platform"
git branch -M main
git remote add origin <your-repository>
git push -u origin main
```

Do not commit a real `.env` file.
