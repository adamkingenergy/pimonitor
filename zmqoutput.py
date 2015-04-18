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

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.socket.send_multipart([self.hostname, ''])

    def write(self, s):
        # Add the incoming data to the buffer
        self.buffer.write(s)

        while self.buffer.available >= self.framesize:
            self.socket.send_multipart([self.hostname, self.buffer.read(self.framesize)])
            
    def flush(self):
        while self.buffer.available > self.framesize:
            self.socket.send_multipart([self.hostname, self.buffer.read(self.framesize)])

        self.socket.send_multipart([self.hostname, self.buffer.read()])

