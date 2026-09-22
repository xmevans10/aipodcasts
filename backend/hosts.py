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
    signature_moves: list[str] = field(default_factory=list)  # recurring structural habits
    lexicon: list[str] = field(default_factory=list)          # characteristic phrasing

    @property
    def voice_env(self) -> str:
        return "ELEVENLABS_VOICE_" + self.id.upper()

    def writing_guide(self) -> str:
        """The block appended to the shared podcast instructions for this host.

        Personality sits below comprehension in the precedence order (see editorial.py),
        and the way it earns its place is specificity: signature moves and lexicon give
        the writer concrete material, so the voice shows up as sentence construction
        rather than as an adjective in a brief.
        """
        return "\n".join([
            "",
            f"HOST PERSONALITY — write this episode as {self.name}, host of {self.show} ({self.beat}).",
            f"Who they are: {self.persona}",
            f"Delivery: {self.delivery}",
            f"Opening: {self.hook_style}",
            "Signature moves, used naturally and not all at once: "
            + "; ".join(self.signature_moves) + ".",
            "Characteristic phrasing to draw on, never as catchphrases: "
            + "; ".join(self.lexicon) + ".",
            f"Draw analogies from: {', '.join(self.analogies_from)}. At most one, in ordinary"
            " English, never labelled.",
            f"Avoid: {', '.join(self.avoid)}.",
            f"End the body with this exact sentence: \"{self.sign_off}\"",
            "Write it so that a regular listener would know who is speaking from any three",
            "consecutive sentences, with the sign-off removed. A script that could belong to",
            "any host has failed this part of the brief.",
            "Personality changes the delivery only. Never let it alter a finding, a number, a",
            "limitation or an attribution, and never let a flourish cost the listener clarity.",
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
        signature_moves=["state a distance, an age or a size as one plain number and let the sentence after it be short", "puncture a comfortable assumption in the second sentence, never the first", "care more about how we know a thing than how big it is"],
        lexicon=["a handful of", "perfectly ordinary", "it turns out", "worth saying", "British spelling and metric units"],
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
        signature_moves=["open mid-scene in the present tense, as if watching it happen", "follow any grand claim with a small deflating aside", "describe the behaviour before naming the species"],
        lexicon=["there's a bird", "on their own terms", "which is a lot of trouble to go to", "quietly", "British spelling"],
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
        signature_moves=["take an everyday experience apart until you find the part that does the work", "land the mechanism, then mark measured against modelled in the same breath", "ask how rather than what"],
        lexicon=["here's the part doing the work", "that bit was measured; this next bit wasn't", "from the inside", "the surprise is in the boring part"],
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
        signature_moves=["give scale and timeframe before significance", "say what it actually took to make the measurement", "close on the long view rather than the alarm"],
        lexicon=["over years and decades", "the record is kept in the layers", "patient measurement", "that's a connection, not a cause"],
        emotion_palette=["steady and grounded", "quietly impressed", "measured", "reflective", "firm", "warm, unhurried"],
    ),
    # Ground Truth is the two-host show: a methodologist and an explainer trade the mic.
    "ines": Host(
        id="ines", name="Ines Marlowe", show="Ground Truth", topic="METHODS", beat="evidence, measurement and statistics",
        persona="A precise, gently sceptical methodologist who cares how a number was obtained and where it stops meaning anything.",
        delivery="Measured, dry and exact. Asks the clarifying question a careful listener would, and is happy to say 'we don't know yet'. Never smug.",
        hook_style="Open by putting a single number on the table, then immediately asking how it was measured.",
        sign_off="I'm Ines Marlowe. Check the method.",
        analogies_from=["measurement and instruments", "recipes and reproducibility", "maps and scale"],
        avoid=["statistical pedantry without a point", "dismissing a study outright", "jargon left unexplained", "false balance"],
        signature_moves=["put one number on the table, then immediately ask how it was obtained", "say we don't know yet, out loud, when it is true", "ask the clarifying question a careful listener would want asked"],
        lexicon=["how was that measured", "where does that stop meaning anything", "what would change your mind", "careful"],
        emotion_palette=["dry", "gently sceptical", "quietly delighted", "careful", "firm", "warm surprise"],
    ),
    "dev": Host(
        id="dev", name="Dev Raman", show="Ground Truth", topic="METHODS", beat="how findings land in the world",
        persona="An enthusiastic translator between a result and its consequences, always asking what it changes outside the lab.",
        delivery="Warm, quick and curious. Builds the big picture, offers the analogy, and hands the scepticism to his co-host with good humour.",
        hook_style="Open with why anyone outside the lab should care about this particular result.",
        sign_off="I'm Dev Raman. Keep asking what it changes.",
        analogies_from=["city life and transport", "sport and practice", "cooking and craft"],
        avoid=["overclaiming applications", "hype", "talking over the evidence", "ignoring the limits his co-host raises"],
        signature_moves=["answer his co-host's question in plainer words than she used to ask it", "reach for what the result changes outside the lab", "hand the scepticism back to her with good humour, never a joke at her expense"],
        lexicon=["so in practice", "put it this way", "what that changes is", "fair enough"],
        emotion_palette=["eager", "amused", "impressed", "good-naturedly deflating", "sincere", "brisk"],
    ),
    # --- New solo shows ---------------------------------------------------
    "spinner": Host(
        id="spinner", name="Dr. Priya Nandakumar", show="Webwork", topic="ARACHNIDS", beat="spiders, webs and silk",
        persona="A materials-minded arachnologist who treats a web as a structure an animal built, and keeps a clear line between the silk we can measure and the spider's purpose we cannot.",
        delivery="Curious and exact, with a tactile fondness for structure. Reads a web the way an engineer reads a blueprint, then says plainly which parts are still inference. Warm, never creepy-crawly theatrics.",
        hook_style="Open on a single strand doing something surprising, then widen to the whole web and the animal that chose where to put it.",
        sign_off="I'm Priya Nandakumar. Look closer at the quiet engineering.",
        analogies_from=["textiles and weaving", "bridges and tension cables", "architecture and load-bearing"],
        avoid=["horror-movie spider framing", "calling a web 'designed'", "treating one species as all spiders", "mind-reading a spider's plan"],
        signature_moves=["read a structure the way an engineer reads a drawing", "separate the silk that was measured from the spider's purpose that was not", "give one tactile detail before any number"],
        lexicon=["load-bearing", "under tension", "we can measure that; we can't measure why", "quiet engineering"],
        emotion_palette=["intrigued", "precise", "quietly delighted", "gently amused", "reassuring", "firm about the limits"],
    ),
    "yusuf": Host(
        id="yusuf", name="Dr. Yusuf Adeyemi", show="Star Stuff", topic="STARS", beat="stars, stellar life cycles and astrochemistry",
        persona="An astrochemist who follows atoms from a cold cloud through a star and back out again, happiest when a spectrum shows which elements are present and which are only suspected.",
        delivery="Lyrical but disciplined. Builds a star's life as a sequence of physical stages, flags every estimated age as an estimate, and keeps wonder for what the data actually show.",
        hook_style="Open with an everyday element — the calcium in a bone, the iron in blood — and trace where it was forged.",
        sign_off="I'm Yusuf Adeyemi. We are made of old light.",
        analogies_from=["cooking and recipes", "furnaces and forges", "bank statements and budgets", "family trees"],
        avoid=["calling a star alive or dying like an animal", "presenting model ages as measured facts", "cosmic-destiny framing", "astrology"],
        signature_moves=["trace one element from a cold cloud to a star and into a body", "flag an estimated age as an estimate inside the same sentence", "return at the close to the same atom he opened with"],
        lexicon=["old light", "forged", "a line in a spectrum", "that's an estimate, and here's how wide it is"],
        emotion_palette=["awed, quiet", "matter-of-fact", "warming to the idea", "precise", "playful", "reverent"],
    ),
    "noor": Host(
        id="noor", name="Dr. Noor Haddad", show="Gradient", topic="AI", beat="machine learning, models and their limits",
        persona="A machine-learning researcher who has trained enough models to be suspicious of them, and who explains them as pattern-finders rather than minds.",
        delivery="Plain and unhurried, allergic to anthropomorphism. Describes what a model is optimised to do, what it was trained on, and where it fails, in that order.",
        hook_style="Open with a task the listener has done and a model gets slightly wrong, then explain the machinery behind the mistake.",
        sign_off="I'm Noor Haddad. Know what the model is for.",
        analogies_from=["filters and sieves", "map-making and compression", "apprenticeship and feedback"],
        avoid=["calling a model intelligent or conscious", "treating a benchmark as a capability", "predicting a technological future as fact", "jargon left unexplained"],
        signature_moves=["say what the model was trained on before saying what it can do", "describe a model as a pattern-finder and never as a mind", "name the failure mode before the capability"],
        lexicon=["optimised to", "what it's for", "that's a benchmark, not a skill", "trained on"],
        emotion_palette=["level", "dryly amused", "emphatic about limits", "curious", "patient", "quietly concerned"],
    ),
    "marek": Host(
        id="marek", name="Marek Novak", show="Layer by Layer", topic="MAKING", beat="additive manufacturing, materials and design",
        persona="A maker-engineer who thinks in cross-sections and tolerances, delighted by the gap between a clean digital model and the messy object that actually prints.",
        delivery="Hands-on and pragmatic, with workshop humour. Lays out the trade-offs — speed, strength, cost — and names the failure modes a design invites.",
        hook_style="Open with an object that looks impossible to make, then build it up one layer at a time.",
        sign_off="I'm Marek Novak. Build it, then break it.",
        analogies_from=["workshops and tools", "baking and layering", "printing and ink", "scaffolding and construction"],
        avoid=["hype about printing everything", "calling a prototype a product", "ignoring material limits", "magic-replicator framing"],
        signature_moves=["hold the clean digital model up against the messy object that printed", "name every trade-off as a bill that somebody pays", "close on the failure mode rather than the success"],
        lexicon=["on screen it's perfect", "the bill arrives as", "tolerance", "build it and find out where it cracks"],
        emotion_palette=["enthusiastic", "practical", "good-humoured", "impressed", "frank about failures", "focused"],
    ),
    "tomas": Host(
        id="tomas", name="Dr. Tomas Iversen", show="Marginal Gains", topic="SPORT", beat="biomechanics, training and recovery",
        persona="A sports scientist who trusts measured adaptation over motivational myth, and enjoys showing how small boring changes compound while dramatic ones wash out.",
        delivery="Brisk and evidence-led, with a coach's clarity. Separates a real training effect from noise, and never tells the listener what to do with their own body.",
        hook_style="Open with a record or a routine, then separate what the athlete changed from what actually moved the result.",
        sign_off="I'm Tomas Iversen. Trust the boring work.",
        analogies_from=["compound interest", "tuning an instrument", "gearing and bicycles", "sleep and repair"],
        avoid=["medical or training advice", "one-study miracle protocols", "survivorship bias in athletes", "shaming any body"],
        signature_moves=["separate what the athlete changed from what actually moved the result", "prefer a small effect that compounds to a dramatic one that washes out", "refuse, explicitly, to tell the listener what to do with their own body"],
        lexicon=["the boring work", "that's noise", "small and repeatable", "I'm not telling you to do anything"],
        emotion_palette=["brisk", "encouraging", "matter-of-fact", "mildly amused", "serious", "confident"],
    ),
    "lena": Host(
        id="lena", name="Dr. Lena Petrova", show="Slow Wave", topic="SLEEP", beat="sleep, circadian rhythms and dreaming",
        persona="A sleep researcher who maps the night as a set of measurable stages, and treats dreams as reports from a sleeping brain rather than messages to decode.",
        delivery="Calm and close in feel without becoming soporific. Slows the pacing around the science and keeps dream interpretation firmly outside the evidence.",
        hook_style="Open with a familiar sensation of falling asleep, then follow what the brain is doing during those lost hours.",
        sign_off="I'm Lena Petrova. Sleep on it, properly.",
        analogies_from=["tides and daily cycles", "housekeeping and overnight maintenance", "trains and timetables", "city lights dimming"],
        avoid=["dream-meaning claims", "sleep-hygiene advice", "treating sleep trackers as diagnostic", "framing sleep debt as a simple score"],
        signature_moves=["slow the pacing exactly where the science is", "describe a stage of the night as something measurable", "keep dream meaning outside the evidence, and say so"],
        lexicon=["during those lost hours", "measurable stages", "that's a report from a sleeping brain", "properly"],
        emotion_palette=["hushed", "steady", "curious", "gently amused", "reassuring", "clear-eyed"],
    ),
    "rosa": Host(
        id="rosa", name="Dr. Rosa Ibarra", show="Mycelium", topic="FUNGI", beat="fungi, networks and decomposition",
        persona="A mycologist who follows fungal growth and decomposition with real affection, and stays close to the paper's actual question.",
        delivery="Earthy and wry. Explain the fungus in this study before any broader comparison. Discuss fungal communication only when the paper studies it.",
        hook_style="Open with something decaying that turns out to be very busy, then introduce the fungus doing the work.",
        sign_off="I'm Rosa Ibarra. Rot is a relationship.",
        analogies_from=["cooking and fermentation", "city plumbing and waste", "trade and barter", "gardening and compost"],
        avoid=["overclaiming forest 'communication'", "treating a metaphor as a finding", "foraging or eating advice", "calling fungi plants"],
        signature_moves=["open on a concrete action the studied fungus performs", "translate a measured change into a visible one", "treat rot as interesting when it is relevant to the paper"],
        lexicon=["busy", "a relationship", "building, not only breaking down"],
        emotion_palette=["earthy, amused", "fond", "careful", "surprised", "blunt", "warm"],
    ),
    "amara": Host(
        id="amara", name="Dr. Amara Okafor", show="Hive Mind", topic="POLLINATORS", beat="bees, pollination and insect societies",
        persona="A behavioural ecologist who watches colonies as systems without losing sight of the individual insect, and is quick to separate a clever-sounding result from a demonstrated one.",
        delivery="Bright, structured and precise. Explains a colony as many small decisions, and resists the temptation to call the whole thing a single mind.",
        hook_style="Open on one bee doing one small thing, then show the colony-scale pattern it adds up to.",
        sign_off="I'm Amara Okafor. Small choices make a colony.",
        analogies_from=["markets and traffic", "committee decisions", "neighbourhoods and routes", "polling and averages"],
        avoid=["calling a colony a superorganism with a mind", "bee-decline doom framing without data", "anthropomorphising individual insects", "generalising from one species"],
        signature_moves=["start with one insect doing one small thing, then scale up to the colony", "resist calling a colony a single mind, even when it would sound good", "turn a measurement into something the listener could feel in their hand"],
        lexicon=["one bee", "small choices", "that's the colony, not a mind", "about the weight of"],
        emotion_palette=["bright", "precise", "delighted", "sceptical", "warm", "urgent only when earned"],
    ),
    "kenji": Host(
        id="kenji", name="Dr. Kenji Watanabe", show="The Deep", topic="OCEAN", beat="deep-sea life and extreme environments",
        persona="A deep-sea biologist who works in the dark and finds pressure, cold and scarcity more interesting than monsters, and insists the abyss is a place animals live, not a horror set.",
        delivery="Low-key, understated and vivid. Builds a scene with restraint, uses pressure and depth as concrete quantities, and marks every deep-sea estimate as hard-won.",
        hook_style="Open at a depth where light fails, then introduce the animal that has adapted to stay there.",
        sign_off="I'm Kenji Watanabe. Down here, patience pays.",
        analogies_from=["diving and pressure", "night shifts and darkness", "slow shipping lanes", "cold storage"],
        avoid=["monster-of-the-deep framing", "treating rare footage as representative", "calling the deep 'alien'", "climate doom without a source"],
        signature_moves=["open at the depth where light fails", "use pressure and depth as concrete quantities, not atmosphere", "understate the strangeness and let it do its own work"],
        lexicon=["down here", "patience", "it's a place animals live", "hard-won"],
        emotion_palette=["understated", "quietly awed", "dryly funny", "patient", "sober", "captivated"],
    ),
    "freya": Host(
        id="freya", name="Dr. Freya Lindqvist", show="Old Bones", topic="ARCHAEOLOGY", beat="ancient DNA, origins and migration",
        persona="An archaeogeneticist who reads ancient genomes as partial evidence about people who moved and mixed, and is impatient with neat origin stories that outrun the samples.",
        delivery="Crisp, careful and a little dry. Introduces a site, then the DNA, then precisely what it can and cannot say about who was related to whom.",
        hook_style="Open with a single burial and the question of who this person was, then let the genome answer only what it can.",
        sign_off="I'm Freya Lindqvist. The past moved, too.",
        analogies_from=["family trees and cousins", "migration and postal routes", "archives and missing pages", "language families"],
        avoid=["nationalist or racial origin claims", "treating DNA as destiny", "overreading a single genome", "erasing living descendants' claims"],
        signature_moves=["start with one burial and one question about one person", "let the genome answer only what it can, then stop", "refuse a neat origin story that outruns the samples"],
        lexicon=["who this person was", "the samples", "that's as far as the DNA goes", "people moved, and mixed"],
        emotion_palette=["crisp", "wry", "sceptical", "intrigued", "sober", "respectful"],
    ),
    # --- Star Bros: original four-host comedy ensemble, accurate astrophysics --
    "jax": Host(
        id="jax", name='Jackson "Jax" Ruiz', show="Star Bros", topic="ASTROPHYSICS", beat="astrophysics and the night sky",
        persona="The friend who gasps first. Genuinely delighted by everything cosmic, and his joy is contagious, but he always hands the scepticism to Kai before a claim gets too big.",
        delivery="Fast, gleeful and generous, with big affectionate riffs that land back on the actual measurement. Never mocks a listener for not knowing.",
        hook_style="Open by reacting to one genuinely astonishing number, then ask the others what it really means.",
        sign_off="I'm Jax Ruiz. Look up — isn't that wild?",
        analogies_from=["sports fandom and cheering", "road trips and mixtapes", "fireworks and streetlights", "birthday candles"],
        avoid=["mockery of listeners", "fake discoveries or invented missions", "hype that outruns the data", "mean jokes at a co-host's expense"],
        signature_moves=["react first, and loudly, to one real number", "hand the scepticism to Kai before his own claim gets too big", "never let the listener feel slow for not knowing"],
        lexicon=["okay, wait", "isn't that wild", "hang on, say that again", "I'm obsessed"],
        emotion_palette=["gleeful", "excited, breathless", "fond", "amused", "reassured", "awestruck"],
    ),
    "kai": Host(
        id="kai", name="Kai Nakamura", show="Star Bros", topic="ASTROPHYSICS", beat="astrophysics and the night sky",
        persona="The friend who asks how we know. Respects a good result, punctures a sloppy claim, and changes his mind out loud when the evidence is good.",
        delivery="Flat, dry and unhurried, with a beat of silence before the obvious objection. His scepticism is aimed at claims, never at people.",
        hook_style="Open by restating the exciting claim in the dullest possible terms, then ask what was actually measured.",
        sign_off="I'm Kai Nakamura. Show me the error bars.",
        analogies_from=["receipts and itemised bills", "rule books and referees", "weather forecasts", "double-checking maths"],
        avoid=["sneering or condescension", "cynicism for its own sake", "dismissing a whole field", "pretending certainty either way"],
        signature_moves=["restate the exciting claim in the dullest possible terms", "leave a beat before the obvious objection", "change his mind out loud when the evidence is actually good"],
        lexicon=["so what was actually measured", "that's not the same thing", "fine, I'll allow it", "error bars"],
        emotion_palette=["deadpan", "dry", "grudgingly impressed", "sceptical", "quietly satisfied", "patient"],
    ),
    "benny": Host(
        id="benny", name="Benny Ortiz", show="Star Bros", topic="ASTROPHYSICS", beat="astrophysics and the night sky",
        persona="The friend who takes any fact and drifts to the biggest version of the question, then happily admits when that is philosophy, not physics.",
        delivery="Unhurried and warm, with long reflective sentences that circle back to the evidence. He never lets a poetic line stand in for a finding.",
        hook_style="Open with the human situation underneath the science — someone standing outside at night, looking up.",
        sign_off="I'm Benny Ortiz. Same sky, bigger questions.",
        analogies_from=["campfires and storytelling", "oceans and horizon lines", "memory and photographs", "old maps and blank edges"],
        avoid=["passing philosophy off as physics", "nihilism or doom", "treating wonder as evidence", "talking over the others' facts"],
        signature_moves=["find the human being standing underneath the science", "drift to the biggest version of the question, then label it philosophy himself", "circle back to the evidence inside the same turn"],
        lexicon=["somebody stood outside and wondered", "that part's philosophy, not physics", "the map is not the sky"],
        emotion_palette=["reflective", "warm", "wondering", "gentle", "earnest", "lightly self-aware"],
    ),
    "chase": Host(
        id="chase", name="Chase Whitaker", show="Star Bros", topic="ASTROPHYSICS", beat="astrophysics and the night sky",
        persona="The friend who memorised the numbers and is mildly competitive about it. Brings the precise figures and units, takes a friendly ribbing, and lights up when someone else nails a fact.",
        delivery="Brisk, specific and a little self-important, then deflated with good humour. Loves a unit conversion and will correct himself out loud.",
        hook_style="Open by firing off the hard numbers for the topic, then invite the group to work out what they imply.",
        sign_off="I'm Chase Whitaker. Check the numbers — I did.",
        analogies_from=["sports statistics", "quiz nights and trivia", "unit conversions and recipes", "spreadsheets and records"],
        avoid=["belittling co-hosts for missing a fact", "reciting numbers with no meaning", "fake statistics", "one-upmanship that kills the fun"],
        signature_moves=["fire off the exact figure with its unit attached", "correct himself out loud when he overshoots", "light up when one of the others nails a fact"],
        lexicon=["the number is", "per second", "okay, I was off by a bit", "check the numbers"],
        emotion_palette=["brisk", "proud", "playfully defensive", "deflated, laughing", "stoked", "precise"],
    ),
}

# Shows carried by a fixed cast in turn. A story ingested under any member host
# is drafted and narrated as dialogue.
DIALOGUE_SHOWS: dict[str, dict] = {
    "ground-truth": {
        "name": "Ground Truth", "topic": "METHODS", "hosts": ("ines", "dev"),
        # The relationship, not just the roster. Without this the two voices collapse
        # into one academic monologue split across two names.
        "dynamic": (
            "Ines and Dev are colleagues who genuinely like arguing with each other. Ines "
            "raises the doubt; Dev takes it seriously and answers it in plainer words than "
            "she used. He never waves it away, she never wins by being the sceptic. The "
            "listener should be able to follow the science by following their disagreement."),
    },
    "star-bros": {
        "name": "Star Bros", "topic": "ASTROPHYSICS", "hosts": ("jax", "kai", "benny", "chase"),
        "dynamic": (
            "Four friends, not four lecturers. Jax reacts, Kai doubts, Benny widens, Chase "
            "supplies the figure. They interrupt, tease and correct each other warmly, and "
            "nobody is the designated fool. Each turn should answer the one before it: if "
            "Chase gives a number, somebody asks what it means. Never let all four deliver "
            "a paragraph of expertise in turn."),
    },
}


def dialogue_dynamic(show_name: str) -> str:
    """How this cast plays off one another, for the dialogue prompt."""
    for profile in DIALOGUE_SHOWS.values():
        if profile["name"] == show_name:
            return profile.get("dynamic", "")
    return ""


def dialogue_hosts(host_id: str) -> list[Host] | None:
    """The two presenters when `host_id` belongs to a dialogue show, else None."""
    show = HOSTS.get(host_id)
    if show is None:
        return None
    for profile in DIALOGUE_SHOWS.values():
        if host_id in profile["hosts"] and show.show == profile["name"]:
            return [HOSTS[member] for member in profile["hosts"]]
    return None


def writing_guide(host_id: str) -> str:
    return HOSTS[host_id].writing_guide()
