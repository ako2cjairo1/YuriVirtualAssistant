import speech_recognition as sr
import os
import random
import playsound
import colorama
import logging
import time
from helper import displayException
from gtts import gTTS
from gtts.tts import gTTSError
from skills_library import SkillsLibrary
from telegram import TelegramBot
from threading import Thread

AUDIO_FOLDER = "./text-to-speech-audio"

ASSISTANT_CYAN_MESSAGE = "\033[1;37;46m"
ASSISTANT_BLACK_NAME = "\033[22;30;46m"

MASTER_GREEN_MESSAGE = "\033[1;37;42m"
MASTER_BLACK_NAME = "\033[22;30;42m"

VIRTUAL_ASSISTANT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\VirtualAssistant"


class SpeechAssistant:

    def __init__(self, masters_name, assistants_name):
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.sleep_assistant = False
        self.not_available_counter = 0
        self.recognizer = sr.Recognizer()
        # let's override the dynamic threshold to 4000,
        # so the timeout we set in listen() will be used
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000

        self.skill = SkillsLibrary(self, self.master_name, self.assistant_name)
        self.bot = TelegramBot("1310031608:AAHkuLvXb_3M-PTCuVl0lbVE4ST3Gi38ceI")
        self.chat_id = None
        self.update_id = None
        self.bot_command = None

        bot_command_thread = Thread(target=self.get_command_from_bot)
        bot_command_thread.setDaemon(True)
        bot_command_thread.start()

    def listen_to_audio(self, ask=None):
        voice_text = ""
        listen_timeout = 3

        if self.isSleeping():
            listen_timeout = 2

        # adjust the recognizer sensitivity to ambient noise
        # and record audio from microphone
        with sr.Microphone() as source:
            if not self.isSleeping():
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                # announce/play something before listening from microphone
                if ask:
                    self.speak(ask)

                if self.bot_command and "/start" not in self.bot_command:
                    voice_text = self.bot_command
                    # self.bot_command = None
                else:
                    # listening
                    audio = self.recognizer.listen(source, timeout=listen_timeout)
                    # try convert audio to text/string data
                    voice_text = self.recognizer.recognize_google(audio)

                self.not_available_counter = 0

            except sr.UnknownValueError:
                displayException(
                    f"{self.assistant_name} could not understand what you have said.", logging.WARNING)

                if self.isSleeping() and self.not_available_counter >= 3:
                    message = f"\"{self.assistant_name}\" is active again."
                    print(message)
                    self.respond_to_bot(message)
                    self.not_available_counter = 0

                return voice_text

            except sr.RequestError:
                self.not_available_counter += 1
                if self.not_available_counter == 3:
                    message = f"\"{self.assistant_name}\" Not Available."
                    displayException(message)
                    self.respond_to_bot(message)

                if self.isSleeping() and self.not_available_counter >= 3:
                    message = f"{self.assistant_name}: reconnecting..."
                    print(message)
                    self.respond_to_bot(message)

            except gTTSError:
                displayException("gTTSError")

            except Exception as ex:
                if "listening timed out" not in str(ex):
                    # bypass the timed out exception, (timeout=3, if total silence for 3 secs.)
                    displayException(
                        "Exception occurred while analyzing audio.")

        if not self.isSleeping() and voice_text.strip():
            print(
                f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_text}")

        if not self.bot_command and voice_text.strip():
            self.respond_to_bot(f"(I heared) you said: {voice_text}")

        self.bot_command = None
        return voice_text.strip()

    def sleep(self, value):
        self.sleep_assistant = value

    def isSleeping(self):
        return self.sleep_assistant

    def respond_to_bot(self, audio_string):
        self.bot.send_message(audio_string, self.chat_id)

    def get_command_from_bot(self):
        while True:
            updates = self.bot.get_updates(self.update_id)
            if updates["ok"] and len(updates["result"]) > 0:
                self.update_id = self.bot.get_last_update_id(updates) + 1

                if not self.chat_id:
                    self.bot.send_message("/start", self.update_id)

                # handle_updates(updates)
                command, self.chat_id = self.bot.get_last_chat_id_and_text(updates)
                self.bot_command = command.strip().lower()

                if self.isSleeping():
                    self.bot_command = f"hey {self.assistant_name} {self.bot_command}"
                    # lower the volume of music player (if there is playing)
                    # so listening microphone will not block our bot_command request
                    self.skill.music_volume(20)

            time.sleep(0.5)

    def speak(self, audio_string, start_prompt=False, end_prompt=False, mute_prompt=False):
        if audio_string.strip():
            try:
                # volume up the music player, if applicable
                self.skill.music_volume(30)
                force_delete = False
                # init google's text-to-speech module
                tts = gTTS(text=audio_string, lang="en-us", slow=False)

                if not os.path.isdir(AUDIO_FOLDER):
                    os.mkdir(AUDIO_FOLDER)

                # generate a filename for the audio file generated by google
                audio_file = f"{AUDIO_FOLDER}/assistants-audio-{str(random.randint(1, 1000))}.mp3"

                if start_prompt and "<start prompt>" in audio_string:
                    audio_file = f"{AUDIO_FOLDER}/start prompt.mp3"

                elif start_prompt and audio_string:
                    tts.save(audio_file)
                    playsound.playsound(f"{AUDIO_FOLDER}/start prompt.mp3")
                    print(
                        f"{ASSISTANT_BLACK_NAME}{self.assistant_name}:{ASSISTANT_CYAN_MESSAGE} {audio_string}")

                    self.respond_to_bot(audio_string)

                    force_delete = True

                elif end_prompt:
                    audio_file = f"{AUDIO_FOLDER}/end prompt.mp3"

                elif mute_prompt:
                    audio_file = f"{AUDIO_FOLDER}/mute prompt.mp3"

                else:
                    tts.save(audio_file)
                    print(
                        f"{ASSISTANT_BLACK_NAME}{self.assistant_name}:{ASSISTANT_CYAN_MESSAGE} {audio_string}")

                    self.respond_to_bot(audio_string)

                # announce/play the generated audio
                playsound.playsound(audio_file)

                if not start_prompt and not end_prompt and not mute_prompt or force_delete:
                    # delete the audio file after announcing to save mem space
                    os.remove(audio_file)

            except Exception as ex:
                if not ("Cannot find the specified file." or "Permission denied:") in str(ex):
                    displayException(
                        "Error occurred (gtts) while trying to speak.")
                    message = f"{self.assistant_name} Not Available. You are not connected to the internet."
                    print(message)
                    self.respond_to_bot(message)
                else:
                    self.not_available_counter += 1
                    if self.not_available_counter == 3:
                        message = f"\"{self.assistant_name}\" Not Available."
                        displayException(message)
                        self.respond_to_bot(message)

                    if self.isSleeping() and self.not_available_counter >= 3:
                        message = f"{self.assistant_name}: reconnecting..."
                        print(message)
                        self.respond_to_bot(message)
