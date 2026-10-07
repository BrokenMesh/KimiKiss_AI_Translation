# Pipeline commands

All paths are relative to the repo root. `build/` and `text/` are gitignored because they contain game data.

```sh
# 0. Fetch the user's ISO outside the repo (verifies the recorded SHA-1)
tools/build/fetch_iso.sh '<url-or-path>'

# 1. Extract the disc
python3 tools/extract/iso_extract.py ../kimikiss-private/kimikiss.iso build/orig build/orig_manifest.json

# 2. Scripts -> JSON
python3 tools/extract/img.py unpack build/orig/SCRIPT.IMG build/script
python3 tools/extract/extract_text.py build/script text

# 3. JSON -> scripts -> SCRIPT.IMG ("translation" field wins over "text")
python3 tools/reinsert/reinsert_text.py build/script text build/out/script
python3 tools/reinsert/img_pack.py build/out/script build/out/SCRIPT.IMG

# Textures
python3 tools/extract/arc.py unpack build/orig/GRAPH/GRAPH0.ARC build/graph0
python3 tools/extract/tim2.py topng build/graph0/0077_ffc76f47.tm2 font.png
python3 tools/extract/tim2.py totim2 font.png build/graph0/0077_ffc76f47.tm2
python3 tools/reinsert/arc_pack.py build/graph0 build/out/GRAPH0.ARC
python3 tools/extract/font.py build/orig/GRAPH/GRAPH0.ARC build/font.png

# Gate G3 and size budget
python3 tools/qa/test_text_roundtrip.py build/orig/SCRIPT.IMG
python3 tools/qa/test_texture_roundtrip.py build/texrt build/orig/GRAPH/*.ARC build/orig/SOUND/MUSIC.ARC
python3 tools/qa/size_report.py build/orig_manifest.json build/orig build/out
```
