# iOS release lanes

`fastlane ios checks` runs backend tests, iOS logic checks, and an unsigned Release
compile. `fastlane ios beta` builds the signed app and uploads it to internal
TestFlight. `fastlane ios setup_app` creates the App Store Connect app record if
needed. The app version and build number are set in `ios/project.yml`.

Run the **ios-testflight** GitHub Actions workflow manually from `main` to
release in CI. It runs the iOS logic checks before signing, then calls the
existing `beta` lane. Configure these GitHub Actions secrets, preferably in the
`testflight` environment:

| Secret | Value |
| --- | --- |
| `ASC_KEY_ID` | App Store Connect API key ID |
| `ASC_ISSUER_ID` | App Store Connect issuer ID |
| `ASC_KEY_P8_BASE64` | Base64 encoding of the API key `.p8` file |
| `APPLE_DISTRIBUTION_P12_BASE64` | Base64 encoding of the Apple Distribution certificate and private key `.p12` |
| `APPLE_DISTRIBUTION_P12_PASSWORD` | Password used when exporting the `.p12` |
| `APP_STORE_PROFILE_BASE64` | Base64 encoding of the App Store provisioning profile for `com.xmevans10.Zwicky`, named `Zwicky App Store` |

Use `base64 < file | tr -d '\n'` to prepare a file secret. Keep the originals
outside the repository. The workflow writes credentials only to the temporary
runner and uploads to **internal** TestFlight; it does not submit to the App
Store or distribute to external testers. A new upload needs a new
`CURRENT_PROJECT_VERSION` in `ios/project.yml`.

For a local release, set `ASC_KEY_ID`, `ASC_ISSUER_ID`, and `ASC_KEY_FILE`
(path to the `.p8`) and ensure the distribution certificate and provisioning
profile are installed in the local keychain/profile directory. Then run
`fastlane ios beta`.
