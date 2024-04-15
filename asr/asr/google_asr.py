from google.cloud import storage
from google.cloud import speech
from google.oauth2 import service_account
from moviepy.editor import VideoFileClip

from . import process_audio

# Google ASR ---------------------------------------------

def upload_to_bucket(blob_name, path_to_file, bucket_name='skripsi-speech-recognizer'):
    """ Upload data to a bucket"""
     
    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'asr/secret/jarkom-fakhri-72a97ef1f543.json')

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

    subtitles = process_audio.generate_srt_from_response(response)
    #return result.alternatives[0].transcript
    return subtitles