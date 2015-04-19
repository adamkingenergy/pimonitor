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

    module_dir = os.path.dirname(__file__)

    network_config = config.load_from_file(os.path.join(module_dir, 'config/network.json'))
    camera_config = config.load_from_file(os.path.join(module_dir, 'config/camera.json'))
    recorder_config = config.load_from_file(os.path.join(module_dir, 'config/recorder.json'))

    eventport = network_config['event_pub_port']
    videoport = network_config['h264_pub_port']

    framerate = camera_config['framerate']

    cameraips = recorder_config['camera_ip_addrs']
    max_duration = recorder_config['max_duration']
    recording_folder = recorder_config['recording_folder']
    event_log = recorder_config['event_log']
    event_log_format = recorder_config['event_log_format']

    context = zmq.Context()

    eventsockets = []
    videosockets = []

    for cameraip in cameraips:
        log.info('Connecting to camera event feed: %s:%i.', cameraip, eventport)
        eventsocket = context.socket(zmq.SUB)
        eventsocket.connect('tcp://%s:%s' % (cameraip, eventport))
        eventsocket.setsockopt(zmq.SUBSCRIBE, '')
        eventsockets += [eventsocket]

        log.info('Connecting to camera video feed: %s:%i.', cameraip, videoport)
        videosocket = context.socket(zmq.SUB)
        videosocket.connect('tcp://%s:%s' % (cameraip, videoport))
        videosocket.setsockopt(zmq.SUBSCRIBE, '')
        videosockets += [videosocket]

    files = {}
    
    poller = zmq.Poller()
    for videosocket in videosockets:
        poller.register(videosocket, zmq.POLLIN)

    for eventsocket in eventsockets:
        poller.register(eventsocket, zmq.POLLIN)

    try:
        while True:
            socks = dict(poller.poll(5000))
            for sock, status in socks.iteritems():
                if sock in videosockets and status == zmq.POLLIN: 
                    host, data = sock.recv_multipart()
                
                    if host not in files:
                        # We're lacking a current output pipe for this host.
                        starttime = datetime.datetime.now()
                        date_folder = os.path.join(recording_folder, starttime.date().isoformat())
                        
                        try:
                            os.makedirs(date_folder)
                        except OSError as exception:
                            if exception.errno != errno.EEXIST:
                                raise
                        
                        vidfile = os.path.join(date_folder, '%s-%s.mp4' % (host, starttime.strftime("%Y%m%d-%H%M%S")))
                    
                        vidproc = Popen(['ffmpeg', '-f', 'h264', '-i', '-', '-codec', 'copy', '-r', '%i' % framerate, vidfile], stdin=PIPE)
                    else:
                        # Retrieve the video output pipe
                        vidproc, vidfile, starttime = files[host] 

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
                        closeout_video(files, host)
                    else:
                        files[host] = (vidproc, vidfile, starttime)

                elif sock in eventsockets and status == zmq.POLLIN:
                    host, event, time = sock.recv_multipart()
                    event_data = {'host': host, 'event': event, 'time': time}

                    # Write the event data to the log file.
                    with open(event_log, 'a+') as event_log_file:
                        event_log_file.write((event_log_format % event_data) + '\n')

                else:
                    # We've not received any data for a while, close off any files past their duration.
                    check_all_closeout_videos(files, max_duration)
                
    except Exception as ex:
        check_all_closeout_videos(files, max_duration)
        raise


def closeout_video(files, host):
    """Closeout the video file for the specified host.
    """
    vidproc, vidfile, starttime = files[host]
    vidproc.stdin.close()
    vidproc.wait()
    del files[host]
    assert os.path.isfile(vidfile), 'FFMPEG was unable to create the MP4 output file.'
    log.info('Closed out video file: %s', vidfile)
    

def check_all_closeout_videos(files, max_duration):
    """Close any videos which have exceeded the max duration.
    """
    for host, (vidproc, vidfile, starttime) in files.iteritems():
        if datetime.datetime.now() > starttime + datetime.timedelta(seconds=max_duration):
            closeout_video(files, host)


if __name__ == '__main__':

    # Setting up logging.
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Start the recorder.
    main()


