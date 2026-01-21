#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

# ls | egrep '.py' | awk '{print "mpy-cross ./"$1}'
rm ./*.mpy
rm -rf ./build
mkdir ./build
mkdir ./build/bin

mpy-cross ./analyzer.py
mpy-cross ./basic_shell_alone.py
mpy-cross ./basicparser.py
mpy-cross ./basictoken.py
mpy-cross ./chunk.py
mpy-cross ./common.py
mpy-cross ./dictfile.py
mpy-cross ./display.py
mpy-cross ./flowsignal.py
mpy-cross ./font.py
mpy-cross ./font6.py
mpy-cross ./font7.py
mpy-cross ./font8.py
mpy-cross ./interpreter.py
mpy-cross ./keyboard.py
mpy-cross ./lexer.py
mpy-cross ./listfile_safe.py
mpy-cross ./listfile.py
# mpy-cross ./main.basic.py
# mpy-cross ./main.py
mpy-cross ./myDMA.py
mpy-cross ./myPWM.py
mpy-cross ./ntp.py
mpy-cross ./ollama.py
mpy-cross ./program.py
mpy-cross ./reload.py
mpy-cross ./request.py
mpy-cross ./scheduler.py
mpy-cross ./sdcard.py
mpy-cross ./settings_esp32s2.py
mpy-cross ./settings_pico2.py
mpy-cross ./shell.py
mpy-cross ./tea.py
mpy-cross ./test_display.py
mpy-cross ./test_main.py
mpy-cross ./uftpd.py
mpy-cross ./uping.py
mpy-cross ./wave.py
# mpy-cross ./wavePlayer.py
mpy-cross ./wifi.py
# mpy-cross ./writer_fast.py
mpy-cross ./writer.py
mpy-cross ./zipfile.py

mv -f ./*.mpy ./build/

cd ./bin
rm -f ./*.mpy
ls | egrep '.py' | awk '{print "mpy-cross ./"$1}' | bash
mv -f ./*.mpy ../build/bin/