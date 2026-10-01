"""Two-pass podcast loudness mastering and final AAC measurement (FFmpeg)."""
import json
import math
import re
import subprocess
from pathlib import Path


def measure(path: Path) -> dict:
    result = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path),
                             '-af', 'loudnorm=I=-16:TP=-2:LRA=11:print_format=json',
                             '-f', 'null', '-'], capture_output=True, text=True, check=True)
    blocks = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, re.DOTALL)
    if not blocks:
        raise ValueError('Missing loudness measurement')
    data = json.loads(blocks[-1])
    for key in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset'):
        if not math.isfinite(float(data[key])):
            raise ValueError('Silent or invalid master')
    return data


def master(path: Path) -> None:
    levels = measure(path)
    settings = ('loudnorm=I=-16:TP=-2:LRA=11:linear=true:'
                f'measured_I={levels["input_i"]}:measured_TP={levels["input_tp"]}:'
                f'measured_LRA={levels["input_lra"]}:measured_thresh={levels["input_thresh"]}:'
                f'offset={levels["target_offset"]}')
    output = path.with_name(path.stem + '-master.wav')
    try:
        subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(path),
                        '-af', settings, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le',
                        str(output)], check=True, capture_output=True)
        output.replace(path)
    finally:
        output.unlink(missing_ok=True)


def validate_encoded(path: Path) -> dict:
    levels = measure(path)
    loudness, peak = float(levels['input_i']), float(levels['input_tp'])
    if not -17 <= loudness <= -15 or peak > -1:
        raise ValueError(f'Encoded audio fails podcast levels: {loudness} LUFS, {peak} dBTP')
    return {'integratedLUFS': loudness, 'truePeakDBTP': peak,
            'loudnessRangeLU': float(levels['input_lra']), 'targetLUFS': -16,
            'truePeakCeilingDBTP': -1}
