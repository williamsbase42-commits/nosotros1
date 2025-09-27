@echo off
echo Instalando dependencias...
py install -r requirements.txt

echo Iniciando servidor Django...
py manage.py runserver

pause
