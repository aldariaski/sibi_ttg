import json, os, pysrt, time
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_q.tasks import async_task, fetch
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator

from .asr import process_audio, google_asr
from . import tasks, models
from asgiref.sync import async_to_sync
from django.http import HttpResponseRedirect


def main_function(request):
    response = {}
    response["message"] = "Invalid method"
    try:
        if request.method == "POST":
            json_data = json.loads(request.body)
            val = URLValidator()
            url = json_data["url"]
            val(url)
            asr_type = json_data["asr"]
            subtitle_duration = "0 seconds"

            url_lastpart = url.rsplit('/', 1)[-1]
            process_audio.extract_audio_from_video(url, 'output_audio.mp3')

            
            if asr_type == "Google":
                blob_url = google_asr.upload_to_bucket(url_lastpart.replace("mp4", "mp3"), 'output_audio.mp3', 
                                            'skripsi-speech-recognizer')
                
                blob_url_gs = blob_url.replace("https://storage.googleapis.com/", "gs://")

                with open('blob_url.txt', 'w', encoding="utf-8") as f:
                    f.write(blob_url + "\n" + blob_url_gs)

                start_time = time.process_time()

                sub = google_asr.google_transcribe_speech(blob_url_gs)
                
                end_time = time.process_time()
                subtitle_duration = str(end_time - start_time) + " seconds"

                with open('temp_subtitle.srt', 'w', encoding='utf-8') as f:
                    for i, (start_time, end_time, text) in enumerate(sub, start=1):
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                        
            elif asr_type == "Wav2Vec":
                sub = json_data["subtitle"]
            elif asr_type == "Azure":
                sub = json_data["subtitle"]
            elif asr_type == 4:
                sub = json_data["subtitle"]

            file = open("temp_subtitle.srt")
            subtitle = file.read()
            subtitle = subtitle[:-1]
            subtitle_model = models.Subtitle(url=url, subtitle=subtitle, asrtype = asr_type, duration = subtitle_duration)
            subtitle_model.save()
            gesture = models.Gesture(url=url, subtitle=subtitle)
            gesture.save()

            
            task = async_task(tasks.request_gesture, gesture.index, url, subtitle)
            response["message"] = "Request successful"
            response["id"] = task
            response["index"] = gesture.index

    except Exception as e:
        response["message"] = str(e)

    return JsonResponse(response, safe=False)