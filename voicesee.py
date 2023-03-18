from issai.asr import ASR
from issai.tts import TTS
from issai import utils
import openai
import subprocess
import telebot
import requests
from PIL import Image
import json
import os
from urllib.parse import urlencode
from twilio.twiml.voice_response import VoiceResponse
from llama_index import GPTSimpleVectorIndex, Document, SimpleDirectoryReader
os.environ['OPENAI_API_KEY'] = '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'

# Loading from a directory
from pathlib import Path
from gpt_index import download_loader
PDFReader = download_loader("PDFReader")
from twilio.rest import Client

# Set up Twilio API credentials
account_sid = 'AC40d557cb23044baf6a7d7f68276fad9f'
auth_token = 'd9d38b0cc3cd358da072ddda9640841e'
twilio_number = '+13854834301'

# Initialize Twilio client
client = Client(account_sid, auth_token)

def call_number(number):
    response = VoiceResponse()
    response.say("Hello, this is a message during the phone call.")
    twiml_url = 'http://twimlets.com/echo?Twiml=' + urlencode(response.to_xml())
    call = client.calls.create(
        to=number,
        from_=twilio_number,
        url=twiml_url
    )
    return call.sid


openai.api_key = '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'
# create directories to save
# input and output files
utils.make_dir("input/voice")
utils.make_dir("input/document")
utils.make_dir("output")

# initialize telegram bot
isRunning = False
tele_token = "5798903974:AAEn4e7bNleNPubLty6q4fTV5tMuPm6_mCU"
tele_bot = telebot.TeleBot(tele_token, threaded=True)

# the first message to ChatGPT
messages = [
    # system message first, it helps set the behavior of the assistant
    {"role": "system", "content": "You are a usefull  assistant"},
]
reset_chat = False  # set False if you want ChatGPT to use chat history

# initialize ASR and TTS models
asr = ASR(lang='en', model='google') # to use offline vosk asr: 'google' -> 'vosk'
tts = TTS('google') # to use offline pyttsx3 tts: 'google' -> 'other'

# def read_image(image_path):
#         # Open the image using PIL
#         with Image.open(image_path) as image:
#             # Use pytesseract to recognize text in the image
#             text = pytesseract.image_to_string(image, lang='eng')
#             print(text)
#             response = openai.Completion.create(
#             model="code-davinci-001",
#             prompt=f"extract what note and nationality from {text}",
#             temperature=0,
#             max_tokens=150,
#             top_p=1.0,
#             frequency_penalty=0.0,
#             presence_penalty=0.0,
#             stop=["#", ";"]
#             )
#             generated_text = response.choices[0].text
#             print("ChatGPT:",generated_text)
        
#         # return generated_text



@tele_bot.message_handler(commands=["start", "go"])
def start_handler(message):
    print(message)
    global isRunning
    if not isRunning:
        tele_bot.send_message(message.chat.id, "Welcome to VoiceSee 🙋‍♂️ , How can i help you today!")
        isRunning = True

# @tele_bot.message_handler(commands=["document"])
# def document_handle(message):
#     # process the voice message
#     print("doc file")
#     file_info = tele_bot.get_file(message.document.file_id)
#     file_data = tele_bot.download_file(file_info.file_path)

#     raw_doc_path = './input/' + file_info.file_path
#     with open(raw_doc_path, 'wb') as f:
#         f.write(file_data)

#     loader = PDFReader()
#     documents = loader.load_data(file=Path(''))
#     index = GPTSimpleVectorIndex(documents)
#     index.save_to_disk('index.json')
#     index = GPTSimpleVectorIndex.load_from_disk(raw_doc_path)
#     response1 = index.query("describe and explain the document?")


#     tele_bot.reply_to(message, "You: Sent a document " )
#     print("User:", asr.message)
#     output_audio_path = os.path.join('output', 'answer.mp3')
#     tts.convert(response1, output_audio_path)
#     tele_bot.send_voice(message.chat.id, voice=open(output_audio_path, "rb"))

@tele_bot.message_handler(content_types=['photo'])
def photo_processing(message):
    photo_file = tele_bot.get_file(message.photo[-1].file_id) # get the last photo in the list
    TOKEN="5798903974:AAEn4e7bNleNPubLty6q4fTV5tMuPm6_mCU"
    # Get link to get file_path
    link1 = "https://api.telegram.org/bot{}/getfile?file_id={}".format(TOKEN, photo_file.file_id)
    r = requests.get(link1)
    file_path = r.json()["result"]["file_path"]

    # Link to download file
    link2 = "https://api.telegram.org/file/bot{}/{}".format(TOKEN, file_path)
    global img_link
    img_link = link2

    url = "https://v1.genr.ai/api/circuit-element/generate-captions"
    payload = {
        "img_url": img_link,
        "n_words": 15
    }
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, json=payload, headers=headers)
    print(response.text)
    parsed_output1 = json.loads(response.text)
    text1 = parsed_output1["output"]
    tele_bot.reply_to(message, "Image Shows: " + text1 )
    output_audio_path = os.path.join('output', 'answer.mp3')
    tts.convert(text1, output_audio_path)
    tele_bot.send_voice(message.chat.id, voice=open(output_audio_path, "rb"))


        
        


@tele_bot.message_handler(content_types=['voice'])
def voice_processing(message):
    # process the voice message
    file_info = tele_bot.get_file(message.voice.file_id)
    file_data = tele_bot.download_file(file_info.file_path)

    raw_audio_path = './input/' + file_info.file_path
    with open(raw_audio_path, 'wb') as f:
        f.write(file_data)

    #tele_bot.reply_to(message, "Processing...")
    input_audio_path = raw_audio_path + ".wav"
    process = subprocess.run(['ffmpeg', '-i', raw_audio_path, input_audio_path])
    if process.returncode != 0:
        raise Exception("Something went wrong")

    # convert the audio input to text
    asr.convert(input_audio_path)
    print(asr.convert(input_audio_path))

    tele_bot.reply_to(message, "You: " + asr.message)
    print("User:", asr.message)

    
# send the message to ChatGPT
    if "help" in asr.message:
        call_number("+917725912536")
        tele_bot.send_message(message.chat.id,"calling help.......")

    else:
        if reset_chat:
            chat_completion = openai.Completion.create(
                engine="text-davinci-003",
                prompt=asr.message,
                temperature=0,
                max_tokens=150,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
        else:
            messages.append({"role": "user", "content": asr.message})
            prompt = "\n".join([m["content"] for m in messages])
            chat_completion = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=150,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            messages.append({"role": "assistant", "content": chat_completion.choices[0].text})

        response = chat_completion.choices[0].text
        print("ChatGPT:",response)
    


        tele_bot.send_message(message.chat.id, response)

    output_audio_path = os.path.join('output', 'answer.mp3')

    # convert the answer 
    # 
    # to speech
    tts.convert(response, output_audio_path)

    tele_bot.send_voice(message.chat.id, voice=open(output_audio_path, "rb"))

    os.remove(raw_audio_path)
    os.remove(input_audio_path)
    os.remove(output_audio_path)

tele_bot.polling(none_stop=True)
