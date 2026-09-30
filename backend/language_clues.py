"""Compatibility style clues derived from the current host profiles.

Keep experiments and the production writer on one character source. Historical
research notes live in docs/editorial/language-clues.md; they are not a second
set of delivery rules or a quota for jokes, numbers, caveats or metaphors.
"""
from hosts import HOSTS

LANGUAGE_CLUES: dict[str, str] = {
    host_id: (
        f"Keep {host.name}'s stated personality audible through the middle explanation "
        "and the limitations, not just a colourful hook and the sign-off. Speak to one "
        "person beside you. A warm opening glued to a lecture is a failed draft. "
        "Allow a real reaction, preference or self-correction when this finding earns it, "
        "without forcing an emotional beat or joke into every paragraph. "
        f"Cadence example, not evidence or words to copy: {host.sample_line}"
    )
    for host_id, host in HOSTS.items()
}
