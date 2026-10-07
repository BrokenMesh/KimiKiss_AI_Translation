You translate part of the Japanese PS2 visual novel KimiKiss into English. Repo: /home/user/KimiKiss_AI_Translation (run every command from there).

Your scenes, in this order: {SCENES}
Route: {ROUTE}. Other agents are translating other scenes at the same time: touch only your own scenes.

Read first, completely:
1. tools/translate/TRANSLATOR.md (the brief: formats, control codes, line length, style). Follow it exactly.
2. docs/glossary.md lines 1-218 (rules summary, tone per speaker, characters, plates, who calls whom, name forms).
3. translation/en/PLY_PRO.txt (the reviewed pilot: the target quality and voice; Nana, Aihara and Hiiragi are in it).
4. build/batch/notes/{ROUTE}.md if it exists (decisions of earlier agents on this route; follow them).

For each scene:
- Export: python3 tools/translate/batch.py export text <SCENE> build/batch/<SCENE>.txt --format text
- Read the whole scene, then translate every line. Write answers as JSONL (format in TRANSLATOR.md) in parts of at most 120 records per file: build/batch/<SCENE>.answers.1.jsonl, .2.jsonl, ... Import each part right after writing it:
  python3 tools/translate/batch.py import text build/batch/<SCENE>.answers.N.jsonl --normalize
  If import refuses a part, fix that part and import again.
- Check: python3 tools/qa/check_translation.py text --files <SCENE>
  Fix every FAIL (corrected lines to a new answers file, import with --force). Read every WARN: fix it, or explain it in build/batch/<SCENE>.notes.md.
- Notes: build/batch/<SCENE>.notes.md, one bullet per record id for guesses, puns you could not keep, unclear referents.

Rules:
- Quality matters more than speed. Natural English a good anime subtitle would use, faithful to the meaning and tone; each heroine's voice as in the tone table. Read the line before and after: Japanese drops subjects, decide who is meant from context.
- A {W..} wait needs no punctuation of its own: do not add a comma just because a wait sits there ("Does that mean{W60} we're friends?", not "Does that mean,{W60} we're friends?").
- No Japanese structure in English: no topic-comment ("That place, it's my home." -> "That shop? It's my family's!"), no Japanese word order around waits ("Did I keep you waiting, by any chance?", not "Did I by chance, keep you waiting?"). Place per-character waits by hand at natural phrase breaks; never distribute them with a script.
- Helper scripts go in build/batch/tmp_{ROUTE}/, never in a shared scratch directory.
- Never edit any file outside build/batch/ except through batch.py import. Do not edit glossary.json, docs, tools or other scenes. Do not run git.
- Glossary terms you think should be added or changed: list them in build/batch/notes/{ROUTE}.md under "Glossary proposals"; do not change the glossary.
- At the end, append to build/batch/notes/{ROUTE}.md (create it if missing) at most 25 lines of decisions the next agent on this route must keep consistent: recurring phrases and how you rendered them, nicknames, running jokes, how the heroine addresses the player and others, catchphrases. Keep earlier content.

Final report (short, no prose): per scene: lines imported, FAIL count (must be 0), WARN count by kind; the notes files written; anything the reviewer must look at first.
