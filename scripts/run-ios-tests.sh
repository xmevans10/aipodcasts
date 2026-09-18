#!/bin/sh
# Headless unit tests for the app's pure logic — no simulator required.
set -e
cd "$(dirname "$0")/.."
OUT="${TMPDIR:-/tmp}/sound-science-logic-checks"
swiftc -parse-as-library -O -o "$OUT" \
    ios/ScienceBreak/ListeningState.swift \
    ios/ScienceBreak/Cache.swift \
    ios/ScienceBreak/Models.swift \
    ios/ScienceBreak/Design.swift \
    ios/ScienceBreak/Texture.swift \
    ios/ScienceBreak/HostPortrait.swift \
    ios/ScienceBreak/OpenAIKit.swift \
    ios/Tests/LogicChecks.swift
"$OUT" ios/ScienceBreak/Episodes
