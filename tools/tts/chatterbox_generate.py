#!/usr/bin/env python3
"""Generate Zwicky voice samples with Chatterbox (open source, MIT). No API key.

Two expressivity mechanisms, mirroring how we direct narration:

  base  (500M)  global per-call emotion: --exaggeration (0.0-1.0+, higher = more
                dramatic) and --cfg-weight (pacing; ~0.3 for slower, deliberate).
  turbo (350M)  inline paralinguistic tags in --text, e.g. [chuckle], [laugh],
                [cough]. Note: turbo/nano *ignore* exaggeration and cfg_weight
                (the library logs a warning); emotion comes from tags and pacing.
  nano  (110M)  same as turbo but smaller/faster (CPU-friendly).

With no reference clip, base and turbo use their built-in default voice.
Python 3.11; `pip install chatterbox-tts`. The bundled Perth watermarker fails
to import in some environments and exposes None, so we substitute its dummy.

Promoted standard: base with temperature 0.65, top_p 0.9, min_p 0.02 (exaggeration
0.5, cfg_weight 0.5). It won the tts-lab sampling suite by listening; the objective
metrics were flat because every take was intelligible. Override any flag to compare.
"""
from __future__ import annotations
import argparse
import os
import time

DEFAULT_TEXT = (
    "Every clear night, the sky answers a question we forgot to ask. "
    "If the universe were infinite, unchanging, and forever old, every direction you looked "
    "would eventually land on a star. The whole sky would glow. It does not. "
    "The darkness is not empty space. It is a measurement: the universe has an age, and light "
    "has a speed, and both of them are written in the gaps between the stars. "
    "Look up tonight. The dark parts are data."
)


def patch_watermarker() -> None:
    import perth
    if getattr(perth, "PerthImplicitWatermarker", None) is None:
        perth.PerthImplicitWatermarker = perth.DummyWatermarker


def load(model_name: str, device: str):
    if model_name == "base":
        from chatterbox.tts import ChatterboxTTS
        return ChatterboxTTS.from_pretrained(device=device)
    import inspect
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    kwargs = {"device": device}
    supports_nano = "nano" in inspect.signature(ChatterboxTurboTTS.from_pretrained).parameters
    if model_name == "nano" and not supports_nano:
        raise SystemExit(
            "The installed chatterbox-tts has no Nano support (added after 0.1.7). "
            "Install from git (pip install git+https://github.com/resemble-ai/chatterbox.git) "
            "or use --model turbo."
        )
    if supports_nano:
        kwargs["nano"] = model_name == "nano"
    return ChatterboxTurboTTS.from_pretrained(**kwargs)


def synthesize(model, model_name: str, text: str, args, device: str):
    """Build kwargs from only the parameters this model's generate() actually accepts.

    Base has no top_k or norm_loudness; turbo/nano ignore exaggeration, cfg_weight and
    min_p. Filtering by signature keeps one CLI honest across all three checkpoints.
    """
    import inspect
    import torch

    if args.seed is not None:
        torch.manual_seed(args.seed)
    kwargs = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "min_p": args.min_p,
        "repetition_penalty": args.repetition_penalty,
        "norm_loudness": args.norm_loudness,
    }
    if model_name == "base":  # turbo/nano ignore these and log a warning
        kwargs["exaggeration"] = args.exaggeration
        kwargs["cfg_weight"] = args.cfg_weight
    params = inspect.signature(model.generate).parameters

    if model_name != "base" and getattr(model, "conds", None) is None:
        # No built-in voice: synthesize a reference with the base model, then clone it.
        import torchaudio as ta
        base = load("base", device)
        os.makedirs(args.out, exist_ok=True)
        ref = os.path.join(args.out, "_reference.wav")
        ta.save(ref, base.generate("This is a reference voice for the Zwicky preview. " * 2), base.sr)
        kwargs["audio_prompt_path"] = args.audio_prompt or ref
    elif args.audio_prompt:
        kwargs["audio_prompt_path"] = args.audio_prompt

    return model.generate(text, **{k: v for k, v in kwargs.items() if k in params and v is not None})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--file", help="read the script from a file instead")
    parser.add_argument("--out", default="tts-out")
    parser.add_argument("--model", default="base", choices=["base", "turbo", "nano"])
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--exaggeration", type=float, default=0.5)
    parser.add_argument("--cfg-weight", type=float, default=0.5)
    # Promoted sampling standard (won the tts-lab sampling suite by listening):
    # base, temperature 0.65, top_p 0.9, min_p 0.02. See experiments/tts_lab.
    parser.add_argument("--temperature", type=float, default=0.65)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--top-k", type=float, default=None)
    parser.add_argument("--min-p", type=float, default=0.02)
    parser.add_argument("--repetition-penalty", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--norm-loudness", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--audio-prompt", default="", help="reference clip to clone (base/turbo/nano)")
    parser.add_argument("--max-words", type=int, default=0)
    parser.add_argument("--name", default="chatterbox")
    args = parser.parse_args()

    text = args.text
    if args.file:
        text = open(args.file, encoding="utf-8").read().strip()
    text = text or DEFAULT_TEXT
    if args.max_words:
        text = " ".join(text.split()[:args.max_words])

    patch_watermarker()
    import torch
    import torchaudio as ta

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"model={args.model} device={device} words={len(text.split())}", flush=True)

    t0 = time.time()
    model = load(args.model, device)
    print(f"load {time.time() - t0:.1f}s", flush=True)
    t0 = time.time()
    wav = synthesize(model, args.model, text, args, device)
    print(f"generate {time.time() - t0:.1f}s", flush=True)

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, args.name + ".wav")
    ta.save(path, wav, model.sr)
    print("saved", path, "sr", model.sr, flush=True)


if __name__ == "__main__":
    main()
