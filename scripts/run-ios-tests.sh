#!/bin/sh
# Headless unit tests for the app's pure logic — no simulator required.
set -e
cd "$(dirname "$0")/.."
OUT="${TMPDIR:-/tmp}/sound-science-logic-checks"
swiftc -parse-as-library -module-cache-path "${TMPDIR:-/tmp}/sound-science-module-cache" -O -o "$OUT" \
    ios/Zwicky/ListeningState.swift \
    ios/Zwicky/Cache.swift \
    ios/Zwicky/Models.swift \
    ios/Zwicky/Telemetry.swift \
    ios/Zwicky/Design.swift \
    ios/Zwicky/Texture.swift \
    ios/Zwicky/HostPortrait.swift \
    ios/Zwicky/OpenAIKit.swift \
    ios/Tests/LogicChecks.swift
"$OUT"

LINK_OUT="${TMPDIR:-/tmp}/zwicky-deep-link-checks"
swiftc -parse-as-library -module-cache-path "${TMPDIR:-/tmp}/sound-science-module-cache" -O -o "$LINK_OUT" \
    ios/Zwicky/DeepLinks.swift \
    ios/Tests/DeepLinkChecks.swift
"$LINK_OUT"
