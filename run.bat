@echo off
cd %~dp0
echo GovInfoWatcher の実行を開始します
echo 実行時刻: %date% %time%
echo ------------------------------

REM Pythonパスの設定（必要に応じて変更）
set PYTHON_PATH=python

REM すべての監視処理を実行
%PYTHON_PATH% scripts\run_all.py

echo ------------------------------
echo 実行が終了しました
echo 終了時刻: %date% %time%
pause 
