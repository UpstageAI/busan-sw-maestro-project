@echo off
chcp 65001 > nul

:: .env 파일 존재 여부 확인
if not exist .env (
    echo [ERROR] .env 파일이 없습니다. .env.example을 참고해 .env를 만들어주세요.
    pause
    exit /b 1
)

echo [1/3] 라이브러리 동기화 중... (uv sync)
call uv sync
if %errorlevel% neq 0 (
    echo [ERROR] uv sync 중 오류가 발생했습니다.
    pause
    exit /b %errorlevel%
)

echo [2/3] 백엔드 서버 실행 중... (포트: 8001)
:: 새 CMD 창을 띄워 백엔드를 실행합니다.
start "Backend - Uvicorn" cmd /k "uv run uvicorn app.main:app --host 0.0.0.0 --port 8001"

echo 3초 대기 중...
timeout /t 3 /nobreak > nul

echo [3/3] 프론트엔드 UI 실행 중... (포트: 8002)
:: 새 CMD 창을 띄워 프론트엔드를 실행합니다.
start "Frontend - Streamlit" cmd /k "uv run streamlit run frontend/ui.py --server.port 8002 --server.headless true --browser.gatherUsageStats false"

echo =======================================================================
echo 백엔드 및 프론트엔드가 성공적으로 실행되었습니다!
echo Backend: http://localhost:8001
echo Frontend: http://localhost:8002
echo =======================================================================