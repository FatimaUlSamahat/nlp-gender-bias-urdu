# How we work in git (read once, 2 minutes)

1. Never commit directly to `main`. Everyone works on their own branch: `eshal/...`, `laiba/...`, `abeeha/...`, `fatima/...`.
2. Start each work session: `git checkout main && git pull`, then `git checkout <your-branch> && git merge main`.
3. Commit small and often with clear messages ("add 14 Urdu templates v1").
4. Push your branch: `git push -u origin <your-branch>`. Open a Pull Request into `main` on GitHub.
5. Someone else reviews and merges (one approval). Then everybody pulls main again.
6. Each person owns a folder or files (see PLAN.md). Don't edit someone else's files; ask them or open a PR to them.
7. Do not commit: models, checkpoints, big datasets, passwords or tokens. Share big files via a shared Drive folder.
8. Notebooks: one per person in `notebooks/<name>_*.ipynb`; clear outputs before committing. Real code goes into `src/`.
9. Results go in `results/` as small JSON/CSV files named `<experiment>_<model>_<lang>.json`, so others can plot them.
10. If git says "conflict": stop, don't force-push, message the group.
