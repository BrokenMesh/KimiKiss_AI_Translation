# Phase 0 status

## Gate G1 (Ghidra loads the ELF and decompiles a function): **blocked**

- JDK 21 is installed (`openjdk 21.0.12`), which Ghidra 12.x requires.
- Downloading Ghidra 12.1.3 failed. This cloud session's GitHub proxy serves only `git clone` of public repositories. Release downloads and the API for `NationalSecurityAgency/ghidra` return 403 ("GitHub access to this repository is not enabled for this session"). The repository can't be attached with credentials because the user has no access to it.
- Ubuntu 24.04's package archive has no Ghidra or PCSX2 package.
- The PS2 EE extension (for example `chaoticgd/ghidra-emotionengine-reloaded`) and `bethington/ghidra-mcp` are also distributed as GitHub release assets, so the same block applies to them.

## Gate G0 (headless PCSX2 boot and screenshot): **not attempted**

PCSX2 builds are also GitHub release assets, so the same block applies. Software rendering under Xvfb would be the route inside this container.

## Options

1. **The user puts the binaries in their own Google Drive** (`drive.usercontent.google.com` is already allowed): the Ghidra 12.1.3 zip, the EE extension zip matching that Ghidra version, the ghidra-mcp release, and a PCSX2 Linux AppImage. Ghidra (Apache-2.0), PCSX2 (GPL-3.0) and both extensions are redistributable. No PS2 BIOS. A BIOS is the user's own dump and stays outside the repo like the ISO.
2. **Run Phase 0 and 3 on the user's own machine** through Remote Control. Ghidra and PCSX2 then run locally with a real display, which also covers G0.
3. **Amend the brief:** do the Phase 3 static analysis with Capstone (on PyPI, which is reachable) and custom scripts instead of Ghidra. That needs the user's approval, because G1 as written requires Ghidra.

Phase 3 does not start until one of these is chosen.
