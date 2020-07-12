import speech_recognition as sr
import os
import random
import playsound
import colorama
import logging
import time
from helper import *
from gtts import gTTS
from gtts.tts import gTTSError

AUDIO_FOLDER = "./text-to-speech-audio"

ASSISTANT_GREEN_MESSAGE = "\033[1;37;42m"
ASSISTANT_BLACK_NAME = "\033[22;30;42m"

MASTER_CYAN_MESSAGE = "\033[1;37;46m"
MASTER_BLACK_NAME = "\033[22;30;46m"


class SpeechAssistant:
    def __init__(self, masters_name, assistants_name):
        self.master_name = masters_name
        self.assistant_name = assistants_name

    def listen_to_audio(self, ask=None):
        voice_text = ""
        recognizer = sr.Recognizer()

        # let's override the dynamic threshold to 400,
        # so the timeout we set in listen() will be used
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 4000

        # adjust the recognizer sensitivity to ambient noise 
        # and record audio from microphone
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                # announce/play something before listening from microphone
                if ask:
                    self.speak(ask)

                # listening
                audio = recognizer.listen(source, timeout=3)
                # try convert audio to text/string data
                voice_text = recognizer.recognize_google(audio)

            except sr.UnknownValueError:
                # displayException("Could not understand audio.")
                displayException("Could not understand audio.", logging.WARNING)
                return voice_text
            except sr.RequestError:
                displayException("gtts Request error", logging.WARNING)
                if voice_text:
                    self.speak(
                        "Sorry! My speech service is not available at the moment.")
            except gTTSError:
                displayException("gTTSError", logging.ERROR)
            except Exception as ex:
                if not "listening timed out" in str(ex):
                    # bypass the timed out exception, (timedout=5, if total silence for 5 secs.)
                    displayException("Exception error")

        if voice_text.strip():
            print(
                f"{ASSISTANT_BLACK_NAME}{self.master_name}:{ASSISTANT_GREEN_MESSAGE} {voice_text}")
        return voice_text.strip()

        
    def speak(self, audio_string, start_prompt=False, end_prompt=False, mute_prompt=False):
        
        if audio_string.strip():
            try:
                # init google's text-to-speech module
                tts = gTTS(text=audio_string, lang="en-us", slow=False)

                if not os.path.isdir(AUDIO_FOLDER):
                    os.mkdir(AUDIO_FOLDER)

                # generate a filename for the audio file generated by google
                audio_file = f"{AUDIO_FOLDER}/assistants-audio-{str(random.randint(1, 1000))}.mp3"
                tts.save(audio_file)

                if start_prompt and "<start prompt>" in audio_string:
                    audio_file = f"{AUDIO_FOLDER}/start prompt.mp3"
                elif start_prompt and audio_string:
                    playsound.playsound(f"{AUDIO_FOLDER}/start prompt.mp3")
                    print(f"{MASTER_BLACK_NAME}{self.assistant_name}:{MASTER_CYAN_MESSAGE} {audio_string}")
                elif end_prompt:
                    audio_file = f"{AUDIO_FOLDER}/end prompt.mp3"
                elif mute_prompt:
                    audio_file = f"{AUDIO_FOLDER}/mute prompt.mp3"
                else:
                    print(f"{MASTER_BLACK_NAME}{self.assistant_name}:{MASTER_CYAN_MESSAGE} {audio_string}")

                # announce/play the generated audio
                playsound.playsound(audio_file)

                if not start_prompt and not end_prompt and not mute_prompt:
                    # delete the audio file after announcing to save mem space
                    os.remove(audio_file)

            except Exception as ex:
                if not ("Cannot find the specified file." or "Permission denied:") in str(ex):
                    displayException("gtts Speak")
                    while not submitTaskWithException(self.speak, audio_string, start_prompt, end_prompt):
                        print("\n**re-connecting to gtts API...")
                        time.sleep(2)
        
        
