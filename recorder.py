#!/usr/bin/env python

# General modules
import sys
import os
import zmq
import logging
import socket
import datetime
import errno
from subprocess import Popen, PIPE

# Project modules
import config

log = logging.getLogger(__name__)

def main():
    hostname = socket.gethostname()
    log.info('Starting recording client on %s.', hostname)

    configfile = 'config/recorder.json'
    log.info('Loading config from %s.', configfile)
    configdata = config.load_from_file(configfile)

    cameraip = configdata['network']['camera_ip_addr']
    eventport = configdata['network']['event_sub_port']
    videoport = configdata['network']['h264_sub_port']

    framerate = configdata['camera']['framerate']

    max_duration = configdata['recorder']['max_duration']
    recording_folder = configdata['recorder']['recording_folder']

    context = zmq.Context()
    log.info('Connecting to camera event feed: %s:%i.', cameraip, eventport)
    eventsocket = context.socket(zmq.SUB)
    eventsocket.connect('tcp://%s:%s' % (cameraip, eventport))
    eventsocket.setsockopt(zmq.SUBSCRIBE, '')

    log.info('Connecting to camera video feed: %s:%i.', cameraip, videoport)
    videosocket = context.socket(zmq.SUB)
    videosocket.connect('tcp://%s:%s' % (cameraip, videoport))
    videosocket.setsockopt(zmq.SUBSCRIBE, '')

    files = {}
    
    poller = zmq.Poller()
    poller.register(videosocket, zmq.POLLIN)

    try:
        while True:
            socks = dict(poller.poll(5000))
            if videosocket in socks and socks[videosocket] == zmq.POLLIN: 
                host, data = videosocket.recv_multipart()
                
                if host not in files:
                    # We're lacking a current output pipe for this host.
                    starttime = datetime.datetime.now()
                    newfilename = '%s%s-%s.mp4' % (recording_folder, host, starttime.strftime("%Y%m%d-%H%M%S"))
                    
                    vidproc = Popen(['ffmpeg', '-f', 'h264', '-i', '-', '-codec', 'copy', '-r', '%i' % framerate, newfilename], stdin=PIPE)
                else:
                    # Retrieve the video output pipe
                    vidproc, starttime = files[host] 

                # Write the data we received on our subscription
                try:
                    vidproc.stdin.write(data)
                except IOError as e:
                    if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
                        # Stop loop on "Invalid pipe" or "Invalid argument".
                        # No sense in continuing with broken pipe.
                        break
                    else:
                        # Raise any other error.
                        raise

                # If the video is now longer than the prescribed duration, we should close it and clean it.
                if datetime.datetime.now() > starttime + datetime.timedelta(seconds=max_duration):
                    vidproc.stdin.close()
                    vidproc.wait()
                    del files[host]
                    assert os.path.isfile(newfilename), 'FFMPEG was unable to create the MP4 output file.'
                else:
                    files[host] = (vidproc, starttime)
    
    except Exception as ex:
        for host, (vidproc, starttime) in files.iteritems():
            vidproc.stdin.close()
            vidproc.wait()
            assert os.path.isfile(newfilename), 'FFMPEG was unable to create the MP4 output file.'
        raise


if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    main()


