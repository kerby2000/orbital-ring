# Generated evidence policy

## Tracked evidence

The repository tracks source scenarios, sweep definitions, and small canonical
human-readable OR-1.1 and OR-2 evidence:

- `evidence/or-1.1/OR-1.1-EVIDENCE.md`;
- the six CSV tables beside that report;
- its machine-readable manifest.
- `evidence/or-2/OR-2-EVIDENCE.md`;
- the eleven OR-2 CSV study/source tables beside that report;
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

## Canonical regeneration sequence

Canonical tracked evidence is produced only after the source commit is clean:

```bash
git checkout <source-commit>
python -m pytest
orbital-ring evidence scenarios/reference.yaml --output evidence/or-1.1
orbital-ring or2-evidence scenarios/reference.yaml --output evidence/or-2
```

The generated manifest must report that source commit and
`source_worktree_dirty: false`. The evidence files are then committed in a
separate evidence-only commit. Reproduction therefore checks out the manifest's
`source_commit`, not the later commit that stores the generated files.
