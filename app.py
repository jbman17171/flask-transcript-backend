from flask import Flask, request, jsonify
from flask_cors import CORS

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

def fetch_transcript_from_youtube(video_id, language="th"):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        formatter = JSONFormatter()
        return {"language_used": language, "transcript": formatter.format_transcript(transcript)}, 200
    except Exception as e:
        return {"error": str(e)}, 400

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins (can restrict later)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Flask Backend!"})

@app.route("/fetch-transcript", methods=["POST"])
def fetch_transcript():
    data = request.json
    video_url = data.get("video_url")
    language = data.get("language", "th")  # Default to Thai

    # Validate the video URL
    from urllib.parse import urlparse, parse_qs
    try:
        parsed_url = urlparse(video_url)
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        if not video_id:
            raise ValueError("Invalid YouTube URL")
    except Exception:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Fetch the transcript
    response, status = fetch_transcript_from_youtube(video_id, language)
    return jsonify(response), status

if __name__ == "__main__":
    app.run(port=8000, debug=True)