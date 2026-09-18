# Zwicky — a little more curious

Decision: an iPhone-first, English-language science audio publication, aimed at curious commuters and walkers who want a satisfying discovery in 3–5 minutes. Start with a free private beta. The product is a small daily ritual, not an endless feed or a general chatbot.

## The promise

“Big ideas. Easy listening.” Start with one editorially selected explainer each weekday; grow toward three when editorial capacity supports it. A lead story, two adjacent discoveries, readable transcripts and clear evidence. Prefer an interesting true detail over a dramatic headline. Success means someone remembers an idea and comes back tomorrow.

The differentiator is editorial trust plus memorable fictional hosts. Generating summaries is a commodity; earning trust, choosing worthwhile stories and developing a voice are the durable work. The business is not validated yet. Naming is provisional pending trademark/domain clearance; do not buy a domain until checked.

## Hosts

| Host | Beat | Delivery | Avoid |
|---|---|---|---|
| Mira Vale | Space and physics | Expansive, curious, dry wit | “Scientists are baffled”, cosmic certainty |
| Clara Rowan | Nature and biology | Warm, attentive, sensory | Attributing intention to ecosystems |
| Elias Reed | Mind and technology | Precise, witty, explanatory | AGI predictions presented as fact |
| Theo Mercer | Earth and human discovery | Grounded, contextual | Medical advice or miracle claims |

Host choice prioritizes that beat on Today. Each story has one assigned host, so the same published audio can serve every listener. Do not synthesize four versions of every story at launch. No real-person voice imitation. Secure commercial voice permissions and provider plan rights before publishing.

## Experience decisions

Three-step onboarding: welcome, favorite host with a clearly labelled device-voice introduction, and a first story ready to play. No forced account or paywall. Skip and explore-first paths are available; selection persists on completion. Today has one clear hero and a finite edition. Discover supports topic filters and search. Library keeps saved and started stories locally. Player supports pause/resume, speed, skipping and sleep on production audio; demo device narration explicitly disables inaccurate seeking. Articles keep their evidence and limitations close to the text. Refresh failure preserves the existing collection. Empty feeds and search results have explicit states.

The implemented beta has four original evergreen demo scripts, not a live news feed. The backend supplies reviewed live stories when configured. Save/history survive relaunch but currently do not sync or guarantee retention when feeds rotate. Offline downloads, notifications, account sync, and paid entitlements are launch work, not implemented claims.

## Pricing hypothesis

Free: daily three-story edition, all four hosts, sources and transcripts. Plus: proposed US $5.99/month or $39.99/year, localized by App Store storefront; archive, offline audio, longer themed collections. No ads, no sale of listening data, no lifetime deal. Do not charge until Plus features are delivered. No trial in initial paid release; the free edition is the trial. Annual renewal and cancellation must be explicit in the native purchase sheet.

Prices are proposed business decisions, not researched willingness-to-pay. Test with 20 interviews and two landing-page price variants before finalizing. StoreKit merchandising is included but disabled without configured product IDs. Production must verify entitlements, handle renewals/refunds/revocation and gate archive access on the server. Never trust a client boolean as proof of purchase.

## Economics model (assumptions, not vendor quotes)

Initial output: 3 episodes/day × 22 weekdays × 4 minutes = 264 synthesized minutes/month. Synthesize once, cache, distribute many times. Start with $150/month provider and infrastructure planning reserve; use actual invoice rates before setting the production budget. Editorial labor will likely dominate early costs.

At 1,000 monthly subscribers × $5.99, gross is $5,990/month. Illustrative 30% distribution deduction leaves $4,193 before taxes, refunds, content, labor and hosting. The deduction is a stress-test assumption, not a statement of applicable Apple fees. With $2,500/month assumed fixed operations/editorial cost plus $0.40 variable cost per paid subscriber, contribution per subscriber is $3.793 and break-even is approximately 660 monthly subscribers. Annual subscribers materially change this model: model them separately using recognized monthly revenue of $39.99/12. Do not call the business profitable from this sketch.

Operational spend control: provider dashboards hard/soft budgets, daily generation count, maximum script length and generation monitoring. The implemented cap counts provider attempts; it is not a dollar meter. Limit initial intake to three approved stories/day. No auto-retries of ambiguous paid calls.

## Acceptance criteria before charging

A real source-to-reviewed-story-to-licensed-audio episode plays on a physical device; no invented facts in 30 reviewed episodes; zero critical unhandled errors in the onboarding/listening path; entitlement and refund tests pass; source corrections can be withdrawn; offline recovery works; privacy/support destinations are live; price value is validated with target listeners.
