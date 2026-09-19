---
name: zwicky-test
description: Run Zwicky's checks before committing or releasing. Use when the user says test, run tests, verify, check the build, or before any commit/release; covers backend pytest, the headless iOS logic checks, and the iOS simulator compile.
---

# Zwicky tests

Run from the repo root. Backend and iOS logic checks need no simulator and no keys.

```bash
python3 -m pytest -q backend/tests          # backend, currently ~67 tests
./scripts/run-ios-tests.sh                  # headless iOS logic, currently 233 checks
```

Compile the app without launching a simulator:

```bash
xcodebuild -project ios/Zwicky.xcodeproj -scheme Zwicky -configuration Release \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build CODE_SIGNING_ALLOWED=NO
```

Notes:
- `run-ios-tests.sh` compiles a fixed list of pure-logic files with `swiftc`; if you add a
  new pure-logic file, add it to that list. SwiftUI-only files are not in it.
- UI behaviour still needs a device; do not claim runtime verification from a compile.
- If iOS files were added or renamed, run `cd ios && xcodegen generate` first.
