# Sound Science native design system

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

Sound Science overrides: paper #F5F2E8 (approx.), ink #1F2421, acid #E0F563; lavender space, sage nature, clay mind, seafoam earth. Serif editorial headlines, system sans body, monospaced overlines. Orbital artwork is original SwiftUI geometry, no downloaded image licensing dependency. Host avatars use SF Symbols inside colored circles; they are fictional editorial identities.

Screens: welcome → favorite host and device-voice introduction → first-story handoff → Today; tabs Today / Discover / Your hosts / Library; article → player / source links / save / share; settings → privacy / editorial policy / connected feed / Plus preview. Mini-player persists between tabs. Purchase surface is native StoreKit only when configured.

Accessibility: minimum 44pt interaction targets, descriptive labels for icon controls, art hidden from VoiceOver, native navigation and text selection. Body text uses semantic styles in most controls. Large editorial titles use fixed sizes; a full accessibility-size and VoiceOver audit remains required before release. Light editorial theme is intentional for beta; dark mode is not implemented. Onboarding uses short step and selection transitions, disabled for Reduce Motion. Its editorial headings scale with Dynamic Type, content scrolls, and the main action stays reachable.

All PNGs in this folder’s sibling `design/` are captures of the compiled iOS app, not fabricated mockups. The demo is the product UI; no separate web app is required.

## 2026-09-17 redesign: shows on a platform

- Each host fronts a show (`Show` in Models.swift): The Long View (Mira Vale), Wild Company (Clara Rowan), Signal & Noise (Elias Reed), Common Ground (Theo Mercer). Covers are code-drawn gradients with the show's symbol and serif title (`ShowCover`).
- Tokens (`Theme` in Design.swift): warm-neutral canvas #FAF9F6, white surfaces with #E5E2DB hairlines, ink #161614; colour lives in show covers. SF Pro for UI, New York serif for display titles, Charter for reading and read-along. Radii from OpenAIKit.
- Home: greeting and weekly summary, continue listening, show cards, latest episodes with play-all, listening stats (minutes this week, finished, day streak; stored on device only).
- Tabs: Home, Browse (shows + episode search), Hosts (persona pages), Library (following, up next, saved / in progress / played), You (daily goal, weekly Swift Charts bar chart, totals, follow toggles, settings). The daily goal is set during onboarding and stored on device.
- Host portraits: DiceBear "Notionists" (CC0 1.0, https://www.dicebear.com/styles/notionists/), fetched once as 256px PNGs with fixed options (hair/lips variants, no glasses/beard/gesture) and bundled as `host-<id>` assets.

## Motion: the living cover (Rive)

`rive/nowplaying/scene.rml` is the animated player cover, authored as text with the Rive CLI (`rive rive/nowplaying --once` writes `build/nowplaying.riv`, which is copied to `ios/ScienceBreak/Animations/`). One artboard serves every show: a `Cover` view model exposes `colorTop`, `colorBottom` and `isPlaying`, so the app binds the show's gradient and play state rather than shipping four files. While playing, two orbits turn, the sphere breathes and a five-bar equalizer dances; paused, the bars settle and the orbits keep drifting slowly — the drift is deliberate, since a fully settled state machine stops advancing and then misses the next `isPlaying` change.

Swift side: [`LivingCover.swift`](../ios/ScienceBreak/LivingCover.swift) wraps `RiveViewModel` (RiveRuntime 6.27.0 via SPM), writes the two colours and the boolean through `enableAutoBind`, and falls back to the static `ShowCover` if the `.riv` is missing. Verify scene changes headlessly before building the app: `rive rive/nowplaying --screenshot=build/playing.png --data=isPlaying=true --data=colorTop=FF8CC084 --advance=70`.
