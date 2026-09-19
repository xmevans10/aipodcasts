#!/usr/bin/env python3
"""Generate a Zwicky voice sample with Chatterbox (open source, MIT). No API key.

Chatterbox is a zero-shot TTS model; with no reference clip it uses its built-in
default voice. Install once with `pip install chatterbox-tts`, then run:

    python tools/tts/chatterbox_generate.py --out tts-out
    python tools/tts/chatterbox_generate.py --file script.txt --max-words 40

The bundled Perth watermarker fails to import in some environments and exposes
None; we substitute its dummy implementation so generation can proceed (this
means the output is not watermarked).
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--file", help="read the script from a file instead")
    parser.add_argument("--out", default="tts-out")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--exaggeration", type=float, default=0.5)
    parser.add_argument("--cfg-weight", type=float, default=0.5)
    parser.add_argument("--max-words", type=int, default=0, help="truncate to N words (0 = all)")
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
    from chatterbox.tts import ChatterboxTTS

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device={device} words={len(text.split())}", flush=True)

    t0 = time.time()
    model = ChatterboxTTS.from_pretrained(device=device)
    print(f"load {time.time() - t0:.1f}s", flush=True)
    t0 = time.time()
    wav = model.generate(text, exaggeration=args.exaggeration, cfg_weight=args.cfg_weight)
    print(f"generate {time.time() - t0:.1f}s", flush=True)

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, args.name + ".wav")
    ta.save(path, wav, model.sr)
    print("saved", path, "sr", model.sr, flush=True)


if __name__ == "__main__":
    main()
