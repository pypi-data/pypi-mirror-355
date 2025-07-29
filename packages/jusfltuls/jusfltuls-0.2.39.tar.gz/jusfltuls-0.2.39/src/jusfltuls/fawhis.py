#!/usr/bin/env python3

#
#   make multiple versions of whisper STT and use mpvsubs.py to play
#
###from fire import Fire
import click
from faster_whisper import WhisperModel
import time
import pysubs2
import os
# importing module
import logging
import datetime as dt
import sys
from console import fg, bg
import autocorrect
#from autocorrect import Speller

#
#from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
#https://github.com/snakers4/silero-vad/wiki/Examples-and-Dependencies#examples
#
#
# Create and configure logger
LOGFILE = os.path.expanduser("~/fwhisp.log")
logging.basicConfig(filename=LOGFILE,
                    format='%(asctime)s %(message)s',
                    filemode='a')
# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.INFO)

"""
https://github.com/SYSTRAN/faster-whisper



2024-08-26 20:09:48,943 Openning FILE speechtest.mp3 with MODEL  tiny.en
2024-08-26 20:09:49,432 Starting FILE speechtest.mp3 with MODEL  tiny.en
2024-08-26 20:09:49,552 Processing audio with duration 01:15.352
2024-08-26 20:09:51,455 Finished FILE speechtest.mp3 with MODEL tiny.en after 0:00:02.022508

2024-08-26 20:09:52,636 Openning FILE speechtest.mp3 with MODEL  base.en
2024-08-26 20:09:53,541 Starting FILE speechtest.mp3 with MODEL  base.en
2024-08-26 20:09:53,657 Processing audio with duration 01:15.352
2024-08-26 20:09:56,501 Finished FILE speechtest.mp3 with MODEL base.en after 0:00:02.959267

2024-08-26 20:09:57,676 Openning FILE speechtest.mp3 with MODEL  small.en
2024-08-26 20:09:58,371 Starting FILE speechtest.mp3 with MODEL  small.en
2024-08-26 20:09:58,489 Processing audio with duration 01:15.352
2024-08-26 20:10:06,467 Finished FILE speechtest.mp3 with MODEL small.en after 0:00:08.095602

2024-08-26 20:10:07,686 Openning FILE speechtest.mp3 with MODEL  medium.en
2024-08-26 20:10:09,583 Starting FILE speechtest.mp3 with MODEL  medium.en
2024-08-26 20:10:09,699 Processing audio with duration 01:15.352
2024-08-26 20:10:31,897 Finished FILE speechtest.mp3 with MODEL medium.en after 0:00:22.314353

2024-08-26 20:10:33,128 Openning FILE speechtest.mp3 with MODEL  distil-medium.en MISSING 45 sec
2024-08-26 20:10:34,222 Starting FILE speechtest.mp3 with MODEL  distil-medium.en
2024-08-26 20:10:34,338 Processing audio with duration 01:15.352
2024-08-26 20:10:43,387 Finished FILE speechtest.mp3 with MODEL distil-medium.en after 0:00:09.164615
"""

@click.command()
@click.argument('infile')
@click.option('--model_size', "-m", default=None, help='Optional model size like tiny.en small base _medium_')
@click.option('--language', "-l", default=None, help='Optionaly force language like cs')
@click.option('--outputname', "-o", default=None, help='Optionaly overwrite output filename')
def main( infile, model_size, language, outputname):
    """
    STT for video by whisper. Give me Video-file and model-name (tiny,base...); saves with modelsize in filename; good to test models
    """
    if model_size is None:
        print( """  --models_size OR  -m
        tiny.en, tiny, base.en, base,
        small.en, small,
        medium.en, medium,
        large-v1, large-v2, large-v3,
        distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3
        """)
        sys.exit(1)


    # model_size = "tiny.en" # 0.075 G
    # model_size = "base.en" # 0.144 G
    # model_size = "small.en" # 0.484 G
    # model_size = "distil-medium.en" # 0.789 G
    # model_size = "medium.en" # 1.53 G
    # model_size = "large-v3"  # 3G
    # model_size = "distil-large-v3"  # 3G


    # Run on GPU with FP16
    #model = WhisperModel(model_size, device="cuda", compute_type="float16")
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

    # or run on CPU with INT8


    ##wav = read_audio( infile) # backend (sox, soundfile, or ffmpeg) required!
    ##speech_timestamps = get_speech_timestamps(wav, model)

    print(f"**** INPUT:  {infile}  /  OUTPUT:  {outputname}")
    if not os.path.exists(infile):
        print("X... file doesnt exist")
        sys.exit(1)
    print(f"******opennin****** MODEL = {model_size} *********************** logfile ", LOGFILE)
    logger.info(f"Openning FILE {infile} with MODEL  {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8" ) # fp32 cpu_threads=16, num_workers=16

    timetag = dt.datetime.now()
    logger.info(f"Starting FILE {infile} with MODEL  {model_size} ")


    # *********************** TRANSCRIBE HERE *****************************
    print("*********** starting transcribe ******** ")
    if language is None:
        segments, info = model.transcribe(infile, beam_size=5)
    else:
        print(f"*****forcing******* LANGUAGE  = {language} *********************")
        segments, info = model.transcribe(infile, beam_size=5, language=language)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    LANG = info.language
    if LANG in ["cs", "en"]:
        print("************  initializing autocorrect *********")
        spell = autocorrect.Speller( LANG)  # I can tune if english or so...


    results= []

    # ***************************** OUTPUTS ********************
    print("****************** going through  segments *********** ")
    for segment in segments:
        SEG_s, SEG_e, SEG_t = segment.start, segment.end, segment.text

        if LANG in ["cs", "en"]:
            SEG_t2 = spell(SEG_t)
            if SEG_t2 != SEG_t:
                print(fg.darkslategray, f"[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t2} ", fg.default)
            SEG_t = SEG_t2

        print(f"[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t} ")
        # srt
        segment_dict = {'start':SEG_s,'end':SEG_e,'text':SEG_t}
        results.append(segment_dict)

    logger.info(f"Finished FILE {infile} with MODEL {model_size} after {dt.datetime.now()-timetag}")

    subs = pysubs2.load_from_whisper(results)
    #save srt file

    # ================================ OUTPUT ====================
    file_name = "x.srt"
    #print("> fi", infile)
    #print("> di", os.path.dirname(infile))
    #print("> st", os.path.splitext(os.path.dirname(infile)))
    #print("> 00", os.path.splitext(os.path.dirname(infile))[0])
    #print("> --" )
    # --------------------   extract dirname from infile ------------
    dirname = ""
    if len(os.path.dirname(infile)) > 2:
        dirname = os.path.splitext(os.path.dirname(infile))[0]
        dirname = f"{dirname}/"
    else:
        dirname = ""
    #print("> dn", dirname)

    # ----------------------------
    if outputname is not None:
        # ------ cancel my dirname idea if already defined in outputname
        if len(os.path.dirname(outputname)) > 2:
            dirname = ""
        if outputname.find(r".srt") > 0:
            file_name = f"{dirname}{outputname}"
        else:
            file_name = f"{dirname}{outputname}.srt"
    else:
        file_name = os.path.splitext(os.path.basename(infile))[0] + f"_{model_size}.srt"
        file_name = f"{dirname}{file_name}"

    #file_name = os.path.splitext(os.path.basename(infile))[0] + f".srt"
    print("i... saving: ", fg.green, file_name, fg.default)
    subs.save( file_name )
    # #save ass file
    # subs.save(file_name+'.ass')

if __name__ == "__main__":
    main()
