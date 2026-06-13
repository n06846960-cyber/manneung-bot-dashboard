
import os
import sqlite3
import requests
from functools import wraps
from flask import Flask, redirect, request, session, render_template, url_for, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("WEB_SECRET_KEY", "change-this-secret")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://127.0.0.1:5000/callback")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")

DISCORD_API = "https://discord.com/api/v10"
OAUTH_SCOPE = "identify guilds"

EMBED_TYPES = {
    "rules": "📌 규칙 임베드",
    "intro": "💬 자기소개 임베드",
    "verify": "✅ 인증 패널",
    "ticket": "🎟️ 티켓 패널",
    "shop": "🛒 상점 안내",
    "point": "💰 포인트 안내",
    "music": "🎵 음악 안내",
    "tts": "🔊 TTS 안내",
}

RECRUIT_ITEMS = {
    "benefit": "📜 관리자 혜택 안내",
    "planning": "🎁 기획팀 모집",
    "newbie": "🐣 뉴관팀 모집",
    "guide": "📢 안내팀 모집",
    "promotion": "💌 홍보팀 모집",
    "security": "🛡️ 보안팀 모집",
    "scrim": "🎮 내전팀 모집",
    "admin": "📚 행정팀 모집",
    "design": "🎨 디자인팀 모집",
    "move": "🚪 이동권한 안내",
    "fixed": "💎 고정멤버 안내",
}

DEFAULT_AUTO_EMBEDS = {
    "rules": {"title":"📌 만능 봇 서버 규칙","description":"{server} 서버 규칙을 확인해주세요.\n서로 존중하고 즐겁게 활동해주세요!","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 | 친목 서버 관리 봇"},
    "intro": {"title":"💬 자기소개 안내","description":"닉네임 / 나이대 / 좋아하는 게임을 편하게 적어주세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 | 친목 서버 관리 봇"},
    "verify": {"title":"✅ 만능 봇 인증 패널","description":"아래 버튼을 눌러 인증을 완료해주세요.\n인증 후 미인증 역할이 제거되고 뉴페이스 역할이 지급됩니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 | 친목 서버 관리 봇"},
    "ticket": {"title":"🎟️ 문의 티켓","description":"문의가 필요하면 티켓을 열어주세요. 운영진이 확인해드려요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 티켓 시스템"},
    "shop": {"title":"🛒 만능 봇 통합 상점","description":"포인트로 아이템을 구매할 수 있어요. `/통합상점`을 사용해보세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 경제 시스템"},
    "point": {"title":"💰 포인트 안내","description":"출석, 이벤트, 활동으로 포인트를 모아보세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 포인트 시스템"},
    "music": {"title":"🎵 음악 안내","description":"음악 명령어와 재생목록을 관리하는 공간입니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 음악 시스템"},
    "tts": {"title":"🔊 TTS 안내","description":"TTS 채널에 메시지를 입력하면 음성으로 읽어줘요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 TTS 시스템"},
}

WELCOME_DEFAULT = {
    "title": "🌸 {username}님, {server}에 오신 걸 환영해요!",
    "description": "{user}님이 **{member_count}번째 가족**으로 입장했어요.\n규칙을 확인하고 즐겁게 활동해주세요!",
    "color": "FFB6C1",
    "image_url": "",
    "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
}

TTS_LANGS = {"ko":"한국어", "en":"영어", "ja":"일본어"}


def db():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    ensure_tables(con)
    return con


def ensure_tables(con):
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS welcome_embeds (guild_id INTEGER PRIMARY KEY,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS auto_embeds (guild_id INTEGER,embed_type TEXT,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT,PRIMARY KEY (guild_id, embed_type))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS security_settings (guild_id INTEGER PRIMARY KEY,malicious_user_detection INTEGER DEFAULT 0,auto_filter INTEGER DEFAULT 1,raid_detection INTEGER DEFAULT 0,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS custom_filter_words (guild_id INTEGER,word TEXT,added_by INTEGER,added_at TEXT,PRIMARY KEY (guild_id, word))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS malicious_users (guild_id INTEGER,user_id INTEGER,reason TEXT,added_by INTEGER,added_at TEXT,PRIMARY KEY (guild_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY,welcome_channel_id INTEGER DEFAULT 0,goodbye_channel_id INTEGER DEFAULT 0,rule_channel_id INTEGER DEFAULT 0,game_role_channel_id INTEGER DEFAULT 0,log_channel_id INTEGER DEFAULT 0,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tts_settings (guild_id INTEGER PRIMARY KEY,lang TEXT DEFAULT 'ko',updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS recruit_embeds (guild_id INTEGER,recruit_key TEXT,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT,PRIMARY KEY (guild_id, recruit_key))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (guild_id INTEGER DEFAULT 0,user_id INTEGER,point INTEGER DEFAULT 0,attendance_count INTEGER DEFAULT 0,streak INTEGER DEFAULT 0,last_attendance TEXT,PRIMARY KEY (guild_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stock_prices (guild_id INTEGER,stock_code TEXT,stock_name TEXT,price INTEGER DEFAULT 1000,last_price INTEGER DEFAULT 1000,updated_at TEXT,PRIMARY KEY (guild_id, stock_code))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS scheduled_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER,channel_id INTEGER,creator_id INTEGER,title TEXT,description TEXT,event_time TEXT,reward_point INTEGER DEFAULT 0,reward_1 TEXT,reward_2 TEXT,reward_3 TEXT,win_reward TEXT,lose_reward TEXT,embed_color TEXT,image_url TEXT,footer TEXT,is_sent INTEGER DEFAULT 0,created_at TEXT)""")
    con.commit()


def discord_headers(token=None):
    return {"Authorization": f"Bearer {token or session.get('access_token')}"}

def bot_headers():
    return {"Authorization": f"Bot {BOT_TOKEN}"}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def fetch_user():
    r = requests.get(f"{DISCORD_API}/users/@me", headers=discord_headers(), timeout=10)
    if r.status_code != 200:
        session.clear(); return None
    return r.json()


def fetch_user_guilds():
    r = requests.get(f"{DISCORD_API}/users/@me/guilds", headers=discord_headers(), timeout=10)
    if r.status_code != 200: return []
    return [g for g in r.json() if int(g.get("permissions", 0)) & 0x8]


def fetch_bot_guild(guild_id):
    if not BOT_TOKEN: return None
    r = requests.get(f"{DISCORD_API}/guilds/{guild_id}?with_counts=true", headers=bot_headers(), timeout=10)
    return r.json() if r.status_code == 200 else None


def fetch_channels(guild_id):
    if not BOT_TOKEN: return []
    r = requests.get(f"{DISCORD_API}/guilds/{guild_id}/channels", headers=bot_headers(), timeout=10)
    if r.status_code != 200: return []
    # type 0 = text, 2 = voice, 4 = category
    return sorted(r.json(), key=lambda x: (x.get('position', 0), x.get('name', '')))


def text_channels(channels):
    return [c for c in channels if c.get("type") == 0]


def require_admin_guild(guild_id):
    return any(str(g["id"]) == str(guild_id) for g in fetch_user_guilds())


def validate_hex(value):
    value = (value or "FFB6C1").strip().replace("#", "")
    if len(value) == 3: value = "".join(ch*2 for ch in value)
    if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value): return "FFB6C1"
    return value.upper()


def as_int(value, default=0):
    try: return int(str(value).strip())
    except Exception: return default


def current_user_id():
    user = fetch_user() or {}
    return as_int(user.get("id"), 0)

@app.route("/")
def index():
    if session.get("access_token"): return redirect(url_for("servers"))
    return render_template("index.html")

@app.route("/login")
def login():
    auth_url = (f"{DISCORD_API}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE.replace(' ', '%20')}")
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code: return redirect(url_for("index"))
    data = {"client_id":DISCORD_CLIENT_ID,"client_secret":DISCORD_CLIENT_SECRET,"grant_type":"authorization_code","code":code,"redirect_uri":DISCORD_REDIRECT_URI}
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=10)
    if r.status_code != 200:
        flash("디스코드 로그인 실패: CLIENT_ID / SECRET / REDIRECT_URI를 확인해주세요.")
        return redirect(url_for("index"))
    session["access_token"] = r.json()["access_token"]
    return redirect(url_for("servers"))

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/servers")
@login_required
def servers():
    return render_template("servers.html", user=fetch_user(), guilds=fetch_user_guilds())

@app.route("/dashboard/<guild_id>")
@login_required
def dashboard(guild_id):
    if not require_admin_guild(guild_id):
        flash("이 서버를 설정할 관리자 권한이 없어요."); return redirect(url_for("servers"))
    guild = fetch_bot_guild(guild_id)
    if not guild: flash("봇이 이 서버에 없거나 BOT TOKEN이 잘못됐어요.")
    channels = fetch_channels(guild_id)
    con = db()
    welcome = con.execute("SELECT * FROM welcome_embeds WHERE guild_id=?", (guild_id,)).fetchone()
    security = con.execute("SELECT * FROM security_settings WHERE guild_id=?", (guild_id,)).fetchone()
    if not security:
        con.execute("INSERT OR IGNORE INTO security_settings(guild_id) VALUES (?)", (guild_id,)); con.commit()
        security = con.execute("SELECT * FROM security_settings WHERE guild_id=?", (guild_id,)).fetchone()
    guild_settings = con.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)).fetchone()
    tts = con.execute("SELECT * FROM tts_settings WHERE guild_id=?", (guild_id,)).fetchone()
    embeds = {}
    for key, default in DEFAULT_AUTO_EMBEDS.items():
        row = con.execute("SELECT * FROM auto_embeds WHERE guild_id=? AND embed_type=?", (guild_id, key)).fetchone()
        embeds[key] = dict(row) if row else default.copy()
    recruit = {}
    for key, label in RECRUIT_ITEMS.items():
        row = con.execute("SELECT * FROM recruit_embeds WHERE guild_id=? AND recruit_key=?", (guild_id, key)).fetchone()
        recruit[key] = dict(row) if row else {"title":label,"description":f"{label} 내용을 웹에서 수정해보세요.","color":"FFB6C1","image_url":"","footer":"🌸 구인구직 안내"}
    stocks = con.execute("SELECT * FROM stock_prices WHERE guild_id=? ORDER BY stock_code", (guild_id,)).fetchall()
    events = con.execute("SELECT * FROM scheduled_events WHERE guild_id=? ORDER BY event_time DESC LIMIT 20", (guild_id,)).fetchall()
    filter_words = con.execute("SELECT * FROM custom_filter_words WHERE guild_id=? ORDER BY word", (guild_id,)).fetchall()
    bad_users = con.execute("SELECT * FROM malicious_users WHERE guild_id=? ORDER BY added_at DESC LIMIT 30", (guild_id,)).fetchall()
    top_points = con.execute("SELECT user_id, point, attendance_count, streak FROM users WHERE guild_id=? ORDER BY point DESC LIMIT 10", (guild_id,)).fetchall()
    con.close()
    return render_template("dashboard.html", guild_id=guild_id, guild=guild, welcome=dict(welcome) if welcome else WELCOME_DEFAULT, security=dict(security), embeds=embeds, embed_types=EMBED_TYPES, channels=channels, text_channels=text_channels(channels), guild_settings=dict(guild_settings) if guild_settings else {}, tts=dict(tts) if tts else {"lang":"ko"}, tts_langs=TTS_LANGS, recruit=recruit, recruit_items=RECRUIT_ITEMS, stocks=stocks, events=events, filter_words=filter_words, bad_users=bad_users, top_points=top_points)

@app.route("/dashboard/<guild_id>/guild_settings", methods=["POST"])
@login_required
def save_guild_settings(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute("""INSERT OR REPLACE INTO guild_settings(guild_id,welcome_channel_id,goodbye_channel_id,rule_channel_id,game_role_channel_id,log_channel_id,updated_at) VALUES (?,?,?,?,?,?,datetime('now','localtime'))""", (guild_id, as_int(request.form.get("welcome_channel_id")), as_int(request.form.get("goodbye_channel_id")), as_int(request.form.get("rule_channel_id")), as_int(request.form.get("game_role_channel_id")), as_int(request.form.get("log_channel_id"))))
    con.commit(); con.close(); flash("서버 채널 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#guild-settings")

@app.route("/dashboard/<guild_id>/welcome", methods=["POST"])
@login_required
def save_welcome(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute("""INSERT OR REPLACE INTO welcome_embeds(guild_id,title,description,color,image_url,footer,updated_at) VALUES (?,?,?,?,?,?,datetime('now','localtime'))""", (guild_id, request.form.get("title","")[:256], request.form.get("description","")[:4096], validate_hex(request.form.get("color")), request.form.get("image_url","")[:500], request.form.get("footer","")[:2048]))
    con.commit(); con.close(); flash("환영 임베드 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#welcome")

@app.route("/dashboard/<guild_id>/embed/<embed_type>", methods=["POST"])
@login_required
def save_auto_embed(guild_id, embed_type):
    if embed_type not in EMBED_TYPES or not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute("""INSERT OR REPLACE INTO auto_embeds(guild_id,embed_type,title,description,color,image_url,footer,updated_at) VALUES (?,?,?,?,?,?,?,datetime('now','localtime'))""", (guild_id, embed_type, request.form.get("title","")[:256], request.form.get("description","")[:4096], validate_hex(request.form.get("color")), request.form.get("image_url","")[:500], request.form.get("footer","")[:2048]))
    con.commit(); con.close(); flash(f"{EMBED_TYPES[embed_type]} 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+f"#{embed_type}")

@app.route("/dashboard/<guild_id>/security", methods=["POST"])
@login_required
def save_security(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute("""INSERT OR REPLACE INTO security_settings(guild_id,malicious_user_detection,auto_filter,raid_detection,updated_at) VALUES (?,?,?,?,datetime('now','localtime'))""", (guild_id, 1 if request.form.get("malicious_user_detection") else 0, 1 if request.form.get("auto_filter") else 0, 1 if request.form.get("raid_detection") else 0))
    con.commit(); con.close(); flash("보안 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#security")

@app.route("/dashboard/<guild_id>/filter_word", methods=["POST"])
@login_required
def save_filter_word(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    word=(request.form.get("word") or "").strip().lower()
    if word:
        con=db(); con.execute("INSERT OR IGNORE INTO custom_filter_words(guild_id,word,added_by,added_at) VALUES (?,?,?,datetime('now','localtime'))", (guild_id, word, current_user_id())); con.commit(); con.close(); flash("검열 단어를 추가했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#security")

@app.route("/dashboard/<guild_id>/filter_word/delete", methods=["POST"])
@login_required
def delete_filter_word(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("DELETE FROM custom_filter_words WHERE guild_id=? AND word=?", (guild_id, request.form.get("word",""))); con.commit(); con.close(); flash("검열 단어를 삭제했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#security")

@app.route("/dashboard/<guild_id>/bad_user", methods=["POST"])
@login_required
def save_bad_user(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    user_id=as_int(request.form.get("user_id")); reason=(request.form.get("reason") or "웹 대시보드 등록")[:300]
    if user_id:
        con=db(); con.execute("INSERT OR REPLACE INTO malicious_users(guild_id,user_id,reason,added_by,added_at) VALUES (?,?,?,?,datetime('now','localtime'))", (guild_id, user_id, reason, current_user_id())); con.commit(); con.close(); flash("악성 유저 목록에 등록했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#security")

@app.route("/dashboard/<guild_id>/bad_user/delete", methods=["POST"])
@login_required
def delete_bad_user(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("DELETE FROM malicious_users WHERE guild_id=? AND user_id=?", (guild_id, as_int(request.form.get("user_id")))); con.commit(); con.close(); flash("악성 유저 목록에서 삭제했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#security")

@app.route("/dashboard/<guild_id>/tts", methods=["POST"])
@login_required
def save_tts(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    lang=request.form.get("lang","ko") if request.form.get("lang") in TTS_LANGS else "ko"
    con=db(); con.execute("INSERT OR REPLACE INTO tts_settings(guild_id,lang,updated_at) VALUES (?,?,datetime('now','localtime'))", (guild_id, lang)); con.commit(); con.close(); flash("TTS 언어 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#voice")

@app.route("/dashboard/<guild_id>/recruit/<recruit_key>", methods=["POST"])
@login_required
def save_recruit(guild_id, recruit_key):
    if recruit_key not in RECRUIT_ITEMS or not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("""INSERT OR REPLACE INTO recruit_embeds(guild_id,recruit_key,title,description,color,image_url,footer,updated_at) VALUES (?,?,?,?,?,?,?,datetime('now','localtime'))""", (guild_id, recruit_key, request.form.get("title","")[:256], request.form.get("description","")[:4096], validate_hex(request.form.get("color")), request.form.get("image_url","")[:500], request.form.get("footer","")[:2048])); con.commit(); con.close(); flash(f"{RECRUIT_ITEMS[recruit_key]} 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#recruit")

@app.route("/dashboard/<guild_id>/stock", methods=["POST"])
@login_required
def save_stock(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    code=(request.form.get("stock_code") or "").strip().upper()[:20]
    name=(request.form.get("stock_name") or "").strip()[:60]
    price=max(1, as_int(request.form.get("price"), 1000))
    if code and name:
        con=db(); old=con.execute("SELECT price FROM stock_prices WHERE guild_id=? AND stock_code=?", (guild_id,code)).fetchone(); last=old[0] if old else price
        con.execute("INSERT OR REPLACE INTO stock_prices(guild_id,stock_code,stock_name,price,last_price,updated_at) VALUES (?,?,?,?,?,datetime('now','localtime'))", (guild_id,code,name,price,last)); con.commit(); con.close(); flash("가상 주식을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#economy")

@app.route("/dashboard/<guild_id>/stock/delete", methods=["POST"])
@login_required
def delete_stock(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("DELETE FROM stock_prices WHERE guild_id=? AND stock_code=?", (guild_id, request.form.get("stock_code",""))); con.commit(); con.close(); flash("가상 주식을 삭제했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#economy")

@app.route("/dashboard/<guild_id>/points", methods=["POST"])
@login_required
def save_points(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    user_id=as_int(request.form.get("user_id")); amount=as_int(request.form.get("amount")); mode=request.form.get("mode","add")
    if user_id:
        con=db(); con.execute("INSERT OR IGNORE INTO users(guild_id,user_id,point) VALUES (?,?,0)", (guild_id,user_id))
        if mode == "set": con.execute("UPDATE users SET point=? WHERE guild_id=? AND user_id=?", (amount,guild_id,user_id))
        else: con.execute("UPDATE users SET point=point+? WHERE guild_id=? AND user_id=?", (amount,guild_id,user_id))
        con.commit(); con.close(); flash("포인트를 변경했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#economy")

@app.route("/dashboard/<guild_id>/event", methods=["POST"])
@login_required
def save_event(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("""INSERT INTO scheduled_events(guild_id,channel_id,creator_id,title,description,event_time,reward_point,reward_1,reward_2,reward_3,win_reward,lose_reward,embed_color,image_url,footer,is_sent,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,datetime('now','localtime'))""", (guild_id, as_int(request.form.get("channel_id")), current_user_id(), request.form.get("title","")[:256], request.form.get("description","")[:4096], request.form.get("event_time","")[:40], as_int(request.form.get("reward_point")), request.form.get("reward_1","")[:500], request.form.get("reward_2","")[:500], request.form.get("reward_3","")[:500], request.form.get("win_reward","")[:500], request.form.get("lose_reward","")[:500], validate_hex(request.form.get("embed_color")), request.form.get("image_url","")[:500], request.form.get("footer","")[:2048])); con.commit(); con.close(); flash("예약 이벤트를 추가했어요. 봇의 이벤트 루프가 DB를 읽으면 자동 발송돼요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#event")

@app.route("/dashboard/<guild_id>/event/delete", methods=["POST"])
@login_required
def delete_event(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con=db(); con.execute("DELETE FROM scheduled_events WHERE guild_id=? AND event_id=?", (guild_id, as_int(request.form.get("event_id")))); con.commit(); con.close(); flash("예약 이벤트를 삭제했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#event")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
