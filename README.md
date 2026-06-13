# 🌸 만능 봇 관리센터

디스코드 만능 봇용 웹 대시보드입니다.

## 제일 쉬운 실행 방법

1. 압축을 풉니다.
2. `.env` 파일에 Discord 정보를 입력합니다.
3. `실행하기.bat`을 더블클릭합니다.
4. 브라우저에서 `http://127.0.0.1:5000` 접속합니다.

## `.env`에서 꼭 확인할 것

```env
DISCORD_CLIENT_ID=봇 애플리케이션 ID
DISCORD_CLIENT_SECRET=OAuth2 Client Secret
DISCORD_BOT_TOKEN=봇 토큰
DISCORD_REDIRECT_URI=http://localhost:5000/callback
WEB_SECRET_KEY=아무긴랜덤문자
PORT=5000
DATABASE_PATH=../database.db
```

`PORT=5000`이면 Discord Developer Portal → OAuth2 → Redirects에 아래 주소를 등록해야 합니다.

```text
http://localhost:5000/callback
```

## 직접 실행하기

```bash
pip install -r requirements.txt
python app.py
```

## 참고

`DATABASE_PATH`는 봇이 사용하는 `database.db` 위치와 맞아야 사이트 설정이 봇에 적용됩니다.
