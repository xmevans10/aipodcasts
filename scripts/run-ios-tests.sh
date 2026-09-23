#!/bin/sh
# Headless unit tests for the app's pure logic — no simulator required.
set -e
cd "$(dirname "$0")/.."
OUT="${TMPDIR:-/tmp}/sound-science-logic-checks"
swiftc -parse-as-library -O -o "$OUT" \
    ios/Zwicky/ListeningState.swift \
    ios/Zwicky/Cache.swift \
    ios/Zwicky/Models.swift \
    ios/Zwicky/Telemetry.swift \
    ios/Zwicky/Design.swift \
    ios/Zwicky/Texture.swift \
    ios/Zwicky/HostPortrait.swift \
    ios/Zwicky/OpenAIKit.swift \
    ios/Tests/LogicChecks.swift
"$OUT" ios/Zwicky/Episodes
