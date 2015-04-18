# pimonitor
Distributed CCTV monitoring and recording on RPi.

### Description

pimonitor creates three node types:

1. Camera - Sources video from the Raspberry Pi camera module, processes it for motion detection and then streams the resulting video and event data to other subscribing nodes.
1. Recorder - Subscribes to the video and event feeds from camera modules and translates raw h264 into archived MP4 files.  It also processes and logs the motion event feed.
1. Monitor - *(not yet implemented)* Subscribes to camera event feeds and displays activity on screen when motion detected.  

This system allows the high-quality captured footage to be quickly transported away from the cameras (which could be subject to physical attack) and to separate dedicated recorders and monitors.  The recommended video quality settings are 1920x1080 resolution at 10 fps with bitrate at 800kbit/s which gives a very clear recording and allows a week of footage to easily fit on cheap commercial hard-drives.


### Dependencies

- picamera
- pyzmq
- ffmpeg


### Daemon Setup

In order to run the camera feed as a daemon (which will automatically start on boot), we need to deploy the source and then configure init.d.  The below steps can also be done for *pimonitorrec*, which is the recording daemon setup.

Download and extract the source:

```bash
cd /usr/local/bin/pimonitor
tar xvf pimonitor-0.1.tar.gz
```

Link the camera daemon script in init.d:

```bash
cd /etc/init.d
sudo ln -s /usr/local/bin/pimonitor/daemon/pimonitorcam.sh pimonitorcam
```

Test the setup:

```bash
sudo /etc/init.d/pimonitorcam start
sudo /etc/init.d/pimonitorcam status
sudo /etc/init.d/pimonitorcam stop
```

Update rc.d to configure restart on boot.

```bash
sudo update-rc.d pimonitorcam defaults
```

### License

Copyright (C) 2015 Adam King

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
full license for details.
