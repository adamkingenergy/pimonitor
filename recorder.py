#!/usr/bin/env python

# General modules
import zmq
import logging
import socket

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

    context = zmq.Context()
    log.info('Connecting to camera event feed: %s:%i.', cameraip, eventport)
    eventsocket = context.socket(zmq.SUB)
    eventsocket.connect('tcp://%s:%s' % (cameraip, eventport))
    eventsocket.setsockopt(zmq.SUBSCRIBE, '')

    log.info('Connecting to camera video feed: %s:%i.', cameraip, videoport)
    videosocket = context.socket(zmq.SUB)
    videosocket.connect('tcp://%s:%s' % (cameraip, videoport))
    videosocket.setsockopt(zmq.SUBSCRIBE, '')

    print eventsocket.recv()

    with open('test.h264', 'wb') as vidfile:    
        while True:
            vidfile.write(videosocket.recv())
            vidfile.flush()
    


if __name__ == '__main__':
    main()



