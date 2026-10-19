import asyncio, os, re, sys, json, hashlib
import edge_tts

HOME = os.path.expanduser("~")
CANDS = [os.environ.get("SRC", ""), "kahaniyan", HOME + "/kahaniyan",
         HOME + "/storage/shared/kahaniyan", HOME + "/kahani-library/kahaniyan"]
SRC = next((c for c in CANDS if c and os.path.isdir(c)), None)
OUT = os.environ.get("OUT", HOME + "/kahani-library/audio")
VOICE = os.environ.get("VOICE", "hi-IN-SwaraNeural")   # पुरुष आवाज़: hi-IN-MadhurNeural
RATE = os.environ.get("RATE", "+0%")                  # धीमी: -10%   तेज़: +10%
CHUNK = 2500      # एक बार में भेजे जाने वाले अक्षर
PART = 18000      # एक MP3 भाग में करीब इतने अक्षर (लगभग 20 मिनट)

def clean(t):
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE00-\uFE0F\u200D]", " ", t)
    t = re.sub("[\"'“”‘’«»„‟‹›`´]", "", t)
    t = re.sub(r"(\.{2,}|…)", ", ", t)
    t = re.sub(r"[ \t]*[—–―‒−]+[ \t]*", ", ", t)
    t = re.sub(r"-+", " ", t)
    t = re.sub(r"[()\[\]{}<>]", ", ", t)
    t = t.replace("॥", "।")
    t = re.sub(r"[#*_~|\\/^=+@]", " ", t)
    t = re.sub(r"[;:]", ",", t)
    t = re.sub(r",([ \t]*,)+", ",", t)
    return t

def split(t):
    t = clean(t)
    t = re.sub(r"[ \t]+", " ", t)
    sents = [s for s in re.split(r"(?<=[।!?\n])", t) if s.strip()]
    out, cur = [], ""
    for s in sents:
        while len(s) > CHUNK:
            k = s.rfind(" ", 0, CHUNK)
            k = k if k > 0 else CHUNK
            if cur:
                out.append(cur); cur = ""
            out.append(s[:k]); s = s[k:]
        if len(cur) + len(s) > CHUNK:
            if cur:
                out.append(cur)
            cur = s
        else:
            cur += s
    if cur.strip():
        out.append(cur)
    return [c.strip() for c in out if c.strip()]

def group(chunks):
    parts, cur, n = [], [], 0
    for c in chunks:
        if cur and n + len(c) > PART:
            parts.append(cur); cur, n = [], 0
        cur.append(c); n += len(c)
    if cur:
        parts.append(cur)
    return parts

async def speak(text, path):
    for i in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            if os.path.getsize(path) > 1000:
                return True
        except Exception as e:
            print("   फिर कोशिश", i + 1, str(e)[:60])
            await asyncio.sleep(3 * (i + 1))
    return False

async def main():
    if not SRC:
        print("❌ 'kahaniyan' फ़ोल्डर नहीं मिला। चलाइए: SRC=/पूरा/रास्ता python make_audio.py")
        return
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    os.makedirs(OUT, exist_ok=True)
    ip = OUT + "/index.json"
    idx = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else {}
    files = [f for f in sorted(os.listdir(SRC)) if f.endswith(".txt") and only in f]
    if not files:
        print("कोई कहानी नहीं मिली:", only); return
    for f in files:
        name = f[:-4]
        sid = hashlib.md5(f.encode()).hexdigest()[:8]
        if idx.get(sid, {}).get("done"):
            print("⏭️ पहले से बनी:", name); continue
        t = open(f"{SRC}/{f}", encoding="utf-8").read().strip()
        parts = group(split(t))
        d = f"{OUT}/{sid}"
        os.makedirs(d, exist_ok=True)
        print(f"🎙️ {name} — {len(t)} अक्षर, {len(parts)} भाग")
        ok = True
        for pi, chs in enumerate(parts, 1):
            pf = f"{d}/{pi:02d}.mp3"
            if os.path.exists(pf) and os.path.getsize(pf) > 1000:
                continue
            buf = b""
            for ci, c in enumerate(chs, 1):
                tmp = f"{d}/tmp.mp3"
                if not await speak(c, tmp):
                    ok = False; break
                buf += open(tmp, "rb").read()
                print(f"   भाग {pi}/{len(parts)} · टुकड़ा {ci}/{len(chs)}", end="\r")
            if not ok:
                break
            open(pf + ".part", "wb").write(buf)
            os.replace(pf + ".part", pf)
            print(f"   ✅ भाग {pi}/{len(parts)} तैयार ({len(buf)//1024} KB)      ")
        if os.path.exists(f"{d}/tmp.mp3"):
            os.remove(f"{d}/tmp.mp3")
        if ok:
            idx[sid] = {"n": len(parts), "t": name, "done": True}
            json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        else:
            print("⚠️ अधूरी रही (दोबारा चलाने पर वहीं से आगे बढ़ेगी):", name)
    tot = sum(os.path.getsize(os.path.join(r, x)) for r, _, fs in os.walk(OUT) for x in fs)
    print("\n📦 audio फ़ोल्डर का कुल आकार:", round(tot / 1e6, 1), "MB  (GitHub के लिए 1000 MB के अंदर रखें)")

asyncio.run(main())
