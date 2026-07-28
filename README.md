# ClearView.ai - Meta AI Watermark Remover

## Architecture
- **Frontend**: Static HTML/CSS/JS (hosted on any static host)
- **Backend**: Cloudflare Worker (JavaScript, not Python)

## Deployment

### 1. Backend (Cloudflare Worker)

```bash
npm install
npx wrangler login
npm run deploy
```

This deploys the worker to `https://clearview-api.<your-subdomain>.workers.dev`

### 2. Frontend (Cloudflare Pages)

```bash
npm run pages:deploy
```

Or deploy manually:
- Go to Cloudflare Dashboard → Pages → Create project
- Connect your Git repo or drag-and-drop the `frontend/` folder
- Set the worker URL in `script.js` (or use same domain with Pages Functions)

### Single Deployment (Frontend + Backend together)

For simplest setup, use Cloudflare Pages:
1. Upload `frontend/` folder as Pages project
2. Create a Pages Function at `functions/api/extract.js` and `functions/api/proxy.js`
3. Both frontend and API live on the same domain

## Why Cloudflare Worker instead of Python?
- No Vercel 10s timeout
- No Python dependency
- Free tier: 100k requests/day
- Edge-deployed (fast worldwide)
- JavaScript is faster for this task

## API Endpoints

### POST /api/extract
```json
{ "url": "https://www.meta.ai/vibes/post/..." }
```
Returns:
```json
{ "video_url": "https://video-arn2-1.xx.fbcdn.net/..." }
```

### GET /api/proxy
`/api/proxy?url=<encoded-video-url>&filename=video.mp4`
Proxies the video download with proper headers.
