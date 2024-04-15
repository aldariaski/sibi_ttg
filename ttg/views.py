import json, os, pysrt, time
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_q.tasks import async_task, fetch
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator

from . import tasks, models
from asgiref.sync import async_to_sync
from django.http import HttpResponseRedirect



def index(request):
    return render(request, "index.html")

@csrf_exempt
def add_gesture(url, subtitle):
    response = {}
    response["message"] = "Invalid method"
    try:
        val = URLValidator()
        val(url)
        subtitle = pysrt.from_string(subtitle)
        subtitle.save("temp.srt")
        file = open("temp.srt")
        subtitle = file.read()
        subtitle = subtitle[:-1]
        gesture = models.Gesture(url=url, subtitle=subtitle)
        gesture.save()
        task = async_task(tasks.request_gesture, gesture.index, url, subtitle)
        response["message"] = "Request successful"
        response["id"] = task
        response["index"] = gesture.index

    except Exception as e:
        response["message"] = str(e)

    return JsonResponse(response, safe=False)
    

def get_task(request):
    response = {}
    response["message"] = "Request successful"
    id = request.GET.get("id", None)
    if id != None and len(id) == 32:
        task = fetch(id)
        if task != None:
            response["name"] = task.name
            response["started"] = task.started
            response["stopped"] = task.stopped
            response["success"] = task.success
            response["time_taken"] = task.time_taken()
        else:
            response["message"] = "Task not found"
    else:
        response["message"] = "Invalid id format"
    return JsonResponse(response)


def get_gesture(request):
    response = {}
    response["message"] = "Request successful"
    index = request.GET.get("index", None)
    if index != None:
        gesture = models.Gesture.objects.get(index=index)
        if gesture != None:
            response["url"] = gesture.url
            response["status"] = gesture.status
            response["final_url"] = gesture.final_url
            response["subtitle"] = gesture.subtitle
        else:
            response["message"] = "Gesture not found"
    else:
        response["message"] = "Invalid index format"
    return JsonResponse(response)


def get_running_gesture(request):
    gestures = models.Gesture.objects.filter(status=models.Gesture.RUNNING).values()
    for gesture in gestures:
        gesture["filename"] = os.path.basename(gesture["url"])
        del gesture["final_url"]
        del gesture["duration"]
        del gesture["generated_duration"]
        del gesture["words"]
        del gesture["words_not_found"]
        del gesture["characters_not_found"]
        del gesture["subtitle"]
        del gesture["status"]
    return HttpResponse(
        json.dumps(list(gestures)), content_type="application/json; charset=UTF-8"
    )


def get_queued_gesture(request):
    gestures = models.Gesture.objects.filter(status=models.Gesture.QUEUED).values()
    for gesture in gestures:
        gesture["filename"] = os.path.basename(gesture["url"])
        del gesture["final_url"]
        del gesture["duration"]
        del gesture["generated_duration"]
        del gesture["words"]
        del gesture["words_not_found"]
        del gesture["characters_not_found"]
        del gesture["subtitle"]
        del gesture["status"]
    return HttpResponse(
        json.dumps(list(gestures)), content_type="application/json; charset=UTF-8"
    )


def get_successful_gesture(request):
    gestures = models.Gesture.objects.filter(status=models.Gesture.SUCCESSFUL).values()
    for gesture in gestures:
        gesture["filename"] = os.path.basename(gesture["url"])
        del gesture["subtitle"]
        del gesture["status"]
    return HttpResponse(
        json.dumps(list(gestures)), content_type="application/json; charset=UTF-8"
    )


def get_failure_gesture(request):
    gestures = models.Gesture.objects.filter(status=models.Gesture.FAILURE).values()
    for gesture in gestures:
        gesture["filename"] = os.path.basename(gesture["url"])
        del gesture["final_url"]
        del gesture["subtitle"]
        del gesture["status"]
    return HttpResponse(
        json.dumps(list(gestures)), content_type="application/json; charset=UTF-8"
    )