#!/usr/bin/env python

import zmq
import io
from streamingbuffer import StreamingBuffer

class ZeroMqOutput(object):
    def __init__(self, socket, hostname, framesize=4096):
        self.socket = socket
        self.hostname = hostname
        self.framesize = framesize
        self.buffer = StreamingBuffer()
        self.started = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

    def write(self, s):
        # Add the incoming data to the buffer
        self.buffer.write(s)

        if not self.started:
            self.socket.send_multipart([self.hostname, 'START', ''])

        self.started = True

        while self.buffer.available >= self.framesize:
            self.socket.send_multipart([self.hostname, 'DATA', self.buffer.read(self.framesize)])
            
    def flush(self):
        if not self.started:
            return

        while self.buffer.available > self.framesize:
            self.socket.send_multipart([self.hostname, 'DATA', self.buffer.read(self.framesize)])

        self.socket.send_multipart([self.hostname, 'DATA', self.buffer.read()])

    def close(self):
        self.sockket.send_multipart([self.hostname, 'END', ''])
        self.started = False

