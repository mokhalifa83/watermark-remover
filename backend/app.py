import os
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import requests

from scraper import extract_video_url
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/api/remove-watermark', methods=['POST'])
def remove_watermark():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        video_url = extract_video_url(url)
        # TODO: Add logic to download video, process it (remove watermark), and return the processed file path
        # For now, just returning the extracted video URL
        return jsonify({'message': 'Video URL extracted', 'video_url': video_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy-download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        req = requests.get(url, stream=True)
        return Response(stream_with_context(req.iter_content(chunk_size=1024)),
                        content_type=req.headers['content-type'],
                        headers={'Content-Disposition': f'attachment; filename={filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
