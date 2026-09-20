#!/usr/bin/env python3
"""Chatterbox TTS research lab: run a blinded-by-construction matrix on a free CI runner.

The harness loads each model once, renders a controlled matrix of short beats, writes
the wavs plus a `metrics.json`, and prints a compact table to stdout so results can be
read straight from the Actions log (audio goes in the artifact for human listening).

Suites:
  sampling   base model, one trap line, sweep temperature/top_p/min_p/repetition_penalty
             and exaggeration/cfg_weight across seeds. Tests hypothesis 1 and 3.
  models     base vs turbo vs nano on identical text: quality/WER + CPU seconds.
  tags       probe candidate Turbo/Nano paralinguistic tags against a no-tag control.
  beats      per-beat direction (port of produce.py) vs one global setting, spliced.
  reference  condition on synthetic references of different delivery; norm_loudness.
  chunk      one long call vs sentence chunks; report truncation/hallucination.

No paid API, no keys. `python experiments/tts_lab/lab.py --suite sampling --out runs/sampling`
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys

sys.path.insert(0, str(HERE))
from metrics import Asr, analyze_audio  # noqa: E402

# A line chosen to tempt continuations: numbers, a contrast, and a clean stop.
TRAP = ("The first estimate was four hundred million years, the second was closer to "
        "two point one billion, and neither number is the interesting part.")

# Two-host flavour beats for the per-beat suite (hosts: a calm methodologist, a warm explainer).
BEATS = [
    {"speaker": "ines", "text": "Here is the number that started the argument: one point two billion years.",
     "params": {"exaggeration": 0.45, "cfg_weight": 0.3, "temperature": 0.6, "top_p": 0.9}},
    {"speaker": "dev", "text": "Which sounds enormous, until you ask what it is actually measuring.",
     "params": {"exaggeration": 0.8, "cfg_weight": 0.3, "temperature": 0.8, "top_p": 0.95}},
    {"speaker": "ines", "text": "That is the whole problem. The instrument was calibrated on a different rock.",
     "params": {"exaggeration": 0.45, "cfg_weight": 0.3, "temperature": 0.6, "top_p": 0.9}},
    {"speaker": "dev", "text": "So the date was never wrong, the recipe was just borrowed from somewhere else.",
     "params": {"exaggeration": 0.75, "cfg_weight": 0.35, "temperature": 0.75, "top_p": 0.95}},
]
GLOBAL = {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "top_p": 1.0}

TAG_CARRIER = ("I checked the numbers twice [TAG] and they still do not add up.")
TAG_CANDIDATES = [
    "chuckle", "laugh", "laughs", "cough", "sigh", "gasp", "whisper", "whispers",
    "clears throat", "sniff", "sniffles", "groan", "scoff", "giggle", "hum",
    "breath", "inhale", "exhale", "yawn", "sneeze",
]

CHUNK_TEXT = (
    "The oldest rocks on the ocean floor are younger than the oldest rocks on the "
    "continents, and that asymmetry is the clue. New crust forms at the ridges, "
    "spreads outward, and is recycled at the trenches, so the seafloor is a moving "
    "tape that never gets older than about two hundred million years. The continents "
    "ride above that process, which is why they can preserve evidence from billions of "
    "years ago. The measurement is not a single date. It is a pattern of ages that "
    "only makes sense if the floor is being made and destroyed at the same time."
)


def patch_watermarker() -> None:
    import perth

    if getattr(perth, "PerthImplicitWatermarker", None) is None:
        perth.PerthImplicitWatermarker = perth.DummyWatermarker


def load_nano(device: str):
    """Load Chatterbox-Nano on the pip 0.1.7 API by porting master's nano path.

    The released wheel has no `nano` flag and no GPT2_small config, so we inject the
    config and replicate `from_local(nano=True)` from resemble-ai/chatterbox master.
    """
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    from chatterbox.models.s3gen import S3Gen
    from chatterbox.models.t3 import T3
    from chatterbox.models.t3.llama_configs import LLAMA_CONFIGS
    from chatterbox.models.t3.modules.t3_config import T3Config
    from chatterbox.models.voice_encoder import VoiceEncoder
    from chatterbox.tts_turbo import ChatterboxTurboTTS, Conditionals

    LLAMA_CONFIGS.setdefault("GPT2_small", {
        "activation_function": "gelu_new", "architectures": ["GPT2LMHeadModel"],
        "attn_pdrop": 0.1, "bos_token_id": 50256, "embd_pdrop": 0.1, "eos_token_id": 50256,
        "initializer_range": 0.02, "layer_norm_epsilon": 1e-05, "model_type": "gpt2",
        "n_ctx": 8196, "n_embd": 768, "hidden_size": 768, "n_head": 12, "n_layer": 12,
        "n_positions": 8196, "n_special": 0, "predict_special_tokens": True,
        "resid_pdrop": 0.1, "summary_activation": None, "summary_first_dropout": 0.1,
        "summary_proj_to_labels": True, "summary_type": "cls_index",
        "summary_use_proj": True, "vocab_size": 50276,
    })

    ckpt = Path(snapshot_download(
        repo_id="ResembleAI/chatterbox-nano",
        allow_patterns=["*.safetensors", "*.json", "*.txt", "*.pt", "*.model"],
    ))
    map_location = "cpu" if device in ("cpu", "mps") else None
    ve = VoiceEncoder()
    ve.load_state_dict(load_file(ckpt / "ve.safetensors"))
    ve.to(device).eval()
    hp = T3Config(text_tokens_dict_size=50276)
    hp.llama_config_name = "GPT2_small"
    hp.speech_tokens_dict_size = 6563
    hp.input_pos_emb = None
    hp.speech_cond_prompt_len = 375
    hp.use_perceiver_resampler = False
    hp.emotion_adv = False
    t3 = T3(hp)
    state = load_file(ckpt / "t3_nano_v1.safetensors")
    if "model" in state:
        state = state["model"][0]
    t3.load_state_dict(state)
    del t3.tfmr.wte
    t3.to(device).eval()
    s3gen = S3Gen(meanflow=True)
    s3gen.load_state_dict(load_file(ckpt / "s3gen_meanflow.safetensors"), strict=True)
    s3gen.to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(ckpt)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    conds = None
    if (ckpt / "conds.pt").exists():
        conds = Conditionals.load(ckpt / "conds.pt", map_location=map_location).to(device)
    return ChatterboxTurboTTS(t3, s3gen, ve, tokenizer, device, conds=conds)


def load_model(name: str, device: str):
    if name == "base":
        from chatterbox.tts import ChatterboxTTS

        return ChatterboxTTS.from_pretrained(device=device)
    if name == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        return ChatterboxTurboTTS.from_pretrained(device=device)
    if name == "nano":
        return load_nano(device)
    raise ValueError(name)


# Which knobs each model's generate() actually accepts (verified against pip 0.1.7).
ALLOWED = {
    "base": ("exaggeration", "cfg_weight", "temperature", "top_p", "min_p", "repetition_penalty"),
    "turbo": ("temperature", "top_p", "top_k", "repetition_penalty", "norm_loudness"),
    "nano": ("temperature", "top_p", "top_k", "repetition_penalty", "norm_loudness"),
}


def generate(model, name: str, text: str, params: dict, seed: int, out: Path,
             audio_prompt_path: str | None = None, extra: dict | None = None) -> float:
    import soundfile as sf
    import torch

    torch.manual_seed(seed)
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:  # noqa: BLE001
        pass
    kwargs = {k: v for k, v in params.items() if k in ALLOWED[name]}
    if audio_prompt_path is not None:
        kwargs["audio_prompt_path"] = audio_prompt_path
    if extra:
        kwargs.update(extra)
    out.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    wav = model.generate(text, **kwargs)
    elapsed = time.time() - start
    sf.write(str(out), wav.squeeze(0).numpy(), model.sr)
    return elapsed


def load_asr(args):
    if args.no_asr:
        return None
    asr = Asr(size=args.asr_model)
    asr._load()
    if asr._model is None:
        print("ASR unavailable:", asr.error, flush=True)
        return None
    return asr


class Models:
    """Lazy model cache so a suite loads each checkpoint at most once."""

    def __init__(self, device: str):
        self.device = device
        self.cache: dict[str, tuple] = {}

    def get(self, name: str):
        if name not in self.cache:
            start = time.time()
            model = load_model(name, self.device)
            self.cache[name] = (model, round(time.time() - start, 1))
            print(f"loaded {name} in {self.cache[name][1]}s", flush=True)
        return self.cache[name][0]


def _record(out_root: Path, suite: str, record: dict) -> None:
    path = out_root / suite / "metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else []
    data.append(record)
    path.write_text(json.dumps(data, indent=1))


def _fmt(record: dict) -> str:
    def g(key, default="-"):
        value = record.get(key)
        return default if value is None else value

    return (f"{record.get('label', '?'):<34} dur={g('duration_s'):>6} "
            f"wer={g('wer'):>6} match={g('match_ratio'):>5} ins={g('insertions'):>2} "
            f"sil={g('silence_ratio'):>5} f0sd={g('f0_std_semitones'):>5} "
            f"gen={g('gen_s'):>5}s")


# ---------------------------------------------------------------- suites

def suite_sampling(models, out, args, asr):
    text = args.text or TRAP
    conditions = {
        "default": {},
        "t0.5": {"temperature": 0.5},
        "t0.5_rp1.5": {"temperature": 0.5, "repetition_penalty": 1.5},
        "t0.65": {"temperature": 0.65},
        "t0.8_topp0.9": {"temperature": 0.8, "top_p": 0.9},
        "t0.65_topp0.9_minp0.02": {"temperature": 0.65, "top_p": 0.9, "min_p": 0.02},
        "minp0.0": {"min_p": 0.0},
        "cfg0.3": {"cfg_weight": 0.3},
        "ex0.7_cfg0.3": {"exaggeration": 0.7, "cfg_weight": 0.3},
        "t0.65_cfg0.3_rp1.3": {"temperature": 0.65, "cfg_weight": 0.3, "repetition_penalty": 1.3},
    }
    model = models.get("base")
    for condition, params in conditions.items():
        for seed in range(args.seeds):
            label = f"{condition}_s{seed}"
            path = out / "sampling" / f"{label}.wav"
            config = {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "top_p": 1.0,
                      "min_p": 0.05, "repetition_penalty": 1.2, **params}
            gen_s = generate(model, "base", text, config, seed, path)
            rec = {"suite": "sampling", "label": label, "seed": seed, "config": config,
                   "model": "base", "gen_s": round(gen_s, 2)}
            rec.update(analyze_audio(str(path), text, asr))
            _record(out, "", rec)
            print(_fmt(rec), flush=True)


def suite_models(models, out, args, asr):
    text = args.text or TRAP
    for name in ("base", "turbo", "nano"):
        try:
            model = models.get(name)
        except Exception as error:  # noqa: BLE001
            print(f"model {name} unavailable: {error}", flush=True)
            continue
        for seed in range(args.seeds):
            label = f"{name}_s{seed}"
            path = out / "models" / f"{label}.wav"
            gen_s = generate(model, name, text, {}, seed, path)
            rec = {"suite": "models", "label": label, "seed": seed, "model": name,
                   "config": {k: "default" for k in ALLOWED[name]},
                   "load_s": models.cache[name][1], "gen_s": round(gen_s, 2)}
            rec.update(analyze_audio(str(path), text, asr))
            _record(out, "", rec)
            print(_fmt(rec), flush=True)


def suite_tags(models, out, args, asr):
    models_to_probe = [m for m in ("turbo", "nano") if m in (args.tag_models or "turbo,nano").split(",")]
    for name in models_to_probe:
        try:
            model = models.get(name)
        except Exception as error:  # noqa: BLE001
            print(f"model {name} unavailable: {error}", flush=True)
            continue
        control_path = out / "tags" / f"{name}_control.wav"
        gen_s = generate(model, name, TAG_CARRIER.replace(" [TAG]", ""), {}, 0, control_path)
        control = analyze_audio(str(control_path), TAG_CARRIER.replace(" [TAG]", ""), asr)
        control_rec = {"suite": "tags", "label": f"{name}_CONTROL", "tag": None, "model": name,
                       "gen_s": round(gen_s, 2), **control}
        _record(out, "", control_rec)
        print(_fmt(control_rec), flush=True)
        control_dur = control["duration_s"]
        for tag in TAG_CANDIDATES:
            text = TAG_CARRIER.replace("[TAG]", f"[{tag}]")
            label = f"{name}_{tag.replace(' ', '_')}"
            path = out / "tags" / f"{label}.wav"
            try:
                gen_s = generate(model, name, text, {}, 0, path)
            except Exception as error:  # noqa: BLE001
                rec = {"suite": "tags", "label": label, "tag": tag, "model": name,
                       "verdict": "ERROR", "error": f"{type(error).__name__}: {error}"}
                _record(out, "", rec)
                print(f"{label:<34} ERROR {error}", flush=True)
                continue
            rec = {"suite": "tags", "label": label, "tag": tag, "model": name,
                   "gen_s": round(gen_s, 2)}
            rec.update(analyze_audio(str(path), text, asr))
            transcript = (rec.get("transcript") or "").lower()
            tag_words = tag.lower().split()
            literal = all(w in transcript for w in tag_words)
            delta = round(rec["duration_s"] - control_dur, 3)
            rec["duration_delta_vs_control"] = delta
            if literal:
                rec["verdict"] = "LITERALIZED (spoken as words) or ignored"
            elif abs(delta) > 0.12:
                rec["verdict"] = "AUDIBLE_EFFECT_candidate (duration shift, no literal tag)"
            else:
                rec["verdict"] = "NO_DETECTABLE_EFFECT"
            _record(out, "", rec)
            print(_fmt(rec), f"tag_delta={delta:+.2f} {rec['verdict']}", flush=True)


def _read_mono(path: Path):
    import numpy as np
    import soundfile as sf

    wav, sr = sf.read(str(path), always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    return wav.astype("float32"), sr


def _splice(paths, out: Path, gap_s: float = 0.35):
    import numpy as np
    import soundfile as sf

    gap = None
    sr = 24000
    pieces = []
    for path in paths:
        wav, sr = _read_mono(path)
        pieces.append(wav)
        pieces.append(np.zeros(int(gap_s * sr), dtype="float32"))
    sf.write(str(out), np.concatenate(pieces), sr)


def suite_beats(models, out, args, asr):
    base = (args.text or "").strip()
    script_text = " ".join(b["text"] for b in BEATS)
    model = models.get("base")
    for condition in ("global", "directed"):
        paths = []
        for index, beat in enumerate(BEATS):
            params = GLOBAL if condition == "global" else beat["params"]
            path = out / "beats" / f"{condition}_{index}.wav"
            generate(model, "base", beat["text"], params, index, path)
            paths.append(path)
        mixed = out / "beats" / f"{condition}_spliced.wav"
        _splice(paths, mixed)
        rec = {"suite": "beats", "label": f"beats_{condition}", "model": "base",
               "condition": condition, "beats": len(BEATS)}
        rec.update(analyze_audio(str(mixed), script_text, asr))
        _record(out, "", rec)
        print(_fmt(rec), flush=True)
    if base:
        pass


def suite_reference(models, out, args, asr):
    text = args.text or TRAP
    base = models.get("base")
    refs = {
        "ref_warm_slow": {"exaggeration": 0.35, "cfg_weight": 0.25, "temperature": 0.6, "top_p": 0.9},
        "ref_bright_quick": {"exaggeration": 0.85, "cfg_weight": 0.5, "temperature": 0.9, "top_p": 1.0},
    }
    ref_text = ("Here is a calm reference reading for the voice. It should be long enough, "
                "and it should carry a clear, steady pace without any drama at all.")
    ref_paths = {}
    for label, params in refs.items():
        path = out / "reference" / f"{label}.wav"
        generate(base, "base", ref_text, params, 1, path)
        ref_paths[label] = path
    targets = [("base", "base"), ("turbo", "turbo")]
    for model_name, _ in targets:
        try:
            model = models.get(model_name)
        except Exception as error:  # noqa: BLE001
            print(f"model {model_name} unavailable: {error}", flush=True)
            continue
        # identity: no reference, for comparison
        for ref_label, ref_path in [("no_ref", None)] + list(ref_paths.items()):
            label = f"{model_name}_{ref_label}"
            path = out / "reference" / f"{label}.wav"
            extra = None
            if ref_path is not None and model_name in ("turbo", "nano"):
                for norm in (True, False):
                    norm_label = f"{label}_norm{int(norm)}"
                    norm_path = out / "reference" / f"{norm_label}.wav"
                    generate(model, model_name, text, {}, 0, norm_path,
                             audio_prompt_path=str(ref_path), extra={"norm_loudness": norm})
                    rec = {"suite": "reference", "label": norm_label, "model": model_name,
                           "reference": ref_label, "norm_loudness": norm}
                    rec.update(analyze_audio(str(norm_path), text, asr))
                    _record(out, "", rec)
                    print(_fmt(rec), flush=True)
                continue
            generate(model, model_name, text, {}, 0, path, audio_prompt_path=str(ref_path) if ref_path else None)
            rec = {"suite": "reference", "label": label, "model": model_name,
                   "reference": ref_label}
            rec.update(analyze_audio(str(path), text, asr))
            _record(out, "", rec)
            print(_fmt(rec), flush=True)


def suite_chunk(models, out, args, asr):
    text = args.text or CHUNK_TEXT
    model = models.get("base")
    full = out / "chunk" / "full.wav"
    gen_s = generate(model, "base", text, {}, 0, full)
    rec = {"suite": "chunk", "label": "chunk_full", "model": "base", "gen_s": round(gen_s, 2)}
    rec.update(analyze_audio(str(full), text, asr))
    _record(out, "", rec)
    print(_fmt(rec), flush=True)
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    paths = []
    for index, sentence in enumerate(sentences):
        path = out / "chunk" / f"seg{index}.wav"
        generate(model, "base", sentence + ".", {}, index, path)
        paths.append(path)
    mixed = out / "chunk" / "chunked.wav"
    _splice(paths, mixed, gap_s=0.18)
    rec = {"suite": "chunk", "label": "chunk_sentences", "model": "base", "segments": len(sentences)}
    rec.update(analyze_audio(str(mixed), text, asr))
    _record(out, "", rec)
    print(_fmt(rec), flush=True)


SUITES = {
    "sampling": suite_sampling,
    "models": suite_models,
    "tags": suite_tags,
    "beats": suite_beats,
    "reference": suite_reference,
    "chunk": suite_chunk,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, choices=sorted(SUITES))
    parser.add_argument("--out", default="tts-lab-out")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--text", default="")
    parser.add_argument("--tag-models", default="turbo,nano")
    parser.add_argument("--asr-model", default="base.en")
    parser.add_argument("--no-asr", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    patch_watermarker()
    import torch

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"suite={args.suite} device={device} seeds={args.seeds}", flush=True)

    asr = load_asr(args)
    models = Models(device)
    try:
        SUITES[args.suite](models, out, args, asr)
    finally:
        print("done", flush=True)


if __name__ == "__main__":
    main()
