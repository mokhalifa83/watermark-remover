const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    if (url.pathname === '/api/extract' && request.method === 'POST') {
      return handleExtract(request);
    }

    if (url.pathname === '/api/proxy' && request.method === 'GET') {
      return handleProxy(request);
    }

    return new Response('ClearView API is running. Use /api/extract endpoint.', {
      headers: { 'Content-Type': 'text/plain', ...CORS_HEADERS },
    });
  },
};

async function handleExtract(request) {
  try {
    const { url: metaUrl } = await request.json();
    if (!metaUrl) {
      return jsonResponse({ error: 'No URL provided' }, 400);
    }

    const videoUrl = await extractVideoUrl(metaUrl);
    return jsonResponse({ video_url: videoUrl });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

async function handleProxy(request) {
  const url = new URL(request.url);
  const videoUrl = url.searchParams.get('url');
  const filename = url.searchParams.get('filename') || 'video_no_watermark.mp4';

  if (!videoUrl) {
    return jsonResponse({ error: 'No URL provided' }, 400);
  }

  const proxyHeaders = {
    'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
    'Referer': 'https://www.meta.ai/',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
  };

  try {
    const videoResponse = await fetch(videoUrl, { headers: proxyHeaders });

    if (videoResponse.status === 403) {
      return jsonResponse(
        { error: 'Video URL expired. Please try again with a fresh link.' },
        410,
      );
    }

    const responseHeaders = new Headers(videoResponse.headers);
    responseHeaders.set('Content-Disposition', `attachment; filename="${filename}"`);
    responseHeaders.set('Access-Control-Allow-Origin', '*');

    return new Response(videoResponse.body, {
      status: videoResponse.status,
      headers: responseHeaders,
    });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

async function extractVideoUrl(shareUrl) {
  const fetchHeaders = {
    'User-Agent':
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    Accept: 'text/html,application/xhtml+xml',
  };

  const response = await fetch(shareUrl, {
    headers: fetchHeaders,
    redirect: 'follow',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch page: ${response.status}`);
  }

  const text = await response.text();
  const mp4Regex = /https:\/\/[^\s<>"']+\.mp4(?:\?[^\s<>"']*)?/g;

  const candidates = [];
  let bestUrl = null;
  let bestResolution = 0;
  let fallbackUrl = null;
  let fallbackSize = 0;

  const seen = new Set();

  for (const match of text.matchAll(mp4Regex)) {
    let raw = match[0];

    let clean = raw
      .replace(/\\u0026/g, '&')
      .replace(/&amp;/g, '&')
      .replace(/\\\//g, '/')
      .replace(/\\u003c[\s\S]*$/, '')
      .replace(/\\$/, '');

    const oeMatch = clean.match(/oe=[a-fA-F0-9]{8}/);
    if (oeMatch) {
      clean = clean.substring(0, oeMatch.index + oeMatch[0].length);
    }

    const lessThanIdx = clean.indexOf('<');
    if (lessThanIdx !== -1) {
      clean = clean.substring(0, lessThanIdx);
    }

    if (seen.has(clean)) continue;
    seen.add(clean);

    const efgMatch = clean.match(/efg=([^&]+)/);
    if (!efgMatch) continue;

    try {
      const efgEncoded = efgMatch[1];
      const efgDecoded = decodeURIComponent(efgEncoded);
      const padding = (4 - (efgDecoded.length % 4)) % 4;
      const efgJson = atob(efgDecoded + '='.repeat(padding));
      const efg = JSON.parse(efgJson);

      const tag = efg.vencode_tag || efg.encoding_tag || '';
      const isProgressive = tag.includes('progressive');

      if (isProgressive) {
        const resMatch = tag.match(/(\d+)p/);
        const resolution = resMatch ? parseInt(resMatch[1], 10) : 0;
        candidates.push({ url: clean, resolution, tag });
      }

      if (!isProgressive && !efg.video_id && !tag.includes('dash-audio')) {
        const bitrate = efg.bitrate || 0;
        candidates.push({ url: clean, resolution: 0, tag, bitrate });
      }
    } catch {
      // skip entries with unparseable efg
    }
  }

  for (const c of candidates) {
    if (c.tag && c.tag.includes('progressive')) {
      if (c.resolution > bestResolution) {
        bestResolution = c.resolution;
        bestUrl = c.url;
      }
    }
  }

  if (!bestUrl) {
    for (const c of candidates) {
      if (c.bitrate && c.bitrate > fallbackSize) {
        fallbackSize = c.bitrate;
        fallbackUrl = c.url;
      }
    }
    if (fallbackUrl) {
      bestUrl = fallbackUrl;
    }
  }

  if (!bestUrl) {
    throw new Error(
      'Could not find a video in this Meta AI link. Make sure it is a direct video post URL.',
    );
  }

  return bestUrl;
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
  });
}
