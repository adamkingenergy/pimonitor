#!/usr/bin/env python

# General modules
import sys
import zmq
import logging
import socket
import datetime

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

    files = {}

    try:
        while True:
            log.debug('Waiting to receive video publish.')
            host, flag, data = videosocket.recv_multipart()

            if flag == 'START':
                log.debug('START feed from %s', host)
                if host in files:
                    files[host].close()
                
                newfilename = '%s-%s.h264' % (host, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
                files[host] = open(newfilename, 'wb')

            elif flag == 'END':
                log.debug('END feed from %s', host)
                if host in files:
                    files[host].close()
 
            elif flag == 'DATA':
                if host in files:
                    files[host].write(data)
                    files[host].flush()
    
    except Exception as ex:
        for vidfile in files.itervalues():
            vidfile.close()
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



