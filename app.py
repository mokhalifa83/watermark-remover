import os
import io
import requests
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS

from scraper import extract_video_url
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)


@app.route('/')
def index():
    return send_file(os.path.join('frontend', 'index.html'))


@app.route('/api/remove-watermark', methods=['POST'])
def remove_watermark():
    """
    Extracts the real video URL from Meta AI and streams the video
    bytes directly back to the client in a single response.

    This is the Vercel-compatible permanent fix:
    - We extract the CDN URL server-side (where yt-dlp can run)
    - We immediately proxy/stream the bytes back to the user
    - The client never touches Meta's CDN directly, so IP blocks don't matter
    - The CDN URL is used and discarded in milliseconds — expiry is irrelevant
    """
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Step 1: Extract the real CDN video URL (server-side, yt-dlp)
        video_url = extract_video_url(url)

        # Step 2: Stream the video bytes back immediately — in the SAME request
        # By the time the URL could expire, we've already started streaming the bytes
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.meta.ai/',
            'Accept': '*/*',
        }

        upstream = requests.get(video_url, headers=headers, stream=True, timeout=60)
        upstream.raise_for_status()

        content_type = upstream.headers.get('Content-Type', 'video/mp4')
        content_length = upstream.headers.get('Content-Length')

        response_headers = {
            'Content-Type': content_type,
            'Content-Disposition': 'attachment; filename="meta_ai_video_no_watermark.mp4"',
            'Cache-Control': 'no-store',
        }
        if content_length:
            response_headers['Content-Length'] = content_length

        return Response(
            stream_with_context(upstream.iter_content(chunk_size=1024 * 256)),
            headers=response_headers,
            status=200
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
