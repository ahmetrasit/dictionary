# Language Rollout Decision

Decision date: 2026-07-25

## Decision

Prioritize Western bridge languages and languages used across Muslim-majority
countries or large Muslim-reading communities before attempting a generic
speaker-count top 50, every European language, or every Turkic language.

The approved first-release set contains **33** translation locales. An earlier
discussion called it 32; the exact enumerated list contained 33, and no listed
locale has been removed:

```text
en de fr es pt-BR it nl pl uk ru sv nb
tr id ur fa-IR prs bn ms ps az-Latn uz-Latn kk ky tk tg-Cyrl
ckb pnb-Arab so sq bs ha sw
```

Locale order is rollout priority, not a claim about speaker population.

Modern Standard Arabic is not part of this translation set. Arabic is the
semantic evidence language for this workflow. A future Arabic explanatory-gloss
track must have its own contract because it paraphrases Arabic evidence rather
than translating it.

## Why

- English, French, German, Spanish, Russian, and other bridge languages cover
  both Western readers and substantial diaspora use.
- Turkish, Indonesian, Urdu, Persian, Bengali, Malay, Pashto, Central Asian
  languages, Kurdish, Punjabi, Somali, Albanian, Bosnian, Hausa, and Swahili
  cover high-priority Muslim-reading audiences without immediately multiplying
  the workflow across every standardized language.
- Thirty-three locales require 34% fewer language runs than 50 locales while
  the semantic package, review standard, and deterministic gates remain the
  same.
- The set deliberately exercises Latin, Cyrillic, Bengali, and Arabic-derived
  writing systems early.

## Prompt architecture

There are not 33 duplicated workflow agents. Every language worker receives:

1. the shared writer or reviewer prompt;
2. one hash-bound locale configuration;
3. one substantive language-specific instruction pack;
4. the root-specific semantic package and response schema.

This composition keeps the semantic and error-profile contract identical while
allowing grammar, idiom, script, loanword, proper-name, and reviewer guidance to
be locale-specific. A change to one locale invalidates only tasks for that
locale.

## Script policy

Do not provide a general `--ignore-arabic` validator switch. Such an override
could silently disable the Arabic-source leakage safeguard for an unrelated
Latin- or Cyrillic-script task and would not be represented in the task hash.

Each locale pack declares its normal target scripts using ISO 15924 codes.
Staging copies and hash-binds that pack. The validator:

- rejects Arabic-script target prose when the locale does not declare `Arab`;
- permits Arabic-derived target prose for locales such as Urdu, Persian, Dari,
  Pashto, Sorani, and Shahmukhi Punjabi;
- continues to require an independent locale review to detect copied Arabic
  evidence, unnatural cognates, or source-language leakage that Unicode script
  detection cannot distinguish.

Script permission is therefore an input to validation, not an operator bypass.

Task manifests and controller-owned seals make script policy changes stale.
These local seals assume the linguistic worker obeys its output-only role. An
adversarial worker must be isolated by the runtime; an unkeyed file beside a
task cannot provide security against a process with unrestricted access to the
same filesystem.

## Locale assumptions

- `kk` currently means standard Kazakh in Cyrillic; a future Latin release must
  use a distinct `kk-Latn` pack.
- `ms`, `ps`, and `bn` use broadly intelligible written standards because the
  approved tags do not specify a region.
- `prs` remains distinct from `fa-IR`.
- `pnb-Arab` explicitly means Western Punjabi in Shahmukhi, not Gurmukhi
  Punjabi or Urdu.
- `ckb` uses a consistent contemporary Sorani convention while acknowledging
  that orthography is not completely unified.
- `nb` is Bokmål and must not silently mix in Nynorsk forms.

## Release gates

A locale is supported only when all of the following exist and validate:

- a locale JSON pack with code, name, scripts, and short instruction;
- a language-specific instruction prompt;
- successful staging and structural validation;
- a writer output passing the generic and locale-aware checks;
- an independent locale-review pass bound to that exact output;
- a deterministically stored reviewed result.

English, German, and Turkish remain the first smoke-test locales. New locales
should first run on a representative 20-root pilot. Lower-resource output is
not accepted merely because it is schema-valid; native or expert sampling is a
release gate outside this automated workflow.
