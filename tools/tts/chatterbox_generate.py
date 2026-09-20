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
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    return ChatterboxTurboTTS.from_pretrained(device=device, nano=(model_name == "nano"))


def synthesize(model, model_name: str, text: str, args, device: str):
    if model_name == "base":
        return model.generate(text, exaggeration=args.exaggeration, cfg_weight=args.cfg_weight)
    # turbo/nano: tags are inline in `text`; exaggeration/cfg_weight are ignored.
    if getattr(model, "conds", None) is not None:
        return model.generate(text)
    # No built-in voice: synthesize a reference with the base model, then clone it.
    import torchaudio as ta
    base = load("base", device)
    os.makedirs(args.out, exist_ok=True)
    ref = os.path.join(args.out, "_reference.wav")
    ta.save(ref, base.generate("This is a reference voice for the Zwicky preview. " * 2), base.sr)
    return model.generate(text, audio_prompt_path=ref)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--file", help="read the script from a file instead")
    parser.add_argument("--out", default="tts-out")
    parser.add_argument("--model", default="base", choices=["base", "turbo", "nano"])
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--exaggeration", type=float, default=0.5)
    parser.add_argument("--cfg-weight", type=float, default=0.5)
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
