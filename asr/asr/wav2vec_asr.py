import librosa
import torch
import os
import srt

from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from datetime import timedelta

ID_MODEL = "indonesian-nlp/wav2vec2-large-xlsr-indonesian"
STT_MAX_CHAR = 37
STT_MAX_LINE = 2
STT_DURATION = 6
DURATION_LIMIT = STT_DURATION*3

def lang_model_selector(audio_lang):
    model_lang = ID_MODEL
    return model_lang

def transcribe_audio(audio_file, offset, duration, model_lang, idx):
    audio, rate = librosa.load(audio_file, offset=offset, duration=duration, sr=16_000)

    tokenizer = Wav2Vec2Processor.from_pretrained(model_lang)
    model = Wav2Vec2ForCTC.from_pretrained(model_lang)

    input_values = tokenizer(audio, sampling_rate=16_000, return_tensors='pt').input_values
    logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim =-1)
    transcriptions = tokenizer.decode(predicted_ids[0])
    transcriptions = transcriptions.split()

    last_index, subtitles = convert_sentences(transcriptions, idx, offset)
    #filename, _ = os.path.splitext(audio_file)
    filename = 'temp_subtitle'
    srt_filename = write_srt(subtitles, filename)
    txt_filename = write_txt(subtitles, filename)
    return last_index, srt_filename, txt_filename


def add_leading_zero(a_time):
    if a_time < 10:
        a_time = "0"+str(a_time)
    return a_time


def print_progress(start_time, end_time):
    start_minute = add_leading_zero(round(start_time//60))
    start_second = add_leading_zero(round(start_time%60))
    start_time = "{}:{}".format(start_minute, start_second)
    end_minute = add_leading_zero(round(end_time//60))
    end_second = add_leading_zero(round(end_time%60))
    end_time = "{}:{}".format(end_minute, end_second)
    print("transcribe audio from {} to {}".format(start_time, end_time))

def transcribe_file(audio_file):
    audio_duration = librosa.get_duration(filename=audio_file)
    audio_offset = 0.0
    iteration_duration = DURATION_LIMIT
    model_lang = lang_model_selector(ID_MODEL)
    print("Language model:", model_lang)
    idx = 1

    while audio_duration > 0:
        if audio_duration < DURATION_LIMIT:
            iteration_duration = audio_duration
            print_progress(audio_offset, audio_offset+iteration_duration)
            last_index, srt_filename, txt_filename = transcribe_audio(
                audio_file, audio_offset, 
                iteration_duration, model_lang, idx
            )
            audio_duration -= audio_duration
        else:
            print_progress(audio_offset, audio_offset+iteration_duration)
            last_index, srt_filename, txt_filename = transcribe_audio(
                audio_file, audio_offset, 
                iteration_duration, model_lang, idx
            )
            audio_offset += DURATION_LIMIT
            audio_duration -= DURATION_LIMIT
        idx = last_index
    
    return srt_filename, txt_filename

def convert_sentences(transcription, idx, start):
    """Create list of subtitles per sentences"""
    max_char = STT_MAX_CHAR * STT_MAX_LINE
    subtitles = []
    timer = timedelta(seconds=0)
    timer += timedelta(seconds=start)
    first_word = True
    char_count = 0
    sentence = ""
    subs_index = idx

    for word in transcription:
        if first_word:
            start = timer

        char_count = len(sentence) + len(word)
        sentence += word.strip() + " "

        if ("." in word or "!" in word or "?" in word or
                char_count > max_char or
                ("," in word and not first_word)):
            subtitles.append(srt.Subtitle(index=subs_index,
                                    start=start,
                                    end=timer + timedelta(seconds=STT_DURATION),
                                    content=srt.make_legal_content(sentence)))
            first_word = True
            subs_index += 1
            timer += timedelta(seconds=STT_DURATION)
            sentence = ""
            char_count = 0
        else:
            first_word = False

    if sentence:
        subtitles.append(srt.Subtitle(
                                    index=subs_index,
                                    start=timer,
                                    end=timer + timedelta(seconds=STT_DURATION),
                                    content=srt.make_legal_content(sentence)))
    subs_index += 1
    return subs_index, subtitles

def write_srt(subtitles, filename):
    srt_file = filename + ".srt"
    print("Writing subtitles to: {}".format(srt_file))
    f = open(srt_file, 'a+')
    f.writelines(srt.compose(subtitles, reindex=False))
    f.close()
    return srt_file

def write_txt(subtitles, filename):
    txt_file = filename + ".txt"
    print("Writing text to: {}".format(txt_file))
    f = open(txt_file, 'a+')
    for s in subtitles:
        f.write(s.content + "\n")
    f.close()
    return txt_file