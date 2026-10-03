@echo off
chcp 65001 >nul
title Radio Local
echo.
echo  Iniciando a Radio Local...
echo.
python radio_server.py
if errorlevel 1 (
    echo.
    echo  Erro: Python nao encontrado.
    echo  Instale o Python em https://www.python.org/downloads/
    echo  e marque a opcao "Add Python to PATH" durante a instalacao.
    pause
)
pause
