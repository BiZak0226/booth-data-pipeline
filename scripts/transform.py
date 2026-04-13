# =========================
# transform.py
# =========================

import json
import re
import os
from collections import defaultdict
from datetime import datetime
import pytz


# =========================
# 1. 경로 설정
# =========================
INPUT_SAT = "data/raw/latest/sat.json"
INPUT_SUN = "data/raw/latest/sun.json"
OUTPUT    = "data/output/cw_332.json"


# =========================
# 2. 파일 로드
# =========================
def load_json(path):
    if not os.path.exists(path):
        print(f"[파일 없음] {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

sat = load_json(INPUT_SAT)
sun = load_json(INPUT_SUN)


# =========================
# 3. 날짜 변환
# =========================
def parse_day(entry):
    if entry == "토요일":
        return ["토"]
    elif entry == "일요일":
        return ["일"]
    elif entry == "양일":
        return ["토", "일"]
    return []


# =========================
# 4. 번호 정규화
# =========================
def normalize_number(code):
    if not isinstance(code, str):
        return None

    code = code.strip().upper()
    if code == "":
        return None

    prefix_match = re.match(r"[A-Z]+", code)
    num_match = re.search(r"\d+", code)

    if not prefix_match or not num_match:
        print(f"[번호 오류] {code}")
        return None

    return f"{prefix_match.group()}_{num_match.group().zfill(2)}"


# =========================
# 5. 링크 정규화
# =========================
def normalize_link(value, platform, booth_code):
    if not value:
        return None

    value = str(value).strip()

    if value in ["없음", "-", ""]:
        return None

    try:
        # URL
        if value.startswith("http"):
            url = value.replace("\\/", "/")

            if "twitter.com" in url:
                url = url.replace("twitter.com", "x.com")

            return url

        # 핸들
        if value.startswith("@"):
            value = value[1:]

        if platform == "twitter":
            return f"https://x.com/{value}"

        if platform == "instagram":
            return f"https://instagram.com/{value}"

    except Exception as e:
        print(f"[링크 오류] {booth_code} → {value} / {e}")

    return None


def extract_links(data, booth_code):
    links = []

    for platform in ["twitter", "instagram"]:
        raw = data.get(platform)
        url = normalize_link(raw, platform, booth_code)

        if url:
            links.append({
                "type": platform,
                "url": url
            })

    return links


# =========================
# 6. SAT + SUN 병합
# =========================
merged = {}

for source in [sat, sun]:
    for code, data in source.items():

        if not isinstance(code, str) or code.strip() == "":
            continue

        code = code.strip().upper()

        if code not in merged:
            merged[code] = data.copy()
        else:
            merged[code]["entryDate"] = "양일"


# =========================
# 7. 그룹화
# =========================
grouped = defaultdict(list)

for code, data in merged.items():
    name = data.get("boothName", "").strip()

    if name == "":
        print(f"[부스명 없음] {code}")
        continue

    grouped[name].append((code, data))


# =========================
# 8. 변환
# =========================
result = []

for name, items in grouped.items():

    # ---------------------
    # 번호 처리
    # ---------------------
    codes = [c for c, _ in items if isinstance(c, str) and c.strip()]
    codes = sorted(codes)

    numbers = [normalize_number(c) for c in codes]
    numbers = [n for n in numbers if n]

    if not numbers:
        print(f"[번호 없음] {codes}")
        continue

    try:
        prefix, idx = numbers[0].split("_")
        id_val = f"{prefix.lower()}-{idx}"
    except:
        print(f"[ID 생성 오류] {numbers}")
        continue


    # ---------------------
    # days
    # ---------------------
    days_set = set()
    for _, d in items:
        days_set.update(parse_day(d.get("entryDate", "")))


    # ---------------------
    # tags
    # ---------------------
    tags_set = set()
    for _, d in items:
        genre = d.get("genre", "")
        genres = genre.replace(" ", "").split(",")

        for g in genres:
            if g and g != "없음":
                tags_set.add(g)


    # ---------------------
    # 🖼 infoImage
    # ---------------------
    info_image = ""

    for code, d in items:
        img = d.get("img")

        if img is None:
            continue

        img = str(img).strip()

        if img == "" or img in ["없음", "-"]:
            continue

        img = img.replace("\\/", "/")

        if not img.startswith("http"):
            print(f"[이미지 이상] {code} → {img}")
            continue

        info_image = img
        break


    # ---------------------
    # 🔗 links
    # ---------------------
    links = []

    for code, d in items:
        links.extend(extract_links(d, code))

    # 중복 제거
    seen = set()
    unique_links = []

    for l in links:
        key = (l["type"], l["url"])
        if key not in seen:
            seen.add(key)
            unique_links.append(l)


    # ---------------------
    # 결과
    # ---------------------
    result.append({
        "id": id_val,
        "name": name,
        "numbers": numbers,
        "displayNumber": f"{numbers[0]}~{numbers[-1]}" if len(numbers) > 1 else numbers[0],
        "spec": "",
        "days": sorted(list(days_set)),
        "description": "",
        "artists": [],
        "infoImage": info_image,
        "goods": [],
        "links": unique_links,
        "tags": sorted(list(tags_set))
    })


# =========================
# 9. 출력
# =========================
os.makedirs("data/output", exist_ok=True)

kst = pytz.timezone("Asia/Seoul")

final_data = {
    "lastUpdate": datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S"),
    "list": result
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"\n완료: {OUTPUT} 생성됨")