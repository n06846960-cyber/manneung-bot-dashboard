"""만능 봇 공통 설정 파일"""

import os

def load_local_env_file(filename: str = ".env"):
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as fp:
            for raw_line in fp:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and (key not in os.environ or not os.environ.get(key, "")):
                    os.environ[key] = value
    except Exception as e:
        print(f"⚠️ .env 로드 실패: {e}")

load_local_env_file()

DIRECT_BOT_TOKEN = ""

TOKEN = (
    os.getenv("DISCORD_TOKEN", "").strip()
    or os.getenv("DISCORD_BOT_TOKEN", "").strip()
    or DIRECT_BOT_TOKEN.strip()
)

BOT_OWNER_IDS = {
    int(x.strip())
    for x in os.getenv("BOT_OWNER_IDS", "305132904651030528").split(",")
    if x.strip().isdigit()
}

DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db").strip() or "database.db"

COLOR_SKY = 0x87CEFA
COLOR_SOFT_SKY = 0xBDEBFF
COLOR_PINK = 0xFFC8DD
COLOR_LAVENDER = 0xCDB4DB
COLOR_MINT = 0xB8F2E6
COLOR_GOLD = 0xFFD166
COLOR_GREEN = 0xA3E4B5
COLOR_WARNING = 0xFF8FAB
COLOR_GRAY = 0xB8C0CC
BOT_COLOR = COLOR_SKY

EXP_COOLDOWN = 60
SPAM_LIMIT = 5
SPAM_TIME = 7
VOICE_EXP_PER_MINUTE = 5
ENHANCE_COOLDOWN_SECONDS = 60
