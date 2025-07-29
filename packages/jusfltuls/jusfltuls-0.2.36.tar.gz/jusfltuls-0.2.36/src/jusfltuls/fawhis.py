#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "faster-whisper",
#     "pysubs2",
# ]
# ///

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


#
#from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
#https://github.com/snakers4/silero-vad/wiki/Examples-and-Dependencies#examples
#
#
# Create and configure logger
logging.basicConfig(filename=os.path.expanduser("~/fwhisp.log"),
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
@click.option('--model_size', "-m", default=None, help='Optional model size like tiny small base _medium_')
@click.option('--language', "-l", default=None, help='Optionaly force language like cs')
def main( infile, model_size, language):
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


    print(f"******************* MODEL = {model_size} ***********************")
    logger.info(f"Openning FILE {infile} with MODEL  {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8") # fp32

    timetag = dt.datetime.now()
    logger.info(f"Starting FILE {infile} with MODEL  {model_size} ")


    # *********************** TRANSCRIBE HERE *****************************
    if language is None:
        segments, info = model.transcribe(infile, beam_size=5)
    else:
        print(f"******************* LANGUAGE  = {language} *********************")
        segments, info = model.transcribe(infile, beam_size=5, language=language)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    results= []

    # ***************************** OUTPUTS ********************
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        # srt
        segment_dict = {'start':segment.start,'end':segment.end,'text':segment.text}
        results.append(segment_dict)

    logger.info(f"Finished FILE {infile} with MODEL {model_size} after {dt.datetime.now()-timetag}")

    subs = pysubs2.load_from_whisper(results)
    #save srt file
    file_name = os.path.splitext(os.path.basename(infile))[0] + f"_{model_size}.srt"
    #file_name = os.path.splitext(os.path.basename(infile))[0] + f".srt"
    print("i... saving", file_name)
    subs.save( file_name )
    # #save ass file
    # subs.save(file_name+'.ass')

if __name__ == "__main__":
    main()
