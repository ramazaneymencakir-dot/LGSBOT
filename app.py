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
.founder { text-align:center; color:#ffffff; font-size:22px; font-weight:900; letter-spacing:1px; margin:8px 0 12px; }
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
ZORUNLU_ALANLAR = {
    "id", "ders", "konu", "zorluk", "tur", "soru",
    "A", "B", "C", "D", "cevap", "cozum", "ipucu",
}

@st.cache_data
def soru_bankasini_yukle():
    if not BANKA_DOSYASI.exists():
        return []
    return json.loads(BANKA_DOSYASI.read_text(encoding="utf-8"))

BANKA = soru_bankasini_yukle()

def soru_bankasini_dogrula(sorular):
    hatalar = []
    if not isinstance(sorular, list):
        return ["questions.json bir JSON listesi olmalıdır."]

    gorulen_idler = set()
    for sira, soru in enumerate(sorular, 1):
        if not isinstance(soru, dict):
            hatalar.append(f"{sira}. kayıt bir nesne değil.")
            continue
        eksikler = sorted(alan for alan in ZORUNLU_ALANLAR if not soru.get(alan))
        if eksikler:
            hatalar.append(f"{sira}. soruda eksik/boş alan: {', '.join(eksikler)}")
        soru_id = soru.get("id")
        if soru_id in gorulen_idler:
            hatalar.append(f"Tekrarlanan soru kimliği: {soru_id}")
        elif soru_id:
            gorulen_idler.add(soru_id)
        if soru.get("cevap") not in {"A", "B", "C", "D"}:
            hatalar.append(f"{sira}. sorunun cevabı A, B, C veya D olmalıdır.")
    return hatalar

BANKA_HATALARI = soru_bankasini_dogrula(BANKA)
if BANKA_HATALARI:
    st.error("Soru bankası doğrulanamadı:\n\n- " + "\n- ".join(BANKA_HATALARI))
    st.stop()

for key, default in {
    "ders": "📐 Matematik",
    "soru": None,
    "cevap_acik": False,
    "cozum_acik": False,
    "son_soru_metni": None,
    "cevaplandi": False,
    "soru_no": 0,
    "dogru": 0,
    "yanlis": 0,
    "yanlislarim": [],
    "cozulen_havuzlar": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def soruyu_temizle():
    st.session_state.soru = None
    st.session_state.cevap_acik = False
    st.session_state.cozum_acik = False
    st.session_state.cevaplandi = False

def secim_degisti():
    soruyu_temizle()

def konu_soru_sayisi(ders, konu):
    return sum(1 for q in BANKA if q.get("ders") == ders and q.get("konu") == konu)

def havuz_anahtari(ders, konu, zorluk, tur):
    return " | ".join((ders, konu, zorluk, tur))

def uygun_sorular(ders, konu, zorluk, tur):
    return [q for q in BANKA if q.get("ders")==ders and q.get("konu")==konu
            and q.get("zorluk")==zorluk and q.get("tur")==tur]

def cozulmemis_sorular(liste, cozulen_idler):
    return [q for q in liste if q["id"] not in set(cozulen_idler)]

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
    liste = uygun_sorular(st.session_state.ders, konu, zorluk, tur)
    if not liste:
        st.session_state.soru = None
        st.warning(f"Bu seçim için soru bankasında henüz soru yok: {konu} → {zorluk} → {tur}")
        return
    anahtar = havuz_anahtari(st.session_state.ders, konu, zorluk, tur)
    cozulenler = set(st.session_state.cozulen_havuzlar.get(anahtar, []))
    kalanlar = cozulmemis_sorular(liste, cozulenler)
    if not kalanlar:
        st.session_state.soru = None
        return
    st.session_state.soru = rastgele_soru_sec(kalanlar)
    st.session_state.cevap_acik = False
    st.session_state.cozum_acik = False
    st.session_state.cevaplandi = False
    st.session_state.soru_no += 1

def havuzu_yeniden_baslat(ders, konu, zorluk, tur):
    anahtar = havuz_anahtari(ders, konu, zorluk, tur)
    st.session_state.cozulen_havuzlar.pop(anahtar, None)
    soruyu_temizle()

st.markdown('<div class="title">🤖 LGSBOT</div>', unsafe_allow_html=True)
st.markdown('<div class="founder">KURUCU: RAMAZAN EYMEN ÇAKIR</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Kişisel LGS Çalışma Merkezi • Soru Bankası Sürümü</div>', unsafe_allow_html=True)
st.info(f"📚 Bankada {len(BANKA)} soru var. Bu sürüm soru çözerken Gemini API kullanmaz; 429 kota hatası oluşturmaz.")

cozulen = st.session_state.dogru + st.session_state.yanlis
basari = (st.session_state.dogru / cozulen * 100) if cozulen else 0
m1, m2, m3, m4 = st.columns(4)
m1.metric("✅ Doğru", st.session_state.dogru)
m2.metric("❌ Yanlış", st.session_state.yanlis)
m3.metric("📝 Çözülen", cozulen)
m4.metric("🏆 Başarı", f"%{basari:.0f}")

st.markdown("### 1️⃣ Dersini seç")
cols = st.columns(4)
for i, ders in enumerate(KONULAR.keys()):
    with cols[i]:
        if st.button(ders, use_container_width=True,
                     type="primary" if st.session_state.ders==ders else "secondary"):
            if st.session_state.ders != ders:
                st.session_state.ders = ders
                st.session_state.pop("konu_secimi", None)
                soruyu_temizle()
                st.rerun()

st.markdown("### 2️⃣ Konuyu seç")
konu_secenekleri = {
    f"{ad} ({konu_soru_sayisi(st.session_state.ders, ad)} soru)": ad
    for ad in KONULAR[st.session_state.ders]
}
konu_etiketi = st.selectbox(
    "Konu",
    list(konu_secenekleri),
    key="konu_secimi",
    on_change=secim_degisti,
    label_visibility="collapsed",
)
konu = konu_secenekleri[konu_etiketi]

st.markdown("### 3️⃣ Zorluk seviyesini seç")
zorluk = st.selectbox(
    "Zorluk",
    ["Kolay","Orta","Zor","Gerçek LGS Seviyesi"],
    index=1,
    key="zorluk_secimi",
    on_change=secim_degisti,
    label_visibility="collapsed",
)

st.markdown("### 4️⃣ Soru türünü seç")
soru_turu = st.radio(
    "Soru türü",
    ["Klasik", "LGS Tarzı"],
    horizontal=True,
    key="soru_turu_secimi",
    on_change=secim_degisti,
    label_visibility="collapsed",
)

secili_havuz = uygun_sorular(st.session_state.ders, konu, zorluk, soru_turu)
secili_anahtar = havuz_anahtari(st.session_state.ders, konu, zorluk, soru_turu)
cozulen_idler = set(st.session_state.cozulen_havuzlar.get(secili_anahtar, []))
kalan_soru_sayisi = sum(q["id"] not in cozulen_idler for q in secili_havuz)
st.info(
    f"🔎 Seçili filtrede {len(secili_havuz)} soru bulundu. "
    f"Kalan soru: {kalan_soru_sayisi}."
)

if len(secili_havuz) == 1:
    st.warning("Bu filtrede yalnızca 1 soru var. Farklı soru için filtreyi değiştirmen gerekir.")

if secili_havuz and kalan_soru_sayisi == 0:
    st.success("🎉 Bu bölümdeki tüm soruları çözdün.")
    if st.button("🔄 Soruları yeniden başlat", use_container_width=True):
        havuzu_yeniden_baslat(st.session_state.ders, konu, zorluk, soru_turu)
        st.rerun()
elif secili_havuz:
    if st.button("🎲 Soru Getir", use_container_width=True, type="primary"):
        soru_getir(soru_turu, konu, zorluk)
        st.rerun()
else:
    st.warning("Bu filtreye uygun soru bulunamadı.")

if st.session_state.soru:
    q = st.session_state.soru

    st.markdown("---")
    st.markdown("## 🎯 Soru")
    st.markdown(q.get("soru",""))

    secilen_cevap = st.radio(
        "Cevabını işaretle",
        ["A", "B", "C", "D"],
        index=None,
        format_func=lambda harf: f"{harf}) {q.get(harf, '')}",
        key=f"cevap_{st.session_state.soru_no}",
        disabled=st.session_state.cevaplandi,
    )

    if st.button(
        "✅ Cevabı Kontrol Et",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.cevaplandi or secilen_cevap is None,
    ):
        st.session_state.cevaplandi = True
        if secilen_cevap == q.get("cevap"):
            st.session_state.dogru += 1
        else:
            st.session_state.yanlis += 1
            soru_kaydi = {
                "ders": q.get("ders", st.session_state.ders),
                "konu": q.get("konu", konu),
                "soru": q.get("soru", ""),
                "verilen": secilen_cevap,
                "dogru": q.get("cevap", ""),
            }
            if not any(x.get("soru") == soru_kaydi["soru"] for x in st.session_state.yanlislarim):
                st.session_state.yanlislarim.append(soru_kaydi)
        q_anahtar = havuz_anahtari(q["ders"], q["konu"], q["zorluk"], q["tur"])
        cozulenler = st.session_state.cozulen_havuzlar.setdefault(q_anahtar, [])
        if q["id"] not in cozulenler:
            cozulenler.append(q["id"])
        st.rerun()

    if st.session_state.cevaplandi:
        if secilen_cevap == q.get("cevap"):
            st.success("🎉 Doğru cevap!")
        else:
            st.error(f"Yanlış cevap. Doğru seçenek: {q.get('cevap', '')}")

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
        if st.button("🔄 Yeni Soru", use_container_width=True, disabled=not st.session_state.cevaplandi):
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

st.markdown("---")
st.markdown(f"## 📕 Yanlışlarım ({len(st.session_state.yanlislarim)})")
if not st.session_state.yanlislarim:
    st.caption("Henüz yanlış cevaplanan soru yok.")
else:
    for i, hata in enumerate(reversed(st.session_state.yanlislarim), 1):
        with st.expander(f"{i}. {hata['ders']} • {hata['konu']}"):
            st.write(hata["soru"])
            st.write(f"Senin cevabın: **{hata['verilen']}**")
            st.write(f"Doğru cevap: **{hata['dogru']}**")
