# VidSumm 🎬🤖

**VidSumm** is an AI-powered Video and YouTube Summarizer that helps users quickly understand the content of videos using NLP-based summarization. It supports both YouTube video URLs and offline video files.

---

## 🚀 Features

- 🔍 Extracts transcripts from YouTube using the YouTube Transcript API
- 🎧 Converts audio to text using `yt-dlp` + `SpeechRecognition` for offline videos
- 🧠 Summarizes content using Hugging Face Transformers and Sumy’s LSA summarizer
- 🌐 Simple web interface using Flask
- 🧾 Batch processing support
- 🔐 User authentication system
- 🧠 Customizable summary length and format

---

## 📦 Tech Stack

- **Backend**: Python, Flask
- **NLP**: Hugging Face Transformers, Sumy (LSA)
- **Audio Processing**: yt-dlp, SpeechRecognition
- **Frontend**: HTML, CSS, Bootstrap
- **Others**: Git, GitHub, Jupyter (for prototyping)

---

## ⚙️ Installation

```bash
git clone https://github.com/your-username/VidSumm.git
cd VidSumm
pip install -r requirements.txt
