import os
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import requests

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
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        video_url = extract_video_url(url)
        return jsonify({'video_url': video_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy-download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    filename = request.args.get('filename', 'video_no_watermark.mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.meta.ai/',
        }
        req = requests.get(url, stream=True, headers=headers, timeout=60)
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024 * 256)),
            content_type=req.headers.get('content-type', 'video/mp4'),
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
