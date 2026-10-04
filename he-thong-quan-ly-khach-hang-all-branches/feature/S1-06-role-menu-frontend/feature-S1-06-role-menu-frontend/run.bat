@echo off
title He Thong Dieu Huong Phan Quyen RBAC - SCRUM-16
echo ============================================================
echo  DANG KHOI DONG HE THONG DIEU HUONG PHAN QUYEN (PYTHON)
echo  User Story: SCRUM-16 / SCRUM-30
echo ============================================================
echo.
py app.py
if %ERRORLEVEL% NEQ 0 (
    python app.py
)
pause
