# Working in this repo

## Commits

- **Commit incrementally.** One logical change per commit, not a mixed grab-bag.
- **Explain each commit** in the message: what changed and why, in the body when it
  isn't obvious from the subject. Start with a short imperative subject.
- Never commit secrets. `backend/.env` and `build/` are git-ignored; keys live only there.
- Don't commit generated output: `build/`, `build-*/`, `ios/Zwicky.xcodeproj` (regenerated).

## Checks before committing

- Backend: `python3 -m pytest -q backend/tests`
- iOS logic (no simulator): `./scripts/run-ios-tests.sh`
- iOS compile: `xcodebuild -project ios/Zwicky.xcodeproj -scheme Zwicky -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build CODE_SIGNING_ALLOWED=NO`
- After adding/renaming iOS files: `cd ios && xcodegen generate`

## iOS

- Source is `ios/Zwicky/` (generated from `ios/project.yml`). Bundle `com.xmevans10.Zwicky`.
- Do not launch the simulator. Install to the connected iPhone with `xcrun devicectl`:
  `xcrun devicectl device install app --device <udid> build/device/Build/Products/Debug-iphoneos/Zwicky.app`
  then `xcrun devicectl device process launch --device <udid> com.xmevans10.Zwicky`.

## Backend

- Stdlib Python only. Operator CLI: `python3 backend/pipeline.py <command>`.
- `python3 backend/pipeline.py doctor` reports which keys and host voices are configured.
- Narration providers are chosen by `VOICE_PROVIDER` (`elevenlabs` | `openai` | `local`);
  see `docs/INTEGRATIONS.md` and `docs/VOICE-OPTIONS.md`.

## Agent harness (opencode)

Project agent config lives in `opencode.json` and `.opencode/`, and is used only by
opencode (Pi's harness is not required). It applies Pi-style primitives:

- **Skills** in `.opencode/skills/*/SKILL.md`: tests, release, episodes, device install.
- **Commands** (prompt templates) in `.opencode/command/`: `/test`, `/release`,
  `/episode`, `/doctor`, `/commit`.
- **Subagents** in `.opencode/agent/`: `verifier` (read-only checks), `release`.
- **Protected paths**: `backend/.env`, `*.p8`, and the generated `ios/Zwicky.xcodeproj`
  are edit-denied; destructive git/`rm -rf` commands ask first.

After changing any of these, restart opencode for the config to reload.

