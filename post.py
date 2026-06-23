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

# 날짜 기준 스타일 로테이션 (짝수일 = viral, 홀수일 = shellness)
TODAY_STYLE = "shellness" if datetime.now().day % 2 == 1 else "viral"

# ── 100개 콘텐츠 시드풀 ───────────────────────────────────────────
CONTENT_POOL = [
    "카카오톡 선물하기로 주기 좋은 2만 원대 남성 그루밍 템",
    "센스 있다는 소리 듣는 남자친구 생일 선물 베스트 5",
    "실패 없는 20대 남성 기념일 선물 추천 (가격대별)",
    "30대 직장인 남자친구를 위한 실용적인 프리미엄 선물",
    "카카오 선물하기 전용: 남성 올인원 스킨케어 패키지 비교",
    "향수에 입문하는 남친을 위한 호불호 없는 니치 향수 추천",
    "피부 타입별 남자친구 선물용 선크림 & 클렌저 세트",
    "남자친구 감동시키는 센스 있는 차량용 방향제 브랜드",
    "센스 넘치는 여친이 골라주는 남성 바디 스프레이 4선",
    "카카오 선물하기 1위 립밤: 남성 발색 립밤 솔직 비교",
    "관리하는 남자를 위한 가성비 헤어 에센스 및 오일 선물",
    "2030 남성이 직접 뽑은 가장 받고 싶은 그루밍 선물",
    "부담 없이 선물하기 좋은 남성 안티에이징 아이크림",
    "트렌디한 남성을 위한 스머지 스틱 및 인센스 홀더 선물",
    "깔끔한 첫인상을 위한 남성 코털 정리기 브랜드 추천",
    "기념일에 실패 없는 여자친구 감동 선물 가이드",
    "센스 있는 남친이 되는 길: 여자친구 향수 선물 베스트",
    "카카오톡 선물하기에서 핫한 여성 뷰티&웰니스 아이템",
    "20대 여성 선호도 1위 디자인 주얼리 브랜드 추천",
    "직장인 여자친구를 위한 힐링 및 데스크테리어 선물",
    "실패 없는 여자친구 화장품/스킨케어 선물 고르는 법",
    "감성 가득한 가성비 여자친구 생일 선물 아이디어",
    "여친 감동 자극: 센스 있는 레터링/각인 선물 아이템",
    "주말 호캉스 갈 때 여자친구 몰래 준비하기 좋은 힐링 기프트",
    "여성들이 직접 말한 '남친에게 받고 감동했던 선물' 리스트",
    "가장 섬세하고 디테일한 남성 MBTI 순위 TOP 5",
    "MBTI별 남성이 스트레스를 해소하는 자기관리 루틴",
    "F형 남친과 T형 남친의 피부 고민 상담 대처법 차이",
    "계획적인 ISTJ 남성을 위한 타임라인별 그루밍 가이드",
    "자유로운 ENFP 남성이 끝까지 지킬 수 있는 최소한의 루틴",
    "자기성찰 끝판왕 INFJ 남성의 내면 및 외모 관리법",
    "사교적인 ESFJ 남성이 모임 전날 무조건 하는 피부 관리",
    "효율 중시 INTJ 남성을 위한 올인원 그루밍 정착기",
    "열정적인 ENFJ 남성의 호감도를 높이는 스타일링 팁",
    "MBTI 유형별 어울리는 남성 향수 노트 매칭 가이드",
    "소심한 I형 남성도 편하게 방문할 수 있는 바버샵 고르는 법",
    "트렌드세터 ENTP 남성을 위한 최신 그루밍 디바이스 추천",
    "감성적인 INFP 남성의 멘탈 케어 및 저녁 스킨케어 의식",
    "행동파 ESTP 남성을 위한 야외 활동 맞춤형 자외선 차단 팁",
    "안정적인 ISFJ 남성이 5년째 유지 중인 데일리 관리법",
    "성공 지향 ENTJ 남성의 프로페셔널한 비즈니스 미팅 스타일링",
    "아이디어가 샘솟는 INTP 남성을 위한 미니멀 홈케어",
    "예술가 기질 ISFP 남성의 개성을 살리는 레이어드 패션",
    "현실적이고 든든한 ESTJ 남성의 완벽한 면도 루틴",
    "에너지 넘치는 ESFP 남성의 올데이 지속 헤어 스타일링",
    "헬스장에서 운동할 때 나만 이때 뿌듯해? 공감 모음",
    "오운완 직후 거울 볼 때 펌핑된 모습에 취하는 순간",
    "새벽 운동 끝내고 샤워실 나올 때 밀려오는 도파민",
    "안 들어가던 바지가 맞기 시작할 때 느끼는 희열",
    "스트랩 감을 때 왠지 모르게 운동 고수가 된 듯한 기분",
    "남성 초보자를 위한 주 3회 분할 운동 루틴 가이드",
    "바쁜 직장인을 위한 효율적인 30분 맨몸 운동 루틴",
    "넓은 어깨를 만들기 위한 필수 상체 운동 3가지",
    "운동 전 수행 능력을 극대화하는 부스터 및 커피 섭취 타이밍",
    "근성장을 위한 운동 후 단백질 및 탄수화물 골든타임",
    "러닝 입문자를 위한 페이스 조절 및 부상 방지 루틴",
    "홈트레이닝으로 탄탄한 복근 만드는 코어 운동 가이드",
    "운동 중 수분 섭취가 피부와 근육에 미치는 영향",
    "직장인 거북목 탈출을 위한 데일리 스트레칭 5분 루틴",
    "하체 운동 하는 날 무조건 지켜야 할 부상 방지 스트레칭",
    "유산소 운동 후 땀 흘린 피부 트러블 막는 클렌저 팁",
    "운동 루틴이 무너졌을 때 멘탈 회복하고 헬스장 복귀하는 룰",
    "등 운동 자극 제대로 느끼는 바른 자세와 호흡법",
    "덤벨 들기 전 무조건 해야 하는 손목 보호 및 강화 루틴",
    "운동할 때 입기 좋은 가성비 스포츠 웨어 브랜드",
    "레이저 제모 통증 50% 줄이는 실전 꿀팁 총정리",
    "피부과 레이저 기기별 차이 완벽 비교 (젠틀맥스 프로 vs 아포지)",
    "남자 수염 제모: 클래리티2와 젠틀맥스 프로 중 나에게 맞는 것은?",
    "레이저 제모 전 마취크림 방치 시간이 통증에 미치는 영향",
    "제모 시술 당일 면도할 때 절대 하지 말아야 할 행동",
    "레이저 제모 후 모낭염 예방을 위한 필수 스킨케어 룰",
    "남자 얼굴 전체 제모 평균 비용 및 합리적인 회차 선택",
    "시술 후 붉어진 피부를 진정시키는 쿨링 홈케어 방법",
    "피부과 가기 전 꼭 알아야 할 수염 제모 부작용과 대처법",
    "남자 턱수염 레이저 제모 주기와 효과 극대화 타이밍",
    "피부과 상담 시 덤터기 안 쓰는 호갱 탈출 질문 리스트",
    "여름철 레이저 제모 후 선크림을 두 배로 발라야 하는 이유",
    "면도독에서 탈출하는 유일한 방법: 레이저 제모 솔직 후기",
    "제모 시술 후 사우나, 음주, 운동은 언제부터 가능할까?",
    "피부과 명장들이 말하는 효과 좋은 레이저 제모의 조건",
    "핏이 다른 남자 기본 무지 티셔츠 브랜드 추천 TOP 5",
    "세탁해도 목 안 늘어나는 탄탄한 반팔 티셔츠 고르는 법",
    "체형별(어좁이, 마른 체형) 단점을 보완하는 티셔츠 핏",
    "남성 비즈니스 캐주얼의 기본: 슬랙스에 어울리는 티셔츠 매치",
    "흰색 티셔츠 비침 방지를 위한 이너 및 원단 두께 가이드",
    "트렌디한 남성 와이드 팬츠 코디 및 신발 매칭 룰",
    "체형이 좋아 보이는 세미 오버핏 셔츠 브랜드 추천",
    "남성 미니멀룩 완성을 위한 필수 에센셜 아이템 7가지",
    "계절별 남성 기본 아우터(자켓, 맥코트) 활용 백서",
    "다리가 길어 보이는 남성 바지 기장 및 수선 팁",
    "남성 피부 고민별(여드름, 칙칙함) 맞춤 비타민 추천",
    "만성 피로에 시달리는 2030 남성 필수 영양제 가이드",
    "지성 피부 남성의 피지 조절을 위한 영양제 조합 (아연, 비타민A)",
    "운동하는 남성을 위한 간 보호제(밀크씨슬)와 비타민B 복합제",
    "눈 피로와 다크서클 개선을 위한 루테인 및 비타민C 섭취법",
    "남성 탈모 예방을 위한 비오틴 및 약용효모 영양제 진실",
    "면역력과 활력을 동시에 챙기는 남성 종합비타민 고르는 법",
    "종합 비타민과 오메가3, 같이 먹어도 괜찮을까? 섭취 타이밍",
    "잦은 회식과 술자리가 잦은 남성을 위한 혈행 개선 영양제",
    "피부 장벽 강화를 위한 먹는 세라마이드와 콜라겐의 효과",
]

# ── MBTI 페르소나 정의 ────────────────────────────────────────────
MBTI_PERSONAS = {
    "ISTJ": {"characteristic": "철저한 계획파, 가성비와 효율 중심", "tone": "이성적이고 수치화된 가이드"},
    "ISFJ": {"characteristic": "안정 추구, 꼼꼼하고 배려 깊음", "tone": "친절하고 실용적인 루틴 제안"},
    "INFJ": {"characteristic": "자기성찰형, 내면 관리에 진심", "tone": "철학적이고 감성적인 어조"},
    "INTJ": {"characteristic": "효율 극대화, 시스템 구축형", "tone": "전략적이고 논리적인 분석"},
    "ISTP": {"characteristic": "도구와 기술에 능숙, 즉흥적 실용주의", "tone": "간결하고 기술적인 설명"},
    "ISFP": {"characteristic": "예술가 기질, 개성과 감성 중시", "tone": "감각적이고 개성 있는 추천"},
    "INFP": {"characteristic": "이상주의자, 자신만의 루틴 추구", "tone": "감성적이고 공감 위주"},
    "INTP": {"characteristic": "분석가, 아이디어와 미니멀 추구", "tone": "논리적이고 호기심 자극"},
    "ESTP": {"characteristic": "행동파, 즉각적인 결과 원함", "tone": "빠르고 자극적인 팁 전달"},
    "ESFP": {"characteristic": "에너지 넘치는 파티형, 트렌드 민감", "tone": "신나고 트렌디한 어조"},
    "ENFP": {"characteristic": "트렌디함 추구, 새로운 시도에 개방적", "tone": "위트 있고 트렌디한 추천 방식"},
    "ENTP": {"characteristic": "트렌드세터, 새 디바이스와 방법 탐구", "tone": "도발적이고 신선한 시각"},
    "ESTJ": {"characteristic": "현실주의자, 체계적 관리 선호", "tone": "명확하고 단호한 가이드"},
    "ESFJ": {"characteristic": "사교적, 타인 시선에 민감", "tone": "공감형 + 호감도 중심 팁"},
    "ENFJ": {"characteristic": "열정적 리더, 호감도 극대화 추구", "tone": "동기부여형 스타일링 어조"},
    "ENTJ": {"characteristic": "성공 지향, 프로페셔널 이미지 관리", "tone": "자신감 있고 전략적인 어조"},
}

HIGHLIGHT_BLUE = (59, 130, 246)   # #3B82F6
LETTER_SPACING = -1


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
            "hl":       ImageFont.truetype(B,  34),
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
    cx = x
    for ch in text:
        if ch == '\n':
            continue  # 줄바꿈 문자는 단일행 렌더러에서 스킵
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


# ── 1. Claude 콘텐츠 생성 (새 마스터 프롬프트 적용) ──────────────
def generate_content() -> dict:
    topic = random.choice(CONTENT_POOL)
    mbti  = random.choice(list(MBTI_PERSONAS.keys()))
    persona = MBTI_PERSONAS[mbti]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""[System Role & Context]
너는 팔로워 50만 명을 보유한 남성 그루밍·라이프스타일 매거진의 총괄 에디터이자, 타깃 심리를 정확히 꿰뚫는 SNS 마케터다. 아래 제공하는 데이터와 규칙을 완벽히 숙지하고 가독성이 극대화된 카드뉴스(5장 분량) 대본을 생성해라.

[Input Data]
오늘의 킬러 주제: {topic}
오늘의 타깃 페르소나 (MBTI): {mbti} — {persona['characteristic']}
톤앤매너 지침: {persona['tone']}

[제약 조건 및 출력 규칙]
1. 톤앤매너: 2030 남성 타깃, 트렌디하고 세련된 매거진 어조 (~해라, ~하자 같은 단호하면서도 힙한 문체)
2. MBTI 반영: {mbti}의 성격적 특성을 콘텐츠 내용이나 서두에 반드시 녹여내라.
3. 레이아웃 한계: 카드 한 장당 타이틀 1줄, 본문 텍스트는 이모지 포함 최대 3줄(명사형/단답형)로 짧게 끊어라.
4. slide_1의 body는 반드시 줄바꿈 없이 한 줄로만 작성해라.
5. 아래 JSON 포맷만 반환해라. 다른 사설 없이 JSON만:

{{
  "slide_1": {{"title": "1장 제목 (후킹성 강한 타이틀, 20자 이내)", "body": "짧은 인트로 또는 MBTI 언급 문구 (줄바꿈 없이 한 줄)"}},
  "slide_2": {{"title": "2장 소제목", "body": "📌 핵심 내용 1\\n💡 핵심 내용 2\\n✅ 핵심 내용 3"}},
  "slide_3": {{"title": "3장 소제목", "body": "📌 핵심 내용 1\\n💡 핵심 내용 2\\n✅ 핵심 내용 3"}},
  "slide_4": {{"title": "4장 소제목", "body": "📌 핵심 내용 1\\n💡 핵심 내용 2\\n✅ 핵심 내용 3"}},
  "slide_5": {{"title": "저장하고 오늘 밤부터 시작.", "body": "🔥 이 정보가 도움 되었다면?\\n❤️ 좋아요 | 📝 댓글 | 📂 저장하기\\n더 많은 그루밍 팁은 @naestyle_official 에서!"}},
  "instagram_caption": "인스타그램 업로드용 캡션. 이모지 포함 3문장 + 빈줄 + 해시태그 8개",
  "pexels_keyword": "영문 3단어 이내 배경 이미지 검색어",
  "unsplash_keyword": "영문 3단어 이내 배경 이미지 검색어"
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text
    parsed = json.loads(text[text.find('{'):text.rfind('}')+1])
    parsed["topic_text"] = topic
    parsed["mbti"] = mbti
    return parsed


# ── 2. 카드 1: Shellness 썸네일 ───────────────────────────────────
def card1_shellness(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    pexels_kw  = content.get("pexels_keyword", "men grooming minimal clean")
    unsplash_kw = content.get("unsplash_keyword", "men skincare minimal")

    bg = fetch_image(pexels_kw, unsplash_kw)
    canvas = crop_sq(bg) if bg else Image.new("RGBA", (W, H), (26,24,22,255))
    canvas = canvas.convert("RGBA")

    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(ov)
    for i in range(220):
        d.rectangle([(0,i),(W,i+1)], fill=(0,0,0,int(90*(1-i/220))))
    for i in range(520):
        d.rectangle([(0,H-520+i),(W,H-520+i+1)], fill=(0,0,0,int(215*(i/520)**1.1)))
    canvas = Image.alpha_composite(canvas, ov)
    draw = ImageDraw.Draw(canvas)

    # MBTI 라벨
    mbti_label = f"For {content.get('mbti', '')}"
    draw_tight(draw, 54, H-460, mbti_label, Fnt["sub"], (255,255,255,120), spacing=3)

    # 메인 카피 (slide_1 title)
    title = content.get("slide_1", {}).get("title", "")
    lines = title.split()
    # 10자 이상이면 절반씩 나눠서 2줄로
    if len(title) > 12:
        mid = len(lines) // 2
        lines = [" ".join(lines[:mid]), " ".join(lines[mid:])]
    else:
        lines = [title]

    y = H - 380
    for line in lines:
        draw_tight(draw, 50, y, line, Fnt["title_lg"], (255,255,255), spacing=-2)
        y += 94

    # slide_1 body (인트로) — 첫 줄만 사용
    intro = content.get("slide_1", {}).get("body", "").split("\n")[0]
    if intro:
        draw_tight(draw, 50, y + 10, intro, Fnt["body_sm"], (255,255,255,180), spacing=-1)

    out = io.BytesIO()
    canvas.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out


# ── 3. 카드 2·3: 본문 슬라이드 (블루 하이라이트) ─────────────────
def card_body(content: dict, idx: int) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    pexels_kw  = content.get("pexels_keyword", "men lifestyle minimal")
    unsplash_kw = content.get("unsplash_keyword", "men minimal aesthetic")

    slide_key = f"slide_{idx + 2}"  # idx=0 → slide_2, idx=1 → slide_3
    slide = content.get(slide_key, {"title": "", "body": ""})

    BG = (244, 242, 239)
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    FRAME_H = 500

    # 상단 이미지
    main_img = fetch_image(pexels_kw, unsplash_kw)
    if main_img:
        frame_bg = crop_rect(main_img.convert("RGB"), W, FRAME_H)
        canvas.paste(frame_bg, (0, 0))
    else:
        canvas.paste(Image.new("RGB", (W, FRAME_H), (200,196,190)), (0,0))

    draw = ImageDraw.Draw(canvas)

    # 자막바
    draw.rectangle([(0, FRAME_H-56), (W, FRAME_H)], fill=(0,0,0,int(255*0.78)))
    caption_text = f"{content.get('mbti','')} | {content.get('topic_text','')[:20]}"
    draw_tight(draw, 50, FRAME_H-42, caption_text, Fnt["caption"], (255,255,255), spacing=-1)

    # 채널 라벨
    draw.rectangle([(0,0),(320,52)], fill=(15,14,12))
    draw_tight(draw, 18, 14, "내스타일 | GROOMING", Fnt["label"], (255,255,255), spacing=0)

    # 슬라이드 제목
    TEXT_Y = FRAME_H + 40
    slide_title = slide.get("title", "")
    draw_tight(draw, 50, TEXT_Y, slide_title, Fnt["product"], (15,14,12), spacing=-2)

    # 구분선
    draw.rectangle([(50, TEXT_Y+58),(W-50, TEXT_Y+59)], fill=(204,200,196))

    # 본문 라인들 (\n 으로 구분)
    body_raw = slide.get("body", "")
    body_lines = body_raw.split("\n")
    by = TEXT_Y + 80
    hl_done = False

    for i, line in enumerate(body_lines):
        if not line.strip():
            by += 16
            continue
        # 첫 번째 라인을 블루 하이라이트로 강조
        if i == 0 and not hl_done:
            hl_w = sum(draw.textlength(c, font=Fnt["hl"])-1 for c in line) + 24
            hl_w = min(hl_w, W - 100)
            draw.rectangle([(48, by-4),(48+hl_w, by+44)], fill=HIGHLIGHT_BLUE)
            draw_tight(draw, 56, by, line, Fnt["hl"], (255,255,255), spacing=-1)
            by += 60
            hl_done = True
        else:
            wrapped = wrap(draw, line, Fnt["body_sm"], W-100, spacing=-1)
            for ln in wrapped:
                draw_tight(draw, 50, by, ln, Fnt["body_sm"], (44,42,38), spacing=-1)
                by += 38
            by += 8
        if by > H - 70:
            break

    # 스와이프 안내
    draw_tight(draw, 50, H-48, "← 스와이프해서 더 보기",
               Fnt["caption"], (154,150,144), spacing=-1)

    out = io.BytesIO()
    canvas.save(out, "PNG")
    out.seek(0)
    return out


# ── 4. 카드 4: 클로징 (slide_5 활용) ────────────────────────────
def card4_closing(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    pexels_kw  = content.get("pexels_keyword", "men portrait dark dramatic")
    unsplash_kw = content.get("unsplash_keyword", "men minimal dark")

    bg = fetch_image(pexels_kw, unsplash_kw)
    canvas = crop_sq(bg) if bg else Image.new("RGBA", (W,H),(22,20,26,255))
    canvas = canvas.convert("RGBA")

    ov = Image.new("RGBA",(W,H),(0,0,0,160))
    canvas = Image.alpha_composite(canvas, ov)
    draw = ImageDraw.Draw(canvas)

    slide5 = content.get("slide_5", {})
    closing_title = slide5.get("title", "저장하고 오늘 밤부터 시작.")
    closing_body  = slide5.get("body", "")

    # 메인 카피
    lines = closing_title.split(" ")
    mid = max(1, len(lines) // 2)
    line_groups = [" ".join(lines[:mid]), " ".join(lines[mid:])] if len(lines) > 2 else [closing_title]

    y = H//2 - 160
    for ln in line_groups:
        lw = sum(draw.textlength(c, font=Fnt["title_lg"])-2 for c in ln)
        draw_tight(draw, (W-lw)//2, y, ln, Fnt["title_lg"], (255,255,255), spacing=-2)
        y += 96

    # 블루 하이라이트 (closing body 첫 줄)
    body_lines = closing_body.split("\n")
    if body_lines:
        sub = body_lines[0]
        sw = sum(draw.textlength(c, font=Fnt["hl"])-1 for c in sub) + 28
        sx = (W-sw)//2
        draw.rectangle([(sx, y+14),(sx+sw, y+60)], fill=HIGHLIGHT_BLUE)
        draw_tight(draw, sx+14, y+14, sub, Fnt["hl"], (255,255,255), spacing=-1)

    # 서브 (closing body 두 번째 줄 이하)
    if len(body_lines) > 1:
        subsub = " | ".join(body_lines[1:])
        ssw = sum(draw.textlength(c, font=Fnt["body_sm"])-1 for c in subsub)
        draw_tight(draw, (W-ssw)//2, y+80, subsub, Fnt["body_sm"], (255,255,255,130), spacing=-1)

    # 브랜드
    bw = sum(draw.textlength(c, font=Fnt["brand"])-1 for c in "내스타일")
    draw_tight(draw, (W-bw)//2, H-56, "내스타일", Fnt["brand"], (255,255,255,90), spacing=2)

    out = io.BytesIO()
    canvas.convert("RGB").save(out,"PNG")
    out.seek(0)
    return out


# ── 5. viral 썸네일 (짝수일) ────────────────────────────────────
def card1_viral(content: dict) -> io.BytesIO:
    W, H = 1080, 1080
    Fnt = F()
    pexels_kw  = content.get("pexels_keyword", "men gym dark dramatic")
    unsplash_kw = content.get("unsplash_keyword", "men dark aesthetic")

    bg = fetch_image(pexels_kw, unsplash_kw)
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
    draw_tight(draw, 60, 52, f"{content.get('mbti','')} 필독", Fnt["sub"], (255,255,255), spacing=-1)

    # slide_1 title 후킹 문구
    title = content.get("slide_1", {}).get("title", "")
    words = title.split()
    mid = max(1, len(words) // 2)
    hook1 = " ".join(words[:mid])
    hook2 = " ".join(words[mid:])

    draw_tight(draw, 50, H-248, hook1, Fnt["title_lg"], (255,255,255), spacing=-2)
    draw_tight(draw, 50, H-140, hook2 if hook2 else content.get("slide_1", {}).get("body", "").split("\n")[0][:20],
               Fnt["title_lg"], (255,230,40), spacing=-2)

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
    }}){{...on PostActionSuccess{{post{{id}}}}...on MutationError{{message}}}}}}}'''
    r = requests.post(
        "https://api.buffer.com",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {BUFFER_API_KEY}"},
        json={"query":query},
    )
    return "post" in (r.json().get("data",{}).get("createPost",{}) or {})


# ── 메인 ─────────────────────────────────────────────────────────
def main():
    print(f"=== {datetime.now().strftime('%m/%d')} | 스타일: {TODAY_STYLE} ===")

    content = generate_content()
    print(f"  주제: {content['topic_text']}")
    print(f"  MBTI: {content['mbti']}")

    if TODAY_STYLE == "shellness":
        print("[shellness 스타일] 카드 4장 생성...")
        c1 = card1_shellness(content)
        c2 = card_body(content, 0)
        c3 = card_body(content, 1)
        c4 = card4_closing(content)
    else:
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

    ok = post(content["instagram_caption"], urls)
    print("=== 완료! ===" if ok else "=== 발행 실패 ===")


if __name__ == "__main__":
    main()
