import re

fn = "library.html"
s = open(fn, encoding="utf-8").read()

if 'id="mnu"' in s:
    print("ℹ️ मेन्यू पहले से जुड़ा है")
    raise SystemExit

TOP = '''<div class="top">
  <a href="index.html" class="nav">🏠 होम</a>
  <button class="nav" onclick="toggleMenu()" aria-label="मेन्यू">⋮</button>
</div>
<div id="mnuBg" onclick="closeMenu()"></div>
<div id="mnu">
  <div class="mh">⚙️ सेटिंग</div>
  <button onclick="closeMenu();shareIt()">📤 शेयर करें</button>
  <button onclick="closeMenu();installApp()">📲 ऐप इंस्टॉल करें</button>
  <div class="mr">🔠 अक्षर <button onclick="sz(-2)">A−</button><button onclick="sz(2)">A+</button></div>
  <div class="mr">🔊 आवाज़ <button onclick="setRate(0.8)">धीमी</button><button onclick="setRate(1)">सामान्य</button><button onclick="setRate(1.3)">तेज़</button></div>
  <button onclick="closeMenu();night()">🌙 रात मोड चालू/बंद</button>
  <button onclick="clearFav()">🤍 पसंद की सूची साफ़ करें</button>
  <button onclick="clearProg()">🔖 पढ़ने की प्रगति मिटाएँ</button>
  <hr>
  <button onclick="closeMenu();ownerLogin()"><span id="lock">🔐</span> मालिक मोड</button>
  <button class="own" onclick="closeMenu();$('md').classList.add('on')">💾 बैकअप (मालिक)</button>
  <hr>
  <a href="privacy.html">🔒 गोपनीयता नीति</a>
  <div class="mi">📚 कहानी पुस्तकालय · © सर्वाधिकार सुरक्षित</div>
</div>'''

CSS = '''
/* ⋮ मेन्यू */
#mnuBg{display:none;position:fixed;inset:0;z-index:69}
#mnuBg.on{display:block}
#mnu{display:none;position:fixed;top:60px;right:8px;width:270px;max-width:92vw;max-height:80vh;overflow-y:auto;background:#fff;border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,.3);z-index:70;padding:8px;animation:pop .2s}
#mnu.on{display:block}
#mnu .mh{font-weight:bold;color:#7a3b12;padding:8px 12px;font-size:16px}
#mnu button{display:block;width:100%;text-align:left;background:none;color:#222;margin:0;padding:12px;border-radius:10px;font-size:15px}
#mnu button:active{background:#f5f0e8}
#mnu .mr{padding:6px 12px;font-size:15px}
#mnu .mr button{display:inline-block;width:auto;background:#7a3b12;color:#fff;margin:3px 2px;padding:7px 12px;text-align:center}
#mnu a{display:block;padding:12px;color:#222;text-decoration:none;font-size:15px}
#mnu hr{border:0;border-top:1px solid #eee;margin:6px 0}
#mnu .mi{font-size:12px;color:#888;text-align:center;padding:8px}
body:not(.owner) #mnu .own{display:none}
'''

SHARE = r'''/* ================= शेयर ================= */
async function shareIt(){
  const inRead = $("read").classList.contains("on") && cur;
  const mine = inRead && String(cur.id).startsWith("u");
  const url = (inRead && !mine) ? SITE + "library.html?s=" + cur.id : SITE;
  const title = inRead ? cur.t : "मेरा कहानी पुस्तकालय";
  const text = inRead ? ("📖 " + cur.t + " — यह कहानी पढ़िए") : "📚 रोचक हिंदी कहानियाँ पढ़िए और सुनिए";
  try{
    if(navigator.share){ await navigator.share({title, text, url}); return }
  }catch(e){ if(e && e.name === "AbortError") return }
  try{
    await navigator.clipboard.writeText(text + "\n" + url);
    toast("🔗 लिंक कॉपी हो गया — कहीं भी चिपकाइए");
  }catch(e){ prompt("यह लिंक कॉपी करें:", url) }
}
function openShared(){
  const id = new URLSearchParams(location.search).get("s");
  if(!id) return;
  const x = A.find(v => v.id === id);
  if(x) op(x, A);
}
'''

JS = r'''/* ================= ⋮ मेन्यू / सेटिंग ================= */
function toggleMenu(){
  const o = $("mnu").classList.toggle("on");
  $("mnuBg").classList.toggle("on", o);
}
function closeMenu(){
  $("mnu").classList.remove("on");
  $("mnuBg").classList.remove("on");
}
function setRate(r){
  localStorage.rate = r;
  closeMenu();
  toast("🔊 आवाज़ की गति बदल गई");
}
function clearFav(){
  if(!confirm("सारी पसंद की सूची साफ़ करें?")) return;
  FAV = new Set(); localStorage.fav = "[]";
  closeMenu(); filt(); toast("🤍 पसंद की सूची साफ़ हो गई");
}
function clearProg(){
  if(!confirm("सब कहानियों की पढ़ने की प्रगति मिटानी है?")) return;
  Object.keys(localStorage).filter(k => /^p([0-9a-f]{8}|u\d+)$/.test(k))
    .forEach(k => localStorage.removeItem(k));
  closeMenu(); toast("🔖 प्रगति मिट गई");
}
let dpInst = null;
window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); dpInst = e });
async function installApp(){
  if(matchMedia("(display-mode: standalone)").matches || navigator.standalone){
    toast("✅ ऐप पहले से इंस्टॉल है"); return;
  }
  if(dpInst){
    dpInst.prompt();
    try{ await dpInst.userChoice }catch(e){}
    dpInst = null;
  }else{
    alert("📲 Chrome में ऊपर ⋮ दबाइए → 'Install app' या 'Add to Home screen' चुनिए।\n\n(iPhone में: Safari → Share → Add to Home Screen)");
  }
}

'''

new_s, n = re.subn(r'<div class="top">.*?</div>', lambda m: TOP, s, count=1, flags=re.S)
if n == 0:
    print("⚠️ ऊपर की पट्टी (top) नहीं मिली"); raise SystemExit
s = new_s

s = s.replace("</style>", CSS + "</style>", 1)

block = JS
if "function shareIt" not in s:
    block = SHARE + block
marker = "/* ================= शुरुआत ================= */"
if marker in s:
    s = s.replace(marker, block + marker, 1)
else:
    i = s.rfind("</script>")
    s = s[:i] + block + s[i:]

if "localStorage.rate" not in s.split("function say()")[1][:400]:
    s = s.replace('u.lang="hi-IN";', 'u.lang="hi-IN";u.rate=+localStorage.rate||1;', 1)

if "load().then(openShared)" not in s:
    s = s.replace("clearForm();drawBtns();load();", "clearForm();drawBtns();load().then(openShared);", 1)

open(fn, "w", encoding="utf-8").write(s)
print("✅ ⋮ मेन्यू जुड़ गया")
