import anthropic
import requests
import json
import os
import random
import base64
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
import io

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BUFFER_API_KEY = os.environ["BUFFER_API_KEY"].strip()
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

BUFFER_API = "https://api.buffer.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "chohihihi/instagram-auto-post-hehe")
BRANCH = "main"
CHANNEL_ID = "6a2a25e38f1d11f9b2742181"

TOPICS = [
    {"type": "레이저제모", "detail": "남성 레이저 제모 (수염, 등, 팔다리, 겨드랑이, 브라질리언), 효과, 횟수, 주의사항"},
    {"type": "피부시술", "detail": "남성 피부과 시술 (리프팅, 보톡스, 흉터, 모공, 레이저, 색소)"},
    {"type": "운동", "detail": "남성 헬스 루틴, 벌크업, 다이어트, 홈트, 자세 교정"},
    {"type": "피부관리", "detail": "남성 기초케어, 선크림, 보습, 각질, 모공 관리"},
    {"type": "그루밍", "detail": "남성 헤어스타일, 수염 관리, 향수, 패션 코디, 자기관리 루틴"},
    {"type": "다이어트", "detail": "남성 식단 관리, 단백질 섭취, 체중 감량, 간헐적 단식"},
]

UNSPLASH_KEYWORDS = {
    "레이저제모": "laser clinic skin treatment",
    "피부시술": "dermatology clinic skincare",
    "운동": "gym fitness workout",
    "피부관리": "skincare beauty routine",
    "그루밍": "men fashion style",
    "다이어트": "healthy food diet fitness",
}


def generate_content():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    topic = random.choice(TOPICS)

    prompt = f"""인스타그램 카드뉴스 콘텐츠를 만들어주세요. 타겟: 자기관리에 관심 있는 20-35세 한국 남성

주제: {topic['type']} - {topic['detail']}

--- 후킹 문구 스타일 (바비톡·강남언니 썸네일 참고, 남성 버전) ---
절대 규칙:
- 첫줄은 "상황/공감/의심" → 둘째줄은 "반전/폭로/해답"의 구조
- 독자가 "어? 나 얘기하는 거 아냐?"라고 느끼게
- 숫자·괄호·감탄사 적극 활용
남성 후킹 예시:
- "등 면도 매일 해도 / 3일이면 다시 올라온다?" → "레이저 제모 현실 공개"
- "헬스 6개월 했는데 / 왜 아직도 뱃살이야?" → "운동 전 이것부터 고쳐"
- "세안 열심히 하는데 / 왜 모공이 더 커지지?" → "피부과가 말 안 해주는 것"
- "피부과 갔더니 / 보톡스 추천받은 20대 남자" → "진짜로 맞아도 될까?"

--- 캡션 스타일 (바비톡 + 강남언니 + 뉴닉 참고) ---
- 이모지를 문장 앞에 붙이는 스타일 (💉🔥💧✨🧬💪🧴)
- 어렵지 않게 정보를 풀어쓰는 뉴닉체 (예: "~거든요", "~이에요", "~한다는 사실!")
- 마지막에 행동 유도 ("저장해두세요 🔖", "알고 계셨나요?")
- 바비톡 예시 캡션:
  "💉 써마지·울쎄라 같은 고주파 리프팅은 피부 속 깊은 곳에 열에너지를 전달해요
  🔥 이 열에너지가 리프팅 효과를 주는 방식인데요, 미리 알면 훨씬 똑똑하게 받을 수 있어요
  💧 시술 전 충분한 수분 섭취와 보습 관리, 잊지 마세요! 저장해두세요 🔖"

--- 정보카드 포인트 스타일 ---
- 소제목은 임팩트 있게 (예: "하루 3세트면 충분", "물 마시면 효과 2배")
- 설명은 구체적 수치·연구 기반 (예: "임상 87% 개선", "8주 후 효과 확인")

다음 JSON 형식으로만 응답 (다른 텍스트 없이):
{{
    "hook_line1": "메인 후킹 문구 첫줄 (15자 이내, 공감·상황 설정)",
    "hook_line2": "메인 후킹 문구 둘째줄 (15자 이내, 반전·해답 암시)",
    "info_title": "정보 카드 제목 (20자 이내, 예: '몰랐으면 후회할 레이저 제모 3가지')",
    "points": [
        {{"title": "소제목 (12자 이내, 임팩트 있게)", "desc": "연구/논문 기반 핵심 사실 (30자 이내, 수치 포함)"}},
        {{"title": "소제목 (12자 이내, 임팩트 있게)", "desc": "연구/논문 기반 핵심 사실 (30자 이내, 수치 포함)"}},
        {{"title": "소제목 (12자 이내, 임팩트 있게)", "desc": "연구/논문 기반 핵심 사실 (30자 이내, 수치 포함)"}}
    ],
    "source": "출처 기관명 (예: 대한피부과학회, 보건복지부, Journal of Dermatology)",
    "caption": "바비톡+강남언니+뉴닉 스타일 캡션. 이모지 포함 정보성 본문 3문장 + 빈줄 + 해시태그 8개"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    start = text.find('{')
    end = text.rfind('}') + 1
    parsed = json.loads(text[start:end])
    parsed["topic"] = topic["type"]
    return parsed


def fetch_unsplash_image(topic):
    keyword = UNSPLASH_KEYWORDS.get(topic, "lifestyle wellness")
    try:
        r = requests.get(
            "https://api.unsplash.com/photos/random",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={"query": keyword, "orientation": "squarish"},
            timeout=10
        )
        print(f"Unsplash 응답: {r.status_code} (키워드: {keyword})")
        if r.status_code == 200:
            url = r.json()["urls"]["regular"]
            print(f"Unsplash 이미지: {url}")
            return url
        else:
            print(f"Unsplash 실패 내용: {r.text[:200]}")
    except Exception as e:
        print(f"Unsplash fetch 실패: {e}")
    return None


def download_image(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def center_crop(img, size=1080):
    w, h = img.size
    scale = max(size / w, size / h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    w2, h2 = img.size
    left = (w2 - size) // 2
    top = (h2 - size) // 2
    return img.crop((left, top, left + size, top + size))


def load_fonts():
    try:
        bold = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
        regular = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        return {
            "hook":        ImageFont.truetype(bold, 76),
            "brand":       ImageFont.truetype(bold, 34),
            "info_title":  ImageFont.truetype(bold, 54),
            "point_num":   ImageFont.truetype(bold, 40),
            "point_title": ImageFont.truetype(bold, 38),
            "point_desc":  ImageFont.truetype(regular, 30),
            "source":      ImageFont.truetype(regular, 24),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ["hook","brand","info_title","point_num","point_title","point_desc","source"]}


def create_main_image(content, bg_url=None):
    """슬라이드 1: Unsplash 사진 + 어두운 오버레이 + 흰색 한글 후킹 문구"""
    W, H = 1080, 1080
    fonts = load_fonts()

    # 배경
    if bg_url:
        try:
            bg = center_crop(download_image(bg_url))
            canvas = bg.convert("RGBA")
        except Exception as e:
            print(f"배경 로드 실패: {e}")
            canvas = Image.new("RGBA", (W, H), (30, 30, 40, 255))
    else:
        canvas = Image.new("RGBA", (W, H), (30, 30, 40, 255))

    # 전체 어둡게 오버레이 (사진이 잘 보이되 텍스트가 읽히도록)
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, dark)

    # 하단 강한 그라데이션 (텍스트 가독성)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(550):
        a = int(200 * (i / 550) ** 1.3)
        y = H - 550 + i
        gd.rectangle([(0, y), (W, y+1)], fill=(0, 0, 0, a))
    canvas = Image.alpha_composite(canvas, grad)

    draw = ImageDraw.Draw(canvas)

    # 브랜드명 (좌상단) — 반투명 필 배경
    brand_draw = ImageDraw.Draw(canvas)
    brand_draw.text((52, 52), "내스타일", font=fonts["brand"], fill=(255, 255, 255, 220))

    # 후킹 문구 2줄
    line1 = content.get("hook_line1", "")
    line2 = content.get("hook_line2", "")
    ty = H - 290

    # 텍스트 그림자
    for dx, dy in [(5, 5), (-5, 5), (5, -5), (-5, -5)]:
        draw.text((50+dx, ty+dy),     line1, font=fonts["hook"], fill=(0, 0, 0, 140))
        draw.text((50+dx, ty+100+dy), line2, font=fonts["hook"], fill=(0, 0, 0, 140))

    # 흰색 텍스트
    draw.text((50, ty),     line1, font=fonts["hook"], fill=(255, 255, 255))
    draw.text((50, ty+100), line2, font=fonts["hook"], fill=(255, 255, 255))

    img_bytes = io.BytesIO()
    canvas.convert("RGB").save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius*2, y0 + radius*2], fill=fill)
    draw.ellipse([x1 - radius*2, y0, x1, y0 + radius*2], fill=fill)
    draw.ellipse([x0, y1 - radius*2, x0 + radius*2, y1], fill=fill)
    draw.ellipse([x1 - radius*2, y1 - radius*2, x1, y1], fill=fill)


def create_info_image(content):
    """슬라이드 2: 바비톡/강남언니 스타일 정보 카드"""
    W, H = 1080, 1080
    fonts = load_fonts()

    PURPLE_DARK  = (62,  42, 100)   # 진한 퍼플
    PURPLE_MID   = (108, 78, 162)   # 중간 퍼플
    PURPLE_LIGHT = (235, 228, 255)  # 연한 라벤더
    WHITE        = (255, 255, 255)
    TEXT_DARK    = (30,  22,  55)
    TEXT_GRAY    = (110, 100, 135)
    CARD_BG      = (252, 250, 255)

    # 배경: 연한 라벤더 그라데이션
    canvas = Image.new("RGB", (W, H), (245, 240, 255))
    draw = ImageDraw.Draw(canvas)

    # 배경 장식 원 (우상단)
    draw.ellipse([(780, -120), (1180, 280)], fill=(220, 210, 248))
    # 배경 장식 원 (좌하단)
    draw.ellipse([(-100, 800), (300, 1200)], fill=(215, 205, 245))

    # 상단 헤더 바
    draw.rectangle([(0, 0), (W, 190)], fill=PURPLE_DARK)

    # 헤더 장식 — 반투명 원
    for cx, cy, r, a in [(900, 0, 200, 25), (200, 190, 130, 20)]:
        circ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(circ)
        cd.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=(255, 255, 255, a))
        canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), circ).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(canvas)

    # 제목
    title = content.get("info_title", "핵심 정보")
    draw.text((W//2, 95), title, font=fonts["info_title"], fill=WHITE, anchor="mm")

    # 포인트 3개 카드
    card_top = 220
    card_h   = 220
    gap      = 24

    for i, point in enumerate(content.get("points", [])[:3]):
        cy = card_top + i * (card_h + gap)
        # 카드 배경 (둥근 사각형)
        draw_rounded_rect(draw, (55, cy, W-55, cy + card_h), radius=22, fill=CARD_BG)

        # 왼쪽 색 강조 바
        draw.rectangle([(55, cy), (75, cy + card_h)], fill=PURPLE_MID)
        draw_rounded_rect(draw, (55, cy, 75, cy + card_h), radius=10, fill=PURPLE_MID)

        # 번호 원
        ex, ey = 120, cy + card_h//2
        draw.ellipse([(ex-38, ey-38), (ex+38, ey+38)], fill=PURPLE_MID)
        num_str = str(i + 1)
        draw.text((ex, ey), num_str, font=fonts["point_num"], fill=WHITE, anchor="mm")

        # 소제목
        draw.text((180, cy + 55), point.get("title", ""), font=fonts["point_title"], fill=TEXT_DARK)

        # 설명 (자동 줄바꿈)
        desc = point.get("desc", "")
        draw.text((180, cy + 108), desc, font=fonts["point_desc"], fill=TEXT_GRAY)

    # 출처 칩
    source_text = f"출처: {content.get('source', '')}"
    chip_y = card_top + 3 * (card_h + gap) + 28
    draw_rounded_rect(draw, (55, chip_y, W-55, chip_y + 60), radius=14, fill=PURPLE_LIGHT)
    draw.text((W//2, chip_y + 30), source_text, font=fonts["source"], fill=PURPLE_DARK, anchor="mm")

    img_bytes = io.BytesIO()
    canvas.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def upload_image_to_imgur(img_bytes):
    r = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": "Client-ID 546c25a59c58ad7"},
        data={"image": base64.b64encode(img_bytes.getvalue()).decode(), "type": "base64"},
        timeout=30,
    )
    print(f"Imgur 응답: {r.status_code}")
    if r.status_code == 200:
        url = r.json()["data"]["link"]
        print(f"Imgur URL: {url}")
        return url
    print(f"Imgur 실패: {r.text[:200]}")
    return None


def post_to_buffer(caption, image_urls):
    safe_caption = caption.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    assets = ", ".join([f'{{ image: {{ url: "{url}" }} }}' for url in image_urls])

    query = f'''
    mutation {{
      createPost(input: {{
        text: "{safe_caption}"
        channelId: "{CHANNEL_ID}"
        schedulingType: automatic
        mode: addToQueue
        metadata: {{ instagram: {{ type: post, shouldShareToFeed: true }} }}
        assets: [{assets}]
      }}) {{
        ... on PostActionSuccess {{ post {{ id }} }}
        ... on MutationError {{ message }}
      }}
    }}'''

    r = requests.post(
        "https://api.buffer.com",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {BUFFER_API_KEY}"},
        json={"query": query}
    )
    print(f"Buffer 응답 코드: {r.status_code}")
    print(f"Buffer 응답: {r.text[:500]}")
    if not r.ok:
        return False
    result = r.json()
    create_result = result.get("data", {}).get("createPost", {}) or {}
    return "post" in create_result


def main():
    print("콘텐츠 생성 중...")
    content = generate_content()
    print(f"생성된 문구: {content['hook_line1']} / {content['hook_line2']}")

    print("Unsplash 이미지 가져오는 중...")
    bg_url = fetch_unsplash_image(content.get("topic", "자기관리"))

    print("이미지 생성 중...")
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    main_img = create_main_image(content, bg_url)
    info_img = create_info_image(content)
    print("이미지 생성 완료")

    print("이미지 업로드 중...")
    url1 = upload_image_to_imgur(main_img)
    url2 = upload_image_to_imgur(info_img)

    if not url1 or not url2:
        print("이미지 업로드 실패")
        return

    print("Buffer에 발행 중...")
    success = post_to_buffer(content["caption"], [url1, url2])
    if success:
        print("포스팅 완료! (카드뉴스 2장)")
    else:
        print("포스팅 실패")


if __name__ == "__main__":
    main()
