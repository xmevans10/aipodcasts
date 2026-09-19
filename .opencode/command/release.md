---
description: Archive and upload a Zwicky build to TestFlight (manual signing).
---
Follow the `zwicky-release` skill. $ARGUMENTS

First confirm with me that you should release, and whether to bump the build number. Then:
bump `CURRENT_PROJECT_VERSION` (and `MARKETING_VERSION` if asked), regenerate the project,
run the checks, archive with manual signing, export/upload with the team API key, and poll
until the build's `processingState` is `VALID`. Report the build number and status.
