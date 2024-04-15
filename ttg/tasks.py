import json
import requests, time, os
from . import models
from urllib.parse import urlparse, quote, urlunparse

def request_gesture(index, url, subtitle):
    time.sleep(5)
    gesture = models.Gesture.objects.get(index=index)
    print("Request received")
    gesture.status = gesture.RUNNING
    gesture.save()
    try:
        payload = {"url": url, "subtitle": subtitle}
        request = requests.get("http://localhost:4444")
        response = request.json()
        if request.ok and response["status"] == "Ready":
            request = requests.post("http://localhost:4444", data=json.dumps(payload))
            print("Payload sent")
            response = request.json()
            if request.ok and response["message"] == "Process video request is successful":
                print("Gesture request is successful")
                while (response["status"] != "Ready"):
                    time.sleep(5)
                    request = requests.get("http://localhost:4444")
                    response = request.json()
                    print(response)
                gesture.status = gesture.SUCCESSFUL
                
                parsed_url = urlparse(response["targetUrl"])
                path_segments = parsed_url.path.split('/')

                # Encode the last segment of the path
                encoded_last_path = quote(path_segments[-1])

                # Join the path segments back together and reconstruct the URL
                modified_path = '/'.join(path_segments[:-1] + [encoded_last_path])
                targetUrl = urlunparse((parsed_url.scheme, parsed_url.netloc, modified_path, parsed_url.params, parsed_url.query, parsed_url.fragment))
                print(targetUrl)

                gesture.final_url = targetUrl
                gesture.duration = response["duration"]
                gesture.generated_duration = response["generatedDuration"]
                gesture.words = response["words"]
                gesture.words_not_found = response["wordsNotFound"]
                gesture.characters_not_found = response["charactersNotFound"]
                gesture.save()
                print("Request successful for task", index)
                return True
            else:
                gesture.status = gesture.FAILURE
                gesture.save()
                return False

        gesture.status = gesture.FAILURE
        gesture.save()
        print("Request gesture failed for task", index)
        return False
    
    except Exception as e:
        print("Request failure:", str(e))
        gesture.status = gesture.FAILURE
        gesture.save()
        return False