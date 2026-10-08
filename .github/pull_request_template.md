## What changes

<!-- Translation lines (which scene), a tool fix, documentation... -->

## Checklist

- [ ] Only files I meant to change; no ISO, no `text/`, no extracted game files, no untouched texture exported from the game (edited images belong in `texture_overrides/`)
- [ ] For translation edits: header lines untouched, every `{...}` code kept, names as in `docs/glossary.md`
- [ ] `python3 tools/qa/check_translation.py text --files <SCENE>` shows no FAIL (or I have no ISO and the maintainers should run it)
