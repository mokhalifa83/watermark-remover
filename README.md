# Meta AI Watermark Remover

A professional web application to remove watermarks from Meta AI videos.

## Project Structure

- `backend/`: Flask application and API.
- `frontend/`: Static frontend files (HTML, CSS, JS).

## Setup & Running

### 1. Backend Setup

Prerequisites: Python 3.8+

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`.

### 2. Frontend Setup

1. Open `frontend/index.html` in your browser.
2. OR serve it using a simple HTTP server for better experience:
   ```bash
   cd frontend
   python -m http.server 8000
   ```
   Then open `http://localhost:8000` in your browser.

## Usage

1. Copy a video share link from Meta AI (Facebook/Instagram/WhatsApp).
2. Paste it into the input field on the web page.
3. Click "Remove Watermark".
4. Download the processed video.

## Notes

- The current implementation contains a placeholder for the actual video extraction and processing logic in `scraper.py` and `app.py`. You will need to implement the specific scraping logic based on the target Meta AI URL structure.
- Video processing (watermark removal) requires OpenCV integration which is stubbed out for now.
