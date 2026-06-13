# 🌸 만능 봇 관리센터 V5 FULL FEATURES

bot(100).py 기준으로 웹 대시보드 메뉴를 확장한 버전입니다.

## 추가된 기능
- 서버 채널 연결: 환영/퇴장/규칙/게임역할/로그 채널 저장
- 환영 메시지 설정
- 보안 설정: 자동검열, 악성 유저 감지, 테러 감지
- 검열 단어 추가/삭제
- 악성 유저 등록/삭제
- 기본 임베드: 규칙/자기소개/인증/티켓/상점/포인트/음악/TTS
- 구인구직 임베드 전체 수정
- 경제: 유저 포인트 지급/설정, 포인트 TOP 10 보기
- 주식: 가상 주식 추가/수정/삭제
- TTS 기본 언어 설정
- 예약 이벤트 추가/삭제

## Render에서 업데이트 방법
1. 이 압축을 풀고 GitHub 저장소에 덮어쓰기 업로드
2. Commit changes
3. Render에서 Manual Deploy → Deploy latest commit

## 중요
이 웹사이트가 저장하는 설정은 SQLite DB에 들어갑니다.
봇과 웹사이트가 같은 database.db를 써야 봇에 바로 적용됩니다.
Render 무료 서버는 파일 저장이 영구적이지 않을 수 있으니, 실제 운영은 외부 DB 또는 같은 서버 공유 DB 구성이 좋습니다.

## 환경변수
- DISCORD_CLIENT_ID
- DISCORD_CLIENT_SECRET
- DISCORD_BOT_TOKEN
- DISCORD_REDIRECT_URI=https://powerfull.o-r.kr/callback
- WEB_SECRET_KEY
- DATABASE_PATH=database.db
