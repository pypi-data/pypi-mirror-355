import argparse
import os
from typing import *

from pydub import AudioSegment, silence

__all__ = ["main", "run"]

AudioSegment.ffprobe = "/opt/homebrew/bin/ffprobe"
AudioSegment.converter = "/opt/homebrew/bin/ffmpeg"


def expandPath(path):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def main(args: Optional[Iterable] = None) -> None:
    parser = argparse.ArgumentParser(
        fromfile_prefix_chars="@",
    )
    parser.add_argument("infile")
    parser.add_argument("outfile")
    parser.add_argument("--factor", type=float)
    parser.add_argument("--length", type=float)
    parser.add_argument("--threshold", type=int)
    ns = parser.parse_args(args=args)
    kwargs = vars(ns)
    run(**kwargs)


def run(
    infile,
    outfile,
    *,
    factor: float = 2.0,
    length: float = 1.0,
    threshold: int = -50,
) -> None:

    infile = expandPath(infile)
    outfile = expandPath(outfile)
    defaultgap = round(length * 1000)

    original = AudioSegment.from_file(infile)
    silentranges = silence.detect_silence(
        original,
        min_silence_len=length,
        silence_thresh=threshold,
    )
    result = calc(
        factor=factor,
        defaultgap=defaultgap,
        original=original,
        silentranges=silentranges,
    )
    result.export(outfile)


def calc(
    *,
    defaultgap,
    factor,
    original,
    silentranges,
):
    cuts = list()
    for start, end in silentranges:
        cuts += [start, end]
    if len(cuts) == 0:
        return original
    if cuts[0]:
        cuts.insert(0, 0)
    else:
        cuts.pop(0)
    if cuts[-1] < len(original):
        cuts.append(len(original))
    else:
        cuts.pop()
    ans = AudioSegment.empty()
    lastend = None
    while cuts:
        start = cuts.pop(0)
        end = cuts.pop(0)
        if lastend is None:
            gap = defaultgap
        else:
            gap = round((start - lastend) * factor)
        ans += AudioSegment.silent(duration=gap)
        ans += original[start:end]
        lastend = end
    ans += AudioSegment.silent(duration=defaultgap)
    return ans
