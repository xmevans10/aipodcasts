"""Automated verification gate: the machine that replaces a human reviewer.

The pipeline could not publish without `approve --reviewer`, so autonomy stopped
there. This module decides, without a person, whether a draft is safe to publish.

Two independent layers:

1. Deterministic checks that always run and cannot be talked out of:
   - every claim quote is verbatim in the source (provenance)
   - every hard number in the script appears in the evidence packet (numeric fidelity)
   - the draft is structurally valid and the evidence packet is the one used

2. Typed decisions (Jev-style): state -> one question with a fixed answer set ->
   answer plus confidence. Used for the judgements a regex cannot make:
   - is each claim entailed by its quoted evidence?
   - does the evidence report an original finding rather than commentary/policy?
   - does the script avoid overstating the evidence?

`decider()` selects a backend: Jev (TypeSafe System One) when TYPESAFE_AI_API_KEY is
set, else DeepSeek, else deterministic only. Any failure to reach a backend does not
auto-approve: the story abstains. Abstaining is a successful outcome for an
autonomous grader.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from provenance import provenance_text, quotes_in_source

ENTAIL_THRESHOLD = 0.80
PRIMARY_THRESHOLD = 0.50
OVERSTATE_THRESHOLD = 0.60
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass
class TypedQuestion:
    id: str
    kind: str  # boolean | choice | score
    instructions: str
    criteria: object = None


@dataclass
class Decision:
    kind: str
    answer: object = None
    probability: float | None = None  # for boolean: probability the answer is True


class Decider:
    name = "base"

    def ask(self, questions: list[TypedQuestion], state: dict) -> dict[str, Decision]:
        raise NotImplementedError


class DeterministicDecider(Decider):
    """No model. Serves only so the interface is total; typed questions are skipped."""

    name = "deterministic"

    def ask(self, questions, state):
        return {}


class OpenAICompatDecider(Decider):
    """Typed questions over an OpenAI-compatible chat endpoint (DeepSeek, gateway)."""

    def __init__(self, base_url: str, api_key: str, model: str, name: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = name

    def ask(self, questions, state):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content":
                 "You answer typed decision questions. Return only JSON: an object keyed by "
                 "question id, each value {\"type\":\"boolean\",\"probability\":0..1} or "
                 "{\"type\":\"choice\",\"choice\":str} or {\"type\":\"score\",\"score\":0..1}. "
                 "Probability is your confidence the statement is true."},
                {"role": "user", "content": json.dumps({
                    "state": state,
                    "questions": [{"id": q.id, "type": q.kind, "instructions": q.instructions,
                                   "criteria": q.criteria} for q in questions]})},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        request = urllib.request.Request(
            self.base_url + "/chat/completions", data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content = json.loads(response.read())["choices"][0]["message"]["content"]
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError,
                TimeoutError) as error:
            raise RuntimeError(f"{self.name} unavailable: {type(error).__name__}") from error
        raw = json.loads(content)
        decisions: dict[str, Decision] = {}
        for question in questions:
            value = raw.get(question.id)
            if not isinstance(value, dict):
                continue
            if value.get("type") == "boolean" and isinstance(value.get("probability"), (int, float)):
                decisions[question.id] = Decision("boolean", bool(value.get("answer", value["probability"] >= 0.5)),
                                                  float(value["probability"]))
            elif value.get("type") == "choice" and isinstance(value.get("choice"), str):
                decisions[question.id] = Decision("choice", value["choice"])
            elif value.get("type") == "score" and isinstance(value.get("score"), (int, float)):
                decisions[question.id] = Decision("score", float(value["score"]))
        return decisions


class JevDecider(Decider):
    """TypeSafe's Jev via the System One API.

    POST {base}/systemone with {model, state, questions}. Boolean questions are sent
    as type 'noul' and answered with a probability; choice/score come back with a
    value and confidence. Verified against @ai-sdk/typesafe-ai 3.0.4.
    """

    name = "jev"

    def __init__(self, api_key: str, base_url: str = "https://api.typesafe.ai/v1",
                 model: str = "jev-latest", transport=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.transport = transport

    @staticmethod
    def _question(question: TypedQuestion) -> dict:
        if question.kind == "boolean":  # Jev calls booleans "noul"
            return {"type": "noul", "instructions": question.instructions}
        return {"type": question.kind, "instructions": question.instructions, "criteria": question.criteria}

    def ask(self, questions, state):
        body = {"model": self.model, "state": state,
                "questions": {q.id: self._question(q) for q in questions}}
        data = self._post(body)
        answers = data.get("answers") or {}
        decisions: dict[str, Decision] = {}
        for question in questions:
            answer = answers.get(question.id)
            if not isinstance(answer, dict):
                continue
            if answer.get("type") == "noul" and isinstance(answer.get("noul"), (int, float)):
                probability = float(answer["noul"])
                decisions[question.id] = Decision("boolean", probability >= 0.5, probability)
            elif answer.get("type") == "choice" and isinstance(answer.get("choice"), str):
                decisions[question.id] = Decision("choice", answer["choice"])
            elif answer.get("type") == "score" and isinstance(answer.get("score"), (int, float)):
                decisions[question.id] = Decision("score", float(answer["score"]))
        return decisions

    def _post(self, body):
        if self.transport is not None:
            return self.transport(body)
        request = urllib.request.Request(
            self.base_url + "/systemone", data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read())
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError,
                TimeoutError) as error:
            raise RuntimeError(f"jev unavailable: {type(error).__name__}") from error


def decider(mode: str = "auto") -> Decider:
    if mode == "deterministic":
        return DeterministicDecider()
    jev_key = os.environ.get("TYPESAFE_AI_API_KEY") or os.environ.get("JEV_API_KEY")
    if mode in ("auto", "jev") and jev_key:
        return JevDecider(jev_key, os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1"),
                          os.environ.get("JEV_MODEL", "jev-latest"))
    if mode == "jev":
        return DeterministicDecider()  # asked for Jev but no key: abstain rather than guess
    deepseek = os.environ.get("DEEPSEEK_API_KEY")
    if mode in ("auto", "deepseek") and deepseek:
        return OpenAICompatDecider("https://api.deepseek.com", deepseek,
                                   os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"), "deepseek")
    return DeterministicDecider()


def hard_numbers(text: str) -> set[str]:
    """Numbers worth checking: 2+ digits or a decimal. Single digits are prose, not data."""
    found = set()
    for match in NUMBER.findall(text or ""):
        token = match.replace(",", "")
        if len(token.replace(".", "")) >= 2:
            found.add(token)
    return found


def numeric_fidelity(draft_text: str, evidence: str) -> list[str]:
    evidence_numbers = hard_numbers(evidence)
    return sorted(number for number in hard_numbers(draft_text) if number not in evidence_numbers)


def _text_of(draft: dict) -> str:
    if "turns" in draft:  # dialogue drafts
        return " ".join(turn.get("text", "") for turn in draft.get("turns") or [])
    return " ".join(str(draft.get(field, "")) for field in ("title", "dek", "body", "caveat"))


def verify_draft(draft: dict, source: dict, packet: dict, decider_: Decider) -> dict:
    failures: list[str] = []
    notes: dict = {}

    # 1. deterministic
    normalized = provenance_text(source.get("text", ""))
    claims = draft.get("claims") or []
    missing_quotes = [c.get("claim", "")[:60] for c in claims
                      if not quotes_in_source(c.get("quote", ""), normalized)]
    if missing_quotes:
        failures.append(f"quote_not_in_source: {missing_quotes}")
    from evidence import evidence_text
    missing_numbers = numeric_fidelity(_text_of(draft), evidence_text(packet))
    if missing_numbers:
        failures.append(f"numbers_not_in_evidence: {missing_numbers}")
    notes["claims_checked"] = len(claims)
    notes["missing_numbers"] = missing_numbers

    # 2. typed decisions (abstain if the backend cannot be reached)
    decisions: dict[str, Decision] = {}
    if not isinstance(decider_, DeterministicDecider) and claims:
        questions = [TypedQuestion(f"entail_{i}", "boolean",
                     "The claim is fully supported by the quoted evidence. "
                     f"Claim: {c.get('claim','')} Evidence: {c.get('quote','')}")
                     for i, c in enumerate(claims)]
        questions.append(TypedQuestion("primary_finding", "boolean",
            "The 'evidence' field reports the authors' own original observation or "
            "measurement, rather than commentary, policy, opinion or a review."))
        questions.append(TypedQuestion("no_overstatement", "boolean",
            "The 'script' field stays within the 'evidence' field and does not overstate it."))
        try:
            decisions = decider_.ask(questions, {
                "script": _text_of(draft),
                "evidence": evidence_text(packet)[:6000],
            })
        except RuntimeError as error:
            failures.append(f"verifier_unavailable: {error}")
        for question in questions:
            decision = decisions.get(question.id)
            if decision is None:
                failures.append(f"no_decision: {question.id}")
                continue
            probability = decision.probability if decision.probability is not None else 0.0
            notes[question.id] = probability
            threshold = {"entail": ENTAIL_THRESHOLD, "primary_finding": PRIMARY_THRESHOLD,
                         "no_overstatement": OVERSTATE_THRESHOLD}
            key = "entail" if question.id.startswith("entail_") else question.id
            if probability < threshold[key]:
                failures.append(f"{question.id}={probability:.2f} below {threshold[key]}")

    report = {
        "pass": not failures,
        "failures": failures,
        "backend": decider_.name,
        "evidence_sha256": hashlib.sha256(evidence_text(packet).encode()).hexdigest()[:16],
        "notes": notes,
        "reviewer": "auto-verifier:" + decider_.name,
    }
    return report


def verify_story(db, story_id: str, decider_mode: str = "auto") -> dict:
    record = db.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    if record is None:
        raise ValueError("Unknown story")
    if not record["draft"]:
        raise ValueError("Story has no draft to verify")
    draft = json.loads(record["draft"])
    source = json.loads(record["source"])
    if record["draft_input"]:
        packet = json.loads(record["draft_input"])
    else:
        from evidence import build_packet
        packet = build_packet(source, int(os.environ.get("LILT_MAX_SOURCE_CHARS", "18000")))
    return verify_draft(draft, source, packet, decider(decider_mode))
