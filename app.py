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
}

DEFAULT_AUTO_EMBEDS = {
    "rules": {
        "title": "📌 만능 봇 서버 규칙",
        "description": "{server} 서버 규칙을 확인해주세요.\n서로 존중하고 즐겁게 활동해주세요!",
        "color": "FFB6C1",
        "image_url": "",
        "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
    },
    "intro": {
        "title": "💬 자기소개 안내",
        "description": "닉네임 / 나이대 / 좋아하는 게임을 편하게 적어주세요.",
        "color": "FFB6C1",
        "image_url": "",
        "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
    },
    "verify": {
        "title": "✅ 만능 봇 인증 패널",
        "description": "아래 버튼을 눌러 인증을 완료해주세요.\n인증 후 미인증 역할이 제거되고 뉴페이스 역할이 지급됩니다.",
        "color": "FFB6C1",
        "image_url": "",
        "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
    },
}

WELCOME_DEFAULT = {
    "title": "🌸 {username}님, {server}에 오신 걸 환영해요!",
    "description": "{user}님이 **{member_count}번째 가족**으로 입장했어요.\n규칙을 확인하고 즐겁게 활동해주세요!",
    "color": "FFB6C1",
    "image_url": "",
    "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
}


def db():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    ensure_tables(con)
    return con


def ensure_tables(con):
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS welcome_embeds (
        guild_id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        color TEXT,
        image_url TEXT,
        footer TEXT,
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS auto_embeds (
        guild_id INTEGER,
        embed_type TEXT,
        title TEXT,
        description TEXT,
        color TEXT,
        image_url TEXT,
        footer TEXT,
        updated_at TEXT,
        PRIMARY KEY (guild_id, embed_type)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS security_settings (
        guild_id INTEGER PRIMARY KEY,
        malicious_user_detection INTEGER DEFAULT 0,
        auto_filter INTEGER DEFAULT 1,
        raid_detection INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)
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
        session.clear()
        return None
    return r.json()


def fetch_user_guilds():
    r = requests.get(f"{DISCORD_API}/users/@me/guilds", headers=discord_headers(), timeout=10)
    if r.status_code != 200:
        return []
    guilds = r.json()
    # 관리자 권한 있는 서버만 표시
    return [g for g in guilds if int(g.get("permissions", 0)) & 0x8]


def fetch_bot_guild(guild_id):
    if not BOT_TOKEN:
        return None
    r = requests.get(f"{DISCORD_API}/guilds/{guild_id}", headers=bot_headers(), timeout=10)
    return r.json() if r.status_code == 200 else None


def require_admin_guild(guild_id):
    guilds = fetch_user_guilds()
    return any(str(g["id"]) == str(guild_id) for g in guilds)


def validate_hex(value):
    value = (value or "FFB6C1").strip().replace("#", "")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        return "FFB6C1"
    return value.upper()


@app.route("/")
def index():
    if session.get("access_token"):
        return redirect(url_for("servers"))
    return render_template("index.html")


@app.route("/login")
def login():
    auth_url = (
        f"{DISCORD_API}/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code&scope={OAUTH_SCOPE.replace(' ', '%20')}"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("index"))
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers, timeout=10)
    if r.status_code != 200:
        flash("디스코드 로그인에 실패했어요. CLIENT_ID/SECRET/REDIRECT_URI를 확인해주세요.")
        return redirect(url_for("index"))
    token = r.json()
    session["access_token"] = token["access_token"]
    return redirect(url_for("servers"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/servers")
@login_required
def servers():
    user = fetch_user()
    guilds = fetch_user_guilds()
    return render_template("servers.html", user=user, guilds=guilds)


@app.route("/dashboard/<guild_id>")
@login_required
def dashboard(guild_id):
    if not require_admin_guild(guild_id):
        flash("이 서버를 설정할 관리자 권한이 없어요.")
        return redirect(url_for("servers"))
    guild = fetch_bot_guild(guild_id)
    if not guild:
        flash("봇이 이 서버에 없거나 BOT TOKEN이 잘못됐어요.")
    con = db()
    welcome = con.execute("SELECT * FROM welcome_embeds WHERE guild_id=?", (guild_id,)).fetchone()
    security = con.execute("SELECT * FROM security_settings WHERE guild_id=?", (guild_id,)).fetchone()
    if not security:
        con.execute("INSERT OR IGNORE INTO security_settings(guild_id) VALUES (?)", (guild_id,))
        con.commit()
        security = con.execute("SELECT * FROM security_settings WHERE guild_id=?", (guild_id,)).fetchone()
    embeds = {}
    for key, default in DEFAULT_AUTO_EMBEDS.items():
        row = con.execute("SELECT * FROM auto_embeds WHERE guild_id=? AND embed_type=?", (guild_id, key)).fetchone()
        embeds[key] = dict(row) if row else default.copy()
    con.close()
    return render_template(
        "dashboard.html",
        guild_id=guild_id,
        guild=guild,
        welcome=dict(welcome) if welcome else WELCOME_DEFAULT,
        security=dict(security),
        embeds=embeds,
        embed_types=EMBED_TYPES,
    )


@app.route("/dashboard/<guild_id>/welcome", methods=["POST"])
@login_required
def save_welcome(guild_id):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    con = db()
    con.execute(
        """
        INSERT OR REPLACE INTO welcome_embeds(guild_id, title, description, color, image_url, footer, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """,
        (
            guild_id,
            request.form.get("title", "")[:256],
            request.form.get("description", "")[:4096],
            validate_hex(request.form.get("color")),
            request.form.get("image_url", "")[:500],
            request.form.get("footer", "")[:2048],
        ),
    )
    con.commit(); con.close()
    flash("환영 임베드 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id))


@app.route("/dashboard/<guild_id>/embed/<embed_type>", methods=["POST"])
@login_required
def save_auto_embed(guild_id, embed_type):
    if embed_type not in EMBED_TYPES or not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    con = db()
    con.execute(
        """
        INSERT OR REPLACE INTO auto_embeds(guild_id, embed_type, title, description, color, image_url, footer, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """,
        (
            guild_id,
            embed_type,
            request.form.get("title", "")[:256],
            request.form.get("description", "")[:4096],
            validate_hex(request.form.get("color")),
            request.form.get("image_url", "")[:500],
            request.form.get("footer", "")[:2048],
        ),
    )
    con.commit(); con.close()
    flash(f"{EMBED_TYPES[embed_type]} 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id))


@app.route("/dashboard/<guild_id>/security", methods=["POST"])
@login_required
def save_security(guild_id):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    con = db()
    con.execute(
        """
        INSERT OR REPLACE INTO security_settings(
            guild_id, malicious_user_detection, auto_filter, raid_detection, updated_at
        ) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
        """,
        (
            guild_id,
            1 if request.form.get("malicious_user_detection") else 0,
            1 if request.form.get("auto_filter") else 0,
            1 if request.form.get("raid_detection") else 0,
        ),
    )
    con.commit(); con.close()
    flash("보안 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
