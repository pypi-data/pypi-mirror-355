#!/usr/bin/env python3
import click
import sys
import shlex
import subprocess as sp
from console import  fg, bg

import os
import glob

# ================================================================================
#   constructs the CMD
# --------------------------------------------------------------------------------
def mpvsub( subtitles, audios, video_file):
    opt = ""
    optau = ""
    if subtitles is not None and len(subtitles) > 0:
        for i in subtitles:
            opt = f"{opt} --sub-file={i} "
    if audios is not None and len(audios) > 0:
        for i in audios:
            optau = f"{optau} --audio-file={i} "
    CMD = f"mpv --no-sub-auto {opt} {optau} {video_file}"
    return CMD
    # mpv "${sub_options[@]}" --no-sub-auto  --sid=1 "$video_file"





# ================================================================================
# RUNS
# --------------------------------------------------------------------------------
def runcmd(CMD):
    #CMD = f"mpv {general_filename} --sub-file={another_filename}"
    args = shlex.split(CMD)
    #print(args)
    #print()
    sp.run(args)

def confirm_selection(audio, subtitle):
    print()
    print(f"Suggested    Audio: {audio}")
    print(f"Suggested Subtitle: {subtitle}")
    print()
    print("Press Enter to confirm, any other key to cancel.")
    choice = input()
    return choice == ''

def get_dirname(infile):
    dirname = ""
    if os.path.dirname(infile) != "":
        dirname = os.path.splitext(os.path.dirname(infile))[0]
        dirname = f"{dirname}/"
    else:
        dirname = ""
    return dirname


def find_best_match(video_file):
    video_base = os.path.splitext(video_file)[0].lower()
    dirname = get_dirname(video_file)
    print(f"i... searching @ {dirname}* ")

    if dirname != "":
        cwd = os.getcwd()
        os.chdir(dirname)
    files = glob.glob("*")
    if dirname != "":
        files = [f"{dirname}{x}" for x in files]
        os.chdir(cwd)

    print(f"i... total files: {len(files)}")
    #print(f"i... total files: {files}")
    audio_exts = ('.mp3', '.opus', '.m4a')
    subtitle_ext = '.srt'

    files = [ x for x in files if len(os.path.splitext(x)[-1]) > 3]
    files = [ x for x in files if (os.path.splitext(x)[-1].lower() in audio_exts) or (os.path.splitext(x)[-1].lower()  in subtitle_ext) ]
    print(f"i... Files:{files}")

    audio_file = None
    subtitle_file = None
    best_audio_score = -1
    best_subtitle_score = -1

    def match_score(name1, name2):
        score = 0
        for c1, c2 in zip(name1, name2):
            if c1 == c2:
                score += 1
            else:
                break
        return score

    for f in files:
        f_lower = f.lower()
        base = os.path.splitext(f_lower)[0]
        score = match_score(video_base, base)
        if score > 0:
            if f_lower.endswith(audio_exts) and score > best_audio_score:
                audio_file = f
                best_audio_score = score
            elif f_lower.endswith(subtitle_ext) and score > best_subtitle_score:
                subtitle_file = f
                best_subtitle_score = score

    return audio_file, subtitle_file


@click.command()
@click.argument('video_file', default=None)
def main( video_file ):
    """
    joins all srt subtitles (local and remote folder too) and
    runs mpv
    """
    if video_file is None:
        print("X... give me video file")
        sys.exit(0)
    fcomment = 6

    fname = os.path.splitext(video_file)[0]


    audio, subtitle = find_best_match(video_file)
    #print("Audio:", audio)
    #print("Subtitle:", subtitle)

    if confirm_selection(audio, subtitle):
        print("Confirmed.")
    else:
        print("Cancelled.")
        sys.exit(0)
    cmd = mpvsub([subtitle], [audio], video_file)
    print(cmd)
    runcmd(cmd)


if __name__ == "__main__":
    main()
