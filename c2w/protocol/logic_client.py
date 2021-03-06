#python
# -*- coding: utf-8 -*-
import frame
import logic
import struct
import ctypes
from c2w.main.constants import ROOM_IDS


class logic_client:
    messageTypeDict = {
    'login'                     :0b0000,
    'message'                   :0b0001,
    'movieList'                 :0b0011,
    'userList'                  :0b0101,
    'messageForward'            :0b1100,
    'privateChat'               :0b1010,
    'ayt'                       :0b0110,
    'error'                     :0b1110,
    'Room request'              :0b1000,
    'leave_room'                :0b1111
    }
    

    @classmethod
    def receiveAck(cls, ack):
        result = False
        if ack == 1 :
            result = True
            
        return result

    @classmethod       
    def ack_message(cls,sequenceNumber, msgType,userId):
        Frame = frame.frame(0,1,msgType,3,sequenceNumber,userId,0,0,"")
        ack_message = logic.logic.ObjectToBinary(Frame)
        return ack_message

            
    @classmethod
    def movieListCient(cls,movieList):
        new_movieList = []
        for m in movieList:
            #self.clientProxy.updateMovieAddressPort(m[1], '0.0.0.1', '8080')
            new_movieList+= [(m[1],'245.0.0.1', '8080'),]
        return new_movieList
    
    @classmethod
    def userListClient(cls, userList):
        print "logic client treating userList received"
        print "userlist recu avant traitment"+str(userList)
        new_userList = []
        for u in userList:
            
            
            if u[2] == 0 :
                new_userList += [(u[1],ROOM_IDS.MAIN_ROOM)]
            elif u[2] == 1 :
                new_userList += [(u[1],ROOM_IDS.MOVIE_ROOM)]
        print "new_userlist"+str(new_userList)
        return new_userList
    
    @classmethod
    def searchMovieIdByname(cls,movieList,roomName):
        movieId = 1000
        for m in movieList:
            if m[1] == roomName :
                movieId = m[0]
        return movieId
    
    
    @classmethod
    def searchUserById(cls,userList,userId):
        userName=""
        for u in userList:
            if u[0] == userId :
                userName = u[1]
        return userName

class messageGenerator:
    
    
    @classmethod
    def generateLoginMessage(cls, userName):
        messageType = 0
        data_length     = len(userName)
        Frame = frame.frame(0,0,0,3,0,0,0,data_length,userName)
        login_message = logic.logic.ObjectToBinary(Frame)
        
        return login_message
    
    @classmethod
    def generateDisconnectionMessage(cls,roomType,sequenceNumber,userId):
        
        Frame = frame.frame(0,0,logic_client.messageTypeDict['leave_room'],roomType,sequenceNumber,userId, 0, 0,"" )
            
        leave_message = logic.logic.ObjectToBinary(Frame)
        
        return leave_message
    
    @classmethod
    def generatejoinRoomMessage(cls,movieId,roomType,sequenceNumber,userId):
        
        if roomType == 0:
            Frame = frame.frame(0,0,logic_client.messageTypeDict['Room request'],1,sequenceNumber,userId,movieId,0,"")
        
        elif roomType == 1:
            Frame = frame.frame(0,0,logic_client.messageTypeDict['Room request'],0,sequenceNumber,userId,0,0,"")
        
        join_room = logic.logic.ObjectToBinary(Frame)
        
        return join_room

    @classmethod
    def generateChatMessage(cls,message,sequenceNumber,userId,destinationId,roomType):
        
        if roomType == 0:
            Frame = frame.frame(0,0,logic_client.messageTypeDict['message'],roomType,sequenceNumber,userId,0,len(message),message)
            
        elif roomType == 1:
            
            Frame = frame.frame(0,0,logic_client.messageTypeDict['message'],roomType,sequenceNumber,userId,destinationId,len(message),message)
        
        chat_message = logic.logic.ObjectToBinary(Frame)
        return chat_message
    


