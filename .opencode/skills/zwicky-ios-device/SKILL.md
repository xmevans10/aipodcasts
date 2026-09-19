---
name: zwicky-ios-device
description: Build and install the Zwicky app on the connected iPhone. Use when the user says device, install to my phone, iPhone, devicectl, or run on device; never use the simulator.
---

# Install Zwicky on the device

Do not launch the simulator (the user asked to keep it shut down). Build Debug for the
connected device, install, and launch with `devicectl`.

```bash
xcrun devicectl list devices        # get the connected iPhone's identifier
cd ios && xcodegen generate && cd ..     # only if files changed

xcodebuild -project ios/Zwicky.xcodeproj -scheme Zwicky -configuration Debug \
  -destination 'id=<UDID>' -allowProvisioningUpdates \
  -derivedDataPath build/device build

xcrun devicectl device install app --device <UDID> \
  build/device/Build/Products/Debug-iphoneos/Zwicky.app
xcrun devicectl device process launch --device <UDID> com.xmevans10.Zwicky
```

Notes:
- If launch fails with "device was not unlocked", ask the user to unlock and retry; the
  install still succeeded.
- The phone drops off the bus intermittently; `devicectl list devices` showing
  `unavailable` means reconnecting is needed before building for `id=<UDID>`.
- Device builds use automatic development signing; the App Store profile is only for
  release uploads (see the `zwicky-release` skill).
