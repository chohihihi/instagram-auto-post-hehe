import anthropic
import requests
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BUFFER_API_KEY = os.environ["BUFFER_API_KEY"]

TOPICS = [
    {"type": "운동", "detail": "남성 헬스 루틴, 벌크업, 다이어트, 홈트, 자세 교정"},
    {"type": "피부관리", "detail": "남성 기초케어, 선크림, 보습, 각질, 모공 관리"},
    {"type": "피부시술", "detail": "남성 피부과 시술 추천 (레이저, 리프팅, 제모, 흉터)"},
    {"type": "예비신랑", "detail": "결혼 준비 꿀팁, 웨딩 다이어트, 정장 선택, 신혼 준비"},
    {"type": "그루밍", "detail": "남성 헤어스타일, 수염 관리, 향수, 패션 코디"},
]

def generate_content():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    topic = random.choice(TOPICS)

    prompt = f"""자기관리하는 20-35세 한국 남성을 타겟으로 한 인스타그램 정보성 카드뉴스 콘텐츠를 만들어주세요.

주제: {topic['type']} - {topic['detail']}

다음 JSON 형식으로 응답해주세요:
{{
    "title": "카드 상단 제목 (예: '남자 피부과 시술 추천 TOP 3') 20자 이내",
    "points": [
        {{"number": "01", "heading": "항목 제목 10자 이내", "desc": "설명 25자 이내"}},
        {{"number": "02", "heading": "항목 제목 10자 이내", "desc": "설명 25자 이내"}},
        {{"number": "03", "heading": "항목 제목 10자 이내", "desc": "설명 25자 이내"}}
    ],
    "footer": "하단 한줄 마무리 멘트 20자 이내",
    "caption": "인스타그램 캡션. 본문 요약 + 줄바꿈 + 해시태그 10개. 해시태그 예: #남자피부관리 #그루밍 #자기관리남 #남자헬스 #피부과추천",
    "bg_color": "배경색 hex (깔끔한 밝은 톤 또는 다크톤)",
    "accent_color": "포인트색 hex (숫자, 강조에 사용)",
    "text_color": "본문 텍스트색 hex"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    start = text.find('{')
    end = text.rfind('}') + 1
    return json.loads(text[start:end])

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_image(content):
    width, height = 1080, 1080
    bg = hex_to_rgb(content.get("bg_color", "#F7F7F7"))
    accent = hex_to_rgb(content.get("accent_color", "#1A1A1A"))
    text_color = hex_to_rgb(content.get("text_color", "#1A1A1A"))

    img = Image.new('RGB', (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    try:
        font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_title = ImageFont.truetype(font_path_bold, 62)
        font_num = ImageFont.truetype(font_path_bold, 48)
        font_heading = ImageFont.truetype(font_path_bold, 42)
        font_desc = ImageFont.truetype(font_path, 34)
        font_footer = ImageFont.truetype(font_path, 30)
    except:
        font_title = font_num = font_heading = font_desc = font_footer = ImageFont.load_default()

    # 상단 배경 바
    draw.rectangle([(0, 0), (1080, 180)], fill=accent)

    # 제목
    draw.text((540, 90), content["title"], font=font_title, fill=(255,255,255), anchor="mm")

    # 포인트 리스트
    y = 260
    for point in content.get("points", []):
        # 번호 원
        draw.ellipse([(80, y-10), (140, y+50)], fill=accent)
        draw.text((110, y+20), point["number"], font=font_num, fill=(255,255,255), anchor="mm")

        # 제목 + 설명
        draw.text((180, y), point["heading"], font=font_heading, fill=text_color)
        draw.text((180, y+48), point["desc"], font=font_desc, fill=tuple(min(c+60,255) for c in text_color))

        # 구분선
        draw.line([(80, y+110), (1000, y+110)], fill=tuple(min(c+80,255) for c in bg), width=2)
        y += 150

    # 하단 푸터
    draw.rectangle([(0, 960), (1080, 1080)], fill=accent)
    draw.text((540, 1020), content.get("footer", ""), font=font_footer, fill=(255,255,255), anchor="mm")

    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def get_instagram_channel_id():
    headers = {"Authorization": f"Bearer {BUFFER_API_KEY}"}
    response = requests.get("https://api.buffer.com/1/channels.json", headers=headers)
    if response.status_code != 200:
        print(f"채널 조회 실패: {response.text}")
        return None
    for channel in response.json().get("data", []):
        if channel.get("service") == "instagram":
            return channel["id"]
    return None

def post_to_buffer(caption, channel_id):
    headers = {"Authorization": f"Bearer {BUFFER_API_KEY}"}
    post_data = {
        "channel_ids": [channel_id],
        "text": caption,
    }
    response = requests.post(
        "https://api.buffer.com/1/updates/create.json",
        headers=headers,
        json=post_data
    )
    print(f"포스팅 결과: {response.status_code} - {response.text}")
    return response.status_code == 200

def main():
    print("콘텐츠 생성 중...")
    content = generate_content()
    print(f"생성된 콘텐츠: {content['title']}")

    print("이미지 생성 중...")
    img_bytes = create_image(content)
    print("이미지 생성 완료")

    print("Buffer 채널 확인 중...")
    channel_id = get_instagram_channel_id()
    if not channel_id:
        print("Instagram 채널을 찾을 수 없습니다")
        return

    print("Buffer에 포스팅 중...")
    success = post_to_buffer(content["caption"], channel_id)
    if success:
        print("포스팅 완료!")
    else:
        print("포스팅 실패")

if __name__ == "__main__":
    main()
