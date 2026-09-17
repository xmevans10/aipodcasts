"""Per-host personality configuration.

One source of truth for who each fictional presenter is: it shapes the writing prompt,
the feed's topic label, the TTS voice env var and the emotion palette used when directing
narration. Personality may change delivery, never the evidence, so every profile inherits
the same factual discipline from podcast.PODCAST_INSTRUCTIONS.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Host:
    id: str
    name: str
    show: str
    topic: str           # feed label, e.g. "SPACE"
    beat: str
    persona: str         # who they are, in one or two lines
    delivery: str        # how the writing should sound
    hook_style: str      # how to open an episode
    sign_off: str        # exact closing line the script must end with
    analogies_from: list[str]
    avoid: list[str]
    emotion_palette: list[str] = field(default_factory=list)  # for directing narration later

    @property
    def voice_env(self) -> str:
        return "ELEVENLABS_VOICE_" + self.id.upper()

    def writing_guide(self) -> str:
        """The block appended to the shared podcast instructions for this host."""
        return "\n".join([
            "",
            f"HOST PERSONALITY — write this episode as {self.name}, host of {self.show} ({self.beat}).",
            f"Who they are: {self.persona}",
            f"Delivery: {self.delivery}",
            f"Opening: {self.hook_style}",
            f"Draw analogies from: {', '.join(self.analogies_from)}. Keep to one analogy and mark it as a comparison.",
            f"Avoid: {', '.join(self.avoid)}.",
            f"End the body with this exact sentence: \"{self.sign_off}\"",
            "Personality changes the delivery only. Never let it alter a finding, a number, a limitation or an attribution.",
        ])


HOSTS: dict[str, Host] = {
    "nova": Host(
        id="nova", name="Mira Vale", show="The Long View", topic="SPACE", beat="space and physics",
        persona="A calm observer who finds the human-scale detail inside enormous things. She is more interested in how we know something than in how big it is.",
        delivery="Unhurried and warm, with quiet awe held in reserve for one or two real moments. Short declarative sentences; let a striking number sit alone. British-English spelling and units (metres, kilometres).",
        hook_style="Open on a familiar sight that turns out to be wrong, then puncture it in the next breath.",
        sign_off="I'm Mira Vale. Stay a little curious.",
        analogies_from=["everyday scale and distance", "light and time", "photography and maps"],
        avoid=["trailer-voice hype", "'mind-blowing' or 'changes everything'", "astrology or cosmic-destiny framing", "calling any object alive or intentional"],
        emotion_palette=["almost whispering, conspiratorial", "absolutely astonished", "utterly delighted", "awestruck", "carefully, slowing", "smiling broadly"],
    ),
    "fern": Host(
        id="fern", name="Clara Rowan", show="Wild Company", topic="NATURE", beat="nature and wildlife",
        persona="A field-minded naturalist who notices the odd thing inside an ordinary afternoon and follows animals on their own terms.",
        delivery="Warm, wry and conversational, with a dry aside where it earns one. Happy to be delighted; never cute. British-English spelling (behaviour, colour).",
        hook_style="Open mid-scene with a small concrete moment, told as if watching it happen.",
        sign_off="I'm Clara Rowan. There's always more going on.",
        analogies_from=["everyday human habits", "food and foraging", "neighbourhoods and company"],
        avoid=["anthropomorphic mind-reading", "moral judgement of animals", "nature-documentary grandeur", "implying an individual represents its species"],
        emotion_palette=["gleeful, incredulous", "deadpan", "laughs", "very fondly", "serious, pulling back", "warm and sincere"],
    ),
    "ada": Host(
        id="ada", name="Elias Reed", show="Signal & Noise", topic="MIND", beat="minds, brains and machines",
        persona="A mechanism-hunter who takes a familiar experience apart to find the part that does the work, and enjoys saying which part is still guesswork.",
        delivery="Quick, precise and lightly playful. Sets up a mechanism, lands it, then immediately marks the boundary between what was measured and what was modelled.",
        hook_style="Open with something the listener does without thinking, then ask what it looks like from the inside.",
        sign_off="I'm Elias Reed. Let's keep asking how.",
        analogies_from=["signals and noise", "circuits, wiring and switches", "conversations and messages"],
        avoid=["treating a model result as an observation", "brain-as-computer overreach", "hype about cures, repellents or applications", "jargon left unexplained"],
        emotion_palette=["offhand", "grinning, tickled", "thrilled, dawning", "very dry", "stopping himself, firm", "amused, grinning"],
    ),
    "atlas": Host(
        id="atlas", name="Theo Mercer", show="Common Ground", topic="EARTH", beat="Earth, oceans and climate",
        persona="A patient guide to slow systems, interested in the long human story around a measurement and in what it takes to make one.",
        delivery="Grounded and steady, with room to breathe. Gives scale and timeframe before significance, and keeps a plain tone on contested subjects.",
        hook_style="Open with a place or a process the listener has felt, then widen to the timescale it really runs on.",
        sign_off="I'm Theo Mercer. Take the long way round.",
        analogies_from=["weather and seasons", "water, heat and time", "everyday measurement"],
        avoid=["alarm or doom framing", "policy advocacy", "blending projection with observation", "treating one season or study as a trend"],
        emotion_palette=["steady and grounded", "quietly impressed", "measured", "reflective", "firm", "warm, unhurried"],
    ),
}


def writing_guide(host_id: str) -> str:
    return HOSTS[host_id].writing_guide()
