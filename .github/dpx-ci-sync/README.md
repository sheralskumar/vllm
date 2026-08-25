# Nightly DPX CI sync

Automated nightly branch that rebases DPX CI changes onto the latest
`vllm-project/vllm` `main` and pushes `fix/rocm-dpx-ci-nightly`.

## Where files live

| Location | Branch | Contents |
|----------|--------|----------|
| Workflow + patches | **`main`** (fork default) | `.github/workflows/nightly-dpx-ci-sync.yml`, script, patches |
| DPX CI edits | **`fix/rocm-dpx-ci`** | `.buildkite/test-amd.yaml`, runner/test helper changes |

The workflow runs from **`main`** only (required for scheduled GHA cron). It
reads `test-amd.yaml` from `fix/rocm-dpx-ci` and applies patches stored on
`main`.

## Branches

| Branch | Purpose |
|--------|---------|
| `fix/rocm-dpx-ci` | Source branch you edit manually |
| `fix/rocm-dpx-ci-nightly` | Nightly output for CI validation |

## How it works

The workflow [`.github/workflows/nightly-dpx-ci-sync.yml`](../workflows/nightly-dpx-ci-sync.yml)
runs daily (08:00 UTC) and on manual dispatch from **`main`**.

The script [`.github/workflows/scripts/nightly-dpx-ci-sync.sh`](../workflows/scripts/nightly-dpx-ci-sync.sh):

1. Resets `fix/rocm-dpx-ci-nightly` to `vllm-project/main`.
2. Copies `.buildkite/test-amd.yaml` from `fix/rocm-dpx-ci`.
3. Applies patches in `patches/` for:
   - `.buildkite/scripts/hardware_ci/run-amd-test.sh`
   - `tests/utils.py`
   - `tests/conftest.py`
4. Force-pushes the sync branch with `--force-with-lease`.

If a patch fails to apply, the workflow fails and opens/updates a GitHub issue
labeled `nightly-dpx-ci-sync`.

## Refreshing patches

After editing the scripted files on `fix/rocm-dpx-ci`, regenerate patches on
**`main`** and commit there:

```bash
git checkout main
git fetch vllm-project main
git fetch origin fix/rocm-dpx-ci

git diff vllm-project/main origin/fix/rocm-dpx-ci -- \
  .buildkite/scripts/hardware_ci/run-amd-test.sh \
  > .github/dpx-ci-sync/patches/run-amd-test.sh.patch

git diff vllm-project/main origin/fix/rocm-dpx-ci -- \
  tests/utils.py \
  > .github/dpx-ci-sync/patches/tests-utils.py.patch

git diff vllm-project/main origin/fix/rocm-dpx-ci -- \
  tests/conftest.py \
  > .github/dpx-ci-sync/patches/tests-conftest.py.patch
```

Verify locally before pushing:

```bash
git checkout main
UPSTREAM_REMOTE=vllm-project bash .github/workflows/scripts/nightly-dpx-ci-sync.sh
```

## Fork setup

The workflow only runs when `github.repository == 'sheralskumar/vllm'`.
Update that guard in the workflow file if your fork path differs.

Ensure GitHub Actions is enabled on the fork and that the default
`GITHUB_TOKEN` can push branches (`Settings → Actions → General → Workflow
permissions → Read and write`).

Disable the upstream vLLM workflows you do not need under **Actions** in the
GitHub UI. Only this workflow is required for nightly DPX CI sync.
