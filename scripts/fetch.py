import requests
import re
import json
import os
import ast

URL = "https://comicw.net/map/"
res = requests.get(URL)
html = res.text


def extract(name):
    pattern = rf"const {name} = ({{.*?}});"
    match = re.search(pattern, html, re.S)

    if not match:
        print(f"{name} 못찾음")
        return {}

    text = match.group(1)

    # -------------------------
    # 🔥 JS → Python 변환 핵심
    # -------------------------

    # 1. 키 따옴표 추가
    text = re.sub(r"(\w+):", r'"\1":', text)

    # 2. 작은따옴표 → 큰따옴표
    text = text.replace("'", '"')

    # 3. trailing comma 제거
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    try:
        return json.loads(text)
    except:
        print("json 실패 → ast 시도")

        try:
            return ast.literal_eval(text)
        except Exception as e:
            print("파싱 실패:", e)
            return {}


sat = extract("APP_MAP_SAT")
sun = extract("APP_MAP_SUN")


# -------------------------
# 저장
# -------------------------
os.makedirs("data/raw/latest", exist_ok=True)

with open("data/raw/latest/sat.json", "w", encoding="utf-8") as f:
    json.dump(sat, f, ensure_ascii=False, indent=2)

with open("data/raw/latest/sun.json", "w", encoding="utf-8") as f:
    json.dump(sun, f, ensure_ascii=False, indent=2)

print("fetch 완료")