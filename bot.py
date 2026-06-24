"""만능 봇 실행 시작 파일

1차 안전 분리 버전입니다.
실제 명령어/이벤트 코드는 bot_legacy.py에 그대로 두고,
bot.py는 실행 진입점만 담당합니다.
다음 단계에서 기능별 Cog를 cogs/ 폴더로 조금씩 옮기면 됩니다.
"""

import bot_legacy  # noqa: F401 - import하면 기존 봇 코드가 그대로 실행됩니다.
