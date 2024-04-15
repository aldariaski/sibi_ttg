import json, os, pysrt, time, shutil
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_q.tasks import async_task, fetch
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator

from .asr import process_audio, google_asr, wav2vec_asr
from .asr.process_audio import remove_microseconds
from . import models
from ttg.views import add_gesture
from asgiref.sync import async_to_sync
from django.http import HttpResponseRedirect
from pydub import AudioSegment


def index(request):
    return render(request, "index.html")

@csrf_exempt
def add(request):
    response = {}
    response["message"] = "Invalid method"
    
    try:
        json_data = json.loads(request.body)
        val = URLValidator()
        url = json_data["url"]
        val(url)    
        async_task(add_subtitle(request))
        response["message"] = "Request successful"

    except Exception as e:
        response["message"] = str(e)


    return JsonResponse(response, safe=False)

@csrf_exempt
def add_subtitle(request):
    response = {}
    response["message"] = "Invalid method"
    try:
        if request.method == "POST":
            json_data = json.loads(request.body)
            print(json.dumps(json_data))
            val = URLValidator()
            url = json_data["url"]
            val(url)
            asr_type = json_data["asr"]
            subtitle_duration = "0 seconds"

            url_lastpart = url.rsplit('/', 1)[-1]

            
            if asr_type != "Manual":
                process_audio.extract_audio_from_video(url, 'output_audio.mp3')


            
            if asr_type == "Google":
                print("Google ASR processing")
                print("Now uploading to bucket")
                try:
                    blob_url = google_asr.upload_to_bucket(url_lastpart.replace("mp4", "mp3"), 'output_audio.mp3', 
                                            'skripsi-speech-recognizer')
                    
                    print("url last path is now", url_lastpart)
                
                    blob_url_gs = blob_url.replace("https://storage.googleapis.com/", "gs://")
                    blob_url_gs_v2 = "gs://skripsi-speech-recognizer/audio-files/" +  url_lastpart.replace("mp4", "mp3")

                    with open('blob_url.txt', 'w', encoding="utf-8") as f:
                        f.write(blob_url + "\n" + blob_url_gs + "\nv2" + blob_url_gs_v2)

                except Exception as e:
                    print(str(e))
                
                print("Now processing speech")
                start_time = time.process_time()

                try:
                    sub = google_asr.google_transcribe_speech(blob_url_gs_v2)

                except Exception as e:
                    print(str(e))

                
                
                end_time = time.process_time()
                subtitle_duration = str(end_time - start_time) + " seconds"
                print(subtitle_duration)

                if os.path.exists("temp_subtitle.srt"):
                    os.remove("temp_subtitle.srt")

                with open('temp_subtitle.srt', 'w', encoding='utf-8') as f:
                    for i, (start_time, end_time, text) in enumerate(sub, start=1):
                        f.write(f"{i}\n")
                        f.write(f"{remove_microseconds(start_time)} --> {remove_microseconds(end_time)}\n")
                        f.write(f"{text}\n\n")
                
                file = open("temp_subtitle.srt")
                shutil.copy2("temp_subtitle.srt", "Google " + url_lastpart.replace("mp4", "srt"))
                subtitle = file.read()
                        
            elif asr_type == "Wav2Vec":
                if os.path.exists("temp_subtitle.srt"):
                    os.remove("temp_subtitle.srt")
                    
                start_time = time.process_time()
                wav2vec_asr.transcribe_file('output_audio.mp3')
                end_time = time.process_time()
                subtitle_duration = str(end_time - start_time) + " seconds"
                file = open("temp_subtitle.srt")
                shutil.copy2("temp_subtitle.srt", "Wav2Vec "+ url_lastpart.replace("mp4", "srt"))


                subtitle = file.read()

            elif asr_type == "Azure":
                if os.path.exists("temp_subtitle.srt"):
                    os.remove("temp_subtitle.srt")
                
                print("Hey")
                sound = AudioSegment.from_mp3("output_audio.mp3")
                sound.export("output_audio.wav", format="wav")     
                    
                start_time = time.process_time()

                try:
                    exec(open('asr/asr/azure_asr.py').read())

                except Exception as e:
                    print(str(e))
                

                end_time = time.process_time()
                subtitle_duration = str(end_time - start_time) + " seconds"

                print(subtitle_duration)
                print("Hello")

                file = open("temp_subtitle.srt")
                shutil.copy2("temp_subtitle.srt", "Azure " + url_lastpart.replace("mp4", "srt"))
                subtitle = file.read()


            elif asr_type == "Manual":
                #time.sleep(1000)
                subtitle = json_data["subtitle"]
                with open('temp_subtitle.srt', 'w', encoding='utf-8') as f:
                    f.write(subtitle)


            
            subtitle_model = models.Subtitle(url=url, subtitle=subtitle, asrtype = asr_type, duration = subtitle_duration)
            subtitle_model.save()

            
            add_gesture(url, subtitle)
            response["message"] = "Request successful"

    except Exception as e:
        response["message"] = str(e)

    return JsonResponse(response, safe=False)
    

def get_subtitle(request):
    subtitles = models.Subtitle.objects.values()
    for subtitled in subtitles:
        subtitled["filename"] = os.path.basename(subtitled["url"])
    return HttpResponse(
        json.dumps(list(subtitles)), content_type="application/json; charset=UTF-8")


