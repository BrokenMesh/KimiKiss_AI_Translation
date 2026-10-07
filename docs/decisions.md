# Decisions

## D-001: Source ISO lives outside the repo

- The user's disc image is stored at `../kimikiss-private/kimikiss.iso` relative to the checkout (override with `KIMIKISS_PRIVATE_DIR`). `tools/build/fetch_iso.sh` refuses a destination inside the repo.
- The image is read-only (`chmod 400`). Builds copy it into `build/`, which is gitignored.
- The first ingest records the SHA-1 in `tools/build/iso.sha1`. Every later ingest and build must match it.
- Defense in depth: `.gitignore` covers disc image, ELF, and IRX extensions plus `build/`, `text/`, and `qa/`. `tools/githooks/pre-commit` rejects staged ISO9660 images, ELF binaries, and files over 5 MiB regardless of name.
- Cloud session containers are ephemeral, so the ISO must be fetched again in each new session.

## D-002: Target edition is SLPS-25850

- The user's disc is the eb!Kore+ re-release (SLPS-25850, volume `KIMIKISSPLUS`), not the 2006 first print the brief names. Patches target this image only. Details are in `docs/source-iso.md`.
- Whether this edition's content differs from the 2006 first print has not been checked yet.
