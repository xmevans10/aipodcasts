# Science Break native design system

OpenAI Apps SDK UI is a React/CSS library, not a Swift package. This project adapts its semantic tokens and component conventions into native SwiftUI; it does not embed a web UI or claim an official Swift port.

Upstream: https://github.com/openai/apps-sdk-ui
Pinned reference: `0f00143c7a639906f1621fe58e1b6be7b5bea46d`
License: MIT, preserved in `licenses/OpenAI-Apps-SDK-UI.txt`.
Read: `variables-semantic.css`, `variables-primitive.css`, and `Button.module.css`.
Native implementation: `ios/ScienceBreak/OpenAIKit.swift`, `Design.swift`.

| Foundation | OpenAI reference | Native adaptation |
|---|---|---|
| Spacing | 4px base | 4pt base; optical editorial adjustments |
| Radii | 6/8/12/16/20/24, full | Same points; Capsule for full |
| Neutral palette | gray-100 #ededed; gray-900 #181818 | Available neutral tokens, warmed for brand |
| Controls | Filled/outline/ghost; pill option | CapsuleButton and native toolbar buttons |
| Selection | Segmented control | Native segmented Picker |
| Search | Input and clear states | Native searchable with empty result state |
| Feedback | Disabled/loading/error | Native states and explicit message text |

Science Break overrides: paper #F5F2E8 (approx.), ink #1F2421, acid #E0F563; lavender space, sage nature, clay mind, seafoam earth. Serif editorial headlines, system sans body, monospaced overlines. Orbital artwork is original SwiftUI geometry, no downloaded image licensing dependency. Host avatars use SF Symbols inside colored circles; they are fictional editorial identities.

Screens: welcome → favorite host and device-voice introduction → first-story handoff → Today; tabs Today / Discover / Your hosts / Library; article → player / source links / save / share; settings → privacy / editorial policy / connected feed / Plus preview. Mini-player persists between tabs. Purchase surface is native StoreKit only when configured.

Accessibility: minimum 44pt interaction targets, descriptive labels for icon controls, art hidden from VoiceOver, native navigation and text selection. Body text uses semantic styles in most controls. Large editorial titles use fixed sizes; a full accessibility-size and VoiceOver audit remains required before release. Light editorial theme is intentional for beta; dark mode is not implemented. Onboarding uses short step and selection transitions, disabled for Reduce Motion. Its editorial headings scale with Dynamic Type, content scrolls, and the main action stays reachable.

All PNGs in this folder’s sibling `design/` are captures of the compiled iOS app, not fabricated mockups. The demo is the product UI; no separate web app is required.
