import azure.cognitiveservices.speech as speechsdk
import os
import time
import pprint
import json
import srt
import datetime


path = os.getcwd()
# Creates an instance of a speech config with specified subscription key and service region.
# Replace with your own subscription key and region identifier from here: https://aka.ms/speech/sdkregion
speech_key, service_region = "4351724cc19948499b20b50718c0862e", "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# Creates an audio configuration that points to an audio file.
# Replace with your own audio filename.
audio_filename = "output_audio.wav"
audio_input = speechsdk.audio.AudioConfig(filename=audio_filename)

# Creates a recognizer with the given settings
speech_config.speech_recognition_language="id-ID"
speech_config.request_word_level_timestamps()



speech_config.enable_dictation()
speech_config.output_format = speechsdk.OutputFormat(1)

speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

#result = speech_recognizer.recognize_once()
all_results = []
results = []
transcript = []
words = []


#https://learn.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.recognitionresult?view=azure-python
def handle_final_result(evt):
    import json
    global all_results
    global results
    global transcript
    global words
    all_results.append(evt.result.text) 
    results = json.loads(evt.result.json)
    transcript.append(results['DisplayText'])
    confidence_list_temp = [item.get('Confidence') for item in results['NBest']]
    max_confidence_index = confidence_list_temp.index(max(confidence_list_temp))
    words.extend(results['NBest'][max_confidence_index]['Words'])



done = False

def stop_cb(evt):
    print('CLOSING on {}'.format(evt))
    print("stop must be done1")
    global done
    done= True
    
speech_recognizer.recognized.connect(handle_final_result) 
#Connect callbacks to the events fired by the speech recognizer    
speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
# stop continuous recognition on either session stopped or canceled events
speech_recognizer.session_stopped.connect(stop_cb)
speech_recognizer.canceled.connect(stop_cb)

speech_recognizer.start_continuous_recognition()

while not done:
    time.sleep(.5)

speech_recognizer.stop_continuous_recognition()
    
print("Printing all results:")
print(all_results)

speech_to_text_response = words

def convertduration(t):
    x= t/10000
    return int((x / 1000)), (x % 1000)


##-- Code to Create Subtitle --#

#3 Seconds
bin = 3.0
duration = 0 
transcriptions = []
transcript = ""
index,prev=0,0
wordstartsec,wordstartmicrosec=0,0
for i in range(len(speech_to_text_response)):
    #Forms the sentence until the bin size condition is met
    transcript = transcript + " " + speech_to_text_response[i]["Word"]
    #Checks whether the elapsed duration is less than the bin size
    if(int((duration / 10000000)) < bin): 
        wordstartsec,wordstartmicrosec=convertduration(speech_to_text_response[i]["Offset"])
        duration= duration+speech_to_text_response[i]["Offset"]-prev
        prev=speech_to_text_response[i]["Offset"]
                #transcript = transcript + " " + speech_to_text_response[i]["Word"]
    else : 
        index=index+1
        #transcript = transcript + " " + speech_to_text_response[i]["Word"]
        transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec), datetime.timedelta(0, wordstartsec+bin, 0), transcript))
        duration = 0 
        #print(transcript)
        transcript=""



transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec), datetime.timedelta(0, wordstartsec+bin, 0), transcript))
subtitles = srt.compose(transcriptions)

with open("temp_subtitle.srt", "w") as f:
    f.write(subtitles)