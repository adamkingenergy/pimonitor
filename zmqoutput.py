#!/usr/bin/env python

import zmq
import io
from streamingbuffer import StreamingBuffer

class ZeroMqOutput(object):
    def __init__(self, socket, framesize=4096):
        self.socket = socket
        self.framesize = framesize
        self.buffer = StreamingBuffer()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

    def write(self, s):
        # Add the incoming data to the buffer
        self.buffer.write(s)

        while self.buffer.available >= self.framesize:
            self.socket.send(self.buffer.read(self.framesize), zmq.SNDMORE)
            
    def flush(self):
        # Only use SNDMORE if we have strictly more data that framesize.
        # This leaves remaining data to be sent by final send (without SNDMORE)
        while self.buffer.available > self.framesize:
            self.socket.send(self.buffer.read(self.framesize), zmq.SNDMORE)

        self.socket.send(self.buffer.read())

