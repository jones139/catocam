System Scripts for CatoCam
##########################


Copy systemd/system/catocam.service to /lib/systemd/system
chmod 644 /lib/systemd/system/catocam.service
chmod +x /home/graham/catocam/catocam.py

systemctl daemon-reload
systemctl enable catocam.service
systemctl start catocam.service

View the log with:
journalctl -f -u catocam.service (view log)