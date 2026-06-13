import anthropic
import requests
import json
import os
import random
import base64
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BUFFER_API_KEY    = os.environ["BUFFER_API_KEY"].strip()
PEXELS_API_KEY    = os.environ["PEXEL_API"]
UNSPLASH_KEY      = os.environ.get("UNSPLASH_ACCESS_KEY", "")
CHANNEL_ID        = "6a2a25e38f1d11f9b2742181"

# 날짜 기준 스타일 로테이션 (짝수일 = 기존 viral, 홀수일 = 새 Shellness+바비톡)
TODAY_STYLE = "shellness" if datetime.now().day % 2 == 1 else "viral"

TOPICS = [
    {
        "type": "레이저제모",
        "detail": "남성 레이저 제모 (수염,등,팔다리,겨드랑이), 효과, 횟수, 주의사항",
        "pexels_thumb": "men dermatology clinic minimal clean",
        "unsplash_thumb": "dermatology skin clinic minimal",
        "pexels_product": "laser beauty skincare device",
        "unsplash_product": "skincare product minimal white",
        "shellness_copy": ("지금 당장\n수염 밀어도\n3일이면 끝이지?", "Laser"),
        "hook1": "면도 독 때문에",
        "hook2": "피부 망가지고 있던 거 맞음.",
    },
    {
        "type": "피부시술",
        "detail": "남성 피부과 시술 (리프팅, 보톡스, 흉터, 모공, 레이저)",
        "pexels_thumb": "men face portrait natural light close up",
        "unsplash_thumb": "men portrait minimal aesthetic",
        "pexels_product": "skincare serum moisturizer bottle",
        "unsplash_product": "cosmetics product flat lay minimal",
        "shellness_copy": ("피부과는\n남자도\n가도 됨.", "Care"),
        "hook1": "피부과 가야 할 것 같은데",
        "hook2": "아직도 미루고 있다면.",
    },
    {
        "type": "운동",
        "detail": "남성 헬스 루틴, 벌크업, 다이어트, 자세 교정",
        "pexels_thumb": "gym fitness dark dramatic lighting",
        "unsplash_thumb": "gym workout minimal dark aesthetic",
        "pexels_product": "protein supplement powder shaker",
        "unsplash_product": "gym equipment dumbbell minimal",
        "shellness_copy": ("6개월 했는데\n거울 앞에서\n멈췄다면.", "Strength"),
        "hook1": "헬스 6개월 했는데",
        "hook2": "왜 아직도 뱃살이야?",
    },
    {
        "type": "피부관리",
        "detail": "남성 기초케어, 선크림, 보습, 각질, 모공 관리",
        "pexels_thumb": "men morning bathroom mirror routine",
        "unsplash_thumb": "men skincare bathroom minimal light",
        "pexels_product": "toner sunscreen skincare tube",
        "unsplash_product": "skincare product clean minimal",
        "shellness_copy": ("세안만으론\n부족하다는 거\n알잖아.", "Skin"),
        "hook1": "세안 열심히 하는데",
        "hook2": "왜 모공이 더 커지지?",
    },
    {
        "type": "그루밍",
        "detail": "남성 헤어스타일, 수염 관리, 향수, 자기관리 루틴",
        "pexels_thumb": "men barber grooming stylish urban",
        "unsplash_thumb": "men grooming style minimal aesthetic",
        "pexels_product": "hair wax pomade perfume bottle",
        "unsplash_product": "perfume bottle minimal clean",
        "shellness_copy": ("향기는\n기억에\n남는다.", "Grooming"),
        "hook1": "향수 하나 바꿨는데",
        "hook2": "반응이 달라졌다는 거.",
    },
    {
        "type": "다이어트",
        "detail": "남성 식단 관리, 단백질 섭취, 체중 감량, 간헐적 단식",
        "pexels_thumb": "healthy food meal prep minimal clean",
        "unsplash_thumb": "healthy food protein minimal flat",
        "pexels_product": "protein food chicken egg healthy",
        "unsplash_product": "healthy meal food minimal",
        "shellness_copy": ("덜 먹는 게\n아니라\n잘 먹는 거야.", "Diet"),
        "hook1": "다이어트 3번째인데",
        "hook2": "매번 실패하는 이유 있음.",
    },
]

HIGHLIGHT_BLUE = (59, 130, 246)   # #3B82F6
LETTER_SPACING = -1               # 전역 자간 (PIL은 직접 지원 안 해 kerning으로 근사)


# ── 폰트 ─────────────────────────────────────────────────────────
def F():
    try:
        B  = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
        EB = "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf"
        R  = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        return {
            "title_xl": ImageFont.truetype(EB, 88),
            "title_lg": ImageFont.truetype(EB, 72),
            "title_md": ImageFont.truetype(EB, 52),
            "sub":      ImageFont.truetype(B,  30),
            "body":     ImageFont.truetype(R,  34),
            "body_sm":  ImageFont.truetype(R,  28),
            "hl":       ImageFont.truetype(B,  34),   # 하이라이트 텍스트
            "product":  ImageFont.truetype(EB, 36),
            "price":    ImageFont.truetype(B,  28),
            "desc":     ImageFont.truetype(R,  27),
            "label":    ImageFont.truetype(B,  22),
            "brand":    ImageFont.truetype(B,  24),
            "caption":  ImageFont.truetype(R,  22),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ["title_xl","title_lg","title_md","sub","body","body_sm",
                                "hl","product","price","desc","label","brand","caption"]}


# ── 자간 tight 텍스트 렌더 헬퍼 ──────────────────────────────────
def draw_tight(draw, x, y, text, font, fill, spacing=-1):
    """자간을 spacing px 만큼 당겨서 글자 단위로 그리기"""
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=fill)
        cx += draw.textlength(ch, font=font) + spacing


def wrap(draw, text, font, max_w, spacing=-1):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        est = sum(draw.textlength(c, font=font) + spacing for c in test)
        if est <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


# ── 이미지 소스: Pexels + Unsplash 랜덤 믹스 ────────────────────
def fetch_image(pexels_kw: str, unsplash_kw: str, square=True) -> Image.Image | None:
    source = random.choice(["pexels", "unsplash"])
    img = _pexels(pexels_kw, square) if source == "pexels" else _unsplash(unsplash_kw)
    if img is None:
        img = _pexels(pexels_kw, square) if source == "unsplash" else _unsplash(unsplash_kw)
    return img


def _pexels(kw: str, square=True) -> Image.Image | None:
    orient = "square" if square else "landscape"
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": kw, "orientation": orient, "per_page": 15},
            timeout=10,
        )
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                url = random.choice(photos)["src"]["large"]
                resp = requests.get(url, timeout=15)
                return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"Pexels 실패({kw}): {e}")
    return None


def _unsplash(kw: str) -> Image.Image | None:
    if not UNSPLASH_KEY:
        return None
    try:
        r = requests.get(
            "https://api.unsplash.com/photos/random",
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            params={"query": kw, "orientation": "squarish"},
            timeout=10,
        )
        if r.status_code == 200:
            url = r.json()["urls"]["regular"]
            resp = requests.get(url, timeout=15)
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"Unsplash 실패({kw}): {e}")
    return None


def crop_sq(img: Image.Image, size=1080) -> Image.Image:
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))
    return img.resize((size, size), Image.LANCZOS)


def crop_rect(img: Image.Image, tw=1060, th=560) -> Image.Image:
    iw, ih = img.size
    scale = max(tw/iw, th/ih)
    img = img.resize((int(iw*scale)+1, int(ih*scale)+1), Image.LANCZOS)
    iw, ih = img.size
    return img.crop(((iw-tw)//2, (ih-th)//2, (iw+tw)//2, (ih+th)//2))


# ── 1. Claude 콘텐츠 생성 ─────────────────────────────────────────
def generate_content(topic: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""인스타그램 카드뉴스 콘텐츠를 만들어주세요.
타겟: 자기관리에 관심 있는 20-35세 한국 남성
주제: {topic['type']} — {topic['detail']}

--- 화법 규칙 (뉴닉체 + 트위터 무드 믹스) ---
뉴닉체: ~거든요, ~이에요, ~한다는 사실! 친근하고 명확하게
트위터 무드: 짧고 단정하게 끊기, 공감 유발, "솔직히", "진짜로", "근데", "맞음" 같은 구어체
핵심 문장에 [HIGHLIGHT] 태그 1개 — 블루 배경에 흰 글씨로 강조될 문장

--- ㄴ 설명 규칙 ---
"ㄴ" 으로 시작, 트위터처럼 짧고 직접적, 수치나 특징 포함

다음 JSON으로만 응답:
{{
  "shellness_body": "뉴닉+트위터 화법 본문. 줄바꿈 \\n. 3-4문단. [HIGHLIGHT]태그로 핵심 1문장 표시",
  "products": [
    {{"name": "제품명 브랜드 포함", "price": "가격", "desc": "ㄴ 짧고 직접적인 설명 (35자 이내)", "pexels_keyword": "영문 3단어", "unsplash_keyword": "영문 3단어"}},
    {{"name": "제품명 브랜드 포함", "price": "가격", "desc": "ㄴ 짧고 직접적인 설명 (35자 이내)", "pexels_keyword": "영문 3단어", "unsplash_keyword": "영문 3단어"}}
  ],
  "caption": "뉴닉+트위터 무드 캡션. 이모지 포함 3문장 + 빈줄 + 해시태그 8개"
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text
    parsed = json.loads(text[text.find('{'):text.rfind('}')+1])
    parsed["topic"] = topic
    return parsed


# ── 2. 카드 1: Shellness 썸네일 (워터마크 없음) ──────────────────
def card1_shellness(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    topic = content["topic"]
    Fnt = F()

    bg = fetch_image(topic["pexels_thumb"], topic["unsplash_thumb"])
    canvas = crop_sq(bg) if bg else Image.new("RGBA", (W, H), (26,24,22,255))
    canvas = canvas.convert("RGBA")

    # 오버레이
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(ov)
    for i in range(220):
        d.rectangle([(0,i),(W,i+1)], fill=(0,0,0,int(90*(1-i/220))))
    for i in range(520):
        d.rectangle([(0,H-520+i),(W,H-520+i+1)], fill=(0,0,0,int(215*(i/520)**1.1)))
    canvas = Image.alpha_composite(canvas, ov)
    draw = ImageDraw.Draw(canvas)

    # 영문 소제목
    _, eng = topic["shellness_copy"]
    draw_tight(draw, 54, H-440, eng, Fnt["sub"], (255,255,255,120), spacing=3)

    # 메인 카피 — ExtraBold, 자간 타이트
    copy_raw, _ = topic["shellness_copy"]
    lines = copy_raw.split("\n")
    y = H - 380
    for line in lines:
        draw_tight(draw, 50, y, line, Fnt["title_lg"], (255,255,255), spacing=-2)
        y += 94

    out = io.BytesIO()
    canvas.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out


# ── 3. 카드 2·3: 바비톡 본문 (블루 하이라이트) ───────────────────
def card_body(content: dict, idx: int) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    topic = content["topic"]
    products = content.get("products", [])
    prod = products[idx % len(products)]

    BG = (244, 242, 239)
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    FRAME_H = 540

    # 상단 이미지
    main_img = fetch_image(topic["pexels_thumb"], topic["unsplash_thumb"])
    if main_img:
        frame_bg = crop_rect(main_img.convert("RGB"), W, FRAME_H)
        canvas.paste(frame_bg, (0, 0))
    else:
        canvas.paste(Image.new("RGB", (W, FRAME_H), (200,196,190)), (0,0))

    draw = ImageDraw.Draw(canvas)

    # 자막바
    draw.rectangle([(0, FRAME_H-56), (W, FRAME_H)], fill=(0,0,0,int(255*0.78)))
    caption_text = f"남 | {topic['hook1']}"
    draw_tight(draw, W//2 - draw.textlength(caption_text, font=Fnt["caption"])//2,
               FRAME_H-42, caption_text, Fnt["caption"], (255,255,255), spacing=-1)

    # 채널 라벨
    draw.rectangle([(0,0),(320,52)], fill=(15,14,12))
    draw_tight(draw, 18, 14, f"내스타일 | {topic['type']}", Fnt["label"], (255,255,255), spacing=0)

    # 제품 플로팅
    prod_img = fetch_image(
        prod.get("pexels_keyword","skincare product"),
        prod.get("unsplash_keyword","product minimal")
    )
    if prod_img:
        PSIZ = 210
        pt = prod_img.convert("RGBA").resize((PSIZ, PSIZ), Image.LANCZOS)
        circ = Image.new("RGBA", (PSIZ+24, PSIZ+24), (0,0,0,0))
        cd = ImageDraw.Draw(circ)
        cd.ellipse([(0,0),(PSIZ+24,PSIZ+24)], fill=(255,255,255,230))
        px, py = W-PSIZ-50, FRAME_H-PSIZ-30
        canvas.paste(circ.convert("RGB"), (px-12, py-12), mask=circ.split()[3])
        canvas.paste(pt.convert("RGB"), (px, py))
        draw = ImageDraw.Draw(canvas)

    # 제품명 + 가격
    TEXT_Y = FRAME_H + 34
    name = prod.get("name","")
    price = prod.get("price","")
    draw_tight(draw, 50, TEXT_Y, name, Fnt["product"], (15,14,12), spacing=-2)
    if price:
        draw_tight(draw, 50, TEXT_Y+52, price, Fnt["price"], (192,57,43), spacing=-1)

    # ㄴ 설명
    desc = prod.get("desc","")
    desc_lines = wrap(draw, desc, Fnt["desc"], W-100, spacing=-1)
    dy = TEXT_Y + 98
    for ln in desc_lines:
        draw_tight(draw, 50, dy, ln, Fnt["desc"], (80,76,70), spacing=-1)
        dy += 36

    # 구분선
    draw.rectangle([(50, dy+16),(W-50, dy+17)], fill=(204,200,196))

    # 본문 (뉴닉+트위터)
    body_raw = content.get("shellness_body","")
    paragraphs = body_raw.split("\n")
    by = dy + 38
    hl_done = False
    hl_marker = "[HIGHLIGHT]"
    hl_text = ""
    if hl_marker in body_raw:
        after = body_raw.split(hl_marker)[1]
        hl_text = after.split("\n")[0].strip()

    for para in paragraphs:
        clean = para.replace(hl_marker,"").strip()
        if not clean:
            by += 16
            continue
        is_hl = (clean == hl_text and not hl_done)
        if is_hl:
            # 블루 하이라이트 박스
            hl_w = sum(draw.textlength(c, font=Fnt["hl"])-1 for c in clean) + 24
            draw.rectangle([(48, by-4),(48+hl_w, by+44)], fill=HIGHLIGHT_BLUE)
            draw_tight(draw, 56, by, clean, Fnt["hl"], (255,255,255), spacing=-1)
            by += 56
            hl_done = True
        else:
            lines = wrap(draw, clean, Fnt["body_sm"], W-100, spacing=-1)
            for ln in lines:
                draw_tight(draw, 50, by, ln, Fnt["body_sm"], (44,42,38), spacing=-1)
                by += 36
            by += 8
        if by > H - 70:
            break

    # 스와이프 안내
    draw_tight(draw, 50, H-48, "← 스와이프해서 다음 꿀템 확인하기",
               Fnt["caption"], (154,150,144), spacing=-1)

    out = io.BytesIO()
    canvas.save(out, "PNG")
    out.seek(0)
    return out


# ── 4. 카드 4: 클로징 (블루 하이라이트) ─────────────────────────
def card4_closing(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    topic = content["topic"]

    bg = fetch_image(topic["pexels_thumb"], topic["unsplash_thumb"])
    canvas = crop_sq(bg) if bg else Image.new("RGBA", (W,H),(22,20,26,255))
    canvas = canvas.convert("RGBA")

    ov = Image.new("RGBA",(W,H),(0,0,0,160))
    canvas = Image.alpha_composite(canvas, ov)
    draw = ImageDraw.Draw(canvas)

    # 메인 카피
    lines = ["다 알면서도", "안 하고 있던", "그 루틴."]
    y = H//2 - 160
    for ln in lines:
        lw = sum(draw.textlength(c, font=Fnt["title_lg"])-2 for c in ln)
        draw_tight(draw, (W-lw)//2, y, ln, Fnt["title_lg"], (255,255,255), spacing=-2)
        y += 96

    # 블루 하이라이트
    sub = "저장하고 오늘 밤부터 시작."
    sw = sum(draw.textlength(c, font=Fnt["hl"])-1 for c in sub) + 28
    sx = (W-sw)//2
    draw.rectangle([(sx, y+14),(sx+sw, y+60)], fill=HIGHLIGHT_BLUE)
    draw_tight(draw, sx+14, y+14, sub, Fnt["hl"], (255,255,255), spacing=-1)

    # 서브
    subsub = "어렵지 않아요. 진짜로요."
    ssw = sum(draw.textlength(c, font=Fnt["body_sm"])-1 for c in subsub)
    draw_tight(draw, (W-ssw)//2, y+80, subsub, Fnt["body_sm"], (255,255,255,130), spacing=-1)

    # 브랜드
    bw = sum(draw.textlength(c, font=Fnt["brand"])-1 for c in "내스타일")
    draw_tight(draw, (W-bw)//2, H-56, "내스타일", Fnt["brand"], (255,255,255,90), spacing=2)

    out = io.BytesIO()
    canvas.convert("RGB").save(out,"PNG")
    out.seek(0)
    return out


# ── 5. 기존 viral 스타일 카드 (짝수일) ───────────────────────────
def card1_viral(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    topic = content["topic"]

    bg = fetch_image(topic["pexels_thumb"], topic["unsplash_thumb"])
    canvas = crop_sq(bg) if bg else Image.new("RGBA",(W,H),(26,26,26,255))
    canvas = canvas.convert("RGBA")

    ov = Image.new("RGBA",(W,H),(0,0,0,0))
    d  = ImageDraw.Draw(ov)
    for i in range(300):
        d.rectangle([(0,i),(W,i+1)],fill=(0,0,0,int(160*(1-i/300))))
    for i in range(440):
        y=H-440+i
        d.rectangle([(0,y),(W,y+1)],fill=(0,0,0,int(220*(i/440)**1.2)))
    canvas = Image.alpha_composite(canvas, ov)
    draw = ImageDraw.Draw(canvas)

    # 빨간 라벨
    draw.rectangle([(44,38),(400,104)], fill=(210,25,25))
    draw_tight(draw, 60, 52, "충격 실화", Fnt["sub"], (255,255,255), spacing=-1)

    # 후킹 문구
    draw_tight(draw, 50, H-248, topic["hook1"], Fnt["title_lg"], (255,255,255), spacing=-2)
    draw_tight(draw, 50, H-140, topic["hook2"], Fnt["title_lg"], (255,230,40), spacing=-2)

    out = io.BytesIO()
    canvas.convert("RGB").save(out,"PNG")
    out.seek(0)
    return out


# ── Imgur 업로드 ─────────────────────────────────────────────────
def upload(img: io.BytesIO) -> str | None:
    r = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": "Client-ID 546c25a59c58ad7"},
        data={"image": base64.b64encode(img.getvalue()).decode(),"type":"base64"},
        timeout=30,
    )
    if r.status_code == 200:
        url = r.json()["data"]["link"]
        print(f"  Imgur: {url}")
        return url
    print(f"  Imgur 실패: {r.text[:150]}")
    return None


# ── Buffer 발행 ──────────────────────────────────────────────────
def post(caption: str, urls: list) -> bool:
    safe   = caption.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")
    assets = ", ".join([f'{{ image: {{ url: "{u}" }} }}' for u in urls])
    query  = f'''mutation{{createPost(input:{{
      text:"{safe}" channelId:"{CHANNEL_ID}"
      schedulingType:automatic mode:addToQueue
      metadata:{{instagram:{{type:post,shouldShareToFeed:true}}}}
      assets:[{assets}]
    }}){{...on PostActionSuccess{{post{{id}}}}...on MutationError{{message}}}}}}'''
    r = requests.post(
        "https://api.buffer.com",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {BUFFER_API_KEY}"},
        json={"query":query},
    )
    return "post" in (r.json().get("data",{}).get("createPost",{}) or {})


# ── 메인 ─────────────────────────────────────────────────────────
def main():
    topic = random.choice(TOPICS)
    print(f"=== {datetime.now().strftime('%m/%d')} | 스타일: {TODAY_STYLE} | 토픽: {topic['type']} ===")

    content = generate_content(topic)

    if TODAY_STYLE == "shellness":
        # 홀수일: Shellness 썸네일 + 바비톡 본문 2장 + 클로징
        print("[shellness 스타일] 카드 4장 생성...")
        c1 = card1_shellness(content)
        c2 = card_body(content, 0)
        c3 = card_body(content, 1)
        c4 = card4_closing(content)
        cards = [c1, c2, c3, c4]
    else:
        # 짝수일: viral 썸네일 + 바비톡 본문 2장 + 클로징
        print("[viral 스타일] 카드 4장 생성...")
        c1 = card1_viral(content)
        c2 = card_body(content, 0)
        c3 = card_body(content, 1)
        c4 = card4_closing(content)
        cards = [c1, c2, c3, c4]

    print("업로드 중...")
    urls = [u for u in [upload(c) for c in cards] if u]
    if len(urls) < 2:
        print("업로드 실패")
        return

    ok = post(content["caption"], urls)
    print("=== 완료! ===" if ok else "=== 발행 실패 ===")


if __name__ == "__main__":
    main()
