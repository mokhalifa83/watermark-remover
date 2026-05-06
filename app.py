import os
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import requests

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_file(os.path.join('frontend', 'index.html'))

try:
    from scraper_v2 import extract_video_url
except ImportError:
    from scraper import extract_video_url

@app.route('/api/remove-watermark', methods=['POST'])
def remove_watermark():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    print(f"Processing URL: {url}")
    try:
        video_url = extract_video_url(url)
        if not video_url:
            return jsonify({'error': 'Could not extract video URL. Please ensure the link is a direct video post.'}), 404
            
        return jsonify({
            'message': 'Video URL extracted', 
            'video_url': video_url,
            'success': True
        })
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy-download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    filename = request.args.get('filename', 'video_no_watermark.mp4')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        cdn_headers = {
            'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            'Referer': 'https://www.meta.ai/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        req = requests.get(url, stream=True, headers=cdn_headers, timeout=30)
        
        if req.status_code == 403:
            return jsonify({'error': 'Video URL access denied by Meta CDN. Try refreshing.'}), 403

        content_type = req.headers.get('content-type', 'video/mp4')
        response_headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Allow-Origin': '*',
        }
        
        content_length = req.headers.get('Content-Length')
        if content_length:
            response_headers['Content-Length'] = content_length

        return Response(
            stream_with_context(req.iter_content(chunk_size=8192)),
            content_type=content_type,
            headers=response_headers
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
