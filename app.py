import os
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import requests

from scraper import extract_video_url
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Move index route to handle base path correctly
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
        # TODO: Add logic to download video, process it (remove watermark), and return the processed file path
        # For now, just returning the extracted video URL
        
        response = jsonify({'message': 'Video URL extracted', 'video_url': video_url})
        
        # Add cache-control headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy-download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.meta.ai/'
        }
        req = requests.get(url, stream=True, headers=headers)
        
        response = Response(stream_with_context(req.iter_content(chunk_size=4096)),
                          content_type=req.headers.get('content-type', 'video/mp4'),
                          headers={'Content-Disposition': f'attachment; filename={filename}'})
        
        # Add cache-control headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
