import os
import json
import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# AYARLAR
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY bulunamadı. .env dosyasını kontrol et.")
    st.stop()

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.6-flash"


# =========================================================
# SAYFA TASARIMI
# =========================================================

st.set_page_config(
    page_title="LGSBOT",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at top left, #17345c 0%, #091321 45%, #050a12 100%);
    color:white;
}

.block-container {
    max-width:1150px;
    padding-top:2rem;
}

.title {
    text-align:center;
    font-size:55px;
    font-weight:900;
}

.subtitle {
    text-align:center;
    color:#afbed1;
    font-size:18px;
    margin-bottom:30px;
}

.question {
    padding:25px;
    border-radius:20px;
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.15);
    font-size:18px;
    line-height:1.7;
}

.answer {
    padding:20px;
    border-radius:16px;
    background:rgba(20,160,90,.12);
    border:1px solid rgba(50,220,120,.3);
}

.solution {
    padding:20px;
    border-radius:16px;
    background:rgba(60,110,220,.12);
    border:1px solid rgba(100,160,255,.3);
}

div.stButton > button {
    border-radius:14px;
    min-height:48px;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DERSLER
# =========================================================

KONULAR = {

    "📐 Matematik": [
        "Çarpanlar ve Katlar",
        "Üslü İfadeler",
        "Kareköklü İfadeler",
        "Veri Analizi",
        "Basit Olayların Olma Olasılığı",
        "Cebirsel İfadeler ve Özdeşlikler",
        "Doğrusal Denklemler",
        "Eşitsizlikler",
        "Üçgenler",
        "Eşlik ve Benzerlik",
        "Dönüşüm Geometrisi",
        "Geometrik Cisimler"
    ],

    "🧪 Fen Bilimleri": [
        "Mevsimler ve İklim",
        "DNA ve Genetik Kod",
        "Basınç",
        "Madde ve Endüstri",
        "Basit Makineler",
        "Enerji Dönüşümleri ve Çevre Bilimi",
        "Elektrik Yükleri ve Elektrik Enerjisi"
    ],

    "📖 Türkçe": [
        "Sözcükte Anlam",
        "Cümlede Anlam",
        "Paragrafta Anlam",
        "Fiilimsiler",
        "Cümlenin Ögeleri",
        "Fiilde Çatı",
        "Cümle Türleri",
        "Yazım Kuralları",
        "Noktalama İşaretleri",
        "Metin Türleri",
        "Görsel Okuma ve Grafik Yorumlama"
    ],

    "🇹🇷 İnkılap Tarihi": [
        "Bir Kahraman Doğuyor",
        "Millî Uyanış",
        "Millî Bir Destan: Ya İstiklal Ya Ölüm",
        "Atatürkçülük ve Çağdaşlaşan Türkiye",
        "Demokratikleşme Çabaları",
        "Atatürk Dönemi Türk Dış Politikası",
        "Atatürk'ün Ölümü ve Sonrası"
    ]
}


# =========================================================
# KONU SINIRLARI
# =========================================================

KONU_KURALLARI = {

    "Çarpanlar ve Katlar": """
Soru mutlaka aşağıdakilerden en az birini gerektirmelidir:

- pozitif tam sayı çarpanları
- asal çarpanlar
- asal çarpanlara ayırma
- EBOB
- EKOK
- aralarında asal sayılar

Öğrenci Çarpanlar ve Katlar konusunu bilmeden soruyu çözememelidir.

Yüzde, oran-orantı veya başka bir matematik konusu
sorunun ana çözüm yöntemi olamaz.
""",

    "Üslü İfadeler": """
Sorunun çözümü mutlaka üslü ifadeler bilgisi gerektirmelidir.
""",

    "Kareköklü İfadeler": """
Sorunun çözümü mutlaka kareköklü ifadeler bilgisi gerektirmelidir.
""",

    "Basınç": """
Soru katı, sıvı veya gaz basıncıyla ilgili çıkarım yaptırmalıdır.
""",

    "DNA ve Genetik Kod": """
Soru DNA, gen, kromozom, nükleotit, kalıtım,
mutasyon, modifikasyon veya adaptasyon konusuyla doğrudan ilgili olmalıdır.
""",

    "Paragrafta Anlam": """
Soru verilen metinden anlam ve çıkarım yapmayı gerektirmelidir.
"""
}


# =========================================================
# HAFIZA
# =========================================================

if "ders" not in st.session_state:
    st.session_state.ders = "📐 Matematik"

if "soru" not in st.session_state:
    st.session_state.soru = None

if "cevap_acik" not in st.session_state:
    st.session_state.cevap_acik = False

if "cozum_acik" not in st.session_state:
    st.session_state.cozum_acik = False


# =========================================================
# GEMINI JSON
# =========================================================



def gemini_json(prompt):

    import time

    son_hata = None

    for deneme in range(4):

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.35
                )
            )

            return json.loads(response.text)

        except Exception as e:

            son_hata = e
            hata = str(e)

            if (
                "503" in hata
                or "UNAVAILABLE" in hata
                or "high demand" in hata.lower()
            ):

                bekleme = (deneme + 1) * 2
                time.sleep(bekleme)
                continue

            raise

    raise Exception(
        "Gemini şu anda çok yoğun. "
        "LGSBOT 4 kez otomatik denedi ancak yanıt alamadı. "
        f"Son hata: {son_hata}"
    )


# =========================================================
# SORU ÜRET
# =========================================================

def soru_uret(ders, konu, tur, zorluk):

    konu_kurali = KONU_KURALLARI.get(
        konu,
        f"Soru doğrudan '{konu}' kazanımını ölçmelidir."
    )

    if tur == "LGS Tarzı":

        stil = """
Bu soru gerçek LGS'deki yeni nesil soru mantığına yaklaşmalıdır.

- Tek işlem sorusu olmasın.
- En az iki bilgiyi ilişkilendirmeyi gerektirsin.
- Gerekiyorsa günlük yaşam senaryosu kullan.
- Gerekiyorsa tablo/veri kullan.
- Muhakeme gerektirsin.
- Gereksiz uzun olmasın.
- A, B, C ve D seçenekleri güçlü çeldiriciler olsun.
- Yanlış seçenekler gerçek öğrenci hatalarından türetilsin.
"""

    else:

        stil = """
Kaliteli fakat daha klasik yapıda 8. sınıf sorusu üret.
A-B-C-D seçenekleri olsun.
Tek doğru cevap bulunsun.
"""

    prompt = f"""
Sen Türkiye'deki LGS sınavına soru hazırlayan uzman bir
8. sınıf öğretmenisin.

DERS:
{ders}

KONU:
{konu}

SORU TÜRÜ:
{tur}

ZORLUK SEVİYESİ:
{zorluk}

KONU SINIRI:

{konu_kurali}

SORU TARZI:

{stil}

KESİN KURALLAR:

1. Soru seçilen konuyu gerçekten ölçmeli.
2. Öğrenci seçilen konuyu bilmeden çözememeli.
3. Gerçek LGS sorularını kopyalama.
4. Tamamen özgün bir soru oluştur.
5. Soru kendi içinde tutarlı olmalı.
6. Yalnızca bir doğru seçenek bulunmalı.
7. Soruyu oluşturduktan sonra kendin çöz.
8. Doğru cevabı ikinci kez kontrol et.
9. Matematiksel işlem varsa tekrar hesapla.
10. Çözüm ve cevap birbiriyle tamamen uyumlu olsun.
ZORLUK KURALI:

- Kolay: temel kazanımı doğrudan ölç.
- Orta: birkaç adım düşünme gerektirsin.
- Zor: güçlü çeldiriciler ve çok adımlı muhakeme kullansın.
- Gerçek LGS Seviyesi: MEB LGS yeni nesil mantığına mümkün olduğunca yaklaşsın; yorum, ilişkilendirme ve muhakeme gerektirsin.

SORUYU GÖNDERMEDEN ÖNCE KENDİN KONTROL ET:

1. Soru gerçekten seçilen konuya ait mi?
2. Öğrenci seçilen konuyu bilmeden çözebiliyorsa soruyu yeniden tasarla.
3. Yalnızca bir doğru seçenek var mı?
4. Verilen cevap gerçekten doğru mu?
5. Çözüm ile cevap tamamen uyumlu mu?
6. Verilen sayılar ve bilgiler tutarlı mı?
7. Matematiksel işlem varsa ikinci kez hesapla.
8. LGS Tarzı seçildiyse gerçekten muhakeme gerektiriyor mu?
9. Soruda çelişki varsa düzelt.
10. Kontrolden geçmeyen ilk taslağı kullanıcıya gönderme.

SADECE tüm kontrollerden geçmiş son soruyu JSON olarak döndür.
SADECE JSON döndür:

{{
    "soru": "soru metni",
    "A": "A seçeneği",
    "B": "B seçeneği",
    "C": "C seçeneği",
    "D": "D seçeneği",
    "cevap": "A",
    "cozum": "adım adım çözüm",
    "ipucu": "kısa LGS ipucu"
}}
"""

    return gemini_json(prompt)


# =========================================================
# KALİTE DENETİMİ
# =========================================================

# =========================================================
# GÜVENLİ SORU ÜRET
# =========================================================

def guvenli_soru_uret(ders, konu, tur, zorluk):

    soru = soru_uret(
        ders,
        konu,
        tur,
        zorluk
    )

    return soru
    son_neden = ""

    for deneme in range(3):

        soru = soru_uret(
            ders,
            konu,
            tur
        )

        kontrol = soru_kontrol(
            ders,
            konu,
            tur,
            soru
        )

        if kontrol.get("onay") is True:
            return soru

        son_neden = kontrol.get(
            "neden",
            "Soru kalite kontrolünden geçmedi."
        )

    raise Exception(
        "LGSBOT uygun bir soru oluşturamadı. "
        + son_neden
    )


# =========================================================
# BAŞLIK
# =========================================================

st.markdown(
    '<div class="title">🤖 LGSBOT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Ramazan Eymen ÇAKIR</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Kişisel LGS Çalışma Merkezi • Gemini destekli</div>',
    unsafe_allow_html=True
)


# =========================================================
# DERS SEÇİMİ
# =========================================================

st.markdown("### 1️⃣ Dersini seç")

dersler = list(KONULAR.keys())

cols = st.columns(4)

for i, ders in enumerate(dersler):

    with cols[i]:

        if st.button(
            ders,
            use_container_width=True,
            type="primary"
            if st.session_state.ders == ders
            else "secondary"
        ):

            st.session_state.ders = ders
            st.session_state.soru = None
            st.session_state.cevap_acik = False
            st.session_state.cozum_acik = False

            st.rerun()


# =========================================================
# KONU
# =========================================================

st.markdown("### 2️⃣ Konuyu seç")

konu = st.selectbox(
    "Konu",
    KONULAR[st.session_state.ders],
    label_visibility="collapsed"
)


# =========================================================
# ZORLUK
# =========================================================

st.markdown("### 3️⃣ Zorluk seviyesini seç")

zorluk = st.selectbox(
    "Zorluk",
    [
        "Kolay",
        "Orta",
        "Zor",
        "Gerçek LGS Seviyesi"
    ],
    index=1,
    label_visibility="collapsed"
)


# =========================================================
# SORU TÜRÜ
# =========================================================

st.markdown("### 4️⃣ Soru türünü seç")

c1, c2 = st.columns(2)

with c1:

    klasik = st.button(
        "✏️ Klasik Soru",
        use_container_width=True
    )

with c2:

    lgs = st.button(
        "🎯 LGS Tarzı Soru",
        use_container_width=True
    )


if klasik:

    st.session_state.cevap_acik = False
    st.session_state.cozum_acik = False

    with st.spinner(
        "Soruyu hazırlıyorum ve doğruluğunu kontrol ediyorum..."
    ):

        try:

          st.session_state.soru = guvenli_soru_uret(
    st.session_state.ders,
    konu,
    "Klasik",
    zorluk
)
            )

        except Exception as e:

            st.error(str(e))


if lgs:

    st.session_state.cevap_acik = False
    st.session_state.cozum_acik = False

    with st.spinner(
        "LGS tarzı soru hazırlanıyor ve kontrol ediliyor..."
    ):

        try:

           st.session_state.soru = guvenli_soru_uret(
    st.session_state.ders,
    konu,
    "LGS Tarzı",
    zorluk
)
            )

        except Exception as e:

            st.error(str(e))


# =========================================================
# SORUYU GÖSTER
# =========================================================

if st.session_state.soru:
    q = st.session_state.soru

    st.markdown("---")
    st.markdown("## 🎯 Soru")

    st.markdown(q.get("soru", ""))

    st.markdown(f"**A)** {q.get('A', '')}")
    st.markdown(f"**B)** {q.get('B', '')}")
    st.markdown(f"**C)** {q.get('C', '')}")
    st.markdown(f"**D)** {q.get('D', '')}")

    # =====================================================
    # ÇİZİM TAHTASI
    # =====================================================

    st.markdown("### 🖊️ Çözüm Tahtası")

    drawing_board = """
    <html>
    <head>

    <style>

    body {
        margin: 0;
        background: transparent;
        font-family: Arial, sans-serif;
    }

    .toolbar {
        background: #111827;
        padding: 10px;
        border-radius: 12px 12px 0 0;
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }

    button {
        padding: 9px 14px;
        border: 0;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        background: #e5e7eb;
    }

    button:hover {
        background: #ffffff;
    }

    .active {
        background: #3b82f6;
        color: white;
    }

    canvas {
        background: white;
        width: 100%;
        height: 420px;
        border-radius: 0 0 12px 12px;
        cursor: crosshair;
        touch-action: none;
    }

    </style>

    </head>

    <body>

    <div class="toolbar">

        <button id="penBtn" onclick="setTool('pen')">
            ✏️ Kalem
        </button>

        <button id="eraserBtn" onclick="setTool('eraser')">
            🧽 Silgi
        </button>

        <button id="rectBtn" onclick="setTool('rectangle')">
            ▭ Dikdörtgen
        </button>

        <button id="circleBtn" onclick="setTool('circle')">
            ◯ Daire
        </button>

        <button id="triangleBtn" onclick="setTool('triangle')">
            △ Üçgen
        </button>

        <button onclick="clearBoard()">
            🗑️ Temizle
        </button>

    </div>

    <canvas id="board"></canvas>


    <script>

    const canvas = document.getElementById("board");
    const ctx = canvas.getContext("2d");

    canvas.width = 1200;
    canvas.height = 420;

    let tool = "pen";

    let drawing = false;

    let startX = 0;
    let startY = 0;

    let savedImage = null;


    function getPosition(e) {

        const rect = canvas.getBoundingClientRect();

        return {

            x:
            (e.clientX - rect.left) *
            (canvas.width / rect.width),

            y:
            (e.clientY - rect.top) *
            (canvas.height / rect.height)

        };

    }


    function setTool(newTool) {

        tool = newTool;

        document
            .querySelectorAll(".toolbar button")
            .forEach(btn => btn.classList.remove("active"));

        if (newTool === "pen")
            document.getElementById("penBtn").classList.add("active");

        if (newTool === "eraser")
            document.getElementById("eraserBtn").classList.add("active");

        if (newTool === "rectangle")
            document.getElementById("rectBtn").classList.add("active");

        if (newTool === "circle")
            document.getElementById("circleBtn").classList.add("active");

        if (newTool === "triangle")
            document.getElementById("triangleBtn").classList.add("active");

    }


    canvas.addEventListener("mousedown", function(e) {

        drawing = true;

        const pos = getPosition(e);

        startX = pos.x;
        startY = pos.y;

        savedImage = ctx.getImageData(
            0,
            0,
            canvas.width,
            canvas.height
        );


        if (tool === "pen" || tool === "eraser") {

            ctx.beginPath();

            ctx.moveTo(startX, startY);

        }

    });


    canvas.addEventListener("mousemove", function(e) {

        if (!drawing)
            return;

        const pos = getPosition(e);

        const currentX = pos.x;
        const currentY = pos.y;


        // -------------------------
        // KALEM
        // -------------------------

        if (tool === "pen") {

            ctx.strokeStyle = "#111111";
            ctx.lineWidth = 3;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";

            ctx.lineTo(currentX, currentY);

            ctx.stroke();

        }


        // -------------------------
        // SİLGİ
        // -------------------------

        else if (tool === "eraser") {

            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 28;
            ctx.lineCap = "round";

            ctx.lineTo(currentX, currentY);

            ctx.stroke();

        }


        // ŞEKİLLERDE ÖNİZLEME
        else {

            ctx.putImageData(savedImage, 0, 0);

            ctx.strokeStyle = "#111111";
            ctx.lineWidth = 3;


            // -------------------------
            // DİKDÖRTGEN
            // -------------------------

            if (tool === "rectangle") {

                ctx.strokeRect(
                    startX,
                    startY,
                    currentX - startX,
                    currentY - startY
                );

            }


            // -------------------------
            // DAİRE / ELİPS
            // -------------------------

            else if (tool === "circle") {

                const centerX =
                    (startX + currentX) / 2;

                const centerY =
                    (startY + currentY) / 2;

                const radiusX =
                    Math.abs(currentX - startX) / 2;

                const radiusY =
                    Math.abs(currentY - startY) / 2;

                ctx.beginPath();

                ctx.ellipse(
                    centerX,
                    centerY,
                    radiusX,
                    radiusY,
                    0,
                    0,
                    Math.PI * 2
                );

                ctx.stroke();

            }


            // -------------------------
            // ÜÇGEN
            // -------------------------

            else if (tool === "triangle") {

                const middleX =
                    (startX + currentX) / 2;

                ctx.beginPath();

                // üst nokta
                ctx.moveTo(
                    middleX,
                    startY
                );

                // sol alt
                ctx.lineTo(
                    startX,
                    currentY
                );

                // sağ alt
                ctx.lineTo(
                    currentX,
                    currentY
                );

                ctx.closePath();

                ctx.stroke();

            }

        }

    });


    canvas.addEventListener("mouseup", function() {

        drawing = false;

        ctx.closePath();

    });


    canvas.addEventListener("mouseleave", function() {

        drawing = false;

    });


    function clearBoard() {

        ctx.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );

    }


    // başlangıç aracı
    setTool("pen");

    </script>

    </body>
    </html>
    """
    components.html(
        drawing_board,
        height=450
    )


    # =====================================================
    # CEVAP
    # =====================================================

    st.markdown("### 🔐 Cevap ve çözüm")

    b1, b2, b3 = st.columns(3)

    with b1:

        if st.button(
            "🔑 Cevabı Göster",
            use_container_width=True
        ):

            st.session_state.cevap_acik = True


    with b2:

        if st.button(
            "🧠 Çözümü Göster",
            use_container_width=True
        ):

            st.session_state.cozum_acik = True


    with b3:

        if st.button(
            "🔄 Yeni Soru",
            use_container_width=True
        ):

            st.session_state.soru = None
            st.session_state.cevap_acik = False
            st.session_state.cozum_acik = False

            st.rerun()


    if st.session_state.cevap_acik:

        st.markdown(
            f"""
            <div class="answer">

            <b>✅ Doğru cevap: {q.get("cevap", "")}</b>

            </div>
            """,
            unsafe_allow_html=True
        )


    if st.session_state.cozum_acik:

        st.markdown(
            f"""
            <div class="solution">

            <b>🧠 Çözüm</b>

            <br><br>

            {q.get("cozum", "")}

            <br><br>

            <b>💡 LGS İpucu:</b>

            {q.get("ipucu", "")}

            </div>
            """,
            unsafe_allow_html=True
        )