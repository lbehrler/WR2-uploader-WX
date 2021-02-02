# Using flock to prevent multiple instances from launching
flock -n /tmp/WR2-ADV-UL.lock sudo python3 /home/pi/WR2-uploader-WX/WR2-adv-uploader.py

