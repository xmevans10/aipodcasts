---
name: zwicky-release
description: Archive and upload a Zwicky build to TestFlight, or prepare a release. Use when the user says release, TestFlight, ship, upload, archive, app store, or bump the build.
---

# Zwicky release (TestFlight)

Only do this when the user asks. Bump the build first if a build with this number exists.

1. Bump `CURRENT_PROJECT_VERSION` in `ios/project.yml` (and `MARKETING_VERSION` for a
   version change), then `cd ios && xcodegen generate`.
2. Run the checks in the `zwicky-test` skill.
3. Archive with manual signing (the App Store profile already exists):

```bash
xcodebuild archive -project ios/Zwicky.xcodeproj -scheme Zwicky -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/release/Zwicky.xcarchive \
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM=8K5ZVPCQ42 \
  PROVISIONING_PROFILE_SPECIFIER="Zwicky App Store" CODE_SIGN_IDENTITY="Apple Distribution"
```

4. Export and upload straight to App Store Connect with the team API key:

```bash
xcodebuild -exportArchive -archivePath build/release/Zwicky.xcarchive \
  -exportOptionsPlist build/release/ExportOptions.plist -exportPath build/release/export \
  -authenticationKeyPath /Users/xanderevans/Documents/fantasy-app/tools/release/private_keys/AuthKey_G3X8K8ZRNJ.p8 \
  -authenticationKeyID G3X8K8ZRNJ \
  -authenticationKeyIssuerID 39423832-9d26-41bd-8f97-a06fdbc3c311
```

5. Poll for processing with the ASC helper (from `/Users/xanderevans/Documents/fantasy-app`):
   `python3 tools/release/asc.py GET "/v1/builds?filter[app]=6813660087&limit=5&sort=-uploadedDate"`
   until `processingState` is `VALID`.

Important: the App Store Connect API cannot create app records. The `Zwicky` record
(bundle `com.xmevans10.Zwicky`, app id `6813660087`) must already exist in the web UI.
`build/release/ExportOptions.plist` is git-ignored and already written if present.
