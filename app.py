
import os
import sqlite3
import requests
from functools import wraps
from flask import Flask, redirect, request, session, render_template, render_template_string, url_for, flash, jsonify
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
    "level": "📈 레벨 안내",
    "enhance": "⚒️ 강화 안내",
    "stock": "📈 주식 안내",
    "event": "🎉 이벤트 안내",
    "coupon": "🎟️ 쿠폰 안내",
    "mission": "🎯 일일미션 안내",
    "title": "🏷️ 칭호 패널",
    "achievement": "🏆 업적 패널",
    "music": "🎵 음악 안내",
    "tts": "🔊 TTS 안내",
    "dev_update": "🚀 업데이트 알림",
    "dev_patch": "📝 패치노트",
    "bot_status": "📊 봇상태 안내",
    "dev_diary": "📅 개발일지",
    "support_welcome": "💬 지원 서버 환영",
    "clean": "🧹 청소 안내",
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
    "level": {"title":"📈 레벨 안내","description":"채팅/음성 활동으로 경험치를 얻고 랭킹에 도전해보세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 레벨 시스템"},
    "enhance": {"title":"⚒️ 강화 안내","description":"아이템을 강화하고 최고 단계에 도전해보세요. 보호권과 확률업권을 활용할 수 있어요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 강화 시스템"},
    "stock": {"title":"📈 가상 주식 안내","description":"포인트로 서버 전용 가상 주식을 사고팔 수 있어요. 실제 투자가 아닌 서버 게임용입니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 주식 시스템"},
    "event": {"title":"🎉 이벤트 안내","description":"예약 이벤트, 개인/팀 보상, 승리팀/패배팀 보상을 관리할 수 있어요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 이벤트 시스템"},
    "coupon": {"title":"🎟️ 쿠폰 안내","description":"쿠폰 코드를 입력하면 포인트나 아이템 보상을 받을 수 있어요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 쿠폰 시스템"},
    "mission": {"title":"🎯 일일미션 안내","description":"채팅과 출석 미션을 완료하고 매일 보상을 받아보세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 일일미션"},
    "title": {"title":"🏷️ 칭호 시스템","description":"포인트로 칭호를 구매하고 대표 칭호를 프로필에 표시할 수 있어요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 칭호 시스템"},
    "achievement": {"title":"🏆 업적 시스템","description":"출석, 포인트, 활동 업적을 달성하고 보상을 받아보세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 업적 시스템"},
    "music": {"title":"🎵 음악 안내","description":"음악 명령어와 재생목록을 관리하는 공간입니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 음악 시스템"},
    "tts": {"title":"🔊 TTS 안내","description":"TTS 채널에 메시지를 입력하면 음성으로 읽어줘요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 TTS 시스템"},
    "dev_update": {"title":"🚀 만능 봇 업데이트","description":"새로운 기능과 개선사항을 알려드립니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 개발로그"},
    "dev_patch": {"title":"📝 패치노트","description":"수정된 버그와 변경된 기능을 확인하세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 패치노트"},
    "bot_status": {"title":"📊 봇 상태","description":"만능 봇의 현재 상태와 안내를 확인할 수 있습니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 상태 안내"},
    "dev_diary": {"title":"📅 개발일지","description":"만능 봇 개발 진행 상황과 예정 기능을 공유합니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 개발일지"},
    "support_welcome": {"title":"🎉 만능 봇 공식 지원 서버에 오신 것을 환영합니다!","description":"오류 문의, 업데이트 소식, 패치노트, 기능 건의를 이곳에서 확인할 수 있습니다.\n궁금한 점이 있으면 티켓을 열어주세요.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 공식 지원센터"},
    "clean": {"title":"🧹 청소 명령어 안내","description":"관리자는 `/청소 개수`로 메시지를 삭제할 수 있어요. 많은 개수도 내부적으로 나눠서 처리됩니다.","color":"FFB6C1","image_url":"","footer":"⭐ 만능 봇 관리 시스템"},
}
WELCOME_DEFAULT = {
    "title": "🌸 {username}님, {server}에 오신 걸 환영해요!",
    "description": "{user}님이 **{member_count}번째 가족**으로 입장했어요.\n규칙을 확인하고 즐겁게 활동해주세요!",
    "color": "FFB6C1",
    "image_url": "",
    "footer": "⭐ 만능 봇 | 친목 서버 관리 봇",
}

TTS_LANGS = {"ko":"한국어", "en":"영어", "ja":"일본어"}


# =========================
# 서버 채널 연결 전체 설정
# =========================
# /서버추가가 쓰던 guild_settings 테이블을 확장해서
# 봇의 주요 기능 채널/카테고리/음성방까지 웹에서 연결할 수 있게 합니다.
# type: 0=text, 2=voice, 4=category
CHANNEL_SETTING_GROUPS = [
    {
        "name": "📌 기본 / 입퇴장 / 인증",
        "fields": [
            {"key": "welcome_channel_id", "label": "👋 환영 채널", "type": 0, "hint": "입장 환영 메시지"},
            {"key": "goodbye_channel_id", "label": "👋 퇴장 채널", "type": 0, "hint": "퇴장 메시지"},
            {"key": "rule_channel_id", "label": "📌 규칙 채널", "type": 0, "hint": "규칙/필독 안내"},
            {"key": "intro_channel_id", "label": "💬 자기소개 채널", "type": 0, "hint": "자기소개 안내"},
            {"key": "verify_channel_id", "label": "✅ 인증 채널", "type": 0, "hint": "인증 패널"},
            {"key": "role_select_channel_id", "label": "🎭 역할선택 채널", "type": 0, "hint": "프로필/크리에이터/게임 역할"},
            {"key": "game_role_channel_id", "label": "🎮 게임역할 채널", "type": 0, "hint": "게임 역할 선택"},
            {"key": "notice_channel_id", "label": "📢 공지 채널", "type": 0, "hint": "중요 공지"},
        ],
    },
    {
        "name": "📁 로그 채널",
        "fields": [
            {"key": "log_channel_id", "label": "📋 대표 로그 채널", "type": 0, "hint": "기본 로그"},
            {"key": "general_log_channel_id", "label": "📋 일반로그", "type": 0, "hint": "일반 기록"},
            {"key": "warning_log_channel_id", "label": "⚠️ 경고로그", "type": 0, "hint": "경고/도배"},
            {"key": "punishment_log_channel_id", "label": "⛔ 처벌로그", "type": 0, "hint": "킥/밴/타임아웃"},
            {"key": "chat_log_channel_id", "label": "💬 채팅로그", "type": 0, "hint": "메시지 삭제/수정"},
            {"key": "voice_log_channel_id", "label": "🔊 음성로그", "type": 0, "hint": "입장/퇴장"},
            {"key": "nickname_log_channel_id", "label": "👤 닉네임로그", "type": 0, "hint": "닉네임 변경"},
            {"key": "level_log_channel_id", "label": "📈 레벨로그", "type": 0, "hint": "레벨업 알림"},
            {"key": "security_log_channel_id", "label": "🛡️ 보안로그", "type": 0, "hint": "보안패널 감지 기록"},
            {"key": "clean_log_channel_id", "label": "🧹 청소로그", "type": 0, "hint": "청소 명령어 기록"},
        ],
    },
    {
        "name": "💰 경제 / 상점 / 성장",
        "fields": [
            {"key": "shop_channel_id", "label": "🛒 상점 채널", "type": 0, "hint": "통합상점"},
            {"key": "point_channel_id", "label": "💰 포인트 채널", "type": 0, "hint": "잔액/송금"},
            {"key": "stock_channel_id", "label": "📈 주식 채널", "type": 0, "hint": "가상 주식"},
            {"key": "attendance_channel_id", "label": "📅 출석 채널", "type": 0, "hint": "출석체크"},
            {"key": "attendance_reward_channel_id", "label": "🎁 출석보상 채널", "type": 0, "hint": "출석 보상"},
            {"key": "level_channel_id", "label": "📈 레벨 채널", "type": 0, "hint": "랭크/레벨 안내"},
            {"key": "enhance_channel_id", "label": "⚒️ 강화 채널", "type": 0, "hint": "강화 시스템"},
            {"key": "coupon_channel_id", "label": "🎟️ 쿠폰 채널", "type": 0, "hint": "쿠폰 사용/안내"},
            {"key": "mission_channel_id", "label": "🎯 일일미션 채널", "type": 0, "hint": "미션/보상"},
            {"key": "title_channel_id", "label": "🏷️ 칭호 채널", "type": 0, "hint": "칭호 패널"},
            {"key": "achievement_channel_id", "label": "🏆 업적 채널", "type": 0, "hint": "업적/보상"},
        ],
    },
    {
        "name": "🎟️ 티켓 / 관리자 / 이벤트",
        "fields": [
            {"key": "ticket_channel_id", "label": "🎟️ 티켓 채널", "type": 0, "hint": "문의/신고/티켓 패널"},
            {"key": "ticket_log_channel_id", "label": "📁 티켓로그 채널", "type": 0, "hint": "티켓 닫기 기록"},
            {"key": "report_channel_id", "label": "🚨 신고 채널", "type": 0, "hint": "신고 접수"},
            {"key": "admin_panel_channel_id", "label": "🛠️ 관리자패널 채널", "type": 0, "hint": "관리 버튼/패널"},
            {"key": "bot_command_channel_id", "label": "🤖 봇명령어 채널", "type": 0, "hint": "명령어 전용"},
            {"key": "event_channel_id", "label": "🎉 이벤트 채널", "type": 0, "hint": "예약 이벤트 발송"},
            {"key": "event_list_channel_id", "label": "📋 이벤트목록 채널", "type": 0, "hint": "이벤트 목록"},
            {"key": "vote_channel_id", "label": "🗳️ 투표 채널", "type": 0, "hint": "투표 패널"},
            {"key": "giveaway_channel_id", "label": "🎁 추첨 채널", "type": 0, "hint": "추첨/랜덤박스"},
        ],
    },
    {
        "name": "🎵 음악 / 🔊 TTS",
        "fields": [
            {"key": "music_command_channel_id", "label": "🎵 음악명령어 채널", "type": 0, "hint": "재생/스킵/대기열"},
            {"key": "music_now_playing_channel_id", "label": "🎶 현재재생 채널", "type": 0, "hint": "현재 재생곡"},
            {"key": "music_queue_channel_id", "label": "📜 재생목록 채널", "type": 0, "hint": "대기열"},
            {"key": "tts_text_channel_id", "label": "🔊 TTS 텍스트 채널", "type": 0, "hint": "채팅을 음성으로 읽기"},
            {"key": "music_voice_channel_id", "label": "🔊 음악 음성채널", "type": 2, "hint": "음악 감상 음성방"},
            {"key": "tts_voice_channel_id", "label": "🔊 TTS 음성채널", "type": 2, "hint": "TTS 통방"},
        ],
    },
    {
        "name": "🌸 구인구직 / 면접",
        "fields": [
            {"key": "recruit_benefit_channel_id", "label": "📜 혜택안내", "type": 0, "hint": "관리자 혜택"},
            {"key": "recruit_planning_channel_id", "label": "🎁 기획팀지원", "type": 0, "hint": "기획팀"},
            {"key": "recruit_newbie_channel_id", "label": "🐣 뉴관팀지원", "type": 0, "hint": "뉴관팀"},
            {"key": "recruit_guide_channel_id", "label": "📢 안내팀지원", "type": 0, "hint": "안내팀"},
            {"key": "recruit_promotion_channel_id", "label": "💌 홍보팀지원", "type": 0, "hint": "홍보팀"},
            {"key": "recruit_security_channel_id", "label": "🛡️ 보안팀지원", "type": 0, "hint": "보안팀"},
            {"key": "recruit_scrim_channel_id", "label": "🎮 내전팀지원", "type": 0, "hint": "내전팀"},
            {"key": "recruit_admin_channel_id", "label": "📚 행정팀지원", "type": 0, "hint": "행정팀"},
            {"key": "recruit_design_channel_id", "label": "🎨 디자인팀지원", "type": 0, "hint": "디자인팀"},
            {"key": "recruit_fixed_channel_id", "label": "💎 고정멤버", "type": 0, "hint": "고정멤버"},
            {"key": "interview_waiting_voice_id", "label": "🔎 면접대기실", "type": 2, "hint": "면접 대기 음성방"},
            {"key": "interview_room_1_voice_id", "label": "🎤 면접실 1", "type": 2, "hint": "면접 음성방"},
            {"key": "interview_room_2_voice_id", "label": "🎤 면접실 2", "type": 2, "hint": "면접 음성방"},
        ],
    },
    {
        "name": "📈 개발로그 / 지원 서버",
        "fields": [
            {"key": "dev_update_channel_id", "label": "🚀 업데이트", "type": 0, "hint": "업데이트 알림"},
            {"key": "dev_patch_channel_id", "label": "📝 패치노트", "type": 0, "hint": "패치노트"},
            {"key": "dev_status_channel_id", "label": "📊 봇상태", "type": 0, "hint": "봇 상태"},
            {"key": "dev_diary_channel_id", "label": "📅 개발일지", "type": 0, "hint": "개발 기록"},
            {"key": "support_welcome_channel_id", "label": "💬 지원서버 환영", "type": 0, "hint": "공식 지원 서버 환영"},
            {"key": "support_notice_channel_id", "label": "📢 지원서버 공지", "type": 0, "hint": "지원 서버 공지"},
        ],
    },
    {
        "name": "📦 카테고리 연결",
        "fields": [
            {"key": "rule_category_id", "label": "📌 필독 카테고리", "type": 4, "hint": "규칙/인증/역할선택"},
            {"key": "welcome_category_id", "label": "👋 인사퇴장 카테고리", "type": 4, "hint": "입퇴장"},
            {"key": "log_category_id", "label": "📁 로그 카테고리", "type": 4, "hint": "서버 로그"},
            {"key": "shop_category_id", "label": "🛒 상점 카테고리", "type": 4, "hint": "경제/상점/주식"},
            {"key": "bot_command_category_id", "label": "🤖 봇명령어 카테고리", "type": 4, "hint": "명령어/출석/레벨"},
            {"key": "music_category_id", "label": "🎵 뮤직 카테고리", "type": 4, "hint": "음악"},
            {"key": "tts_category_id", "label": "🔊 TTS 카테고리", "type": 4, "hint": "TTS"},
            {"key": "recruit_category_id", "label": "🌸 구인구직 카테고리", "type": 4, "hint": "지원 채널"},
            {"key": "event_category_id", "label": "🎉 이벤트 카테고리", "type": 4, "hint": "이벤트"},
            {"key": "devlog_category_id", "label": "📈 개발로그 카테고리", "type": 4, "hint": "업데이트/패치노트"},
            {"key": "server_stats_category_id", "label": "📊 서버스텟 카테고리", "type": 4, "hint": "서버 통계"},
            {"key": "temp_voice_category_id", "label": "😴 잠수방 카테고리", "type": 4, "hint": "자동 음성방"},
            {"key": "enhance_category_id", "label": "⚒️ 강화 카테고리", "type": 4, "hint": "강화방"},
        ],
    },
]

CHANNEL_SETTING_FIELDS = [field for group in CHANNEL_SETTING_GROUPS for field in group["fields"]]
CHANNEL_SETTING_FIELD_NAMES = [field["key"] for field in CHANNEL_SETTING_FIELDS]
CHANNEL_SETTING_TYPES = {field["key"]: field["type"] for field in CHANNEL_SETTING_FIELDS}

SECURITY_FIELDS = [
    "malicious_user_detection", "auto_filter", "raid_detection",
    "spam_protection", "mention_spam_detection", "new_account_guard",
    "dangerous_file_block", "token_leak_guard", "permission_guard",
    "security_log_enabled",
]

SECURITY_LABELS = {
    "malicious_user_detection": "악성유저감지",
    "auto_filter": "자동검열",
    "raid_detection": "테러감지",
    "spam_protection": "도배보호",
    "mention_spam_detection": "멘션테러감지",
    "new_account_guard": "새계정보호",
    "dangerous_file_block": "위험파일차단",
    "token_leak_guard": "토큰보호",
    "permission_guard": "권한보호",
    "security_log_enabled": "보안로그",
}

DEFAULT_MISSION_SETTINGS = {"chat_target": 20, "reward_point": 500, "reward_box": 1}
SUPPORT_SERVER_INVITE = os.getenv("SUPPORT_SERVER_INVITE", "https://discord.gg/dSjteDX5Se")
PUBLIC_DASHBOARD_URL = os.getenv("PUBLIC_DASHBOARD_URL", "https://powerfull.o-r.kr/")

DEFAULT_TITLE_SHOP = [
    ("새싹", "🌱", 500, "처음 시작하는 멤버에게 어울리는 기본 칭호"),
    ("단골손님", "🌸", 2500, "꾸준히 활동하는 멤버용 칭호"),
    ("만능러", "⭐", 5000, "여러 기능을 즐기는 멤버용 칭호"),
    ("포인트부자", "💰", 10000, "경제 시스템 고수 느낌 칭호"),
    ("서버수호자", "🛡️", 15000, "서버를 지켜주는 멤버용 칭호"),
    ("레전드", "👑", 30000, "최상위 활동 멤버용 프리미엄 칭호"),
]

def db():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    ensure_tables(con)
    return con


def ensure_column(cur, table, column, definition):
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    if column not in columns:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass


def seed_title_shop(cur, guild_id=0):
    for name, emoji, price, desc in DEFAULT_TITLE_SHOP:
        cur.execute(
            """
            INSERT OR IGNORE INTO title_shop(guild_id,title_name,emoji,price,description,is_active,created_at)
            VALUES (?,?,?,?,?,1,datetime('now','localtime'))
            """,
            (guild_id, name, emoji, price, desc),
        )


def ensure_tables(con):
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS welcome_embeds (guild_id INTEGER PRIMARY KEY,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS auto_embeds (guild_id INTEGER,embed_type TEXT,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT,PRIMARY KEY (guild_id, embed_type))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS security_settings (guild_id INTEGER PRIMARY KEY,malicious_user_detection INTEGER DEFAULT 0,auto_filter INTEGER DEFAULT 1,raid_detection INTEGER DEFAULT 0,spam_protection INTEGER DEFAULT 1,mention_spam_detection INTEGER DEFAULT 1,new_account_guard INTEGER DEFAULT 0,dangerous_file_block INTEGER DEFAULT 1,token_leak_guard INTEGER DEFAULT 1,permission_guard INTEGER DEFAULT 1,security_log_enabled INTEGER DEFAULT 1,updated_at TEXT)""")
    for col, default in {
        "spam_protection": "INTEGER DEFAULT 1",
        "mention_spam_detection": "INTEGER DEFAULT 1",
        "new_account_guard": "INTEGER DEFAULT 0",
        "dangerous_file_block": "INTEGER DEFAULT 1",
        "token_leak_guard": "INTEGER DEFAULT 1",
        "permission_guard": "INTEGER DEFAULT 1",
        "security_log_enabled": "INTEGER DEFAULT 1",
    }.items():
        ensure_column(cur, "security_settings", col, default)
    cur.execute("""CREATE TABLE IF NOT EXISTS security_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER,user_id INTEGER DEFAULT 0,action TEXT,reason TEXT,channel_id INTEGER DEFAULT 0,created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS custom_filter_words (guild_id INTEGER,word TEXT,added_by INTEGER,added_at TEXT,PRIMARY KEY (guild_id, word))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS malicious_users (guild_id INTEGER,user_id INTEGER,reason TEXT,added_by INTEGER,added_at TEXT,PRIMARY KEY (guild_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY,welcome_channel_id INTEGER DEFAULT 0,goodbye_channel_id INTEGER DEFAULT 0,rule_channel_id INTEGER DEFAULT 0,game_role_channel_id INTEGER DEFAULT 0,log_channel_id INTEGER DEFAULT 0,updated_at TEXT)""")
    for col in CHANNEL_SETTING_FIELD_NAMES:
        ensure_column(cur, "guild_settings", col, "INTEGER DEFAULT 0")
    cur.execute("""CREATE TABLE IF NOT EXISTS tts_settings (guild_id INTEGER PRIMARY KEY,lang TEXT DEFAULT 'ko',voice_profile TEXT DEFAULT 'yeonhong',voice_name TEXT,rate TEXT DEFAULT '+0%',pitch TEXT DEFAULT '+0Hz',updated_at TEXT)""")
    for col, default in {"voice_profile":"TEXT DEFAULT 'yeonhong'","voice_name":"TEXT","rate":"TEXT DEFAULT '+0%'","pitch":"TEXT DEFAULT '+0Hz'"}.items():
        ensure_column(cur, "tts_settings", col, default)
    cur.execute("""CREATE TABLE IF NOT EXISTS recruit_embeds (guild_id INTEGER,recruit_key TEXT,title TEXT,description TEXT,color TEXT,image_url TEXT,footer TEXT,updated_at TEXT,PRIMARY KEY (guild_id, recruit_key))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (guild_id INTEGER DEFAULT 0,user_id INTEGER,point INTEGER DEFAULT 0,attendance_count INTEGER DEFAULT 0,streak INTEGER DEFAULT 0,last_attendance TEXT,PRIMARY KEY (guild_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER,item_name TEXT,amount INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS levels (user_id INTEGER PRIMARY KEY,exp INTEGER DEFAULT 0,level INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS voice_levels (user_id INTEGER PRIMARY KEY,exp INTEGER DEFAULT 0,level INTEGER DEFAULT 1,total_seconds INTEGER DEFAULT 0)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS enhance_items (guild_id INTEGER DEFAULT 0,user_id INTEGER,item_name TEXT,level INTEGER DEFAULT 0,success_count INTEGER DEFAULT 0,fail_count INTEGER DEFAULT 0,down_count INTEGER DEFAULT 0,destroy_count INTEGER DEFAULT 0,total_attempts INTEGER DEFAULT 0,best_level INTEGER DEFAULT 0,updated_at TEXT,PRIMARY KEY (guild_id, user_id, item_name))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stock_prices (guild_id INTEGER,stock_code TEXT,stock_name TEXT,price INTEGER DEFAULT 1000,last_price INTEGER DEFAULT 1000,updated_at TEXT,PRIMARY KEY (guild_id, stock_code))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stock_holdings (guild_id INTEGER,user_id INTEGER,stock_code TEXT,amount INTEGER DEFAULT 0,avg_price INTEGER DEFAULT 0,PRIMARY KEY (guild_id, user_id, stock_code))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stock_logs (guild_id INTEGER,user_id INTEGER,stock_code TEXT,action TEXT,amount INTEGER,price INTEGER,total INTEGER,created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS scheduled_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT,guild_id INTEGER,channel_id INTEGER,creator_id INTEGER,title TEXT,description TEXT,event_time TEXT,reward_point INTEGER DEFAULT 0,reward_1 TEXT,reward_2 TEXT,reward_3 TEXT,participant_reward TEXT,win_reward TEXT,lose_reward TEXT,embed_color TEXT,image_url TEXT,footer TEXT,is_sent INTEGER DEFAULT 0,created_at TEXT)""")
    for col, default in {"participant_reward":"TEXT","reward_1":"TEXT","reward_2":"TEXT","reward_3":"TEXT","win_reward":"TEXT","lose_reward":"TEXT","embed_color":"TEXT","image_url":"TEXT","footer":"TEXT"}.items():
        ensure_column(cur, "scheduled_events", col, default)

    # bot.py 경제 업그레이드: 일일미션 / 쿠폰
    cur.execute("""CREATE TABLE IF NOT EXISTS daily_mission_progress (guild_id INTEGER,user_id INTEGER,mission_date TEXT,message_count INTEGER DEFAULT 0,attendance_done INTEGER DEFAULT 0,claimed INTEGER DEFAULT 0,claimed_at TEXT,PRIMARY KEY (guild_id, user_id, mission_date))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS daily_mission_settings (guild_id INTEGER PRIMARY KEY,chat_target INTEGER DEFAULT 20,reward_point INTEGER DEFAULT 500,reward_box INTEGER DEFAULT 1,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS coupon_codes (guild_id INTEGER,code TEXT,reward_point INTEGER DEFAULT 0,item_name TEXT,item_amount INTEGER DEFAULT 0,max_uses INTEGER DEFAULT 1,used_count INTEGER DEFAULT 0,expires_at TEXT,is_active INTEGER DEFAULT 1,created_by INTEGER,created_at TEXT,PRIMARY KEY (guild_id, code))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS coupon_claims (guild_id INTEGER,code TEXT,user_id INTEGER,claimed_at TEXT,PRIMARY KEY (guild_id, code, user_id))""")

    # bot.py 칭호 / 업적 업그레이드
    cur.execute("""CREATE TABLE IF NOT EXISTS user_titles (guild_id INTEGER,user_id INTEGER,title_name TEXT,acquired_at TEXT,PRIMARY KEY (guild_id, user_id, title_name))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_equipped_titles (guild_id INTEGER,user_id INTEGER,title_name TEXT,updated_at TEXT,PRIMARY KEY (guild_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS achievement_claims (guild_id INTEGER,user_id INTEGER,achievement_key TEXT,claimed_at TEXT,PRIMARY KEY (guild_id, user_id, achievement_key))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS title_shop (guild_id INTEGER,title_name TEXT,emoji TEXT DEFAULT '🏷️',price INTEGER DEFAULT 0,description TEXT,is_active INTEGER DEFAULT 1,created_at TEXT,PRIMARY KEY (guild_id, title_name))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS custom_achievements (guild_id INTEGER,achievement_key TEXT,name TEXT,emoji TEXT DEFAULT '🏆',condition_text TEXT,reward_point INTEGER DEFAULT 0,reward_item TEXT,reward_item_amount INTEGER DEFAULT 0,reward_title TEXT,is_active INTEGER DEFAULT 1,created_at TEXT,PRIMARY KEY (guild_id, achievement_key))""")
    seed_title_shop(cur, 0)

    # 개발로그 / 지원 서버 / 청소 설정
    cur.execute("""CREATE TABLE IF NOT EXISTS devlog_settings (guild_id INTEGER PRIMARY KEY,category_id INTEGER DEFAULT 0,update_channel_id INTEGER DEFAULT 0,patch_channel_id INTEGER DEFAULT 0,status_channel_id INTEGER DEFAULT 0,diary_channel_id INTEGER DEFAULT 0,notify_role_id INTEGER DEFAULT 0,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS support_settings (guild_id INTEGER PRIMARY KEY,support_invite TEXT,dashboard_url TEXT,welcome_title TEXT,welcome_description TEXT,welcome_channel_id INTEGER DEFAULT 0,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS clean_settings (guild_id INTEGER PRIMARY KEY,max_delete INTEGER DEFAULT 0,batch_size INTEGER DEFAULT 100,delay_seconds REAL DEFAULT 1.0,log_enabled INTEGER DEFAULT 1,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS feature_flags (guild_id INTEGER,feature_key TEXT,is_enabled INTEGER DEFAULT 1,updated_at TEXT,PRIMARY KEY (guild_id, feature_key))""")

    # 커스텀 보조 봇 슬롯 설정
    # 실제 봇 토큰은 Render 환경변수 CUSTOM_BOT_TOKEN_1~3에 저장하고,
    # 이 테이블은 서버별로 어떤 슬롯을 어떤 통방/음성채널에 연결할지만 저장합니다.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_voice_bots (
            guild_id INTEGER,
            slot INTEGER,
            bot_name TEXT,
            avatar_url TEXT,
            voice_channel_id INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            created_by INTEGER DEFAULT 0,
            updated_at TEXT,
            PRIMARY KEY (guild_id, slot)
        )
    """)
    for col, default in {
        "avatar_url": "TEXT",
        "voice_channel_id": "INTEGER DEFAULT 0",
        "enabled": "INTEGER DEFAULT 1",
        "created_by": "INTEGER DEFAULT 0",
        "updated_at": "TEXT",
    }.items():
        ensure_column(cur, "custom_voice_bots", col, default)
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


def as_float(value, default=0.0):
    try: return float(str(value).strip())
    except Exception: return default


def as_bool_form(name):
    return 1 if request.form.get(name) else 0


def normalize_code(value, max_len=30):
    value = (value or "").strip().upper()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^A-Z0-9_-]", "", value)
    return value[:max_len]


def discord_color_int(hex_value):
    return int(validate_hex(hex_value), 16)


def send_discord_embed(channel_id, title, description, color="FFB6C1", image_url="", footer="", content=""):
    if not BOT_TOKEN:
        return False, "BOT TOKEN이 설정되지 않았어요."
    channel_id = as_int(channel_id)
    if not channel_id:
        return False, "채널 ID가 올바르지 않아요."
    embed = {
        "title": (title or "만능 봇 알림")[:256],
        "description": (description or "")[:4096],
        "color": discord_color_int(color),
    }
    if image_url:
        embed["image"] = {"url": image_url[:500]}
    if footer:
        embed["footer"] = {"text": footer[:2048]}
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content[:2000]
    try:
        r = requests.post(f"{DISCORD_API}/channels/{channel_id}/messages", headers={**bot_headers(), "Content-Type": "application/json"}, json=payload, timeout=10)
        if r.status_code in (200, 201, 204):
            return True, "발송 완료"
        return False, f"Discord API 오류: {r.status_code} / {r.text[:200]}"
    except Exception as e:
        return False, str(e)


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
    mission_settings = con.execute("SELECT * FROM daily_mission_settings WHERE guild_id=?", (guild_id,)).fetchone()
    if not mission_settings:
        con.execute("INSERT OR IGNORE INTO daily_mission_settings(guild_id,chat_target,reward_point,reward_box,updated_at) VALUES (?,?,?,?,datetime('now','localtime'))", (guild_id, DEFAULT_MISSION_SETTINGS["chat_target"], DEFAULT_MISSION_SETTINGS["reward_point"], DEFAULT_MISSION_SETTINGS["reward_box"]))
        con.commit()
        mission_settings = con.execute("SELECT * FROM daily_mission_settings WHERE guild_id=?", (guild_id,)).fetchone()
    devlog = con.execute("SELECT * FROM devlog_settings WHERE guild_id=?", (guild_id,)).fetchone()
    support = con.execute("SELECT * FROM support_settings WHERE guild_id=?", (guild_id,)).fetchone()
    clean = con.execute("SELECT * FROM clean_settings WHERE guild_id=?", (guild_id,)).fetchone()
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
    coupons = con.execute("SELECT * FROM coupon_codes WHERE guild_id=? ORDER BY created_at DESC LIMIT 30", (guild_id,)).fetchall()
    mission_today = con.execute("SELECT COUNT(*) AS users, SUM(claimed) AS claimed FROM daily_mission_progress WHERE guild_id=? AND mission_date=date('now','localtime')", (guild_id,)).fetchone()
    title_shop = con.execute("SELECT * FROM title_shop WHERE guild_id IN (0, ?) ORDER BY guild_id, price", (guild_id,)).fetchall()
    custom_achievements = con.execute("SELECT * FROM custom_achievements WHERE guild_id=? ORDER BY created_at DESC", (guild_id,)).fetchall()
    security_logs = con.execute("SELECT * FROM security_logs WHERE guild_id=? ORDER BY log_id DESC LIMIT 15", (guild_id,)).fetchall()
    stock_logs = con.execute("SELECT * FROM stock_logs WHERE guild_id=? ORDER BY created_at DESC LIMIT 15", (guild_id,)).fetchall()
    con.close()
    return render_template("dashboard.html", guild_id=guild_id, guild=guild, welcome=dict(welcome) if welcome else WELCOME_DEFAULT, security=dict(security), security_fields=SECURITY_FIELDS, security_labels=SECURITY_LABELS, embeds=embeds, embed_types=EMBED_TYPES, channels=channels, text_channels=text_channels(channels), guild_settings=dict(guild_settings) if guild_settings else {}, tts=dict(tts) if tts else {"lang":"ko"}, tts_langs=TTS_LANGS, recruit=recruit, recruit_items=RECRUIT_ITEMS, stocks=stocks, events=events, filter_words=filter_words, bad_users=bad_users, top_points=top_points, coupons=coupons, mission_settings=dict(mission_settings), mission_today=dict(mission_today) if mission_today else {}, title_shop=title_shop, custom_achievements=custom_achievements, devlog=dict(devlog) if devlog else {}, support=dict(support) if support else {"support_invite": SUPPORT_SERVER_INVITE, "dashboard_url": PUBLIC_DASHBOARD_URL}, clean=dict(clean) if clean else {"max_delete":0,"batch_size":100,"delay_seconds":1.0,"log_enabled":1}, security_logs=security_logs, stock_logs=stock_logs, channel_setting_groups=CHANNEL_SETTING_GROUPS)

CHANNEL_SETTINGS_PAGE_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h1>📦 전체 서버 채널 연결</h1>
<p>이 페이지는 <b>guild_settings</b> 테이블에 모든 기능 채널을 저장합니다.</p>
<p><a href="{{ url_for('dashboard', guild_id=guild_id) }}#guild-settings">← 대시보드로 돌아가기</a></p>

<form method="post" action="{{ url_for('save_guild_settings', guild_id=guild_id) }}">
  {% for group in channel_setting_groups %}
  <section class="card" style="margin:18px 0;padding:18px;border:1px solid rgba(255,255,255,.12);border-radius:16px;">
    <h2>{{ group.name }}</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;">
      {% for f in group.fields %}
      <label style="display:block;">
        <div style="font-weight:700;margin-bottom:6px;">{{ f.label }}</div>
        <select name="{{ f.key }}" style="width:100%;padding:10px;border-radius:10px;">
          <option value="0">미설정</option>
          {% for c in channels %}
            {% if c.type == f.type %}
              <option value="{{ c.id }}" {% if (guild_settings.get(f.key, 0)|string) == (c.id|string) %}selected{% endif %}>
                {% if c.type == 4 %}📁{% elif c.type == 2 %}🔊{% else %}#{% endif %} {{ c.name }}
              </option>
            {% endif %}
          {% endfor %}
        </select>
        <small>{{ f.hint }} · DB: {{ f.key }}</small>
      </label>
      {% endfor %}
    </div>
  </section>
  {% endfor %}
  <button type="submit" style="padding:12px 18px;border-radius:12px;font-weight:800;">✅ 전체 채널 설정 저장</button>
</form>
{% endblock %}
"""

@app.route("/dashboard/<guild_id>/channels")
@login_required
def channel_settings_page(guild_id):
    if not require_admin_guild(guild_id):
        flash("이 서버를 설정할 관리자 권한이 없어요.")
        return redirect(url_for("servers"))
    channels = fetch_channels(guild_id)
    con = db()
    row = con.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)).fetchone()
    con.close()
    return render_template_string(
        CHANNEL_SETTINGS_PAGE_TEMPLATE,
        guild_id=guild_id,
        channels=channels,
        guild_settings=dict(row) if row else {},
        channel_setting_groups=CHANNEL_SETTING_GROUPS,
    )

@app.route("/dashboard/<guild_id>/guild_settings", methods=["POST"])
@login_required
def save_guild_settings(guild_id):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))

    submitted_fields = [field for field in CHANNEL_SETTING_FIELD_NAMES if field in request.form]

    # 예전 dashboard.html에서 5개만 보내도 호환되고,
    # 새 전체 채널 연결 페이지에서는 모든 기능 채널을 한 번에 저장합니다.
    if not submitted_fields:
        submitted_fields = ["welcome_channel_id", "goodbye_channel_id", "rule_channel_id", "game_role_channel_id", "log_channel_id"]

    con = db()
    con.execute(
        "INSERT OR IGNORE INTO guild_settings(guild_id, updated_at) VALUES (?, datetime('now','localtime'))",
        (guild_id,)
    )

    for field in submitted_fields:
        if field not in CHANNEL_SETTING_FIELD_NAMES:
            continue
        con.execute(
            f"UPDATE guild_settings SET {field}=?, updated_at=datetime('now','localtime') WHERE guild_id=?",
            (as_int(request.form.get(field)), guild_id),
        )

    con.commit()
    con.close()
    flash(f"서버 채널 설정 {len(submitted_fields)}개를 저장했어요.")
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
    values = {key: as_bool_form(key) for key in SECURITY_FIELDS}
    # 보안로그는 실수로 꺼지는 것을 줄이려고 체크박스가 없으면 기본 켜짐으로 둡니다.
    if "security_log_enabled" not in request.form:
        values["security_log_enabled"] = 1
    con = db()
    con.execute(
        """
        INSERT INTO security_settings(
            guild_id, malicious_user_detection, auto_filter, raid_detection,
            spam_protection, mention_spam_detection, new_account_guard,
            dangerous_file_block, token_leak_guard, permission_guard,
            security_log_enabled, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
        ON CONFLICT(guild_id) DO UPDATE SET
            malicious_user_detection=excluded.malicious_user_detection,
            auto_filter=excluded.auto_filter,
            raid_detection=excluded.raid_detection,
            spam_protection=excluded.spam_protection,
            mention_spam_detection=excluded.mention_spam_detection,
            new_account_guard=excluded.new_account_guard,
            dangerous_file_block=excluded.dangerous_file_block,
            token_leak_guard=excluded.token_leak_guard,
            permission_guard=excluded.permission_guard,
            security_log_enabled=excluded.security_log_enabled,
            updated_at=excluded.updated_at
        """,
        (guild_id, *(values[key] for key in SECURITY_FIELDS)),
    )
    con.commit(); con.close(); flash("보안패널 전체 설정을 저장했어요.")
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


@app.route("/dashboard/<guild_id>/send_embed", methods=["POST"])
@login_required
def send_embed_message(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    ok, msg = send_discord_embed(
        request.form.get("channel_id"),
        request.form.get("title", "만능 봇 알림"),
        request.form.get("description", ""),
        request.form.get("color", "FFB6C1"),
        request.form.get("image_url", ""),
        request.form.get("footer", "⭐ 만능 봇"),
        request.form.get("content", ""),
    )
    flash("임베드 알림을 보냈어요." if ok else f"임베드 발송 실패: {msg}")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#notice")

@app.route("/dashboard/<guild_id>/support", methods=["POST"])
@login_required
def save_support_settings(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute(
        """
        INSERT OR REPLACE INTO support_settings(
            guild_id,support_invite,dashboard_url,welcome_title,welcome_description,welcome_channel_id,updated_at
        ) VALUES (?,?,?,?,?,?,datetime('now','localtime'))
        """,
        (
            guild_id,
            request.form.get("support_invite", SUPPORT_SERVER_INVITE)[:300],
            request.form.get("dashboard_url", PUBLIC_DASHBOARD_URL)[:300],
            request.form.get("welcome_title", "🎉 만능 봇 공식 지원 서버에 오신 것을 환영합니다!")[:256],
            request.form.get("welcome_description", "")[:4096],
            as_int(request.form.get("welcome_channel_id")),
        ),
    )
    con.commit(); con.close(); flash("지원 서버/홈페이지 환영 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#support")

@app.route("/dashboard/<guild_id>/support/send_welcome", methods=["POST"])
@login_required
def send_support_welcome(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    channel_id = request.form.get("channel_id")
    title = request.form.get("title") or "🎉 만능 봇 공식 지원 서버에 오신 것을 환영합니다!"
    desc = request.form.get("description") or (
        "만능 봇은 환영 메시지, 인증 패널, 보안, 티켓, 경제 시스템을 한 곳에서 관리할 수 있는 통합 관리 봇입니다.\n\n"
        f"💬 지원 서버: {SUPPORT_SERVER_INVITE}\n"
        f"🚀 대시보드: {PUBLIC_DASHBOARD_URL}"
    )
    ok, msg = send_discord_embed(channel_id, title, desc, request.form.get("color", "FFB6C1"), request.form.get("image_url", ""), "⭐ 만능 봇 공식 지원센터")
    flash("지원 서버 환영 메시지를 보냈어요." if ok else f"환영 메시지 발송 실패: {msg}")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#support")


# === DASHBOARD_SEND_BUTTONS_PATCH_V1 ===
# 대시보드에서 저장 버튼 옆 발송/테스트 버튼을 쓰기 위한 기능입니다.
DASH_AUTO_EMBED_CHANNEL_FIELDS = {
    "rules": "rule_channel_id",
    "intro": "intro_channel_id",
    "verify": "verify_channel_id",
    "ticket": "ticket_channel_id",
    "shop": "shop_channel_id",
    "point": "point_channel_id",
    "level": "level_channel_id",
    "enhance": "enhance_channel_id",
    "stock": "stock_channel_id",
    "event": "event_channel_id",
    "coupon": "coupon_channel_id",
    "mission": "mission_channel_id",
    "title": "title_channel_id",
    "achievement": "achievement_channel_id",
    "music": "music_command_channel_id",
    "tts": "tts_text_channel_id",
    "dev_update": "dev_update_channel_id",
    "dev_patch": "dev_patch_channel_id",
    "bot_status": "dev_status_channel_id",
    "dev_diary": "dev_diary_channel_id",
    "support_welcome": "support_welcome_channel_id",
    "clean": "bot_command_channel_id",
}

DASH_RECRUIT_CHANNEL_FIELDS = {
    "benefit": "recruit_benefit_channel_id",
    "planning": "recruit_planning_channel_id",
    "newbie": "recruit_newbie_channel_id",
    "guide": "recruit_guide_channel_id",
    "promotion": "recruit_promotion_channel_id",
    "security": "recruit_security_channel_id",
    "scrim": "recruit_scrim_channel_id",
    "admin": "recruit_admin_channel_id",
    "design": "recruit_design_channel_id",
    "fixed": "recruit_fixed_channel_id",
    "move": "recruit_guide_channel_id",
}


def dash_get_guild_channel_id(guild_id, field_name):
    if not field_name:
        return 0
    con = db()
    try:
        row = con.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)).fetchone()
        if row and field_name in row.keys():
            return as_int(row[field_name], 0)
    except Exception:
        return 0
    finally:
        con.close()
    return 0


def dash_render_welcome_text(text, guild_id):
    text = text or ""
    user = fetch_user() or {}
    guild = fetch_bot_guild(guild_id) or {}
    username = user.get("global_name") or user.get("username") or "관리자"
    user_id = user.get("id") or "0"
    server_name = guild.get("name") or "서버"
    member_count = guild.get("approximate_member_count") or guild.get("member_count") or "0"
    rule_channel_id = dash_get_guild_channel_id(guild_id, "rule_channel_id")
    replacements = {
        "{user}": f"<@{user_id}>",
        "{username}": username,
        "{server}": server_name,
        "{member_count}": str(member_count),
        "{rule_channel}": f"<# {rule_channel_id}>".replace("# ", "#") if rule_channel_id else "미설정",
    }
    for key, value in replacements.items():
        text = text.replace(key, str(value))
    return text


def dash_send_form_embed(guild_id, channel_field, success_text, redirect_hash, *, render_welcome=False):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    channel_id = dash_get_guild_channel_id(guild_id, channel_field)
    if not channel_id:
        flash(f"발송할 채널이 미설정이에요. 전체 채널에서 {channel_field}를 먼저 설정해주세요.")
        return redirect(url_for("dashboard", guild_id=guild_id) + redirect_hash)

    title = request.form.get("title", "만능 봇 알림")
    description = request.form.get("description", "")
    footer = request.form.get("footer", "⭐ 만능 봇")
    if render_welcome:
        title = dash_render_welcome_text(title, guild_id)
        description = dash_render_welcome_text(description, guild_id)
        footer = dash_render_welcome_text(footer, guild_id)

    ok, msg = send_discord_embed(
        channel_id,
        title,
        description,
        request.form.get("color", "FFB6C1"),
        request.form.get("image_url", ""),
        footer,
    )
    flash(success_text if ok else f"발송 실패: {msg}")
    return redirect(url_for("dashboard", guild_id=guild_id) + redirect_hash)


@app.route("/dashboard/<guild_id>/welcome/test", methods=["POST"])
@login_required
def test_welcome(guild_id):
    return dash_send_form_embed(
        guild_id,
        "welcome_channel_id",
        "환영 테스트 메시지를 보냈어요.",
        "#welcome",
        render_welcome=True,
    )


@app.route("/dashboard/<guild_id>/embed/<embed_type>/send", methods=["POST"])
@login_required
def send_auto_embed_now(guild_id, embed_type):
    if embed_type not in EMBED_TYPES:
        flash("알 수 없는 기본 임베드 종류예요.")
        return redirect(url_for("dashboard", guild_id=guild_id) + "#embeds")
    return dash_send_form_embed(
        guild_id,
        DASH_AUTO_EMBED_CHANNEL_FIELDS.get(embed_type, "notice_channel_id"),
        f"{EMBED_TYPES[embed_type]} 임베드를 발송했어요.",
        "#embeds",
    )


@app.route("/dashboard/<guild_id>/recruit/<recruit_key>/send", methods=["POST"])
@login_required
def send_recruit_now(guild_id, recruit_key):
    if recruit_key not in RECRUIT_ITEMS:
        flash("알 수 없는 구인구직 임베드 종류예요.")
        return redirect(url_for("dashboard", guild_id=guild_id) + "#recruit")
    return dash_send_form_embed(
        guild_id,
        DASH_RECRUIT_CHANNEL_FIELDS.get(recruit_key, "recruit_guide_channel_id"),
        f"{RECRUIT_ITEMS[recruit_key]} 임베드를 발송했어요.",
        "#recruit",
    )
# === /DASHBOARD_SEND_BUTTONS_PATCH_V1 ===


@app.route("/dashboard/<guild_id>/devlog", methods=["POST"])
@login_required
def save_devlog_settings(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db()
    con.execute(
        """
        INSERT OR REPLACE INTO devlog_settings(
            guild_id,category_id,update_channel_id,patch_channel_id,status_channel_id,diary_channel_id,notify_role_id,updated_at
        ) VALUES (?,?,?,?,?,?,?,datetime('now','localtime'))
        """,
        (guild_id, as_int(request.form.get("category_id")), as_int(request.form.get("update_channel_id")), as_int(request.form.get("patch_channel_id")), as_int(request.form.get("status_channel_id")), as_int(request.form.get("diary_channel_id")), as_int(request.form.get("notify_role_id"))),
    )
    con.commit(); con.close(); flash("개발로그 채널 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#devlog")

@app.route("/dashboard/<guild_id>/devlog/send", methods=["POST"])
@login_required
def send_devlog_notice(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    notice_type = request.form.get("notice_type", "update")
    channel_field = {"update":"update_channel_id", "patch":"patch_channel_id", "status":"status_channel_id", "diary":"diary_channel_id"}.get(notice_type, "update_channel_id")
    con = db(); row = con.execute("SELECT * FROM devlog_settings WHERE guild_id=?", (guild_id,)).fetchone(); con.close()
    channel_id = request.form.get("channel_id") or (row[channel_field] if row and row[channel_field] else 0)
    mention = ""
    if row and row["notify_role_id"]:
        mention = f"<@&{row['notify_role_id']}>"
    ok, msg = send_discord_embed(channel_id, request.form.get("title", "🚀 만능 봇 업데이트"), request.form.get("description", ""), request.form.get("color", "FFB6C1"), request.form.get("image_url", ""), request.form.get("footer", "⭐ 만능 봇 개발로그"), mention)
    flash("개발로그 알림을 보냈어요." if ok else f"개발로그 발송 실패: {msg}")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#devlog")

@app.route("/dashboard/<guild_id>/mission", methods=["POST"])
@login_required
def save_mission_settings(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    chat_target = max(1, as_int(request.form.get("chat_target"), DEFAULT_MISSION_SETTINGS["chat_target"]))
    reward_point = max(0, as_int(request.form.get("reward_point"), DEFAULT_MISSION_SETTINGS["reward_point"]))
    reward_box = max(0, as_int(request.form.get("reward_box"), DEFAULT_MISSION_SETTINGS["reward_box"]))
    con = db(); con.execute("INSERT OR REPLACE INTO daily_mission_settings(guild_id,chat_target,reward_point,reward_box,updated_at) VALUES (?,?,?,?,datetime('now','localtime'))", (guild_id, chat_target, reward_point, reward_box)); con.commit(); con.close(); flash("일일미션 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#mission")

@app.route("/dashboard/<guild_id>/coupon", methods=["POST"])
@login_required
def save_coupon(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    code = normalize_code(request.form.get("code"))
    if not code:
        flash("쿠폰 코드를 입력해주세요."); return redirect(url_for("dashboard", guild_id=guild_id)+"#coupon")
    con = db()
    old = con.execute("SELECT used_count FROM coupon_codes WHERE guild_id=? AND code=?", (guild_id, code)).fetchone()
    used_count = old[0] if old else 0
    con.execute(
        """
        INSERT OR REPLACE INTO coupon_codes(guild_id,code,reward_point,item_name,item_amount,max_uses,used_count,expires_at,is_active,created_by,created_at)
        VALUES (?,?,?,?,?,?,?,?,1,?,datetime('now','localtime'))
        """,
        (guild_id, code, max(0, as_int(request.form.get("reward_point"))), request.form.get("item_name", "")[:80], max(0, as_int(request.form.get("item_amount"))), max(1, as_int(request.form.get("max_uses"), 1)), used_count, request.form.get("expires_at", "")[:40], current_user_id()),
    )
    con.commit(); con.close(); flash(f"쿠폰 `{code}`를 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#coupon")

@app.route("/dashboard/<guild_id>/coupon/delete", methods=["POST"])
@login_required
def delete_coupon(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    code = normalize_code(request.form.get("code"))
    con = db(); con.execute("UPDATE coupon_codes SET is_active=0 WHERE guild_id=? AND code=?", (guild_id, code)); con.commit(); con.close(); flash(f"쿠폰 `{code}`를 비활성화했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#coupon")

@app.route("/dashboard/<guild_id>/title_shop", methods=["POST"])
@login_required
def save_title_shop(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    title_name = (request.form.get("title_name") or "")[:40].strip()
    if not title_name:
        flash("칭호 이름을 입력해주세요."); return redirect(url_for("dashboard", guild_id=guild_id)+"#title")
    con = db(); con.execute("INSERT OR REPLACE INTO title_shop(guild_id,title_name,emoji,price,description,is_active,created_at) VALUES (?,?,?,?,?,1,datetime('now','localtime'))", (guild_id, title_name, (request.form.get("emoji") or "🏷️")[:10], max(0, as_int(request.form.get("price"))), request.form.get("description", "")[:300])); con.commit(); con.close(); flash("칭호 상점 항목을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#title")

@app.route("/dashboard/<guild_id>/title_shop/delete", methods=["POST"])
@login_required
def delete_title_shop(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db(); con.execute("UPDATE title_shop SET is_active=0 WHERE guild_id=? AND title_name=?", (guild_id, request.form.get("title_name", ""))); con.commit(); con.close(); flash("칭호 상점 항목을 비활성화했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#title")

@app.route("/dashboard/<guild_id>/title/give", methods=["POST"])
@login_required
def give_user_title(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    user_id = as_int(request.form.get("user_id")); title_name = (request.form.get("title_name") or "")[:40].strip()
    if user_id and title_name:
        con = db(); con.execute("INSERT OR IGNORE INTO user_titles(guild_id,user_id,title_name,acquired_at) VALUES (?,?,?,datetime('now','localtime'))", (guild_id, user_id, title_name)); con.commit(); con.close(); flash("유저에게 칭호를 지급했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#title")

@app.route("/dashboard/<guild_id>/title/remove", methods=["POST"])
@login_required
def remove_user_title(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db(); con.execute("DELETE FROM user_titles WHERE guild_id=? AND user_id=? AND title_name=?", (guild_id, as_int(request.form.get("user_id")), request.form.get("title_name", ""))); con.commit(); con.close(); flash("유저 칭호를 회수했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#title")

@app.route("/dashboard/<guild_id>/achievement", methods=["POST"])
@login_required
def save_custom_achievement(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    key = normalize_code(request.form.get("achievement_key"), 50).lower()
    name = (request.form.get("name") or "")[:80].strip()
    if not key or not name:
        flash("업적 키와 이름을 입력해주세요."); return redirect(url_for("dashboard", guild_id=guild_id)+"#achievement")
    con = db(); con.execute("""INSERT OR REPLACE INTO custom_achievements(guild_id,achievement_key,name,emoji,condition_text,reward_point,reward_item,reward_item_amount,reward_title,is_active,created_at) VALUES (?,?,?,?,?,?,?,?,?,1,datetime('now','localtime'))""", (guild_id, key, name, (request.form.get("emoji") or "🏆")[:10], request.form.get("condition_text", "")[:300], max(0, as_int(request.form.get("reward_point"))), request.form.get("reward_item", "")[:80], max(0, as_int(request.form.get("reward_item_amount"))), request.form.get("reward_title", "")[:40])); con.commit(); con.close(); flash("커스텀 업적을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#achievement")

@app.route("/dashboard/<guild_id>/achievement/delete", methods=["POST"])
@login_required
def delete_custom_achievement(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    con = db(); con.execute("UPDATE custom_achievements SET is_active=0 WHERE guild_id=? AND achievement_key=?", (guild_id, request.form.get("achievement_key", ""))); con.commit(); con.close(); flash("커스텀 업적을 비활성화했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#achievement")

@app.route("/dashboard/<guild_id>/clean", methods=["POST"])
@login_required
def save_clean_settings(guild_id):
    if not require_admin_guild(guild_id): return redirect(url_for("servers"))
    max_delete = max(0, as_int(request.form.get("max_delete"), 0))
    batch_size = min(100, max(1, as_int(request.form.get("batch_size"), 100)))
    delay_seconds = max(0.0, min(10.0, as_float(request.form.get("delay_seconds"), 1.0)))
    con = db(); con.execute("INSERT OR REPLACE INTO clean_settings(guild_id,max_delete,batch_size,delay_seconds,log_enabled,updated_at) VALUES (?,?,?,?,?,datetime('now','localtime'))", (guild_id, max_delete, batch_size, delay_seconds, as_bool_form("log_enabled"))); con.commit(); con.close(); flash("청소 명령어 설정을 저장했어요.")
    return redirect(url_for("dashboard", guild_id=guild_id)+"#clean")

@app.route("/api/health")
def api_health():
    return jsonify({"ok": True, "service": "powerfull-dashboard"})

@app.route("/api/guild/<guild_id>/overview")
@login_required
def api_guild_overview(guild_id):
    if not require_admin_guild(guild_id):
        return jsonify({"ok": False, "error": "권한 없음"}), 403
    con = db()
    data = {
        "ok": True,
        "guild_id": guild_id,
        "top_points": [dict(r) for r in con.execute("SELECT user_id, point, attendance_count, streak FROM users WHERE guild_id=? ORDER BY point DESC LIMIT 10", (guild_id,)).fetchall()],
        "coupons": [dict(r) for r in con.execute("SELECT code,reward_point,item_name,item_amount,max_uses,used_count,is_active,expires_at FROM coupon_codes WHERE guild_id=? ORDER BY created_at DESC LIMIT 20", (guild_id,)).fetchall()],
        "security_logs": [dict(r) for r in con.execute("SELECT user_id,action,reason,channel_id,created_at FROM security_logs WHERE guild_id=? ORDER BY log_id DESC LIMIT 20", (guild_id,)).fetchall()],
    }
    con.close()
    return jsonify(data)


@app.route("/api/guild/<guild_id>/channel-settings")
@login_required
def api_channel_settings(guild_id):
    if not require_admin_guild(guild_id):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    con = db()
    row = con.execute("SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)).fetchone()
    con.close()
    return jsonify({
        "ok": True,
        "guild_id": str(guild_id),
        "settings": dict(row) if row else {},
        "fields": CHANNEL_SETTING_GROUPS,
    })


# =========================
# 커스텀 보조 봇 대시보드
# =========================
CUSTOM_BOT_SLOT_COUNT = 3
CUSTOM_BOT_INVITE_PERMISSIONS = os.getenv("CUSTOM_BOT_INVITE_PERMISSIONS", "8").strip()


def custom_bot_token_status(slot: int):
    return bool(os.getenv(f"CUSTOM_BOT_TOKEN_{slot}", "").strip())


def custom_bot_client_id(slot: int):
    return os.getenv(f"CUSTOM_BOT_CLIENT_ID_{slot}", "").strip()


def custom_bot_invite_url(slot: int, guild_id=None):
    client_id = custom_bot_client_id(slot)
    if not client_id:
        return ""
    base = "https://discord.com/oauth2/authorize"
    url = (
        f"{base}?client_id={client_id}"
        f"&permissions={CUSTOM_BOT_INVITE_PERMISSIONS}"
        f"&integration_type=0"
        f"&scope=bot"
    )
    if guild_id:
        url += f"&guild_id={guild_id}&disable_guild_select=true"
    return url


def voice_channels(channels):
    return [c for c in channels if c.get("type") == 2]


CUSTOM_BOTS_PAGE_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<style>
.custom-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
.custom-card { padding:18px; border-radius:18px; border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.06); }
.custom-card h2 { margin:0 0 10px; }
.custom-card label { display:block; margin:10px 0 6px; font-weight:700; }
.custom-card input,.custom-card select { width:100%; padding:10px; border-radius:10px; border:1px solid rgba(255,255,255,.18); box-sizing:border-box; }
.custom-card button,.custom-btn { display:inline-block; border:0; border-radius:999px; padding:10px 14px; font-weight:800; text-decoration:none; cursor:pointer; margin-top:10px; }
.custom-save { background:linear-gradient(135deg,#ff7ac8,#8c7bff); color:white; }
.custom-danger { background:#ff5f7a; color:white; }
.custom-ghost { background:rgba(255,255,255,.12); color:inherit; }
.custom-note { opacity:.82; line-height:1.6; }
.badge { display:inline-block; padding:5px 9px; border-radius:999px; font-size:12px; font-weight:800; }
.ok { background:rgba(87,242,135,.16); color:#57f287; }
.warn { background:rgba(255,214,102,.16); color:#ffd666; }
</style>

<h1>🤖 커스텀 봇 추가</h1>
<p class="custom-note">
  이 페이지에서 서버별 커스텀 봇 1~3번 슬롯을 추가/수정할 수 있어요.<br>
  실제 보조 봇은 Render 환경변수 <b>CUSTOM_BOT_TOKEN_1~3</b>에 토큰이 있어야 온라인이 됩니다.
</p>
<p>
  <a class="custom-btn custom-ghost" href="{{ url_for('dashboard', guild_id=guild_id) }}">← 대시보드로 돌아가기</a>
  <a class="custom-btn custom-ghost" href="{{ url_for('channel_settings_page', guild_id=guild_id) }}">📦 채널 연결</a>
</p>

<div class="custom-grid">
{% for slot in [1,2,3] %}
  {% set row = custom_bots.get(slot) %}
  <section class="custom-card">
    <h2>🎧 {{ slot }}번 커스텀 봇</h2>
    {% if token_status.get(slot) %}
      <span class="badge ok">✅ 토큰 있음</span>
    {% else %}
      <span class="badge warn">⚠️ CUSTOM_BOT_TOKEN_{{ slot }} 없음</span>
    {% endif %}

    <form method="post" action="{{ url_for('save_custom_bot_slot', guild_id=guild_id, slot=slot) }}">
      <label>봇 표시 이름</label>
      <input name="bot_name" maxlength="32" value="{{ row.bot_name if row else '커스텀봇 ' ~ slot }}" placeholder="예: 만능 뮤직 {{ slot }}">

      <label>입장할 통방/음성채널</label>
      <select name="voice_channel_id" required>
        <option value="0">통방/음성채널 선택</option>
        {% for c in voice_channels %}
          <option value="{{ c.id }}" {% if row and (row.voice_channel_id|string)==(c.id|string) %}selected{% endif %}>🔊 {{ c.name }}</option>
        {% endfor %}
      </select>

      <label>프로필 이미지 URL 선택사항</label>
      <input name="avatar_url" maxlength="500" value="{{ row.avatar_url if row else '' }}" placeholder="https://...">

      <label style="display:flex;align-items:center;gap:8px;font-weight:700;">
        <input type="checkbox" name="enabled" value="1" style="width:auto;" {% if not row or row.enabled %}checked{% endif %}>
        활성화
      </label>

      <button class="custom-save" type="submit">✅ {{ slot }}번 커스텀 봇 추가/저장</button>
    </form>

    {% if row %}
      <form method="post" action="{{ url_for('delete_custom_bot_slot', guild_id=guild_id, slot=slot) }}" onsubmit="return confirm('{{ slot }}번 커스텀 봇 설정을 삭제할까요?');">
        <button class="custom-danger" type="submit">🗑️ 설정 삭제</button>
      </form>
      <p class="custom-note">최근 수정: {{ row.updated_at or '기록 없음' }}</p>
    {% endif %}

    {% if invite_urls.get(slot) %}
      <a class="custom-btn custom-ghost" href="{{ invite_urls.get(slot) }}" target="_blank">➕ {{ slot }}번 보조 봇 서버에 초대</a>
    {% else %}
      <p class="custom-note">초대 버튼을 쓰려면 Render 환경변수 <b>CUSTOM_BOT_CLIENT_ID_{{ slot }}</b>도 넣어주세요.</p>
    {% endif %}
  </section>
{% endfor %}
</div>

<section class="custom-card" style="margin-top:18px;">
  <h2>사용 순서</h2>
  <p class="custom-note">
    1. Discord Developer Portal에서 보조 봇 1~3개를 만들고 서버에 초대<br>
    2. Render Environment에 <b>CUSTOM_BOT_TOKEN_1</b>, <b>CUSTOM_BOT_TOKEN_2</b>, <b>CUSTOM_BOT_TOKEN_3</b> 입력<br>
    3. 여기에서 각 슬롯의 이름과 통방을 저장<br>
    4. Discord에서 <b>/커스텀</b> 실행 후 1번/2번/3번 통방 입장 사용
  </p>
</section>
{% endblock %}
"""


CUSTOM_BOTS_SELECT_SERVER_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h1>🤖 커스텀 봇 서버 선택</h1>
<p>커스텀 봇을 추가할 서버를 선택해주세요.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;">
{% for g in guilds %}
  <section style="padding:18px;border-radius:16px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.06);">
    <h2 style="margin-top:0;">{{ g.name }}</h2>
    <a style="display:inline-block;padding:10px 14px;border-radius:999px;background:linear-gradient(135deg,#ff7ac8,#8c7bff);color:white;text-decoration:none;font-weight:800;" href="{{ url_for('custom_bots_page', guild_id=g.id) }}">커스텀 봇 추가</a>
  </section>
{% endfor %}
</div>
{% endblock %}
"""


@app.route("/custom-bots")
@login_required
def custom_bots_select_server():
    return render_template_string(CUSTOM_BOTS_SELECT_SERVER_TEMPLATE, guilds=fetch_user_guilds())


@app.route("/dashboard/<guild_id>/custom-bots")
@login_required
def custom_bots_page(guild_id):
    if not require_admin_guild(guild_id):
        flash("이 서버를 설정할 관리자 권한이 없어요.")
        return redirect(url_for("servers"))
    channels = fetch_channels(guild_id)
    con = db()
    rows = con.execute(
        "SELECT slot, bot_name, avatar_url, voice_channel_id, enabled, updated_at FROM custom_voice_bots WHERE guild_id=? ORDER BY slot",
        (guild_id,),
    ).fetchall()
    con.close()
    custom_bots = {int(r["slot"]): dict(r) for r in rows}
    token_status = {slot: custom_bot_token_status(slot) for slot in range(1, CUSTOM_BOT_SLOT_COUNT + 1)}
    invite_urls = {slot: custom_bot_invite_url(slot, guild_id) for slot in range(1, CUSTOM_BOT_SLOT_COUNT + 1)}
    return render_template_string(
        CUSTOM_BOTS_PAGE_TEMPLATE,
        guild_id=guild_id,
        channels=channels,
        voice_channels=voice_channels(channels),
        custom_bots=custom_bots,
        token_status=token_status,
        invite_urls=invite_urls,
    )


@app.route("/dashboard/<guild_id>/custom-bots/<int:slot>/save", methods=["POST"])
@login_required
def save_custom_bot_slot(guild_id, slot):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    if slot < 1 or slot > CUSTOM_BOT_SLOT_COUNT:
        flash("커스텀 봇 슬롯은 1~3번만 사용할 수 있어요.")
        return redirect(url_for("custom_bots_page", guild_id=guild_id))

    bot_name = (request.form.get("bot_name") or f"커스텀봇 {slot}").strip()[:32]
    avatar_url = (request.form.get("avatar_url") or "").strip()[:500]
    voice_channel_id = as_int(request.form.get("voice_channel_id"), 0)
    enabled = as_bool_form("enabled")

    if not voice_channel_id:
        flash("입장할 통방/음성채널을 선택해주세요.")
        return redirect(url_for("custom_bots_page", guild_id=guild_id))

    con = db()
    con.execute(
        """
        INSERT INTO custom_voice_bots(guild_id, slot, bot_name, avatar_url, voice_channel_id, enabled, created_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(guild_id, slot) DO UPDATE SET
            bot_name=excluded.bot_name,
            avatar_url=excluded.avatar_url,
            voice_channel_id=excluded.voice_channel_id,
            enabled=excluded.enabled,
            created_by=excluded.created_by,
            updated_at=excluded.updated_at
        """,
        (guild_id, slot, bot_name, avatar_url, voice_channel_id, enabled, current_user_id()),
    )
    con.commit(); con.close()
    flash(f"{slot}번 커스텀 봇 설정을 저장했어요. Discord에서 /커스텀으로 입장시킬 수 있어요.")
    return redirect(url_for("custom_bots_page", guild_id=guild_id))


@app.route("/dashboard/<guild_id>/custom-bots/<int:slot>/delete", methods=["POST"])
@login_required
def delete_custom_bot_slot(guild_id, slot):
    if not require_admin_guild(guild_id):
        return redirect(url_for("servers"))
    con = db()
    con.execute("DELETE FROM custom_voice_bots WHERE guild_id=? AND slot=?", (guild_id, slot))
    con.commit(); con.close()
    flash(f"{slot}번 커스텀 봇 설정을 삭제했어요.")
    return redirect(url_for("custom_bots_page", guild_id=guild_id))



# =========================
# 봇 초대 링크 / 서버 추가 버튼
# =========================
# Discord OAuth2 봇 초대 링크입니다.
# permissions=8 은 관리자 권한입니다. 권한을 줄이고 싶으면 Discord Permission Calculator 값으로 바꾸세요.
DISCORD_BOT_CLIENT_ID = os.getenv("DISCORD_BOT_CLIENT_ID", "1510625526300278879").strip()
DISCORD_BOT_INVITE_PERMISSIONS = os.getenv("DISCORD_BOT_INVITE_PERMISSIONS", "8").strip()


def get_bot_invite_url(guild_id=None):
    base = "https://discord.com/oauth2/authorize"
    scope = "bot%20applications.commands"
    url = (
        f"{base}?client_id={DISCORD_BOT_CLIENT_ID}"
        f"&permissions={DISCORD_BOT_INVITE_PERMISSIONS}"
        f"&integration_type=0"
        f"&scope={scope}"
    )
    if guild_id:
        url += f"&guild_id={guild_id}&disable_guild_select=true"
    return url


@app.route("/invite")
def invite_bot():
    guild_id = request.args.get("guild_id", "").strip()
    return redirect(get_bot_invite_url(guild_id or None))


@app.route("/bot-invite")
def bot_invite_page():
    invite_url = get_bot_invite_url()
    return f"""
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>만능 봇 서버 추가</title>
        <style>
            body {
                margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
                font-family: Arial, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                background: radial-gradient(circle at top, #ffd7ee 0, #151521 45%, #0b0b12 100%);
                color:white;
            }
            .card {
                width:min(560px, calc(100% - 36px));
                padding:34px; border-radius:28px;
                background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.18);
                box-shadow:0 24px 70px rgba(0,0,0,.35); backdrop-filter: blur(16px);
                text-align:center;
            }
            h1 { margin:0 0 12px; font-size:32px; }
            p { color:#e9e9f5; line-height:1.7; margin:0 0 24px; }
            .btn {
                display:inline-block; padding:15px 24px; border-radius:999px;
                background:linear-gradient(135deg, #ff7ac8, #8c7bff);
                color:white; font-weight:800; text-decoration:none;
                box-shadow:0 14px 28px rgba(255,122,200,.28);
            }
            .sub { margin-top:18px; font-size:13px; color:#cfcfe6; }
            .back { display:inline-block; margin-top:18px; color:#fff; opacity:.78; text-decoration:none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 만능 봇 서버 추가</h1>
            <p>아래 버튼을 누르면 디스코드 서버 선택 화면으로 이동합니다.<br>서버에 추가하려면 해당 서버의 <b>서버 관리 권한</b>이 필요합니다.</p>
            <a class="btn" href="{invite_url}">➕ 봇을 서버에 추가하기</a>
            <div class="sub">초대 후 대시보드에서 서버를 다시 선택하면 설정할 수 있어요.</div>
            <a class="back" href="/servers">← 서버 목록으로 돌아가기</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
