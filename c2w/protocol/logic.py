#python
# -*- coding: utf-8 -*-
import frame
import struct
import ctypes
from c2w.main.constants import ROOM_IDS

class logic:
        
    def getLoginData( stream, dataLength):
        print "-------------getLoginData-------------------"
        if dataLength != 0:
            offset = 6
            return struct.unpack_from( '!%ss'% (str(dataLength)), stream, offset)[0]
        else:
            return ''

    def getDisconnectionData( stream, dataLength):
	
	return  ""

    def getMessageData( stream, dataLength ):
        print "-------------getMessageData-------------------"
        if dataLength != 0:
            offset = 6
            return struct.unpack_from( '!%ss'% (str(dataLength)), stream, offset)[0]
        else:
            return ''
    

    def getRoomRequestData(stream, dataLength):
        print "-------------getRoomRequestData-------------------"
        if dataLength != 0:
            offset = 6
            return struct.unpack_from( '!H%ss'% (str(dataLength-2)), stream, offset)
        else:
            return ''
            

    def getLeavePrivateChatData( stream, dataLength):
        pass
    

    def getMovieListData( stream, dataLength):
        print "-------------getMovieListData-------------------"
        movieList = []
        print "dataLength:"+ str(dataLength)
        offset = 6
        while(offset < dataLength+6):
            nameLength = struct.unpack_from( '!B', stream, offset)[0]
            roomId = struct.unpack_from( '!B', stream, offset + 1)[0]
            title =struct.unpack_from( '!%ss'% (str(nameLength)), stream, offset + 2)[0]
            offset += nameLength + 2
            movieList.append([roomId, title])
        
        print "movieList"+ str(movieList)
        return movieList
    

    def getUserListData( stream, dataLength):
        
        print "-------------getUserListData-------------------"
        userList = []
        offset = 6
        while(offset < dataLength+6):
            nameLength = struct.unpack_from( '!B', stream, offset)[0]
            userId = struct.unpack_from( '!B', stream, offset + 1)[0]
            status_int = struct.unpack_from( '!B', stream, offset + 2)[0] #1000000 128 / 0000000  0
            if(status_int == 128):
                status = 1	# v=integer value of MOVIE_ROOM
            else:
                status = 0	# v=integer value of MAIN_ROOM
            name =struct.unpack_from( '!%ss'% (str(nameLength)), stream, offset + 3)[0]
            offset += nameLength + 3
            userList.append([userId, name, status])
        
        
        return userList
    

    def getPrivateChatData(stream, dataLength):
        print "-------------getErrorData-------------------"
        if dataLength != 0:
            offset = 6
            return struct.unpack_from( '!%ss'% (str(nameLength)), stream, offset)[0]
        else:
            return ''
        
    def getLeavePrivateChatRequestForwardData( stream, dataLength):
        pass
    

    def getAYTData( stream, dataLength):
        pass
    

    def getErrorData(stream, dataLength):
        print "-------------getErrorData-------------------"
        if dataLength != 0:
            offset = 6
            return struct.unpack_from( '!B', stream, offset)[0]
        else:
            return ''
        

####################################################################################
    def sendLoginData(dataLength, data, buf):
        print "-------------sendLoginData-------------------"
        print "data:"+data
        if dataLength != 0:
            offset = 6
            struct.pack_into( '!%ss'% (str(dataLength)), buf, offset, data)
        else:
            buf = buf
        return buf

    def sendDisconnectionData(dataLength, data, buf):
	return buf
	

    def sendMessageData(dataLength, data, buf):
        print "-------------sendMessageData-------------------"
        print "data:"+data
        if dataLength != 0:
            offset = 6
            struct.pack_into( '!%ss'% (str(dataLength)), buf, offset, data)
        else:
            buf = buf
        return buf
    

    def sendRoomRequestData(dataLength, data, buf):
	print "-------------sendRoomRequestData-------------------"
        print "data:"+ str(data)
        print "dataLength" +str(dataLength)
	if dataLength == 0:
            pass
        else:
            struct.pack_into( '!H%ss'% (str(dataLength-2)), buf, 6, data[0], data[1])
            result = logic.binaryToObject(buf)
        return  buf
    

    def sendLeavePrivateChatData(dataLength, data, buf):
        pass
    

    def sendMovieListData(dataLength, data, buf):
        #struct.pack_into('BBBBH%ss'% dataLength, buf, 0, firstByte, sequenceNumber, userId, destinationId, dataLength)
        print "-----------------------sendMovieListData-----------------------------"
        offset = 6
        
        for movie in data:
            nameLength = movie[0]
           
            struct.pack_into('!BB%ss'% (str(nameLength)), buf, offset, nameLength, movie[1], movie[2])
            offset = offset + 2 + nameLength
        
        print 'data' + buf.raw
        
        return buf
    
    
    def sendUserListData(dataLength, data, buf):
        print "-----------------------sendUserListData-----------------------------"
        offset = 6
        
        for user in data:
            nameLength = user[0]
            if user[2]=='MAIN_ROOM':
                Reserve = 0
            else:
                Reserve = 128
            struct.pack_into('!BBB%ss'% (str(nameLength)), buf, offset, nameLength, user[1], Reserve, user[3])
            offset = offset + 3 + nameLength
        
        print 'data' + buf.raw
        
        return buf
    

    def sendPrivateChatData(dataLength, data, buf):
        print "-----------------------sendPrivateChatData-----------------------------"
        if dataLength != 0:
            offset = 6
            struct.pack_into('!%ss'% (str(nameLength)), buf, offset, data)
        else:
            buf = buf
        return buf
    

    def sendLeavePrivateChatRequestForwardData(dataLength, data, buf):
        pass
    

    def sendAYTData(dataLength, data, buf):
        pass
    

    def sendErrorData(dataLength,data, buf):
        print "-------------sendErrorData-------------------"
        print "data:"+str(data)
        if dataLength != 0:
            offset = 6
            struct.pack_into('!B', buf, offset, data)
        else:
            buf = buf
        return buf
        
####################################################################################

    
    dataFunDict_get = {
        int('0000', 2) : getLoginData,
        int('1111', 2) : getDisconnectionData,
        int('0001', 2) : getMessageData,
        int('1000', 2) : getRoomRequestData,
        int('0111', 2) : getLeavePrivateChatData,
        int('0011', 2) : getMovieListData,
        int('0101', 2) : getUserListData,
        int('1100', 2) : getMessageData,
        int('1010', 2) : getPrivateChatData,
        int('1001', 2) : getLeavePrivateChatRequestForwardData,
        int('0110', 2) : getAYTData,
        int('1110', 2) : getErrorData,
    }
    
    dataFunDict_send = {
        int('0000', 2) : sendLoginData,
        int('1111', 2) : sendDisconnectionData,
        int('0001', 2) : sendMessageData,
        int('1000', 2) : sendRoomRequestData,
        int('0111', 2) : sendLeavePrivateChatData,
        int('0011', 2) : sendMovieListData,
        int('0101', 2) : sendUserListData,
        int('1100', 2) : sendMessageData,
        int('1010', 2) : sendPrivateChatData,
        int('1001', 2) : sendLeavePrivateChatRequestForwardData,
        int('0110', 2) : sendAYTData,
        int('1110', 2) : sendErrorData,
    }
    
    

    @classmethod
    def ObjectToBinary(cls, Frame, Mode = "UDP"):
        
        firstByte 	= (Frame.fragment<<7) + (Frame.ack<<6) + (Frame.msgType<<2) + (Frame.roomType)
        print "--------------------------Objet to binary------------------------------------"
          
        sequenceNumber  = Frame.sequenceNumber
        userId 		= Frame.userId
        destinationId   = Frame.destinationId
        dataLength 	= Frame.dataLength
        data = Frame.data
        
        print "Frame.msgType: "+ str(Frame.msgType)
        print "Frame.roomType: "+ str(Frame.roomType)
        
        print "firstByte:"+str(firstByte)
        print "Frame.sequenceNumber: "+ str(sequenceNumber)
        print "Frame.userId: "+ str(userId)
        print "Frame.destinationId: "+ str(destinationId)
        print "Frame.DataLength: "+ str(dataLength)
        print "Frame_data: "+ str(Frame.data)
        
        
        
        buf = ctypes.create_string_buffer(6 + dataLength)
        struct.pack_into('!BBBBH', buf, 0, firstByte, sequenceNumber, userId, destinationId, dataLength)
        
        if Frame.ack == 0 :
            buf = cls.dataFunDict_send[Frame.msgType](dataLength, data, buf)

        elif (Frame.ack == 1) & (Frame.msgType == 14):
	    buf = cls.dataFunDict_send[Frame.msgType](dataLength, data, buf)
            
        elif (Frame.ack == 1) & (Frame.msgType == 8):
	    buf = cls.dataFunDict_send[Frame.msgType](dataLength, data, buf)
            
        if Mode == "UDP":
            return buf
        else:
            return buf.raw

    @classmethod
    def binaryToObject(cls, stream):
        
        print "--------------------Binary to objet---------------------------"
        info = struct.unpack_from('!BBBBH', stream)
        firstByte = info[0]
        sequenceNumber = info[1]
        userId = info[2]
        destinationId = info[3]
        dataLength = info [4]
        #objectTotal = struct.unpack_from('BBBBH'+str(dataLength)+'s', stream)
	#data = objectTotal[5]
	print "sequenceNumber: "+ str(sequenceNumber)
        #Treating the first byte to get info
        print "firstByte:"+str(firstByte)
        fragment = firstByte >> 7
        print "fragmentation:"+str(fragment)
        
        workingByte = firstByte - (fragment << 7)        
        
        ack = workingByte >> 6
        
        print "ack:"+str(ack)
        workingByte = workingByte - (ack << 6)
        
        msgType = workingByte >> 2
        print "msgType:"+str(msgType)
        
        workingByte = workingByte - (msgType << 2)
        
        roomType = workingByte
        print "roomType:"+str(roomType)
        
        #getting the data
        print "dataLength:"+str(dataLength)
        
        if (dataLength > 0) & (ack == 0):
            data = cls.dataFunDict_get[msgType](stream, dataLength)
        elif (dataLength > 0) & (ack == 1) & (msgType == 14) :
            data = cls.dataFunDict_get[msgType](stream, dataLength)
        elif (dataLength > 0) & (ack == 1) & (msgType == 8) :
            data = cls.dataFunDict_get[msgType](stream, dataLength)
        else:
            data = ''
        
        print "UserID: "+ str (userId)
        print "Data: "+ str(data)
    
	# composer un trame en condition que frame est deja importe
        Frame = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength, data)
        
        return Frame
    
    
    
