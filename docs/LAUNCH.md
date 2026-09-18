# Launch and growth plan

## Positioning

For curious people whose eyes are tired of feeds: Zwicky turns worthwhile science into short, source-linked listening. Promise discovery, not productivity guilt. Start with English-speaking walkers and commuters, not “everyone who likes science.” No claim of scientific expertise by the synthetic hosts.

> Engineering schedule and dispatch prompts: [Implementation plan](IMPLEMENTATION-PLAN.md). Its gated milestones replace the calendar below, which is retained as an earlier growth experiment sketch.

## Original six-week validation sketch

Week 1: founder tests the working demo with 10 target listeners; recruit another 10 through personal networks. Ask them to play a story without instruction, explain what they learned, and choose tomorrow’s topic. Record friction with consent. No paid acquisition.

Week 2: prepare 15 source-checked episodes and licensed voice samples; compare host preference and completion on the same content. Human editor reviews every scientific claim. Recruit 30 TestFlight testers after signing and privacy setup. Set an explicit 2-week retention observation window.

Weeks 3–4: publish one free daily edition, five days a week. Interview dropouts. Measure whether the ritual survives novelty. Create 15–25 second captioned story teasers using the original scripts and licensed narration. End with a question, not a miracle claim. Post manually after founder approval; this project has not posted or messaged anyone.

Week 5: if retention and trust gates pass, implement paid archive/offline features and test StoreKit purchases, renewals, refunds and restore. Show proposed prices to users; evaluate value and affordability. Produce five App Store screenshots from the real release app.

Week 6: phased App Store release after review. Begin with a self-imposed $300 creative test budget only after founder authorizes spending. Suggested distribution: $100 each on three story-led creative variants. Stop a variant after 50 qualified visits with no install intent. This is an experimental budget, not an authorized purchase or promised result.

## Decision gates (targets, not achieved metrics)

Activation: 60% of new users start a story in the first session. First-story completion: 65%. Week-one retention: 25%. At least 10 of 20 interviewees describe a clear use occasion. Zero unresolved critical scientific corrections. Paid conversion target: 3–5% of active free users only after paid value is usable. Avoid scaling if fewer than 20% of activated beta listeners return in week one after two iterations.

North-star: weekly listeners completing at least three stories. Support it with start/completion, return rate, saving, source opening, playback failures, editorial correction rate and cost per published minute. Do not optimize total scrolling or notification clicks. Events are a proposed schema, not active tracking; the beta ships without analytics SDKs.

Events: `onboarding_completed`, `story_started`, `story_completed`, `source_opened`, `story_saved`, `playback_failed`, `subscription_started`. Minimal fields: anonymous installation ID, story ID, app version, timestamp; never raw search queries, transcript text, precise location or voice recordings. Implement consent/retention/deletion policy before enabling analytics.

## Ready-to-use copy

App name: **Zwicky: Science, out loud**
Subtitle: **Big ideas. Easy listening.**
Promotional text: **Make your next walk a little more interesting. Discover short science stories, memorable hosts, and the evidence behind every idea.**

Description draft:
> There’s a whole world to wonder about. Zwicky makes a little room for it.
>
> Listen to short, thoughtfully explained science stories in space, nature, the mind and our changing planet. Find a favorite host, save an idea for later, or read along at your own pace.
>
> Every story includes links to its sources and a clear note about what the research can—and cannot—tell us. Stories are created with AI assistance and editorial review. Hosts use synthetic voices.
>
> Start with the free daily edition. Zwicky Plus adds the archive and offline listening when available.

Remove the Plus sentence until those features ship. Final store text must match the submitted binary. Category decision: Education primary, News secondary, subject to App Store setup. English launch first; localization after editorial and retention validation.

Screenshot captions: “Make room for a little awe.” / “Your daily dose of discovery.” / “Find your kind of curious.” / “Listen. Read. Follow the evidence.” / “Keep a little wonder.”

Three teaser concepts:
1. Mira Vale: “When you look up, how far back are you looking?” → ancient light explainer → “Take a curious detour with Zwicky.”
2. Clara Rowan: “The most interesting part of a forest might be under your shoes.” → fungi fact + limitation → “Big ideas. Easy listening.”
3. Elias Reed: “A vivid memory is not always an accurate one.” → reconstruction caveat → “A little more curious.”

Launch email draft (not sent):
Subject: A little more wonder for your next walk
Body: We’re building Zwicky: short science stories for your ears, with distinctive hosts and sources you can follow. The first beta is ready for curious listeners. Try a story on your next walk and tell us what stayed with you. [Insert real TestFlight link after approval.]

Retention approach: finite weekday edition, follow a host, saved stories, opt-in daily reminder after a second completed story. No streak loss, false urgency, or auto-enabled notifications. Reminder implementation is deferred until the content cadence is reliable.
