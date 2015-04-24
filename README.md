# pimonitor
Distributed CCTV monitoring and recording on RPi.

### Description

pimonitor is a modular CCTV solution which allows high-quality video to be quickly transported away from cameras and stored on dedicated recorders or viewed on monitors.  The system is specifically designed to be run on the low-power and low-cost Raspberrry Pi, making full use of the GPU for high-quality video recording encoded in h264.  The configuration is flexible so your system may for example include multiple cameras or monitors, or omit recording if you like.  A complete system of camera, recorder and monitor can be put together for around £100.

The recommended video quality settings are 1920x1080 resolution at 15 fps with bitrate at 1Mbit/s which gives a very clear recording and easily allows a month of footage to fit on cheap hard-drives.


### Dependencies

- [picamera](http://picamera.readthedocs.org) - Camera module only
- [pyzmq](http://pyzmq.github.io/pyzmq) - Data transport
- [wxPython](http://www.wxpython.org) - Monitor module only
- [ffmpeg](http://www.ffmpeg.org) - Recorder module only [(Raspberry Pi build instructions)](http://www.jeffreythompson.org/blog/2014/11/13/installing-ffmpeg-for-raspberry-pi/)


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

Released under GPLv2, see LICENSE for details.

Copyright (C) 2015 Adam King

