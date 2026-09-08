#!/usr/bin/env bash
# Nightly sync: rebase DPX CI changes onto upstream vLLM main and push a
# throwaway branch for CI validation.
#
# Strategy:
#   1. Reset the sync branch to upstream/main.
#   2. Take test-amd.yaml from the source branch (manual DPX matrix edits).
#   3. Apply patches stored on the fork automation branch (main).
#
# Patches are read via `git show` so they remain available after the sync
# branch is reset to upstream/main (which does not contain fork-only files).
set -euo pipefail

UPSTREAM_REMOTE="${UPSTREAM_REMOTE:-upstream}"
UPSTREAM_BRANCH="${UPSTREAM_BRANCH:-main}"
SOURCE_BRANCH="${SOURCE_BRANCH:-fix/rocm-dpx-ci}"
SYNC_BRANCH="${SYNC_BRANCH:-fix/rocm-dpx-ci-nightly}"
PATCH_DIR="${PATCH_DIR:-.github/dpx-ci-sync/patches}"
ORIGIN_REMOTE="${ORIGIN_REMOTE:-origin}"
AUTOMATION_REF="${AUTOMATION_REF:-main}"

PATCH_FILES=(
  run-amd-test.sh.patch
  tests-utils.py.patch
  tests-conftest.py.patch
)

log() {
  printf '[nightly-dpx-ci-sync] %s\n' "$*"
}

die() {
  printf '[nightly-dpx-ci-sync] ERROR: %s\n' "$*" >&2
  exit 1
}

resolve_ref() {
  local ref=$1
  if git rev-parse --verify "${ref}" >/dev/null 2>&1; then
    echo "${ref}"
    return 0
  fi
  if git rev-parse --verify "${ORIGIN_REMOTE}/${ref}" >/dev/null 2>&1; then
    echo "${ORIGIN_REMOTE}/${ref}"
    return 0
  fi
  die "Unknown git ref: ${ref}"
}

apply_patch_from_ref() {
  local automation_ref=$1
  local patch_name=$2

  log "Applying ${PATCH_DIR}/${patch_name} from ${automation_ref}"
  if ! git show "${automation_ref}:${PATCH_DIR}/${patch_name}" | git apply --3way; then
    die "Failed to apply ${patch_name}. Refresh patches on ${AUTOMATION_REF}."
  fi
}

main() {
  local automation_ref upstream_ref source_ref
  automation_ref=$(resolve_ref "${AUTOMATION_REF}")

  for patch_name in "${PATCH_FILES[@]}"; do
    git cat-file -e "${automation_ref}:${PATCH_DIR}/${patch_name}" \
      || die "Missing ${PATCH_DIR}/${patch_name} on ${automation_ref}"
  done

  log "Fetching ${ORIGIN_REMOTE}/${SOURCE_BRANCH}"
  git fetch "${ORIGIN_REMOTE}" "${SOURCE_BRANCH}"

  log "Fetching ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
  git fetch "${UPSTREAM_REMOTE}" "${UPSTREAM_BRANCH}"

  upstream_ref="${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"
  source_ref="${ORIGIN_REMOTE}/${SOURCE_BRANCH}"

  git rev-parse --verify "${upstream_ref}" >/dev/null \
    || die "Unknown upstream ref: ${upstream_ref}"
  git rev-parse --verify "${source_ref}" >/dev/null \
    || die "Unknown source ref: ${source_ref}"

  log "Creating ${SYNC_BRANCH} from ${upstream_ref}"
  git checkout -B "${SYNC_BRANCH}" "${upstream_ref}"

  log "Taking .buildkite/test-amd.yaml from ${source_ref}"
  git checkout "${source_ref}" -- .buildkite/test-amd.yaml

  for patch_name in "${PATCH_FILES[@]}"; do
    apply_patch_from_ref "${automation_ref}" "${patch_name}"
  done

  git add \
    .buildkite/test-amd.yaml \
    .buildkite/scripts/hardware_ci/run-amd-test.sh \
    tests/utils.py \
    tests/conftest.py

  if git diff --staged --quiet; then
    log "No changes relative to ${upstream_ref}; sync branch is already current."
    exit 0
  fi

  local upstream_sha source_sha automation_sha
  upstream_sha=$(git rev-parse --short "${upstream_ref}")
  source_sha=$(git rev-parse --short "${source_ref}")
  automation_sha=$(git rev-parse --short "${automation_ref}")

  git commit -m "$(cat <<EOF
Nightly DPX CI sync onto vllm-project/main@${upstream_sha}.

Source branch: ${SOURCE_BRANCH}@${source_sha}
Automation ref: ${AUTOMATION_REF}@${automation_sha}
Synced branch: ${SYNC_BRANCH}
EOF
)"

  log "Sync commit created on ${SYNC_BRANCH}"
}

main "$@"
