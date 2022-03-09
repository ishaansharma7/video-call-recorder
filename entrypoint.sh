#!/bin/bash
echo "reached"
rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse
pulseaudio -D --verbose --exit-idle-time=-1 --disallow-exit
/bin/bash