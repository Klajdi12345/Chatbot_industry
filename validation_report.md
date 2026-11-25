# Raporti i validimit: `data\semundjet.json`

Data: 2026-11-24

## Struktura

- Formati: JSON, UTF-8 (81190 bajt)
- Rrënja: `_pershkrimi`, `_skema_versioni`, `hyrjet`; hyrjet janë te `hyrjet` (listë)
- Rreshta (hyrje): 45
- Fushat e skemës: `id` (str), `emri_shqip` (str), `emri_anglisht` (str), `kodi_icd10` (str), `kategoria` (str), `pjesa_e_trupit_ose_sistemi` (str), `pershkrimi` (str), `shkaqet` (list), `faktoret_e_rrezikut` (list), `simptomat` (list), `shenjat_urgjente` (list), `diagnoza` (list), `trajtimi_konservativ` (list), `trajtimi_kirurgjik` (list), `koha_e_sherimit` (dict), `komplikimet` (list), `parandalimi` (list), `burimi` (str), `data_e_shtimit` (str)
- `koha_e_sherimit`: {"min": javë, "max": javë, "njesia": "javë"}; për sëmundjet kronike {"min": null, "max": null, "njesia": "javë", "shenim": "kronike: ..."}
- `kategoria`: sëmundje / thyerje; `kodi_icd10`: format OBSH (p.sh. S52.5) ose `PER_VERIFIKIM`

## Përmbledhje

- Hyrje: **45**
- Gabime: **0**
- Paralajmërime: **0**
- PER_VERIFIKIM: **0**

## Gabime

Asnjë.

## Paralajmërime

Asnjë.

## Për verifikim

Asnjë.
