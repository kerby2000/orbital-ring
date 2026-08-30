# Generated evidence policy

## Tracked evidence

The repository tracks source scenarios, sweep definitions, and small canonical
human-readable OR-1.1 evidence:

- `evidence/or-1.1/OR-1.1-EVIDENCE.md`;
- the four CSV tables beside that report;
- its machine-readable manifest.

The existing `artifacts/` directory from OR-1 is retained so reviewed baseline
evidence is not silently deleted. Those files predate the OR-1.1 provenance
schema and are explicitly legacy evidence, not the preferred pattern for new
bulk outputs.

## CI and regenerated products

Bulk JSON, Parquet, plots, and repeated sweep outputs should normally be written
under `ci-evidence/` or `artifacts/generated/`. Both paths are ignored by Git.
GitHub Actions archives `ci-evidence/` as workflow artifacts for each tested
Python version. Source scenarios and sweep definitions remain tracked.

## Commit provenance limitation

A committed artifact cannot reliably contain the SHA of the commit that
contains it. Embedding that SHA changes the file, which changes the commit SHA.
Therefore manifests separate:

- `source_commit`: the checked-out source commit used for generation;
- `source_worktree_dirty`: whether uncommitted changes were present;
- `artifact_commit`: null in file-contained manifests.

CI artifacts are not committed back to the repository. Their `source_commit`
therefore identifies the exact checked-out commit without a self-reference
problem. GitHub Actions also associates the archived artifact with its workflow
run and commit.
