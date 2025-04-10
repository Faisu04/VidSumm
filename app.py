from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import re
import ffmpeg
import speech_recognition as sr
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from yt_dlp import YoutubeDL
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.tokenizers import Tokenizer
import nltk

# Download necessary resources
nltk.download('punkt')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to extract video ID from YouTube URL
def extract_video_id(youtube_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    return match.group(1) if match else None

# Function to fetch transcript using YouTubeTranscriptAPI
def fetch_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except TranscriptsDisabled:
        return None
    except Exception as e:
        return None

# Function to summarize text
def summarize_text(text, method="transformers"):
    if not text:
        return "No text to summarize."

    if method == "transformers":
        summarizer = pipeline("summarization")
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        summary = " ".join([
            summarizer(chunk, max_length=300, min_length=100, do_sample=False)[0]["summary_text"]
            for chunk in chunks
        ])
        return summary
    elif method == "lsa":
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        # Increase the number of sentences for longer summaries
        summary = summarizer(parser.document, 15)  # Adjust this value for longer summaries
        return ' '.join([str(sentence) for sentence in summary])

# Function to download audio from YouTube
def download_audio(video_url, output_path="video_audio.mp3"):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        return None

# Function to transcribe audio
def transcribe_audio(audio_path):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Audio is not clear enough to transcribe."
    except sr.RequestError as e:
        return f"Could not connect to the transcription service. Error: {e}"
    except FileNotFoundError:
        return "Audio file not found."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Function to extract audio from video
def extract_audio(video_path, audio_output_path):
    try:
        ffmpeg.input(video_path).output(
            audio_output_path, format='wav', ac=1, ar='16000'
        ).run(overwrite_output=True)
    except Exception as e:
        raise RuntimeError(f"Error extracting audio: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize_youtube', methods=['POST'])
def summarize_youtube():
    data = request.json
    youtube_url = data.get("youtube_url")
    if not youtube_url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = extract_video_id(youtube_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    transcript = fetch_transcript(video_id)
    if transcript:
        text = " ".join([i['text'] for i in transcript])
        summary = summarize_text(text)
        return jsonify({"summary": summary})
    else:
        return jsonify({"error": "Unable to fetch transcript"}), 500

@app.route('/summarize_offline', methods=['POST'])
def summarize_offline():
    if 'video' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    allowed_extensions = {'mp4', 'avi', 'mkv', 'mov'}
    if not file.filename.rsplit('.', 1)[-1].lower() in allowed_extensions:
        return jsonify({"error": f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"}), 400

    try:
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)

        audio_output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.wav')
        extract_audio(video_path, audio_output_path)

        text = transcribe_audio(audio_output_path)

        if "Error" in text:
            return jsonify({"error": text}), 500

        # Extend summary length for offline videos
        summary = summarize_text(text, method="lsa")  # Using LSA summarizer with extended summary length
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
