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
runs daily (05:55 UTC) and on manual dispatch from **`main`**.

The script [`.github/workflows/scripts/nightly-dpx-ci-sync.sh`](../workflows/scripts/nightly-dpx-ci-sync.sh):

1. Resets `fix/rocm-dpx-ci-nightly` to `vllm-project/main`.
2. Copies `.buildkite/test-amd.yaml` from `fix/rocm-dpx-ci`.
3. Applies patches in `patches/` for:
   - `.buildkite/scripts/hardware_ci/run-amd-test.sh`
   - `tests/utils.py`
   - `tests/conftest.py`
4. Force-pushes the sync branch with `--force-with-lease`.

If a patch fails to apply, the workflow fails. Check the Actions run email
or the workflow log on GitHub for details.

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

### Repository secret (required)

The nightly branch is based on full upstream `main`, which includes
`.github/workflows/*`. The default `GITHUB_TOKEN` **cannot** push commits that
modify workflow files. Create a PAT and add it as repo secret **`DPX_CI_SYNC_TOKEN`**:

**Fine-grained PAT (recommended):** scoped to `sheralskumar/vllm` only
- Contents: Read and write
- Workflows: Read and write

**Classic PAT:** scopes `repo` + `workflow`

The workflow passes this token to `actions/checkout` so clone and push both use
it.

### Actions settings

Ensure GitHub Actions is enabled on the fork (`Settings → Actions → General`).

Disable the upstream vLLM workflows you do not need under **Actions** in the
GitHub UI. Only this workflow is required for nightly DPX CI sync.

### One-time tag bootstrap

If Buildkite fails with `No numeric version tag is reachable from the CI
revision`, push upstream tags to the fork once:

```bash
git fetch vllm-project --tags
git push origin --tags
```
