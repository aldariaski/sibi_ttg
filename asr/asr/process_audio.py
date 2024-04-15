import requests
import os
import datetime

from google.cloud import storage
from google.cloud import speech
from google.oauth2 import service_account
from moviepy.editor import VideoFileClip

# Audio ---------------------------------------------

def extract_audio_from_video(video_url, output_audio_path):
    video_clip = VideoFileClip(video_url)
    audio_clip = video_clip.audio

    # Save the audio clip to a file
    audio_clip.write_audiofile(output_audio_path)

    # Close the video and audio clips
    video_clip.close()
    audio_clip.close()

def convert_time(timestamp):
    m, s = divmod(timestamp.seconds, 60)
    h, m = divmod(m, 60)
    hours = h
    minutes = m
    seconds = s
    microseconds = timestamp.microseconds
    milliseconds = microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def remove_microseconds(time_str):
    # Split the time string based on comma
    time_parts = time_str.split('.')

    # Take only the first part (time)
    time_without_microseconds = time_parts[0]

    return time_without_microseconds

def generate_srt_from_response(response):
    subtitles = []

    for result in response.results:
        if result.alternatives:
            alternative = result.alternatives[0]
            
            if alternative.words:
                start_time = convert_time(alternative.words[0].start_time)
                end_time = convert_time(alternative.words[-1].end_time)
                transcript = alternative.transcript

                subtitles.append((start_time, end_time, transcript))

    return subtitles

# Google ASR ---------------------------------------------

def upload_to_bucket(blob_name, path_to_file, bucket_name='skripsi-speech-recognizer'):
    """ Upload data to a bucket"""
     
    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'ttg/secret/jarkom-fakhri-72a97ef1f543.json')

    #print(buckets = list(storage_client.list_buckets())
    blob_name = "audio-files/" + blob_name

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    #response = requests.get(path_to_file)
    blob.upload_from_filename(path_to_file)
    
    #returns a public url
    return blob.public_url


def google_transcribe_speech(gcs_uri):
    # Instantiates a client
    credentials = service_account.Credentials.from_service_account_file('ttg/secret/jarkom-fakhri-72a97ef1f543.json') 
    
    client=speech.SpeechClient(credentials=credentials)
    audio=speech.RecognitionAudio(uri=gcs_uri)

    config=speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=48000,
        language_code="id-ID",
        model="latest_long",
        audio_channel_count=2,
        enable_automatic_punctuation=True,
        enable_word_confidence=True,
        enable_word_time_offsets=True,
        alternative_language_codes=["en-US"],
    )

    # Detects speech in the audio file
    operation=client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response=operation.result(timeout=1000)

    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

    subtitles = generate_srt_from_response(response)
    #return result.alternatives[0].transcript
    return subtitles