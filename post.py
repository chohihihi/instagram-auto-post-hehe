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

BUFFER_API = "https://api.buffer.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "chohihihi/instagram-auto-post-hehe")
BRANCH = "main"

BUFFER_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BUFFER_API_KEY}",
}

TOPICS = [
    {"type": "피부시술", "detail": "리프팅, 보톡스, 필러, 써마지, 실리프팅, 레이저 등 피부과 시술"},
    {"type": "운동", "detail": "헬스, 필라테스, 요가, 홈트, 다이어트 운동 루틴"},
    {"type": "데이트", "detail": "데이트 코스, 연애 꿀팁, 커플 일상, 소개팅"},
    {"type": "피부관리", "detail": "기초케어, 선크림, 보습, 각질, 모공, 화이트닝"},
    {"type": "자기관리", "detail": "2030 자기관리 루틴, 멘탈관리, 라이프스타일, 식단"},
]


def generate_content():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    topic = random.choice(TOPICS)
    use_character = random.random() < 0.2  # 20% 확률로 캐릭터 변주

    prompt = f"""인스타그램 계정 babitalk.official 스타일로 2030 자기관리에 관심 있는 여성을 타겟으로 한 콘텐츠를 만들어주세요.

주제: {topic['type']} - {topic['detail']}
스타일: {'캐릭터 밈 (캐릭터 표정/상황으로 공감 유발)' if use_character else '강아지/동물 밈 짤 스타일 (귀여운 짤 + 공감 후킹 문구)'}

바비톡 썸네일 문구 스타일 예시:
- "써마지 받기 전, 왜 물부터 마셔야 할까?"
- "실리프팅, 다 녹으면 전보다 더 처질까?"
- "필터랑 실물 갭 크다는 말 당신의 반응은?"
- "유형별 시술을 대하는 속마음, 번역해 봤더니..."

규칙:
- hook_line1/2는 두 줄로 쪼개서 자연스럽게 이어지는 하나의 문장/질문
- 첫 줄은 상황이나 키워드 제시, 둘째 줄은 질문이나 반전으로 끝내기
- 캡션은 바비톡처럼 이모지를 문장 앞에 붙이는 스타일, 정보성 2-3문장 후 해시태그

다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
    "hook_line1": "후킹 문구 첫째줄 (16자 이내)",
    "hook_line2": "후킹 문구 둘째줄 (16자 이내)",
    "caption": "인스타그램 캡션. 이모지 활용한 바비톡 스타일 본문 2-3문장 + 빈줄 + 해시태그 6-8개"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    start = text.find('{')
    end = text.rfind('}') + 1
    parsed = json.loads(text[start:end])
    parsed["use_character"] = use_character  # 코드에서 직접 결정
    return parsed


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


MEME_SUBREDDITS = [
    "aww", "rarepuppers", "AnimalsBeingDerps",
    "WhatsWrongWithYourDog", "dogmemes", "catmemes",
    "animalsbeingbros", "AnimalsBeingGeniuses",
]

def fetch_reddit_meme_image():
    """Reddit 서브레딧에서 랜덤 밈 이미지 URL 반환 (API 키 불필요)"""
    subreddit = random.choice(MEME_SUBREDDITS)
    headers = {"User-Agent": "instagram-autopost/1.0"}
    try:
        r = requests.get(
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50",
            headers=headers, timeout=10
        )
        if r.status_code != 200:
            return None
        posts = r.json()["data"]["children"]
        # 이미지 포스트만 필터 (jpg/png, 외부링크 제외)
        image_posts = [
            p["data"]["url"] for p in posts
            if p["data"].get("url", "").lower().endswith((".jpg", ".jpeg", ".png"))
            and not p["data"].get("is_self", True)
            and not p["data"].get("over_18", False)
        ]
        if image_posts:
            chosen = random.choice(image_posts)
            print(f"Reddit 밈 사용: r/{subreddit} — {chosen}")
            return chosen
    except Exception as e:
        print(f"Reddit fetch 실패 ({subreddit}): {e}")
    return None


def download_image(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def center_crop(img, size=1080):
    """정사각형 center crop"""
    w, h = img.size
    scale = max(size / w, size / h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    w2, h2 = img.size
    left = (w2 - size) // 2
    top = (h2 - size) // 2
    return img.crop((left, top, left + size, top + size))


def create_image(content):
    width, height = 1080, 1080
    use_character = content.get("use_character", False)

    # --- 배경 이미지 준비 ---
    bg_img = None
    if use_character:
        # character/ 폴더가 있으면 거기서, 없으면 dog.ceo 폴백
        api_url = f"https://api.github.com/repos/{REPO}/contents/character"
        r = requests.get(api_url, headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        })
        files = [f for f in (r.json() if r.status_code == 200 else [])
                 if f["name"].lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        if files:
            chosen = random.choice(files)
            raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/character/{chosen['name']}"
            try:
                bg_img = center_crop(download_image(raw_url))
            except Exception as e:
                print(f"캐릭터 이미지 로드 실패: {e}")

    if bg_img is None:
        # Reddit 밈 이미지 자동 fetch
        meme_url = fetch_reddit_meme_image()
        if meme_url:
            try:
                bg_img = center_crop(download_image(meme_url))
            except Exception as e:
                print(f"Reddit 이미지 로드 실패: {e}")

    # 캔버스 (이미지 없을 때 연보라 기본 배경)
    if bg_img:
        canvas = bg_img.convert("RGBA")
    else:
        canvas = Image.new("RGBA", (width, height), (230, 220, 245, 255))

    draw = ImageDraw.Draw(canvas)

    # --- 하단 그라데이션 오버레이 ---
    gradient_h = 460
    gradient_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient_layer)
    for i in range(gradient_h):
        alpha = int(200 * (i / gradient_h) ** 1.6)
        y = height - gradient_h + i
        grad_draw.rectangle([(0, y), (width, y + 1)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, gradient_layer)
    draw = ImageDraw.Draw(canvas)

    # --- 폰트 ---
    try:
        bold = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
        regular = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        font_hook = ImageFont.truetype(bold, 78)
        font_brand = ImageFont.truetype(bold, 34)
    except Exception:
        font_hook = font_brand = ImageFont.load_default()

    # --- 브랜드명 (좌상단) ---
    draw.text((52, 52), "내스타일", font=font_brand, fill=(255, 255, 255, 210))

    # --- 후킹 문구 2줄 (하단) ---
    line1 = content.get("hook_line1", "")
    line2 = content.get("hook_line2", "")
    text_y = height - 270

    # 그림자
    shadow_offset = 4
    draw.text((50 + shadow_offset, text_y + shadow_offset), line1,
              font=font_hook, fill=(0, 0, 0, 160))
    draw.text((50 + shadow_offset, text_y + 95 + shadow_offset), line2,
              font=font_hook, fill=(0, 0, 0, 160))
    # 본문
    draw.text((50, text_y), line1, font=font_hook, fill=(255, 255, 255, 255))
    draw.text((50, text_y + 95), line2, font=font_hook, fill=(255, 255, 255, 255))

    img_bytes = io.BytesIO()
    canvas.convert("RGB").save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def gql(query):
    r = requests.post(BUFFER_API, headers=BUFFER_HEADERS, json={"query": query})
    print(f"Buffer 응답 코드: {r.status_code}")
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        print(f"GraphQL 에러: {result['errors']}")
    return result


def get_instagram_channel_id():
    orgs = gql("query { organizations { id name } }")
    org_id = orgs["data"]["organizations"][0]["id"]
    print(f"Organization: {orgs['data']['organizations'][0]['name']}")

    channels = gql(f'''
    query {{
      channels(input: {{ organizationId: "{org_id}" }}) {{
        id name service
      }}
    }}''')["data"]["channels"]

    for ch in channels:
        print(f"채널 발견: {ch['name']} ({ch['service']})")
        if ch["service"].lower() == "instagram":
            return ch["id"]
    return None


def upload_image_to_repo(img_bytes):
    filename = f"images/{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    api_url = f"https://api.github.com/repos/{REPO}/contents/{filename}"

    r = requests.put(
        api_url,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "message": f"Add {filename}",
            "content": base64.b64encode(img_bytes.getvalue()).decode(),
            "branch": BRANCH,
        },
    )
    if r.status_code not in (200, 201):
        print(f"이미지 커밋 실패: {r.status_code} - {r.text}")
        return None

    raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{filename}"
    for _ in range(10):
        if requests.head(raw_url).status_code == 200:
            print(f"이미지 URL 확인 완료: {raw_url}")
            return raw_url
        time.sleep(3)

    print("이미지 URL 확인 실패 (시간 초과)")
    return None


def post_to_buffer(caption, channel_id, image_url):
    """즉시 발행: 지금+2분으로 customScheduled 설정"""
    due_at = (datetime.now(timezone.utc) + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    safe_caption = (
        caption.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    )
    query = f'''
    mutation {{
      createPost(input: {{
        text: "{safe_caption}"
        channelId: "{channel_id}"
        schedulingType: customScheduled
        dueAt: "{due_at}"
        assets: [{{ image: {{ url: "{image_url}" }} }}]
      }}) {{
        ... on PostActionSuccess {{ post {{ id dueAt }} }}
        ... on MutationError {{ message }}
      }}
    }}'''
    result = gql(query)
    create_result = result.get("data", {}).get("createPost", {}) or {}
    print(f"포스팅 결과: {create_result}")
    return "post" in create_result


def main():
    print("콘텐츠 생성 중...")
    content = generate_content()
    print(f"생성된 문구: {content['hook_line1']} / {content['hook_line2']}")

    print("이미지 생성 중...")
    img_bytes = create_image(content)
    print("이미지 생성 완료")

    print("이미지 업로드 중...")
    image_url = upload_image_to_repo(img_bytes)
    if not image_url:
        print("이미지 업로드 실패")
        return

    print("Buffer 채널 확인 중...")
    channel_id = get_instagram_channel_id()
    if not channel_id:
        print("Instagram 채널을 찾을 수 없습니다")
        return

    print("Buffer에 즉시 발행 중...")
    success = post_to_buffer(content["caption"], channel_id, image_url)
    if success:
        print("포스팅 완료! (약 2분 후 인스타그램에 게시됩니다)")
    else:
        print("포스팅 실패")


if __name__ == "__main__":
    main()
