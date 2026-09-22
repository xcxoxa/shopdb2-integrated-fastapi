@echo off
chcp 65001 >nul
cd /d "%~dp0shopdb2_backend_uv_fastapi1"
echo OFFIT 성수점과 seller02 계정을 연결합니다.
echo.
uv run python sync_offit_seongsu_branch.py
echo.
if errorlevel 1 (
  echo DB 수정에 실패했습니다. 위 오류 내용을 확인해주세요.
) else (
  echo 완료되었습니다. 통합 로그인에서 seller02로 다시 로그인해주세요.
)
pause
