addEventListener("fetch", event => {
  event.respondWith(handle(event.request));
});

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(data, status) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

async function handle(request) {
  var url = new URL(request.url);
  if (url.pathname === "/api/extract" && request.method === "POST") return handleExtract(request);
  if (url.pathname === "/api/proxy" && request.method === "GET") return handleProxy(request);
  if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
  return new Response(HTML, {
    status: 200,
    headers: { "Content-Type": "text/html;charset=utf-8", ...CORS },
  });
}

async function handleExtract(request) {
  try {
    var data = await request.json();
    if (!data || !data.url) return json({ error: "No URL" }, 400);
    var videoUrl = await extractVideoUrl(data.url);
    return json({ video_url: videoUrl });
  } catch (err) {
    return json({ error: err.message }, 500);
  }
}

async function handleProxy(request) {
  var url = new URL(request.url);
  var videoUrl = url.searchParams.get("url");
  if (!videoUrl) return json({ error: "No URL" }, 400);
  try {
    var vr = await fetch(videoUrl, {
      headers: { "User-Agent": "facebookexternalhit/1.1", "Referer": "https://www.meta.ai/" },
    });
    if (vr.status === 403) return json({ error: "URL expired" }, 410);
    var h = new Headers(vr.headers);
    h.set("Access-Control-Allow-Origin", "*");
    return new Response(vr.body, { status: vr.status, headers: h });
  } catch (err) {
    return json({ error: err.message }, 500);
  }
}

async function extractVideoUrl(shareUrl) {
  var r = await fetch(shareUrl, {
    headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "en-US,en;q=0.9" },
    redirect: "follow",
  });
  if (!r.ok) throw new Error("Failed: " + r.status);
  var t = await r.text();
  var re = /https:\/\/[^\s<>"']+\.mp4(?:\?[^\s<>"']*)?/g;
  var cs = [];
  var seen = {};
  var m;
  while ((m = re.exec(t)) !== null) {
    var c = m[0].replace(/\\u0026/g, "&").replace(/&amp;/g, "&").replace(/\\\//g, "/");
    var oe = c.match(/oe=[a-fA-F0-9]{8}/);
    if (oe) c = c.substring(0, oe.index + oe[0].length);
    var lt = c.indexOf("<");
    if (lt > -1) c = c.substring(0, lt);
    if (seen[c]) continue;
    seen[c] = true;
    var efg = c.match(/efg=([^&]+)/);
    if (!efg) continue;
    try {
      var d = decodeURIComponent(efg[1]);
      var pg = (4 - (d.length % 4)) % 4;
      var meta = JSON.parse(atob(d + "=".repeat(pg)));
      var tag = meta.vencode_tag || meta.encoding_tag || "";
      if (tag.indexOf("progressive") > -1) {
        var res = tag.match(/(\d+)p/);
        cs.push({ u: c, r: res ? parseInt(res[1], 10) : 0, tag: tag });
      }
    } catch (e) {}
  }
  var best = null, bestR = 0;
  for (var i = 0; i < cs.length; i++) {
    if (cs[i].tag.indexOf("progressive") > -1 && cs[i].r > bestR) {
      best = cs[i].u;
      bestR = cs[i].r;
    }
  }
  if (!best) throw new Error("No video found");
  return best;
}

var HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ClearView</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body{background:#020202;color:#fff;line-height:1.6}
.container{max-width:1200px;margin:0 auto;padding:0 1.5rem}
.hero{min-height:90vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:4rem 0}
.hero h1{font-size:3rem;font-weight:900;margin-bottom:1rem}
.hero h1 span{background:linear-gradient(to right,#fff 20%,#ef4444 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{color:#a3a3a3;max-width:500px;margin:0 auto 2rem}
.input-group{border:1px solid rgba(255,50,50,0.15);padding:6px;border-radius:100px;display:flex;max-width:550px;margin:0 auto;background:rgba(255,255,255,0.03)}
input{flex:1;background:transparent;border:none;padding:1rem 1.5rem;font-size:1rem;color:#fff;outline:none}
input::placeholder{color:rgba(255,255,255,0.3)}
.btn{background:linear-gradient(135deg,#e50914 0%,#800000 100%);color:#fff;border:none;padding:0 1.5rem;border-radius:100px;font-weight:600;cursor:pointer;white-space:nowrap;box-shadow:0 4px 15px rgba(229,9,20,0.4)}
.btn:disabled{opacity:.7;cursor:not-allowed}
.result-card{margin-top:2rem;border:1px solid rgba(255,50,50,0.15);border-radius:24px;padding:2rem;max-width:700px;margin:auto}
.hidden{display:none!important}
.error{color:#ff4d4d;margin-top:1rem}
footer{padding:2rem 0;text-align:center;color:#a3a3a3;border-top:1px solid rgba(255,50,50,0.15)}
@media(max-width:768px){
.hero h1{font-size:2rem}
.input-group{flex-direction:column;border-radius:12px;padding:.75rem}
input{width:100%;padding:.8rem;text-align:center;margin-bottom:.5rem}
.btn{width:100%;padding:1rem}
}
</style>
</head>
<body>
<div class="container">
<section class="hero">
<h1>Remove Meta AI Watermarks<br><span>Free Online Tool</span></h1>
<p class="subtitle">Paste your Meta AI video link and get a clean video.</p>
<div class="input-group">
<input type="text" id="url" placeholder="Paste Meta AI video link...">
<button id="go" class="btn">Remove Watermark</button>
</div>
<p id="error" class="error hidden"></p>
<div id="result" class="result-card hidden">
<div id="videoWrapper"></div>
<div class="result-actions" style="margin-top:1.5rem;display:flex;gap:1rem;justify-content:center">
<a href="#" id="download" class="btn" style="display:inline-flex;align-items:center;gap:.5rem;padding:.75rem 1.5rem;text-decoration:none">Download</a>
<button id="reset" class="btn" style="background:transparent;border:1px solid rgba(255,255,255,0.2);box-shadow:none">Another</button>
</div>
</div>
</section>
</div>
<footer><div class="container"><p>&copy; 2026 ClearView</p></div></footer>
<script>
document.getElementById("go").onclick=async function(){
  var u=document.getElementById("url").value.trim();
  var er=document.getElementById("error");
  var r=document.getElementById("result");
  if(!u){er.textContent="Enter a URL";er.classList.remove("hidden");return;}
  er.classList.add("hidden");r.classList.add("hidden");
  var btn=document.getElementById("go");btn.disabled=true;btn.textContent="Processing...";
  try{
    var p=await(await fetch("/api/extract",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:u})})).json();
    if(p.error)throw new Error(p.error);
    var proxyUrl="/api/proxy?url="+encodeURIComponent(p.video_url)+"&filename=video.mp4";
    document.getElementById("videoWrapper").innerHTML="<video controls width=\"100%\" src=\""+proxyUrl+"\" autoplay></video>";
    document.getElementById("download").href=proxyUrl;
    r.classList.remove("hidden");
  }catch(e){er.textContent=e.message;er.classList.remove("hidden");}
  finally{btn.disabled=false;btn.textContent="Remove Watermark";}
};
document.getElementById("reset").onclick=function(){
  document.getElementById("result").classList.add("hidden");
  document.getElementById("url").value="";
};
</script>
</body>
</html>`;
