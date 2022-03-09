#!/bin/bash
rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse
pulseaudio -D --verbose --exit-idle-time=-1 --disallow-exit
python3 meeting_recorder.py