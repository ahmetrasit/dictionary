#!/usr/bin/env python3
"""Build the self-contained water-root report reader at repository root."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "data" / "output" / "water_secondary_resonance"
MANIFEST_PATH = RUN_DIR / "manifest.json"
ROOT_REPORT_DIR = RUN_DIR / "root_reports"
SECONDARY_REPORT_DIR = RUN_DIR / "secondary_reports"
OUTPUT_PATH = REPO_ROOT / "index.html"

FAMILY_NAMES = {
    "water": "mâ' · su maddesi",
    "sea": "bahr · deniz alanı",
    "drink": "şurb · içe alma",
    "water_give": "saky · su sağlama",
    "drown": "ğark · boğulma",
    "hot_water": "hamîm · kaynar su",
    "rain": "matar · hedefe inen yağmur",
    "great_water": "yamm · kuşatıcı su",
    "wave": "mevc · dalga",
    "life_rain": "ğays · rahatlatan yağmur",
    "salty_bitter": "ucâc · tuzlu-acı su",
    "fresh_sweet": "furât · tatlı su",
    "torrent": "seyl · arazi akışı",
    "downpour": "vâbil · ağır yağmur",
    "rain_drop": "vedk · buluttan çıkan yağmur",
    "water_arrival": "vürûd · suya varış",
    "stale_water": "âsin · değişen su",
    "well": "bi'r · kuyu",
    "split_emergence": "inbicâs · kaynaktan çıkış",
    "pouring": "seccâc · bol dökülüş",
}

VERDICT_LINE = re.compile(
    r"^\*\*.*(?:—\s*(?:A|B|C|REJECT)\s*—|reddedildi|"
    r"aday dal yok|ikincil dal yok).*\*\*$",
    re.IGNORECASE,
)


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def render_markdown(pandoc: str, path: Path) -> str:
    source_lines = path.read_text(encoding="utf-8").splitlines()
    separated_lines: list[str] = []
    for line in source_lines:
        if VERDICT_LINE.match(line.strip()) and separated_lines[-1:]:
            if separated_lines[-1].strip():
                separated_lines.append("")
        separated_lines.append(line)

    result = subprocess.run(
        [pandoc, "--from=gfm", "--to=html5"],
        input="\n".join(separated_lines),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise SystemExit("Required command not found: pandoc")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    families = manifest["family_stats"]
    if len(families) != 20:
        raise SystemExit(f"Expected 20 root families, found {len(families)}")

    seen_roots: set[str] = set()
    rows: list[str] = []
    templates: list[str] = []
    documents: list[dict[str, str]] = []

    for family in families:
        family_id = family["family_id"]
        root_id = family["root_packet"]
        label_ar = family["label_ar"]
        if root_id in seen_roots:
            raise SystemExit(f"Duplicate root in manifest: {root_id}")
        seen_roots.add(root_id)

        root_md = ROOT_REPORT_DIR / f"{root_id}.md"
        root_pdf = ROOT_REPORT_DIR / "pdf" / f"{root_id}.pdf"
        secondary_md = SECONDARY_REPORT_DIR / f"{root_id}.md"
        secondary_pdf = SECONDARY_REPORT_DIR / "pdf" / f"{root_id}.pdf"
        for path in (root_md, root_pdf, secondary_md, secondary_pdf):
            if not path.is_file():
                raise SystemExit(f"Missing report asset: {path}")

        family_name = FAMILY_NAMES[family_id]
        search_text = f"{label_ar} {family_name} {root_id} {family_id}"
        root_key = f"{root_id}-root"
        secondary_key = f"{root_id}-secondary"
        root_title = f"{label_ar} · Kök ilişki raporu"
        secondary_title = f"{label_ar} · Ayet bazlı ikincil rezonans"

        rows.append(
            f"""
          <li class="root-item" data-search="{html.escape(search_text.lower())}">
            <div class="root-identity">
              <span class="root-ar" lang="ar" dir="rtl">{html.escape(label_ar)}</span>
              <span class="root-name">{html.escape(family_name)}</span>
              <code>{html.escape(root_id)}</code>
            </div>
            <div class="root-links" aria-label="{html.escape(label_ar)} rapor bağlantıları">
              <a class="md-link" data-document="{root_key}" href="{html.escape(rel(root_md))}">Kök MD</a>
              <a class="pdf-link" href="{html.escape(rel(root_pdf))}" target="_blank" rel="noopener">Kök PDF</a>
              <a class="md-link" data-document="{secondary_key}" href="{html.escape(rel(secondary_md))}">Rezonans MD</a>
              <a class="pdf-link" href="{html.escape(rel(secondary_pdf))}" target="_blank" rel="noopener">Rezonans PDF</a>
            </div>
          </li>""".rstrip()
        )

        for key, title, kind, path in (
            (root_key, root_title, "Kök ilişki raporu", root_md),
            (
                secondary_key,
                secondary_title,
                "Ayet bazlı ikincil rezonans",
                secondary_md,
            ),
        ):
            rendered = render_markdown(pandoc, path)
            templates.append(f'<template id="doc-{key}">\n{rendered}\n</template>')
            documents.append(
                {
                    "key": key,
                    "title": title,
                    "kind": kind,
                    "source": rel(path),
                    "root": root_id,
                }
            )

    document_json = json.dumps(documents, ensure_ascii=False).replace("</", "<\\/")
    page = PAGE_TEMPLATE.replace("{{ROOT_ROWS}}", "\n".join(rows))
    page = page.replace("{{DOCUMENT_TEMPLATES}}", "\n".join(templates))
    page = page.replace("{{DOCUMENT_INDEX}}", document_json)
    checks = {
        "root rows": page.count('class="root-item"'),
        "Markdown links": page.count('class="md-link"'),
        "PDF links": page.count('class="pdf-link"'),
        "embedded documents": page.count('<template id="doc-'),
    }
    expected = {
        "root rows": 20,
        "Markdown links": 40,
        "PDF links": 40,
        "embedded documents": 40,
    }
    if checks != expected:
        raise SystemExit(f"Generated index failed count checks: {checks}")
    if "https://" in page or "http://" in page or "src=\"//" in page:
        raise SystemExit("Generated index unexpectedly depends on a remote resource")
    OUTPUT_PATH.write_text(page, encoding="utf-8")
    print(f"Built {OUTPUT_PATH} with 20 roots and 40 embedded reports")
    return 0


PAGE_TEMPLATE = r'''<!doctype html>
<!-- Generated by scripts/build_water_reports_index.py. -->
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Su Kökleri Okuma Arşivi</title>
  <style>
    :root {
      --paper: #fff1e5;
      --paper-deep: #f2dfce;
      --paper-light: #fff8f2;
      --ink: #262a33;
      --muted: #6b625d;
      --rule: #c9b7a7;
      --teal: #0d7680;
      --claret: #990f3d;
      --orange: #e87d1e;
      --sidebar-width: 360px;
    }

    * { box-sizing: border-box; }

    html { background: var(--paper); }

    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: Arial, "Arial Unicode MS", sans-serif;
      letter-spacing: 0;
    }

    a { color: var(--teal); }

    a:focus-visible,
    input:focus-visible {
      outline: 3px solid var(--orange);
      outline-offset: 2px;
    }

    .shell {
      display: grid;
      grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
      min-height: 100vh;
    }

    .library {
      align-self: start;
      border-right: 1px solid var(--rule);
      background: var(--paper-deep);
      height: 100vh;
      min-width: 0;
      overflow-y: auto;
      position: sticky;
      top: 0;
    }

    .library-header {
      border-top: 8px solid var(--claret);
      border-bottom: 1px solid var(--rule);
      padding: 28px 24px 22px;
    }

    .eyebrow {
      color: var(--claret);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .library h1 {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 27px;
      font-weight: 500;
      line-height: 1.06;
      margin: 8px 0 10px;
    }

    .library-intro {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 0;
    }

    .search-wrap {
      border-bottom: 1px solid var(--rule);
      padding: 14px 24px;
    }

    .search-wrap label {
      display: block;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 6px;
      text-transform: uppercase;
    }

    #root-search {
      border: 1px solid #8d8179;
      border-radius: 0;
      background: var(--paper-light);
      color: var(--ink);
      font: inherit;
      height: 38px;
      padding: 0 10px;
      width: 100%;
    }

    .root-list {
      list-style: none;
      margin: 0;
      padding: 0;
    }

    .root-item {
      border-bottom: 1px solid var(--rule);
      padding: 14px 24px 15px;
    }

    .root-item[hidden] { display: none; }

    .root-identity {
      align-items: baseline;
      display: grid;
      gap: 2px 10px;
      grid-template-columns: 54px minmax(0, 1fr);
      margin-bottom: 9px;
    }

    .root-ar {
      color: var(--claret);
      font-family: "Arial Unicode MS", Arial, sans-serif;
      font-size: 21px;
      font-weight: 700;
      grid-row: 1 / span 2;
      text-align: right;
    }

    .root-name {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 15px;
      font-weight: 700;
      min-width: 0;
    }

    .root-identity code {
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 10px;
    }

    .root-links {
      display: grid;
      gap: 5px 12px;
      grid-template-columns: 1fr 1fr;
    }

    .root-links a {
      border-bottom: 1px solid currentColor;
      color: var(--ink);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.45;
      text-decoration: none;
      width: max-content;
    }

    .root-links a:hover,
    .root-links a.active { color: var(--claret); }

    .root-links .pdf-link { color: var(--teal); }

    .reading-pane { min-width: 0; }

    .document-bar {
      align-items: center;
      background: var(--paper);
      border-top: 8px solid var(--teal);
      border-bottom: 1px solid var(--rule);
      display: flex;
      justify-content: space-between;
      min-height: 74px;
      padding: 14px 36px;
      position: sticky;
      top: 0;
      z-index: 2;
    }

    .document-kind {
      color: var(--claret);
      display: block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .document-title {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 18px;
      font-weight: 500;
      margin-top: 3px;
    }

    .source-path {
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      max-width: 100%;
      overflow-wrap: anywhere;
    }

    .reader {
      margin: 0 auto;
      max-width: 920px;
      padding: 40px 42px 80px;
    }

    .reader h1,
    .reader h2,
    .reader h3 {
      font-family: Georgia, "Times New Roman", serif;
      font-weight: 500;
    }

    .reader h1 {
      border-bottom: 4px solid var(--orange);
      font-size: 29px;
      line-height: 1.08;
      margin: 0 0 26px;
      padding-bottom: 13px;
    }

    .reader h2 {
      border-top: 1px solid var(--rule);
      color: var(--claret);
      font-size: 20px;
      line-height: 1.18;
      margin: 34px 0 12px;
      padding-top: 14px;
    }

    .reader h3 {
      color: var(--teal);
      font-size: 16px;
      margin: 24px 0 9px;
    }

    .reader p,
    .reader li {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 14px;
      line-height: 1.55;
    }

    .reader p { margin: 0 0 12px; }
    .reader li { margin-bottom: 5px; }
    .reader ul, .reader ol { padding-left: 26px; }

    .reader strong { font-weight: 700; }

    .reader code {
      background: var(--paper-deep);
      color: #174f54;
      font-family: "Arial Unicode MS", ui-monospace, monospace;
      font-size: .88em;
      padding: 1px 4px;
    }

    .reader table {
      border-collapse: collapse;
      display: block;
      font-size: 14px;
      margin: 24px 0;
      max-width: 100%;
      overflow-x: auto;
    }

    .reader th,
    .reader td {
      border-bottom: 1px solid var(--rule);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }

    .reader th { background: var(--paper-deep); }

    .verdict-guide {
      border-left: 5px solid var(--teal);
      background: var(--paper-deep);
      margin: 0 0 26px;
      padding: 12px 14px;
    }

    .verdict-guide strong {
      color: var(--claret);
      display: block;
      font-family: Arial, "Arial Unicode MS", sans-serif;
      font-size: 11px;
      margin-bottom: 4px;
      text-transform: uppercase;
    }

    .verdict-guide p {
      font-family: Arial, "Arial Unicode MS", sans-serif;
      font-size: 12px;
      line-height: 1.45;
      margin: 0;
    }

    .verdict-reject {
      background: #990f3d;
      color: #fff;
      display: inline-block;
      font-family: Arial, "Arial Unicode MS", sans-serif;
      font-size: 10px;
      font-weight: 700;
      line-height: 1.3;
      margin: 3px 2px;
      padding: 3px 6px;
      text-transform: uppercase;
    }

    .rejected-candidate {
      border-left: 4px solid var(--claret);
      background: rgba(153, 15, 61, .07);
      padding: 7px 10px;
    }

    p.rejected-candidate { margin-bottom: 0; }

    .rejected-details {
      border-left: 4px solid var(--claret);
      background: rgba(153, 15, 61, .07);
      margin-top: 0;
      padding: 2px 14px 9px 34px;
    }

    .rejection-reason { color: var(--claret); }

    .empty-state {
      color: var(--muted);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 18px;
      padding: 24px;
    }

    @media (max-width: 820px) {
      .shell { display: block; }
      .library {
        border-right: 0;
        height: auto;
        overflow: visible;
        position: static;
      }
      .library-header { padding: 22px 18px 18px; }
      .library h1 { font-size: 25px; }
      .search-wrap { padding: 12px 18px; }
      .root-list {
        max-height: 330px;
        overflow-y: auto;
      }
      .root-item { padding: 12px 18px; }
      .document-bar {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
        padding: 12px 18px;
        position: static;
      }
      .document-title { font-size: 17px; }
      .reader { padding: 34px 18px 64px; }
      .reader h1 { font-size: 26px; }
      .reader h2 { font-size: 19px; }
      .reader p, .reader li { font-size: 14px; }
    }

    @media print {
      .library, .document-bar { display: none; }
      .shell { display: block; }
      .reader { max-width: none; padding: 0; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="library" aria-label="Su kökü raporları">
      <header class="library-header">
        <div class="eyebrow">Kur'an su söz varlığı</div>
        <h1>Su kökleri okuma arşivi</h1>
        <p class="library-intro">20 kök · 40 Markdown raporu · iki ayrı okuma düzeyi</p>
      </header>
      <div class="search-wrap">
        <label for="root-search">Köklerde ara</label>
        <input id="root-search" type="search" placeholder="ماء, bahr, root_..." autocomplete="off">
      </div>
      <nav aria-label="Kök listesi">
        <ul class="root-list" id="root-list">
{{ROOT_ROWS}}
        </ul>
      </nav>
      <p class="empty-state" id="empty-state" hidden>Bu aramayla eşleşen kök yok.</p>
    </aside>

    <main class="reading-pane">
      <header class="document-bar">
        <div>
          <span class="document-kind" id="document-kind"></span>
          <div class="document-title" id="document-title"></div>
        </div>
        <span class="source-path" id="source-path"></span>
      </header>
      <article class="reader" id="reader" aria-labelledby="document-title" tabindex="-1"></article>
    </main>
  </div>

{{DOCUMENT_TEMPLATES}}
  <script>
    const documents = {{DOCUMENT_INDEX}};
    const documentMap = new Map(documents.map((document) => [document.key, document]));
    const reader = document.getElementById('reader');
    const title = document.getElementById('document-title');
    const kind = document.getElementById('document-kind');
    const sourcePath = document.getElementById('source-path');
    const defaultDocument = 'root_001458-secondary';

    function decorateSecondaryVerdicts() {
      const guide = document.createElement('aside');
      guide.className = 'verdict-guide';
      guide.innerHTML = `
        <strong>Karar anahtarı</strong>
        <p><b>A</b> güçlü, <b>B</b> destekli, <b>C</b> zayıf/keşifsel öneridir.
        <b>REJECT</b>, ayetin veya beş ayetlik sürprizin değil, adı verilen
        <b>ikincil kök dalı önerisinin reddedildiği</b> anlamına gelir.</p>`;
      reader.prepend(guide);

      [...reader.querySelectorAll('strong')].forEach((marker) => {
        if (!/REJECT|reddedildi/i.test(marker.textContent)) return;
        const candidate = marker.textContent
          .replace(/\s*—\s*REJECT\s*—\s*reddedildi\s*/i, '')
          .replace(/^REJECT\s*$/i, '')
          .trim();
        marker.textContent = candidate
          ? `REDDEDİLEN DAL ÖNERİSİ · ${candidate}`
          : 'İKİNCİL DAL ÖNERİSİ REDDEDİLDİ';
        marker.classList.add('verdict-reject');
        const candidateItem = marker.closest('li');
        const candidateBlock = candidateItem || marker.closest('p');
        if (candidateBlock) candidateBlock.classList.add('rejected-candidate');

        let details = candidateItem;
        if (!candidateItem && candidateBlock?.nextElementSibling?.tagName === 'UL') {
          details = candidateBlock.nextElementSibling;
          details.classList.add('rejected-details');
        }
        if (!details) return;
        [...details.querySelectorAll('strong')].forEach((label) => {
          if (!/^Neden bu (pencere|derece):?$/i.test(label.textContent.trim())) return;
          label.textContent = 'Reddedilme gerekçesi:';
          label.classList.add('rejection-reason');
        });
      });
    }

    function showDocument(key, updateHash = true, moveFocus = true) {
      const metadata = documentMap.get(key);
      const template = document.getElementById(`doc-${key}`);
      if (!metadata || !template) return false;

      document.querySelectorAll('.md-link.active').forEach((link) => {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      });
      const activeLink = document.querySelector(`.md-link[data-document="${key}"]`);
      if (activeLink) {
        activeLink.classList.add('active');
        activeLink.setAttribute('aria-current', 'page');
      }

      reader.replaceChildren(template.content.cloneNode(true));
      if (key.endsWith('-secondary')) decorateSecondaryVerdicts();
      title.textContent = metadata.title;
      kind.textContent = metadata.kind;
      sourcePath.textContent = metadata.source;
      document.title = `${metadata.title} · Su Kökleri`;
      if (updateHash && window.location.hash !== `#${key}`) {
        history.pushState(null, '', `#${key}`);
      }
      document.querySelector('.reading-pane').scrollIntoView({ block: 'start' });
      if (moveFocus) reader.focus({ preventScroll: true });
      return true;
    }

    document.addEventListener('click', (event) => {
      const link = event.target.closest('.md-link');
      if (!link) return;
      event.preventDefault();
      showDocument(link.dataset.document);
    });

    function restoreHistorySelection() {
      const key = window.location.hash.slice(1);
      showDocument(key || defaultDocument, false);
    }
    window.addEventListener('hashchange', restoreHistorySelection);
    window.addEventListener('popstate', restoreHistorySelection);

    const search = document.getElementById('root-search');
    const items = [...document.querySelectorAll('.root-item')];
    const emptyState = document.getElementById('empty-state');
    search.addEventListener('input', () => {
      const query = search.value.trim().toLocaleLowerCase('tr');
      let visible = 0;
      items.forEach((item) => {
        const match = !query || item.dataset.search.includes(query);
        item.hidden = !match;
        if (match) visible += 1;
      });
      emptyState.hidden = visible !== 0;
    });

    const initialKey = window.location.hash.slice(1);
    if (!showDocument(initialKey, false, false)) {
      showDocument(defaultDocument, false, false);
      history.replaceState(null, '', `#${defaultDocument}`);
    }
  </script>
</body>
</html>
'''


if __name__ == "__main__":
    raise SystemExit(main())
