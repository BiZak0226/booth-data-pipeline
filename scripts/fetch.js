// scripts/fetch.js

const https = require("https");
const fs = require("fs");

const URL = "https://comicw.net/map/";

function fetchPage() {
  return new Promise((resolve) => {
    https.get(URL, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(data));
    });
  });
}

function extractVar(html, varName) {
  const regex = new RegExp(`const ${varName} = ([\\s\\S]*?);`);
  const match = html.match(regex);

  if (!match) {
    console.log(`${varName} 못찾음`);
    return {};
  }

  try {
    // Function으로 안전 실행
    const fn = new Function(`return ${match[1]}`);
    return fn();
  } catch (e) {
    console.log(`${varName} 파싱 실패`, e);
    return {};
  }
}

(async () => {
  const html = await fetchPage();

  const sat = extractVar(html, "APP_MAP_SAT");
  const sun = extractVar(html, "APP_MAP_SUN");

  if (!sat || !sun) {
    console.log("데이터 없음 → 종료");
    process.exit(1);
  }

  fs.mkdirSync("data/raw/latest", { recursive: true });

  fs.writeFileSync(
    "data/raw/latest/sat.json",
    JSON.stringify(sat, null, 2)
  );

  fs.writeFileSync(
    "data/raw/latest/sun.json",
    JSON.stringify(sun, null, 2)
  );

  console.log("fetch 완료");
})();