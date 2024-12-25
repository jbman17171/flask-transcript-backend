import os
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from youtube_transcript_api import YouTubeTranscriptApi

# Bright Data proxy credentials
PROXY_HOST = os.getenv("BRIGHTDATA_PROXY_HOST")
PROXY_PORT = os.getenv("BRIGHTDATA_PROXY_PORT")
PROXY_USERNAME = os.getenv("BRIGHTDATA_PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("BRIGHTDATA_PROXY_PASSWORD")

def fetch_transcript_with_youtube_api(video_id, language="en"):
    try:
        # Configure proxy URL
        proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

        # Patch the youtube-transcript-api session to use the proxy
        from requests import Session
        session = Session()
        session.proxies.update({
            "http": proxy_url,
            "https": proxy_url,
        })

        # Monkey-patch the session
        from youtube_transcript_api._api import YouTubeTranscriptApi as PatchedAPI
        PatchedAPI._session = session

        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return {"status": "success", "transcript": transcript}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 400


def validate_video_with_playwright(video_url):
    try:
        with sync_playwright() as p:
            # Configure Playwright to use the proxy
            proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
            browser = p.chromium.launch(
                proxy={"server": proxy_url},
                headless=True
            )
            context = browser.new_context()
            page = context.new_page()

            # Navigate to the YouTube video URL
            page.goto(video_url, timeout=60000)
            if "video unavailable" in page.content():
                return False, "Video is unavailable"

            # Close the browser
            browser.close()
            return True, None
    except Exception as e:
        return False, str(e)


app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Flask Backend!"})

@app.route("/fetch-transcript", methods=["POST"])
def fetch_transcript():
    data = request.json
    video_url = data.get("video_url")
    language = data.get("language", "en")

    # Validate the YouTube video with Playwright
    is_valid, error_message = validate_video_with_playwright(video_url)
    if not is_valid:
        return jsonify({"status": "error", "message": error_message}), 400

    # Extract video ID
    from urllib.parse import urlparse, parse_qs
    try:
        parsed_url = urlparse(video_url)
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        if not video_id:
            raise ValueError("Invalid YouTube URL")
    except Exception:
        return jsonify({"status": "error", "message": "Invalid YouTube URL"}), 400

    # Fetch transcript using YouTube Transcript API with proxy
    response, status = fetch_transcript_with_youtube_api(video_id, language)
    return jsonify(response), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)