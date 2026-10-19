import re, os

# ---------- 1) library.html : "सुनें" की सफ़ाई ----------
JS = r'''function cleanTTS(t){
  return t
    .replace(/https?:\/\/\S+/g," ")
    .replace(/[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{200D}]/gu," ")
    .replace(/["'“”‘’«»„‟‹›`´]/g,"")
    .replace(/(\.{2,}|…)/g,", ")
    .replace(/\s*[—–―‒−]+\s*/g,", ")
    .replace(/-+/g," ")
    .replace(/[()\[\]{}<>]/g,", ")
    .replace(/॥/g,"।")
    .replace(/[#*_~|\\\/^=+@]/g," ")
    .replace(/[;:]/g,",")
    .replace(/([,\s]*,[,\s]*)+/g,", ")
    .replace(/[ \t]+/g," ");
}
function sp(t){
  const pieces=cleanTTS(t).split(/(?<=[,।!?\n])|(?<=\.)(?=\s)/);
  const out=[];let buf="";
  const flush=()=>{const b=buf.trim();if(b)out.push(b);buf=""};
  for(let p of pieces){
    const end=/[।!?\n.]\s*$/.test(p);
    p=p.replace(/[,\n]+/g," ").replace(/।/g,".").replace(/\s+/g," ").trim();
    if(!p)continue;
    if(buf&&buf.length+p.length>200)flush();
    buf+=(buf?" ":"")+p;
    while(buf.length>200){
      let k=buf.lastIndexOf(" ",200);if(k<50)k=200;
      out.push(buf.slice(0,k).trim());buf=buf.slice(k).trim();
    }
    if(end||buf.length>=40)flush();
  }
  flush();
  return out;
}
'''

fn = "library.html"
s = open(fn, encoding="utf-8").read()
if "function cleanTTS" in s:
    print("ℹ️ library.html में सफ़ाई पहले से है")
else:
    s2, n = re.subn(r"function sp\(t\)\{.*?\n\}\n(?=function say\(\))", lambda m: JS, s, count=1, flags=re.S)
    if n:
        open(fn, "w", encoding="utf-8").write(s2)
        print("✅ library.html: सुनने की सफ़ाई जुड़ गई")
    else:
        print("⚠️ library.html में sp() वाला हिस्सा नहीं मिला")

# ---------- 2) make_audio.py : MP3 के लिए सफ़ाई ----------
PY = r'''def clean(t):
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

'''
fn = "make_audio.py"
if os.path.exists(fn):
    s = open(fn, encoding="utf-8").read()
    if "def clean(t)" in s:
        print("ℹ️ make_audio.py में सफ़ाई पहले से है")
    elif "def split(t):\n" in s:
        s = s.replace("def split(t):\n", PY + "def split(t):\n    t = clean(t)\n", 1)
        open(fn, "w", encoding="utf-8").write(s)
        print("✅ make_audio.py: MP3 की सफ़ाई जुड़ गई")
    else:
        print("⚠️ make_audio.py में split() नहीं मिला")
else:
    print("ℹ️ make_audio.py अभी नहीं है — कोई बात नहीं")
