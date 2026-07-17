# Turkish Transliteration Guide

**Version:** 1.0
**Date:** 2026-06-06

This is the canonical transliteration mapping for Arabic → Turkish Latin script, used by the concept-gloss pipeline and displayed in the app as a user-facing legend.

## Consonants

| Arabic | Name | Turkish | Example |
|---|---|---|---|
| ب | bâ | b | bismi → **b**ismi |
| ت | tâ | t | taqvâ → **t**aḳvâ |
| ث | se | se | sesebe → **se**bât |
| ج | cîm | c | cehennem → **c**ehennem |
| ح | ḥâ | ḥ | ḥamd → **ḥ**amd |
| خ | ḫâ | ḫ | ḫâliq → **ḫ**âliḳ |
| د | dâl | d | dîn → **d**în |
| ذ | ẕâl | ẕ | ẕâlike → **ẕ**âlike |
| ر | râ | r | rabb → **r**abb |
| ز | ze | z | zekvât → **z**ekât |
| س | sîn | s | sirât → **s**irâṭ |
| ش | şîn | ş | şems → **ş**ems |
| ص | ṣâd | ṣ | ṣirâṭ → **ṣ**irâṭ |
| ض | ḍâd | ḍ | ḍâllîn → **ḍ**âllîn |
| ط | ṭâ | ṭ | ṭayyib → **ṭ**ayyib |
| ظ | ẓâ | ẓ | ẓâlim → **ẓ**âlim |
| ع | ayn | ʿ | ʿabede → **ʿ**abede |
| غ | ğayn | ğ | ğafûr → **ğ**afûr |
| ف | fâ | f | fâtiḥa → **f**âtiḥa |
| ق | ḳâf | ḳ | ḳur'ân → **ḳ**ur'ân |
| ك | kâf | k | kitâb → **k**itâb |
| ل | lâm | l | lillâhi → **l**illâhi |
| م | mîm | m | mâlik → **m**âlik |
| ن | nûn | n | naʿbüdü → **n**aʿbüdü |
| ه | hâ | h | hüde → **h**üde |
| و | vâv | v | vaʿd → **v**aʿd |
| ي | yâ | y | yevm → **y**evm |

## Hamza and Ta Marbuta

| Arabic | Name | Turkish | Rule |
|---|---|---|---|
| ء | hemze | ʾ | Written as ʾ between vowels or at word boundary |
| ة | tâ-i merbûṭa | -t (in iḍâfa), silent otherwise | raḥme**t**-i ilâhiyye (in construct); raḥme (standalone) |

## Vowels

| Type | Arabic | Turkish | Example |
|---|---|---|---|
| Short a | فَتْحَة | e / a | **ke**tebe, **na**ʿbüdü |
| Short i | كَسْرَة | i / ı | **bi**smi, **ḥı**kme |
| Short u | ضَمَّة | ü / u | **kü**tüb, **ḥu**kûm |
| Long â | ا / ى | â | kitâ**b**, ṣirâ**ṭ** |
| Long î | ي | î | raḥî**m**, dî**n** |
| Long û | و | û | ğafû**r**, rûḥ |

## Definite Article (ال)

| Context | Rule | Example |
|---|---|---|
| Before moon letters | el- | **el**-ḥamdü, **el**-kitâb |
| Before sun letters | assimilates | **eş**-şems, **er**-raḥmân, **eṣ**-ṣirâṭ, **eḍ**-ḍâllîn |

Sun letters: ت ث د ذ ر ز س ش ص ض ط ظ ل ن

## Distinguishing Similar Sounds

The key purpose of this system is to distinguish Arabic consonants that flat transliteration merges:

| Pair | Distinction | Visual cue |
|---|---|---|
| ḥ (ح) vs h (ه) | emphatic deep-throat h vs plain h | dot below |
| ṣ (ص) vs s (س) vs ş (ش) | emphatic s vs plain s vs sh | dot below / plain / cedilla |
| ṭ (ط) vs t (ت) | emphatic t vs plain t | dot below |
| ḍ (ض) vs d (د) | emphatic d vs plain d | dot below |
| ẓ (ظ) vs z (ز) vs ẕ (ذ) | emphatic z vs plain z vs soft th-z | dot below / plain / dot below |
| ḳ (ق) vs k (ك) | deep k vs plain k | dot below |
| ʿ (ع) vs ʾ (ء) | ayn vs hamza | hook vs apostrophe |
| ğ (غ) vs g | ghayn vs plain g | breve above |

## Notes

- This system is based on English academic transliteration adapted for Turkish orthographic conventions.
- Turkish native letters are used where they match Arabic sounds: **ş** (shin), **c** (jim), **ğ** (ghayn).
- Circumflex (â, î, û) marks long vowels — the Turkish convention, not macrons (ā, ī, ū).
- Short vowels follow Turkish vowel harmony where applicable in pronunciation.
- This guide serves both the concept-gloss pipeline (agent-produced transliterations) and the app (user-facing legend).
