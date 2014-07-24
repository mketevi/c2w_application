#python
# -*- coding: utf-8 -*-

class frame:
    
    def __init__(self, fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength = 0, data = ""):
        self.fragment = fragment
        self.ack = ack
        self.msgType = msgType
        self.roomType = roomType
        self.sequenceNumber = sequenceNumber
        self.userId = userId
        self.destinationId = destinationId
        self.data = data
        if dataLength == 0:
            self.dataLength = len(data)
        else:
            self.dataLength = dataLength
    
    def getMsgType():
        return self.msgType
    
    def dataAppend(data):
        self.data = self.data + data
