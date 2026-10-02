@echo off
chcp 65001 >nul
echo.
echo  WAPP Day-Ahead Market Simulator
echo  Projet MS OSE 2025 - Mines Paris-PSL
echo.

:: Create data directory if needed
if not exist data mkdir data

:: Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo  Serveur local disponible sur :
echo  http://%IP%:8501
echo.
echo  Partagez cette adresse aux participants sur le meme reseau Wi-Fi.
echo  Appuyez sur Ctrl+C pour arreter.
echo.

streamlit run app.py ^
    --server.address 0.0.0.0 ^
    --server.port 8501 ^
    --server.headless true ^
    --browser.gatherUsageStats false

pause
