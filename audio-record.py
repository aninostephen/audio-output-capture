from faster_whisper import WhisperModel
import wave
import os
import soundcard as sc
import openai
import cv2
import keyboard
import pyaudiowpatch as pyaudio
import threading
from audio_groq_service import groq_execute

openai.api_key = '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'

messages = [
    {"role": "system", "content": "Its all about web development interview"},
]

def ask_chatgpt(msg):

    if msg:
        messages.append({"role": "user", "content": "just answer the question about web development: " + msg})
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        response = chat.choices[0].message.content
        print(f"Answer: {response}")

def transcribe_chunk(model, chunk_file):
    segments, _ = model.transcribe(chunk_file)
    transcriptions = ""
    for segment in segments:
        transcription = "%s" % segment.text
        transcriptions += transcription
    return transcriptions


def record_chunk(p, stream, file_path, sample_format, fs, chunk, channels, chunk_length=5):
    frames = []
    for _ in range(0, int(fs / chunk * chunk_length)):
        data = stream.read(chunk)
        frames.append(data)
    
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()


def record_output_voice(p):
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        print("Looks like WASAPI is not available on the system. Exiting...")
        exit()
    
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
        else:
            print("Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices.\nExiting...\n")
            exit()

    return default_speakers

def record_audio_thread():
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 or 16000 samples per second
    seconds = 2
    filename = "audio.wav"

    global isRun
    global isDoneProcessRecord
    p = pyaudio.PyAudio()
    default_speakers = record_output_voice(p)
    stream = p.open(
        format=pyaudio.paInt16,
        channels=default_speakers["maxInputChannels"],
        rate=int(default_speakers["defaultSampleRate"]),
        input=True,
        input_device_index=default_speakers["index"],
        frames_per_buffer=chunk)
    
    channels = default_speakers["maxInputChannels"]
    fs = int(default_speakers["defaultSampleRate"])
    print('Initialized record_audio_thread')
    while True:
        if isRun:
            record_chunk(p, stream, filename, sample_format, fs, chunk, channels, seconds)
            isDoneProcessRecord = True
        if isBreak:
            print('Stop the record_audio_thread')
            break

def audio_record():
    filename = "audio.wav"

    model_size = 'medium.en'
    #model_size = "large-v3"
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    global isDoneProcessRecord
    global isRun
    global transcript_bind
    global isBreak
    print('Initialized audio_record')
    while True:
        if (isRun and isDoneProcessRecord):
            transcription = transcribe_chunk(model, filename)
            transcript_bind += transcription
            isDoneProcessRecord = False
            os.remove(filename)
        
        if isBreak:
            print('Stop the audio_record')
            break

def keyboard_input_thread():
    global isRun
    global transcript_bind
    global NEON_GREEN
    global RESET_COLOR
    global isBreak
    global isDoneProcessRecord
    print('Initialized keyboard_input_thread')
    while True:
        key = cv2.waitKey(1) & 0xFF
        if ((key == ord('w') or keyboard.is_pressed('w')) and isRun):
            print('Stop Recording!')
            isRun = False
            isDoneProcessRecord = False
            print(NEON_GREEN + transcript_bind + RESET_COLOR)
            ask_chatgpt(transcript_bind)
            #print(f"Answer: {groq_execute(transcript_bind)}")
        if ((key == ord('q') or keyboard.is_pressed('q')) and not isRun):
            print('Start Recording!')
            transcript_bind = ' '
            isRun = True
        if ((key == ord('0') or keyboard.is_pressed('0')) and not isBreak):
            isBreak = True
            print('Stop the keyboard_input_thread')
            break

if __name__ == "__main__":
    isRun = False
    isDoneProcessRecord = False
    transcript_bind = ' '
    isBreak = False
    NEON_GREEN = "\033[1;32m"
    RESET_COLOR = "\033[1;31m"
    thread = threading.Thread(target=audio_record)
    thread2 = threading.Thread(target=record_audio_thread)
    thread3 = threading.Thread(target=keyboard_input_thread)

    thread.start()
    thread2.start()
    thread3.start()
    thread.join()
    thread2.join()
    thread3.join()
