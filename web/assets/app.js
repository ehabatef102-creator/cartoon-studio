/* ============================================================
   استوديو الكرتون — محرك الواجهة
   وضعان:
   - خادم: /api/* (سيناريو LLM + Edge TTS + ffmpeg مونتاج)
   - متصفح: Pollinations (صور) + WebAudio (موسيقى) + Canvas/MediaRecorder (مونتاج WebM)
   ============================================================ */
(function () {
  "use strict";

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const icons = () => window.lucide && lucide.createIcons();

  const CLIENT_STYLE =
    "2D animation, soft painterly backgrounds, warm cinematic lighting, expressive big-eyed characters, " +
    "clean bold outlines, consistent character model sheets, cinematic 2.39:1 wide framing, " +
    "dramatic volumetric light, filmic color grade, high detail feature-film quality";

  const BEATS = ["setup", "inciting", "rising1", "rising2", "climax", "falling", "resolution"];
  const BEAT_AR = { setup: "تمهيد", inciting: "الحادثة", rising1: "تصاعد ١", rising2: "تصاعد ٢", climax: "الذروة", falling: "التنفيس", resolution: "الحل", crossover: "عالم مشترك" };

  const MOTION = {
    setup: [1.04, 1.12, 0, 0],
    inciting: [1.06, 1.18, 0.01, 0],
    rising1: [1.08, 1.22, -0.02, 0.01],
    rising2: [1.12, 1.3, 0.01, -0.02],
    climax: [1.18, 1.36, 0.02, 0.01],
    falling: [1.24, 1.06, 0, 0],
    resolution: [1.2, 1.0, 0, 0],
    crossover: [1.06, 1.16, 0.02, 0],
  };

  const state = {
    mode: null,
    token: localStorage.getItem("studio_token") || "",
    apiBase: (localStorage.getItem("studio_api_base") || "").replace(/\/+$/, ""),
    packs: [],
    selected: 1,
    project: null,
    running: false,
    meta: { universe: null },
  };

  function apiUrl(path) {
    return state.apiBase + path;
  }

  let SHARED_AC = null;
  function sharedAudio() {
    if (!SHARED_AC) SHARED_AC = new (window.AudioContext || window.webkitAudioContext)();
    return SHARED_AC;
  }

  const options = () => ({
    music: $("#opt-music").checked,
    motion: $("#opt-motion").checked,
    tts: $("#opt-tts").checked,
    sceneSec: parseInt($("#scene-sec").value, 10) || 8,
  });

  /* ---------------- أدوات مساعدة ---------------- */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  async function fetchJSON(url, opts) {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }

  function setMsg(text, type) {
    const m = $("#form-msg");
    m.textContent = text || "";
    m.className = "form-msg" + (type ? " is-" + type : "") + (text ? "" : " is-hidden");
  }

  function beatName(b) {
    return BEAT_AR[b] || b || "";
  }

  /* ---------------- وضع التشغيل ---------------- */
  async function detectMode() {
    const bases = [];
    if (state.apiBase) bases.push(state.apiBase);
    bases.push(""); // نفس الأصل (الخادم المستضاف ذاتيًا)
    const token = state.token || "admin123";
    for (const base of bases) {
      try {
        const r = await fetch(base + "/api/packs", { headers: { "x-admin-token": token } });
        if (r.ok) {
          const d = await r.json();
          if (d && Array.isArray(d.packs)) {
            state.mode = "server";
            state.apiBase = base;
            if (!state.token) state.token = token;
            return d;
          }
        }
      } catch (e) { /* جرّب الأساس التالي */ }
    }
    state.mode = "client";
    try {
      const d = await fetchJSON("packs.json");
      return d;
    } catch (e) {
      throw new Error("تعذر تحميل بيانات المكتبة (packs.json).");
    }
  }

  function renderModeBadge() {
    const b = $("#mode-badge");
    b.classList.remove("is-loading");
    if (state.mode === "server") {
      b.classList.add("is-server");
      b.innerHTML = '<i data-lucide="server"></i><span>وضع الخادم</span>';
    } else {
      b.classList.add("is-client");
      b.innerHTML = '<i data-lucide="globe"></i><span>وضع المتصفح</span>';
    }
    icons();
  }

  /* ---------------- العرض: الهيرو والمكتبة ---------------- */
  function renderHeroSlate() {
    const p = state.packs[0];
    if (!p) return;
    const img = $("#hero-slate-img");
    img.src = "https://image.pollinations.ai/prompt/" + encodeURIComponent(scenePrompt(p, p.pilot.scenes[0])).slice(0, 3000) + "&width=960&height=540&nologo=true&seed=7";
    img.onerror = () => { img.closest(".slate-media").style.background = "radial-gradient(circle at 30% 20%, var(--ink-3), var(--ink))"; };
    $("#hero-slate-title").textContent = p.title;
    $("#hero-slate-sub").textContent = (p.pilot && p.pilot.title) || "";
  }

  function renderPacksGrid() {
    const g = $("#packs-grid");
    g.innerHTML = state.packs.map((p, i) => {
      const s0 = p.pilot && p.pilot.scenes ? p.pilot.scenes[0] : null;
      const img = s0 ? pollImageURL(scenePrompt(p, s0), 900, 520, 5 + i) : "";
      return `
      <article class="pack-card ${i === 0 ? "is-featured" : ""}" data-index="${i + 1}">
        <div class="pack-strip"></div>
        <div class="pack-media">
          <span class="pack-genre">${esc(p.genre)}</span>
          <img src="${img}" alt="${esc(p.title)}" loading="lazy">
        </div>
        <div class="pack-body">
          <h3>${esc(p.title)}</h3>
          <div class="pack-meta">
            <span><i data-lucide="users"></i>${esc(p.audience)}</span>
            <span><i data-lucide="film"></i>${esc(p.pilot.title)}</span>
            <span><i data-lucide="layers"></i>${p.pilot.scenes.length} مشاهد</span>
          </div>
          <p class="pack-logline">${esc(p.logline)}</p>
        </div>
      </article>`;
    }).join("");
    $$("#packs-grid .pack-card").forEach((c) => {
      c.addEventListener("click", () => { state.selected = +c.dataset.index; switchTab("template"); setMsg(""); scrollToStudio(); });
    });
    icons();
  }

  function renderPackPicker() {
    const w = $("#pack-picker");
    w.innerHTML = state.packs.map((p, i) => {
      const s0 = p.pilot.scenes[0];
      return `
      <label class="pack-option ${i + 1 === state.selected ? "is-active" : ""}" data-index="${i + 1}">
        <img class="opt-thumb" src="${pollImageURL(scenePrompt(p, s0), 160, 120, 100 + i)}" alt="">
        <span><span class="opt-name">${esc(p.title)}</span><br><span class="opt-sub">${esc(p.genre)} · ${p.pilot.scenes.length} مشاهد</span></span>
      </label>`;
    }).join("");
    $$("#pack-picker .pack-option").forEach((o) => {
      o.addEventListener("click", () => {
        $$("#pack-picker .pack-option").forEach((x) => x.classList.remove("is-active"));
        o.classList.add("is-active");
        state.selected = +o.dataset.index;
      });
    });
    icons();
  }

  function scrollToStudio() {
    document.querySelector("#studio").scrollIntoView({ behavior: "smooth" });
  }

  function switchTab(name) {
    $$(".tab").forEach((t) => t.classList.toggle("is-active", t.dataset.tab === name));
    $$(".tab-pane").forEach((p) => p.classList.toggle("is-hidden", p.dataset.pane !== name));
  }

  /* ---------------- برومبتات ---------------- */
  function scenePrompt(pack, scene) {
    if (scene.image_prompt) return scene.image_prompt;
    return scene.action || pack.logline;
  }

  function pollImageURL(prompt, w, h, seed) {
    return (
      "https://image.pollinations.ai/prompt/" +
      encodeURIComponent(prompt + " " + CLIENT_STYLE).slice(0, 3000) +
      `?width=${w}&height=${h}&nologo=true&seed=${seed}`
    );
  }

  async function pollImage(prompt, w, h, seed) {
    const r = await fetch(pollImageURL(prompt, w, h, seed));
    if (!r.ok) throw new Error("image " + r.status);
    return URL.createObjectURL(await r.blob());
  }

  /* ---------------- واجهة المخرجات ---------------- */
  function showOutput() {
    $("#output").classList.remove("is-hidden");
    $("#output").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function setPhase(name) {
    $$(".phase").forEach((p) => {
      const active = p.dataset.phase === name;
      p.classList.toggle("is-active", active);
      const order = ["writing", "images", "audio", "montage", "done"];
      p.classList.toggle("is-done", order.indexOf(name) > order.indexOf(p.dataset.phase));
    });
    $("#progress-fill").style.width = ({ writing: 12, images: 40, audio: 68, montage: 88, done: 100 })[name] + "%";
  }

  function setProgress(pct, text) {
    $("#progress-fill").style.width = Math.max(2, Math.min(100, pct)) + "%";
    if (text) $("#progress-text").textContent = text;
  }

  function sceneCardHTML(scene, idx, total) {
    return `
    <article class="scene-card" id="scene-card-${scene.num}">
      <div class="sc-img loading">
        <span class="sc-beat">${beatName(scene.beat)}</span>
        <img alt="${esc(scene.title)}" data-src="" data-prompt="${encodeURIComponent(scene.image_prompt || "")}" data-seed="${1000 + scene.num}">
      </div>
      <div class="sc-body">
        <h4>${esc(scene.title)}</h4>
        <div class="sc-meta">مشهد ${scene.num} من ${total} · ${scene.seconds} ث</div>
        <button class="btn btn-ghost btn-sm listen-btn" data-num="${scene.num}" style="margin-top:10px;font-size:.8rem">استمع للمشهد</button>
      </div>
    </article>`;
  }

  function renderScenes(scenes) {
    const g = $("#scenes-grid");
    g.innerHTML = scenes.map((s, i) => sceneCardHTML(s, i, scenes.length)).join("");
    $$(".listen-btn").forEach((b) => b.addEventListener("click", () => listenScene(+b.dataset.num)));
    icons();
  }

  function setSceneImage(num, url) {
    const img = $(`#scene-card-${num} img`);
    if (!img) return;
    img.onload = () => { img.classList.add("loaded"); img.closest(".sc-img").classList.remove("loading"); };
    img.src = url;
  }

  /* ---------------- أصوات ---------------- */
  const TTS_BLOB = {}; // num -> objectURL (قابل للفك داخل المونتاج)
  const TTS_PLAY = {}; // num -> url مباشر للاستماع (Google TTS)

  function googleTTSURL(text) {
    return "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ar&tts=1&total=1&idx=0&q=" +
      encodeURIComponent(text.slice(0, 180));
  }

  async function generateNarration(scene, num) {
    if (!options().tts) return;
    const text = (scene.dialogue || []).map((d) => d[d.length - 1]).filter(Boolean).join(" ");
    if (!text) return;
    TTS_PLAY[num] = googleTTSURL(text);
    try {
      const r = await fetch("https://oopstts.vercel.app/azure/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.slice(0, 1000), voice: "ar-SA-ZariyahNeural" }),
      });
      if (!r.ok) throw new Error("tts " + r.status);
      TTS_BLOB[num] = URL.createObjectURL(await r.blob());
    } catch (e) { /* المونتاج يكمل بموسيقى + ترجمة */ }
  }

  async function listenScene(num) {
    const scene = state.project.pilot.scenes.find((s) => s.num === num);
    if (!scene) return;
    const text = (scene.dialogue || []).map((d) => d[d.length - 1]).filter(Boolean).join(" ");
    if (!text) return;
    if (TTS_BLOB[num]) {
      new Audio(TTS_BLOB[num]).play().catch(() => {});
      return;
    }
    if (TTS_PLAY[num]) {
      const a = new Audio(TTS_PLAY[num]);
      a.crossOrigin = "anonymous";
      a.play().catch(() => {});
      return;
    }
    if (window.speechSynthesis) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "ar-SA";
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    }
  }

  /* ---------------- المونتاج (Canvas + MediaRecorder) ---------------- */
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }

  function drawWrappedText(ctx, text, cx, y, maxW, lineH) {
    ctx.direction = "rtl";
    ctx.textAlign = "center";
    const words = text.split(/\s+/);
    let line = "";
    const lines = [];
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxW && line) {
        lines.push(line);
        line = w;
      } else line = test;
    }
    if (line) lines.push(line);
    const start = y - (lines.length - 1) * lineH;
    lines.forEach((l, i) => {
      ctx.direction = "rtl";
      ctx.textAlign = "center";
      ctx.fillText(l, cx, start + i * lineH, maxW);
    });
  }

  async function makeMusicBuffer(ac) {
    const dur = 8, sr = ac.sampleRate;
    const off = new OfflineAudioContext(2, sr * dur, sr);
    const master = off.createGain();
    master.gain.value = 0.16;
    master.connect(off.destination);
    const chords = [[130.81, 164.81, 196.0], [110.0, 146.83, 174.61], [98.0, 130.81, 164.81], [87.31, 110.0, 146.83]];
    chords.forEach((freqs, ci) => {
      const t0 = (ci * dur) / chords.length;
      freqs.forEach((f, i) => {
        const osc = off.createOscillator();
        osc.type = i === 0 ? "triangle" : "sawtooth";
        osc.frequency.value = f;
        osc.detune.value = i * 4;
        const filt = off.createBiquadFilter();
        filt.type = "lowpass";
        filt.frequency.value = 900 + i * 300;
        const g = off.createGain();
        g.gain.setValueAtTime(0, t0);
        g.gain.linearRampToValueAtTime(0.6, t0 + 1.2);
        g.gain.linearRampToValueAtTime(0.45, t0 + dur / chords.length - 1.4);
        g.gain.linearRampToValueAtTime(0, t0 + dur / chords.length);
        osc.connect(filt).connect(g).connect(master);
        osc.start(t0);
        osc.stop(t0 + dur / chords.length);
      });
    });
    const lfo = off.createOscillator();
    lfo.frequency.value = 0.25;
    const lfoGain = off.createGain();
    lfoGain.gain.value = 0.05;
    lfo.connect(lfoGain).connect(master.gain);
    lfo.start();
    const buf = await off.startRendering();
    return buf;
  }

  function drawScene(ctx, canvas, scene, image, local, dur, nextImage, globalT) {
    const W = canvas.width, H = canvas.height;
    ctx.fillStyle = "#0d0b12";
    ctx.fillRect(0, 0, W, H);

    const m = MOTION[scene.beat] || MOTION.setup;
    const p = easeInOut(Math.min(1, local / dur));
    const scale = lerp(m[0], m[1], p);
    const dx = lerp(m[2], m[3], p);

    const img = image.image;
    const iw = img.naturalWidth || W, ih = img.naturalHeight || H;
    const cover = Math.max(W / iw, H / ih) * scale;
    const dw = iw * cover, dh = ih * cover;
    const cx = W / 2 + dx * W * 0.05;
    const cy = H / 2;
    ctx.drawImage(img, cx - dw / 2, cy - dh / 2, dw, dh);

    if (nextImage && local > dur - 0.6) {
      const a = (local - (dur - 0.6)) / 0.6;
      ctx.globalAlpha = a;
      ctx.drawImage(nextImage.image, cx - dw / 2, cy - dh / 2, dw, dh);
      ctx.globalAlpha = 1;
    }

    // أشرطة السينما
    ctx.fillStyle = "#0d0b12";
    ctx.fillRect(0, 0, W, H * 0.07);
    ctx.fillRect(0, H - H * 0.07, W, H * 0.07);

    ctx.font = "700 26px Changa, sans-serif";
    ctx.fillStyle = "rgba(255, 217, 122, 0.95)";
    ctx.direction = "ltr";
    ctx.textAlign = "left";
    ctx.fillText("مشهد " + scene.num, 28, 42);
    ctx.direction = "rtl";
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(244, 239, 228, 0.55)";
    ctx.fillText(Math.floor(globalT / 60) + ":" + String(Math.floor(globalT % 60)).padStart(2, "0"), W / 2, 42);

    // الحوار/النص
    const caption = (scene.dialogue || []).map((d) => d[d.length - 1]).filter(Boolean).join(" ");
    if (caption) {
      ctx.font = "500 28px Tajawal, sans-serif";
      ctx.fillStyle = "rgba(21, 18, 28, 0.72)";
      const bandY = H - H * 0.19;
      ctx.fillRect(40, bandY, W - 80, 104);
      ctx.fillStyle = "#f4efe4";
      drawWrappedText(ctx, caption, W / 2, bandY + 58, W - 130, 38);
    }
  }

  async function renderMontage(project, images, narration, opt) {
    const ac = sharedAudio();
    try { await ac.resume(); } catch (e) {}
    const canvas = document.createElement("canvas");
    canvas.width = 1280;
    canvas.height = 720;
    const ctx = canvas.getContext("2d");

    const scenes = project.pilot.scenes;
    const durs = scenes.map((s) => Math.max(2, Math.min(opt.sceneSec, s.seconds || opt.sceneSec)));
    const total = durs.reduce((a, b) => a + b, 0);
    const starts = [];
    let acc = 0;
    for (const d of durs) { starts.push(acc); acc += d; }

    // تحميل الصور
    const loaded = [];
    for (let i = 0; i < scenes.length; i++) {
      const img = new Image();
      await new Promise((res) => { img.onload = res; img.onerror = res; img.src = images[i]; });
      loaded.push(img);
    }

    // الموسيقى
    const music = opt.music ? await makeMusicBuffer(ac) : null;
    const master = ac.createGain();
    master.gain.value = 1;
    const dest = ac.createMediaStreamDestination();
    master.connect(dest);
    let musicNode = null;
    if (music) {
      musicNode = ac.createBufferSource();
      musicNode.buffer = music;
      musicNode.loop = true;
      musicNode.connect(master);
      musicNode.start();
    }

    // التعليق الصوتي
    const voiceGain = ac.createGain();
    voiceGain.gain.value = 0.9;
    voiceGain.connect(master);
    const scheduled = [];
    for (let i = 0; i < scenes.length; i++) {
      const src = narration[i];
      if (!src) continue;
      try {
        const r = await fetch(src);
        const buf = await ac.decodeAudioData(await r.arrayBuffer());
        scheduled.push({ start: starts[i], buf });
      } catch (e) { /* نكمل بدون */ }
    }

    const stream = new MediaStream([
      ...canvas.captureStream(30).getVideoTracks(),
      ...dest.stream.getAudioTracks(),
    ]);
    const mime = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"]
      .find((m) => MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) || "video/webm";
    const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 4e6 });
    const chunks = [];
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const done = new Promise((res) => { rec.onstop = () => res(new Blob(chunks, { type: mime })); });

    const startT = ac.currentTime + 0.4;
    for (const s of scheduled) {
      const src = ac.createBufferSource();
      src.buffer = s.buf;
      src.connect(voiceGain);
      src.start(startT + s.start);
    }

    rec.start(250);
    setProgress(88, "المونتاج يعمل الآن — لا تُغلق التبويب…");
    const draw = () => {
      const t = ac.currentTime - startT;
      let idx = scenes.length - 1;
      for (let i = 0; i < scenes.length; i++) {
        if (t < starts[i] + durs[i]) { idx = i; break; }
      }
      const local = Math.max(0, t - starts[idx]);
      drawScene(ctx, canvas, scenes[idx], loaded[idx], local, durs[idx], loaded[idx + 1], t);
      if (t < total + 0.5) requestAnimationFrame(draw);
      else { try { rec.stop(); } catch (e) {} }
    };
    requestAnimationFrame(draw);

    const blob = await done;
    if (musicNode) { try { musicNode.stop(); } catch (e) {} }
    return blob;
  }

  /* ---------------- الوضع: متصفح ---------------- */
  function storyToPack(idea) {
    let chunks = idea.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);
    if (chunks.length < 2) {
      const parts = idea.split(/[.!؟?]\s+/).map((s) => s.trim()).filter((s) => s.length > 30);
      if (parts.length >= 2) chunks = parts;
      else chunks = [idea];
    }
    chunks = chunks.slice(0, 8);
    const first = (idea.split("\n")[0] || "حلقتك المخصصة").trim().slice(0, 40);
    const scenes = chunks.map((chunk, i) => ({
      num: i + 1,
      title: "مشهد " + (i + 1),
      seconds: 8,
      mood: "مغامرة",
      beat: BEATS[Math.min(i, BEATS.length - 1)],
      dialogue: [[null, chunk]],
      action: chunk,
      image_prompt: chunk,
      sfx: [],
      camera: [],
    }));
    return {
      slug: "custom",
      title: first,
      genre: "فكرة مخصصة",
      audience: "—",
      logline: idea.slice(0, 220),
      pilot: {
        title: "حلقتك المخصصة",
        duration: chunks.length + " مشاهد",
        hook: idea.slice(0, 150),
        moral: "",
        scenes,
      },
      characters: [],
    };
  }

  async function runClientJob(idea) {
    const opt = options();
    let project;
    if (idea) {
      project = storyToPack(idea);
    } else {
      project = JSON.parse(JSON.stringify(state.packs[state.selected - 1]));
    }
    state.project = project;

    $("#output-title").textContent = project.title + " — " + project.pilot.title;
    $("#output-sub").textContent = "مولد في المتصفح بأدوات مجانية (Pollinations + WebAudio + Canvas).";
    showOutput();
    renderScenes(project.pilot.scenes);
    setPhase("writing");
    setProgress(6, "تجهيز المشاهد وبرومبتات الإخراج…");
    await new Promise((r) => setTimeout(r, 400));

    // الصور
    setPhase("images");
    const images = [];
    for (let i = 0; i < project.pilot.scenes.length; i++) {
      const s = project.pilot.scenes[i];
      setProgress(10 + Math.round(((i + 1) / project.pilot.scenes.length) * 55), `توليد الصورة السينمائية ${i + 1} من ${project.pilot.scenes.length}…`);
      try {
        const url = await pollImage(scenePrompt(project, s), 1280, 720, 2000 + s.num);
        images.push(url);
        setSceneImage(s.num, url);
      } catch (e) {
        images.push("");
      }
    }

    // التعليق الصوتي
    setPhase("audio");
    if (opt.tts) {
      setProgress(72, "توليد التعليق الصوتي للمشاهد…");
      for (const s of project.pilot.scenes) await generateNarration(s, s.num);
    }

    // المونتاج
    setPhase("montage");
    const narration = project.pilot.scenes.map((s) => TTS_BLOB[s.num]);
    let videoBlob = null;
    if (images.some(Boolean)) {
      try {
        videoBlob = await renderMontage(project, images, narration, opt);
      } catch (e) {
        console.error("montage failed", e);
      }
    }

    setPhase("done");
    setProgress(100, "اكتمل الإنتاج!");
    renderResultActions(project, images, videoBlob, opt);
  }

  function download(blob, name) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  async function renderResultActions(project, images, videoBlob, opt) {
    const box = $("#result-actions");
    box.innerHTML = "";

    const zips = document.createElement("script");
    if (videoBlob) {
      const video = document.createElement("video");
      video.controls = true;
      video.className = "preview-video";
      video.src = URL.createObjectURL(videoBlob);
      $("#result-video .result-empty").replaceWith(video);
    }

    const addBtn = (icon, label, fn, disabled) => {
      const b = document.createElement("button");
      b.className = "btn " + (disabled ? "btn-ghost" : "btn-gold");
      b.innerHTML = `<i data-lucide="${icon}"></i> ${label}`;
      if (disabled) b.disabled = true;
      b.onclick = fn;
      box.appendChild(b);
      icons();
      return b;
    };

    if (videoBlob) {
      addBtn("download", "تحميل الفيديو (WebM)", () => download(videoBlob, project.slug + "-montage.webm"));
    } else {
      addBtn("clapperboard", "الفيديو غير متاح", () => {}, true);
    }
    addBtn("image", "تحميل الصور كملف ZIP", () => downloadImagesZip(project, images));
    addBtn("file-text", "تحميل السيناريو (Markdown)", () => download(new Blob([markdownOf(project)], { type: "text/markdown;charset=utf-8" }), project.slug + "-script.md"));
    const listen = addBtn("audio-lines", "استمع للقصة كاملة", () => listenFullStory(project));

    if (window.JSZip) return;
    if (!zips.dataset.loaded) {
      zips.dataset.loaded = "1";
      zips.src = "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js";
      zips.onerror = () => {
        zips.remove();
      };
      document.head.appendChild(zips);
    }
  }

  async function downloadImagesZip(project, images) {
    if (!window.JSZip) {
      for (let i = 0; i < images.length; i++) {
        if (!images[i]) continue;
        try {
          const blob = await (await fetch(images[i])).blob();
          download(blob, project.slug + "-scene-" + (i + 1) + ".jpg");
        } catch (e) {}
      }
      return;
    }
    const zip = new JSZip();
    for (let i = 0; i < images.length; i++) {
      if (!images[i]) continue;
      try {
        const blob = await (await fetch(images[i])).blob();
        zip.file("scene_" + String(i + 1).padStart(2, "0") + ".jpg", blob);
      } catch (e) {}
    }
    const blob = await zip.generateAsync({ type: "blob" });
    download(blob, project.slug + "-scenes.zip");
  }

  function markdownOf(project) {
    let md = "# " + project.title + "\n\n" + (project.logline || "") + "\n\n";
    project.pilot.scenes.forEach((s) => {
      md += `## المشهد ${s.num} — ${s.title} (${s.seconds} ث)\n\n${s.action}\n\n`;
      (s.dialogue || []).forEach((d) => {
        md += `- **${d[0] || "الراوي"}:** ${d[d.length - 1]}\n`;
      });
      md += "\n---\n\n";
    });
    return md;
  }

  function listenFullStory(project) {
    const parts = project.pilot.scenes
      .map((s) => (s.dialogue || []).map((d) => d[d.length - 1]).filter(Boolean).join(" "))
      .filter(Boolean);
    if (!parts.length) return;
    const urls = parts.map((p) => googleTTSURL(p));
    if (window.speechSynthesis) speechSynthesis.cancel();
    let i = 0;
    const next = () => {
      if (i >= urls.length) return;
      const a = new Audio(urls[i++]);
      a.onended = next;
      a.onerror = () => setTimeout(next, 300);
      a.play().catch(() => setTimeout(next, 300));
    };
    next();
  }

  /* ---------------- الوضع: خادم ---------------- */
  async function runServerJob(idea) {
    const opt = options();
    const body = {
      index: idea ? null : state.selected,
      idea: idea || null,
      render_video: true,
      audio_design: opt.music ? "auto" : null,
      motion: opt.motion ? "auto" : null,
      title: null,
    };
    if (!idea && state.titleOverride) body.title = state.titleOverride;

    $("#output-sub").textContent = "المحرك يعمل على الخادم: سيناريو + صور + صوت + مونتاج ffmpeg.";
    showOutput();
    setPhase("writing");
    setProgress(2, "تجهيز المهمة…");

    const r = await fetch(apiUrl("/api/jobs"), {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-admin-token": state.token },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      setMsg(e.detail || "فشل بدء المهمة — تأكد من كلمة مرور الخادم.", "error");
      throw new Error("job create failed");
    }
    const { id } = await r.json();

    let storyboard = null;
    const poll = setInterval(async () => {
      try {
        const j = await fetchJSON(apiUrl("/api/jobs/" + id), { headers: { "x-admin-token": state.token } });
        updateServerJob(j);
        if (j.status === "done") {
          clearInterval(poll);
          try { storyboard = await fetchJSON(apiUrl("/api/jobs/" + id + "/asset?path=storyboard.json"), { headers: { "x-admin-token": state.token } }); } catch (e) {}
          finishServerJob(j, storyboard);
        } else if (j.status === "error" || j.status === "failed") {
          clearInterval(poll);
          setMsg(j.error || "حدث خطأ في الإنتاج.", "error");
        }
      } catch (e) { /* تجاهل مؤقت */ }
    }, 2500);
  }

  function updateServerJob(j) {
    const p = j.progress || 0;
    let phase = "writing";
    if (j.status === "done") phase = "done";
    else if (p >= 80) phase = "montage";
    else if (p >= 55) phase = "audio";
    else if (p >= 12) phase = "images";
    setPhase(phase);
    setProgress(p, j.phase ? j.phase + (j.scene ? " — مشهد " + j.scene : "") : "يعمل…");
    if (j.images && j.images.length) {
      if (!state.project) {
        // نبني مشاهد وهمية بالأرقام الظاهرة
        const nums = j.images.map((p) => +(p.match(/scene_(\d+)/) || [])[1]).filter((n) => n);
        const scenes = nums.sort((a, b) => a - b).map((n) => ({ num: n, title: "مشهد " + n, seconds: 0, beat: "" }));
        state.project = { pilot: { scenes }, slug: j.pack_slug || j.id, title: j.pack_title || "حلقتك" };
        renderScenes(scenes);
      }
      j.images.forEach((p, i) => {
        const n = +(p.match(/scene_(\d+)/) || [])[1];
        if (n && !$(`#scene-card-${n} img`).dataset.loaded) {
          setSceneImage(n, apiUrl("/api/jobs/" + j.id + "/asset?path=" + encodeURIComponent(p) + "&token=" + encodeURIComponent(state.token)));
          $(`#scene-card-${n} img`).dataset.loaded = "1";
        }
      });
    }
  }

  function finishServerJob(j, storyboard) {
    setPhase("done");
    setProgress(100, "اكتمل الإنتاج على الخادم!");
    if (storyboard && storyboard.scenes) {
      const scenes = storyboard.scenes.map((s) => ({ num: s.num, title: s.title, seconds: s.seconds, beat: s.beat, dialogue: s.dialogue || [] }));
      state.project = { pilot: { scenes }, slug: j.pack_slug || j.id, title: j.pack_title || "حلقتك" };
      renderScenes(scenes);
    }

    const video = document.createElement("video");
    video.controls = true;
    video.className = "preview-video";
    video.src = apiUrl("/api/jobs/" + j.id + "/asset?path=video%2Ffinal.mp4&token=" + encodeURIComponent(state.token));
    const vc = $("#result-video .result-empty");
    if (vc) vc.replaceWith(video);

    const box = $("#result-actions");
    box.innerHTML = "";
    const mk = (label, icon, href) => {
      const a = document.createElement("a");
      a.className = "btn btn-gold";
      a.href = href;
      a.innerHTML = `<i data-lucide="${icon}"></i> ${label}`;
      box.appendChild(a);
      icons();
    };
    mk("تحميل كل شيء (ZIP)", "folder-down", apiUrl("/api/jobs/" + j.id + "/download?token=" + encodeURIComponent(state.token)));
    mk("الستوريبورد", "layout-dashboard", apiUrl("/api/jobs/" + j.id + "/asset?path=storyboard.json&token=" + encodeURIComponent(state.token)));
    if (!j.images || !j.images.length) return;
    mk("تحميل الصور", "image", apiUrl("/api/jobs/" + j.id + "/download?token=" + encodeURIComponent(state.token) + "&view=images"));
  }

  /* ---------------- بدء الإنتاج ---------------- */
  function startProduction() {
    if (state.running) return;
    const idea = ($("#idea").value || "").trim();
    if (!idea && !state.selected) {
      setMsg("اختر سلسلة أو اكتب فكرتك أولًا.", "error");
      return;
    }
    setMsg("");
    state.running = true;
    $("#btn-generate").disabled = true;
    $("#btn-generate").innerHTML = '<i data-lucide="loader-circle"></i> يعمل…';
    icons();
    try { sharedAudio().resume().catch(() => {}); } catch (e) {}
    const run = () =>
      (state.mode === "server" ? runServerJob(idea) : runClientJob(idea)).catch(() => {}).finally(() => {
        state.running = false;
        $("#btn-generate").disabled = false;
        $("#btn-generate").innerHTML = '<i data-lucide="play"></i> ابدأ الإنتاج';
        icons();
      });
    run();
  }

  /* ---------------- إعدادات ---------------- */
  function setupSettings() {
    const modal = $("#settings-modal");
    $("#btn-settings").addEventListener("click", () => {
      $("#admin-pass").value = state.token;
      $("#api-base").value = state.apiBase;
      modal.classList.remove("is-hidden");
      icons();
    });
    $("#settings-close").addEventListener("click", () => modal.classList.add("is-hidden"));
    $("#settings-save").addEventListener("click", async () => {
      state.token = $("#admin-pass").value.trim();
      state.apiBase = ($("#api-base").value || "").trim().replace(/\/+$/, "");
      localStorage.setItem("studio_token", state.token);
      localStorage.setItem("studio_api_base", state.apiBase);
      modal.classList.add("is-hidden");
      await init();
    });
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.classList.add("is-hidden"); });
  }

  /* ---------------- تشغيل ---------------- */
  async function init() {
    try {
      const d = await detectMode();
      state.packs = d.packs;
      if (d.universe) state.meta.universe = d.universe;
      renderModeBadge();
      renderHeroSlate();
      renderPacksGrid();
      renderPackPicker();
      icons();
    } catch (e) {
      setMsg(e.message, "error");
    }

    $$(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));
    $("#btn-generate").addEventListener("click", startProduction);
    $("#scene-sec").addEventListener("input", (e) => {
      $("#scene-sec-label").textContent = e.target.value + " ثوانٍ";
    });
    setupSettings();
    icons();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
