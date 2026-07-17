#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
upstream_root="${1:-${project_root}/../quran-roots}"

if [[ ! -d "${upstream_root}/_corpus" ]]; then
  echo "Quran-roots corpus not found: ${upstream_root}" >&2
  exit 1
fi

mkdir -p \
  "${project_root}/data/upstream/furuq" \
  "${project_root}/data/upstream/qac" \
  "${project_root}/data/upstream/qnet/incidence_full" \
  "${project_root}/data/upstream/qnet/bridge_theme_full" \
  "${project_root}/data/upstream/attachments/final_v3" \
  "${project_root}/data/working" \
  "${project_root}/docs/upstream"

copy_one() {
  local source_rel="$1"
  local target_rel="$2"
  local source_path="${upstream_root}/${source_rel}"
  local target_path="${project_root}/${target_rel}"

  if [[ ! -f "${source_path}" ]]; then
    echo "Missing required upstream file: ${source_path}" >&2
    exit 1
  fi

  cp -p "${source_path}" "${target_path}"
}

copy_one "_corpus/furuq/v2/furuq_v4.sqlite.gz" \
  "data/upstream/furuq/furuq_v4.sqlite.gz"
copy_one "_corpus/furuq/v2/README.md" \
  "data/upstream/furuq/README.md"
copy_one "_corpus/furuq/v2/CURRENT_STATUS.md" \
  "docs/upstream/furuq-v2-current-status.md"

copy_one "_corpus/qac/qac.sqlite.gz" \
  "data/upstream/qac/qac.sqlite.gz"
copy_one "_corpus/qac/MANIFEST.sha256" \
  "data/upstream/qac/MANIFEST.upstream.sha256"
copy_one "_corpus/qac/README.md" \
  "data/upstream/qac/README.md"
copy_one "_corpus/qac/SCHEMA.md" \
  "data/upstream/qac/SCHEMA.md"

copy_one "_corpus/activation/Qnet/v2/network/incidence_full/raw_keyword_incidence.sqlite" \
  "data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite"
copy_one "_corpus/activation/Qnet/v2/network/incidence_full/manifest.json" \
  "data/upstream/qnet/incidence_full/manifest.json"
copy_one "_corpus/activation/Qnet/v2/network/incidence_full/README.md" \
  "data/upstream/qnet/incidence_full/README.md"

copy_one "_corpus/activation/Qnet/v2/network/bridge_theme_full/bridge_theme_staging.sqlite" \
  "data/upstream/qnet/bridge_theme_full/bridge_theme_staging.sqlite"
copy_one "_corpus/activation/Qnet/v2/network/bridge_theme_full/manifest.json" \
  "data/upstream/qnet/bridge_theme_full/manifest.json"
copy_one "_corpus/activation/Qnet/v2/network/bridge_theme_full/README.md" \
  "data/upstream/qnet/bridge_theme_full/README.md"

attachment_source="${upstream_root}/_corpus/attachment-enrichment/output/final_v3"
while IFS= read -r -d '' source_path; do
  cp -p "${source_path}" "${project_root}/data/upstream/attachments/final_v3/"
done < <(find "${attachment_source}" -maxdepth 1 -type f -print0)

copy_one "_corpus/attachment-enrichment/README.md" \
  "docs/upstream/attachment-enrichment.md"
copy_one "METHODOLOGY.md" \
  "docs/upstream/meaning-methodology.md"
copy_one "_corpus/ARCHITECTURE.md" \
  "docs/upstream/corpus-architecture.md"
copy_one "_corpus/docs/03-loanword-policy.md" \
  "docs/upstream/loanword-policy.md"
copy_one "_corpus/docs/05-gloss-menu-policy.md" \
  "docs/upstream/gloss-menu-policy.md"
copy_one "_corpus/docs/08-language-agent-contract.md" \
  "docs/upstream/language-agent-contract.md"
copy_one "_translations/_methodologies/concept-envelope-gloss.md" \
  "docs/upstream/concept-envelope-gloss.md"
copy_one "_translations/tr/tr-spec.md" \
  "docs/upstream/turkish-translation-spec.md"
copy_one "_translations/tr/tr-transliteration-guide.md" \
  "docs/upstream/turkish-transliteration-guide.md"

gzip -t "${project_root}/data/upstream/furuq/furuq_v4.sqlite.gz"
gzip -t "${project_root}/data/upstream/qac/qac.sqlite.gz"

furuq_tmp="${project_root}/data/working/furuq_v4.sqlite.tmp.$$"
qac_tmp="${project_root}/data/working/qac.sqlite.tmp.$$"
trap 'rm -f "${furuq_tmp}" "${qac_tmp}"' EXIT

gzip -dc "${project_root}/data/upstream/furuq/furuq_v4.sqlite.gz" > "${furuq_tmp}"
gzip -dc "${project_root}/data/upstream/qac/qac.sqlite.gz" > "${qac_tmp}"
mv "${furuq_tmp}" "${project_root}/data/working/furuq_v4.sqlite"
mv "${qac_tmp}" "${project_root}/data/working/qac.sqlite"
trap - EXIT

for database in \
  "${project_root}/data/working/furuq_v4.sqlite" \
  "${project_root}/data/working/qac.sqlite" \
  "${project_root}/data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite" \
  "${project_root}/data/upstream/qnet/bridge_theme_full/bridge_theme_staging.sqlite"
do
  result="$(sqlite3 "${database}" 'PRAGMA quick_check;')"
  if [[ "${result}" != "ok" ]]; then
    echo "SQLite quick_check failed for ${database}: ${result}" >&2
    exit 1
  fi
done

(
  cd "${project_root}"
  find data/upstream -type f \
    \( -name '*.sqlite' -o -name '*.sqlite.gz' -o -name '*.tsv' -o -name '*.json' \) \
    -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 shasum -a 256
) > "${project_root}/data/upstream/MANIFEST.sha256"

echo "Upstream resources synchronized and verified."
du -sh "${project_root}/data/upstream" "${project_root}/data/working"
