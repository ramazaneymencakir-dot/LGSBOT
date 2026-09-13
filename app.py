import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="LGSBOT", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #17345c 0%, #091321 45%, #050a12 100%);
    color:white;
}
.block-container { max-width:1150px; padding-top:2rem; }
.title { text-align:center; font-size:55px; font-weight:900; }
.subtitle { text-align:center; color:#afbed1; font-size:18px; margin-bottom:12px; }
.question { padding:25px; border-radius:20px; background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.15); font-size:18px; line-height:1.7; }
.answer { padding:20px; border-radius:16px; background:rgba(20,160,90,.12);
    border:1px solid rgba(50,220,120,.3); }
.solution { padding:20px; border-radius:16px; background:rgba(60,110,220,.12);
    border:1px solid rgba(100,160,255,.3); }
div.stButton > button { border-radius:14px; min-height:48px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

KONULAR = {
    "📐 Matematik": ["Çarpanlar ve Katlar","Üslü İfadeler","Kareköklü İfadeler","Veri Analizi",
        "Basit Olayların Olma Olasılığı","Cebirsel İfadeler ve Özdeşlikler","Doğrusal Denklemler",
        "Eşitsizlikler","Üçgenler","Eşlik ve Benzerlik","Dönüşüm Geometrisi","Geometrik Cisimler"],
    "🧪 Fen Bilimleri": ["Mevsimler ve İklim","DNA ve Genetik Kod","Basınç","Madde ve Endüstri",
        "Basit Makineler","Enerji Dönüşümleri ve Çevre Bilimi","Elektrik Yükleri ve Elektrik Enerjisi"],
    "📖 Türkçe": ["Sözcükte Anlam","Cümlede Anlam","Paragrafta Anlam","Fiilimsiler","Cümlenin Ögeleri",
        "Fiilde Çatı","Cümle Türleri","Yazım Kuralları","Noktalama İşaretleri","Metin Türleri",
        "Görsel Okuma ve Grafik Yorumlama"],
    "🇹🇷 İnkılap Tarihi": ["Bir Kahraman Doğuyor","Millî Uyanış","Millî Bir Destan: Ya İstiklal Ya Ölüm",
        "Atatürkçülük ve Çağdaşlaşan Türkiye","Demokratikleşme Çabaları",
        "Atatürk Dönemi Türk Dış Politikası","Atatürk'ün Ölümü ve Sonrası"]
}

BANKA_DOSYASI = Path(__file__).with_name("questions.json")

@st.cache_data
def soru_bankasini_yukle():
    if not BANKA_DOSYASI.exists():
        return []
    return json.loads(BANKA_DOSYASI.read_text(encoding="utf-8"))

BANKA = soru_bankasini_yukle()

for key, default in {
    "ders": "📐 Matematik",
    "soru": None,
    "cevap_acik": False,
    "cozum_acik": False,
    "son_soru_metni": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def uygun_sorular(ders, konu, zorluk, tur):
    exact = [q for q in BANKA if q.get("ders")==ders and q.get("konu")==konu
             and q.get("zorluk")==zorluk and q.get("tur")==tur]
    if exact:
        return exact, False
    fallback = [q for q in BANKA if q.get("ders")==ders and q.get("konu")==konu and q.get("tur")==tur]
    return fallback, True

def rastgele_soru_sec(liste):
    if not liste:
        return None
    adaylar = [q for q in liste if q.get("soru") != st.session_state.son_soru_metni]
    if not adaylar:
        adaylar = liste
    soru = random.choice(adaylar)
    st.session_state.son_soru_metni = soru.get("soru")
    return soru

def soru_getir(tur, konu, zorluk):
    liste, fallback = uygun_sorular(st.session_state.ders, konu, zorluk, tur)
    if not liste:
        st.session_state.soru = None
        st.warning(f"Bu seçim için soru bankasında henüz soru yok: {konu} → {zorluk} → {tur}")
        return
    st.session_state.soru = rastgele_soru_sec(liste)
    st.session_state.cevap_acik = False
    st.session_state.cozum_acik = False
    if fallback:
        st.info("Bu zorluk seviyesinde henüz soru yok; aynı konudan mevcut başka bir zorluk getirildi.")

st.markdown('<div class="title">🤖 LGSBOT</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ramazan Eymen ÇAKIR</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Kişisel LGS Çalışma Merkezi • Soru Bankası Sürümü</div>', unsafe_allow_html=True)
st.info(f"📚 Bankada {len(BANKA)} soru var. Bu sürüm soru çözerken Gemini API kullanmaz; 429 kota hatası oluşturmaz.")

st.markdown("### 1️⃣ Dersini seç")
cols = st.columns(4)
for i, ders in enumerate(KONULAR.keys()):
    with cols[i]:
        if st.button(ders, use_container_width=True,
                     type="primary" if st.session_state.ders==ders else "secondary"):
            st.session_state.ders = ders
            st.session_state.soru = None
            st.session_state.cevap_acik = False
            st.session_state.cozum_acik = False
            st.rerun()

st.markdown("### 2️⃣ Konuyu seç")
konu = st.selectbox("Konu", KONULAR[st.session_state.ders], label_visibility="collapsed")

st.markdown("### 3️⃣ Zorluk seviyesini seç")
zorluk = st.selectbox("Zorluk", ["Kolay","Orta","Zor","Gerçek LGS Seviyesi"],
                      index=1, label_visibility="collapsed")

st.markdown("### 4️⃣ Soru türünü seç")
c1, c2 = st.columns(2)
with c1:
    klasik = st.button("✏️ Klasik Soru", use_container_width=True)
with c2:
    lgs = st.button("🎯 LGS Tarzı Soru", use_container_width=True)

if klasik:
    soru_getir("Klasik", konu, zorluk)
if lgs:
    soru_getir("LGS Tarzı", konu, zorluk)

if st.session_state.soru:
    q = st.session_state.soru

    st.markdown("---")
    st.markdown("## 🎯 Soru")
    st.markdown(q.get("soru",""))
    st.markdown(f"**A)** {q.get('A','')}")
    st.markdown(f"**B)** {q.get('B','')}")
    st.markdown(f"**C)** {q.get('C','')}")
    st.markdown(f"**D)** {q.get('D','')}")

    st.markdown("### 🖊️ Çözüm Tahtası")

    drawing_board = """
    <html><head><style>
    body { margin:0; background:transparent; font-family:Arial,sans-serif; }
    .toolbar { background:#111827; padding:10px; border-radius:12px 12px 0 0;
        display:flex; gap:6px; flex-wrap:wrap; }
    button { padding:9px 14px; border:0; border-radius:8px; cursor:pointer;
        font-weight:bold; background:#e5e7eb; }
    button:hover { background:#ffffff; }
    .active { background:#3b82f6; color:white; }
    canvas { background:white; width:100%; height:420px; border-radius:0 0 12px 12px;
        cursor:crosshair; touch-action:none; }
    </style></head><body>
    <div class="toolbar">
      <button id="penBtn" onclick="setTool('pen')">✏️ Kalem</button>
      <button id="eraserBtn" onclick="setTool('eraser')">🧽 Silgi</button>
      <button id="rectBtn" onclick="setTool('rectangle')">▭ Dikdörtgen</button>
      <button id="circleBtn" onclick="setTool('circle')">◯ Daire</button>
      <button id="triangleBtn" onclick="setTool('triangle')">△ Üçgen</button>
      <button onclick="clearBoard()">🗑️ Temizle</button>
    </div>
    <canvas id="board"></canvas>
    <script>
    const canvas=document.getElementById("board"), ctx=canvas.getContext("2d");
    canvas.width=1200; canvas.height=420;
    let tool="pen", drawing=false, startX=0, startY=0, savedImage=null;

    function pos(e){
      const r=canvas.getBoundingClientRect(), p=e.touches?e.touches[0]:e;
      return {x:(p.clientX-r.left)*(canvas.width/r.width),
              y:(p.clientY-r.top)*(canvas.height/r.height)};
    }
    function setTool(t){
      tool=t;
      document.querySelectorAll(".toolbar button").forEach(b=>b.classList.remove("active"));
      const ids={pen:"penBtn",eraser:"eraserBtn",rectangle:"rectBtn",circle:"circleBtn",triangle:"triangleBtn"};
      if(ids[t]) document.getElementById(ids[t]).classList.add("active");
    }
    function start(e){
      drawing=true; const p=pos(e); startX=p.x; startY=p.y;
      savedImage=ctx.getImageData(0,0,canvas.width,canvas.height);
      if(tool==="pen"||tool==="eraser"){ctx.beginPath();ctx.moveTo(startX,startY);}
      e.preventDefault();
    }
    function move(e){
      if(!drawing)return;
      const p=pos(e), x=p.x, y=p.y;
      if(tool==="pen"){
        ctx.strokeStyle="#111";ctx.lineWidth=3;ctx.lineCap="round";ctx.lineJoin="round";
        ctx.lineTo(x,y);ctx.stroke();
      } else if(tool==="eraser"){
        ctx.strokeStyle="#fff";ctx.lineWidth=28;ctx.lineCap="round";
        ctx.lineTo(x,y);ctx.stroke();
      } else {
        ctx.putImageData(savedImage,0,0);ctx.strokeStyle="#111";ctx.lineWidth=3;
        if(tool==="rectangle") ctx.strokeRect(startX,startY,x-startX,y-startY);
        else if(tool==="circle"){
          const cx=(startX+x)/2,cy=(startY+y)/2,rx=Math.abs(x-startX)/2,ry=Math.abs(y-startY)/2;
          ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.stroke();
        } else if(tool==="triangle"){
          const mx=(startX+x)/2;ctx.beginPath();ctx.moveTo(mx,startY);
          ctx.lineTo(startX,y);ctx.lineTo(x,y);ctx.closePath();ctx.stroke();
        }
      }
      e.preventDefault();
    }
    function stop(e){drawing=false;ctx.closePath();if(e)e.preventDefault();}
    function clearBoard(){ctx.clearRect(0,0,canvas.width,canvas.height);}
    canvas.addEventListener("mousedown",start);canvas.addEventListener("mousemove",move);
    canvas.addEventListener("mouseup",stop);canvas.addEventListener("mouseleave",stop);
    canvas.addEventListener("touchstart",start,{passive:false});
    canvas.addEventListener("touchmove",move,{passive:false});
    canvas.addEventListener("touchend",stop,{passive:false});
    setTool("pen");
    </script></body></html>
    """
    components.html(drawing_board, height=450)

    st.markdown("### 🔐 Cevap ve çözüm")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔑 Cevabı Göster", use_container_width=True):
            st.session_state.cevap_acik = True
    with b2:
        if st.button("🧠 Çözümü Göster", use_container_width=True):
            st.session_state.cozum_acik = True
    with b3:
        if st.button("🔄 Yeni Soru", use_container_width=True):
            soru_getir(q.get("tur","Klasik"), konu, zorluk)
            st.rerun()

    if st.session_state.cevap_acik:
        st.markdown(
            f'<div class="answer"><b>✅ Doğru cevap: {q.get("cevap","")}</b></div>',
            unsafe_allow_html=True
        )

    if st.session_state.cozum_acik:
        solution_html = (
            '<div class="solution"><b>🧠 Çözüm</b><br><br>'
            + q.get("cozum","")
            + '<br><br><b>💡 LGS İpucu:</b> '
            + q.get("ipucu","")
            + '</div>'
        )
        st.markdown(solution_html, unsafe_allow_html=True)
