
import frame
import logic
import logic_client
import struct
import ctypes
from c2w.main.constants import ROOM_IDS
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Protocol

from twisted.internet import reactor
    
class client(object):
    
    movieList = []
    userList = []
    server_userList = []
    server_movieList = []
    movieroom_server_userList = []
    POSSIBLE_STATUS = {'DISCONNECTED':2,
                        'IN_MAIN_ROOM':ROOM_IDS.MAIN_ROOM,
                        'IN_MOVIE_ROOM':ROOM_IDS.MOVIE_ROOM,
                        'WAITING_FOR_USERLIST':3,
                        'WAITING_FOR_MOVIELIST':4,
                        'WAITING_FOR_ACK':5,
                        'DOING_NOTHING':6}
    movie_title_asking =""
    init_main = 0
    
    def __init__(self,clientProxy, protocolUsing = None, addr = None):
        
        self.clientProxy = clientProxy
        self.protocolUsing = protocolUsing
        self.addr = addr
        self.sequenceNumber = 0
        self.roomType = 0
        self.currentStatus =0
        self.userId = 0
        self.userName =""
        self.telegramme = ""
        
        self.timer = None
        self.timer_counter = 0
	
	self.timer_num_limit = 3
	self.delay = 2		# pour passer le test, faut qu'on ait un delai moins de 2
    
    def sendMessage(self,message):
        if self.timer_counter < self.timer_num_limit :
            self.protocolUsing.sendMessage(message)
            b = reactor.callLater(self.delay, self.sendMessage,message)
            self.timer = b
            self.timer_counter +=1

    
    def sendMessage_ack(self,message):
        print "--------------------------send message acki-------------------"
        self.protocolUsing.sendMessage(message)
    
    
    
    def setsequenceNumber(self,sequenceNumber):
        sequenceNumber +=1                                            
        sequenceNumber = sequenceNumber%256
        return sequenceNumber
    
    
    def sendLoginRequest(self, userName):
        login_message = logic_client.messageGenerator.generateLoginMessage(userName)
        print "---------------------Send message--------------------------------"
        
        
        self.timer_counter =0
        self.sendMessage(login_message)
        self.userName = userName
        
        self.sequenceNumber = self.setsequenceNumber(self.sequenceNumber)
        self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_ACK']
        
        print "--------------------launching timer------------------------------"
        
    
    def sendJoinRoomRequest(self, roomName):
        
        movieId = logic_client.logic_client.searchMovieIdByname(self.server_movieList,roomName)
        self.movie_title_asking = roomName
        room_request_message = logic_client.messageGenerator.generatejoinRoomMessage(movieId,self.roomType,self.sequenceNumber,self.userId)
        print "---------------------Sending room request message-----------------"
        
        
        self.timer_counter =0
        self.sendMessage(room_request_message)
        self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_ACK']
        
    def sendChatMessageOIE(self, message):
        print "roomType"+str(self.roomType)
        print "currentStatus"+str(self.currentStatus)
        if self.movie_title_asking =="":
            
            chat_message = logic_client.messageGenerator.generateChatMessage(message,self.sequenceNumber,self.userId,0,self.roomType)
        
        else :
            destinationId = logic_client.logic_client.searchMovieIdByname(self.server_movieList,self.movie_title_asking)
            chat_message = logic_client.messageGenerator.generateChatMessage(message,self.sequenceNumber,self.userId,destinationId,self.roomType)
        
        self.timer_counter =0
        print "chat message"+str(chat_message)
        self.sendMessage(chat_message)
        self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_ACK']

    def sendLeaveRoomMessage(self):
        
        
        self.timer_counter =0
        print "roomType"+str(self.roomType)
        leave_message = logic_client.messageGenerator.generateDisconnectionMessage(self.roomType, self.sequenceNumber,self.userId)
        self.sendMessage(leave_message)
        self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_ACK']    
               
            
    def testingFragmentation(self,datagram):
	print "-----------------------------Framing process------------------------------"
        
	print "received data: %r" % (datagram)
	self.telegramme = self.telegramme + datagram
	
	if len(self.telegramme) >= 6:	
            info = struct.unpack_from('!BBBBH', self.telegramme)
            dataLength = info [4]
            
            limit = dataLength + 6
            print 'limit:' + str(limit) 

            self.response = []
            while (len(self.telegramme) >= limit):
                print 'telegramme1 %r' % self.telegramme

                binary_Frame_receive = self.telegramme[:limit]  # True means framing statement
                self.receivedMessagetreatment(binary_Frame_receive)
                self.telegramme = self.telegramme[limit:]
                print 'Frame_receive = ' + str(binary_Frame_receive)
                print 'telegramme %r' % self.telegramme 
                
                if len(self.telegramme) >= 6:			    	
                    info = struct.unpack_from('!BBBBH', self.telegramme)
                    dataLength = info [4]
                    limit = dataLength + 6
                    print 'limit:' + str(limit)
                
                else:
                    break
            
    
    
    def receivedMessagetreatment(self,data):
        # Testing acknoledgment
        frame = logic.logic.binaryToObject(data)
        
        """ if the received message is not acknolegdment client has to do something"""

        if (logic_client.logic_client.receiveAck(frame.ack) == False):
            self.treatingNotAck(frame)
            
                
        elif (logic_client.logic_client.receiveAck(frame.ack) == True):
            self.treatingAck(frame)
            
    def treatingNotAck(self,frame):
        
        print "-------------------treating received message from the server----------------------"
        print"-------------------------Message is not ack ---------------------------------------"
            
            
        """now we test if it is a message coming from the server"""
        if frame.msgType == logic_client.logic_client.messageTypeDict['message']:
            self.notAckMessageTreatment(frame) 
            
            """ we test if it is a movielist coming from the server"""
        elif frame.msgType == logic_client.logic_client.messageTypeDict['movieList']:
            self.notAckMovieListTreament(frame)
            
            
        elif frame.msgType == logic_client.logic_client.messageTypeDict['userList']:
            self.notAckUserListTreament(frame)
            
            
        elif frame.msgType == logic_client.logic_client.messageTypeDict['messageForward']:
            print"-------------------------treating messageForward received----------------------"
        
        elif frame.msgType == logic_client.logic_client.messageTypeDict['privateChat']:
            print"-------------------------treating privatechat received--------------------------"
    
    def treatingAck(self, frame):

        print "-------------------------Acknowledge message received--------------------------"
        print "frame data"
        print frame.data
        if frame.msgType == logic_client.logic_client.messageTypeDict['login']:
            self.userId = frame.userId
            self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_MOVIELIST']
            print "timer is cancelled"
            self.timer.cancel()
        
        elif (frame.msgType == logic_client.logic_client.messageTypeDict['Room request'] )& (frame.roomType == 3) :
            print "------------------received movie request acknoledgement--------------------"
            print "frame roomType received"+str(frame.roomType)
            self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_USERLIST']
            self.roomType = 1
            print "frame data received"+str(frame.data)
            self.clientProxy.updateMovieAddressPort(self.movie_title_asking, frame.data[1], frame.data[0])
            self.timer.cancel()
            #self.handling_timer(self.timer)
            
        elif (frame.msgType == logic_client.logic_client.messageTypeDict['Room request'] )& (frame.roomType == 0) :
            
            
            print "frame roomType received"+str(frame.roomType)
            print "------------------received back to main room request acknoledgement--------------------"
            self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_USERLIST']
            self.roomType = 0
            self.timer.cancel()
            #self.handling_timer(self.timer)
            
        elif frame.msgType == logic_client.logic_client.messageTypeDict['message']:
            print "------------------received ack for previous sent message--------------------"
            self.timer.cancel()
            #self.handling_timer(self.timer)
            
        elif frame.msgType == logic_client.logic_client.messageTypeDict['leave_room']:
            print "------------------received ack for leaving application--------------------"
            #self.clientProxy.applicationQuit()
            self.clientProxy.leaveSystemOKONE()
            self.timer.cancel()
            #self.handling_timer(self.timer)
         
    def notAckMessageTreatment(self, frame ):
        
        print frame.destinationId
        userName = logic_client.logic_client.searchUserById(self.server_userList,frame.destinationId)
        print self.server_userList
        print"--------------------------receive message from-----------------------"
        print userName
        print "------------------------displaying  in the room-----------------------"
        self.clientProxy.chatMessageReceivedONE(userName,frame.data)
        message_ack = logic_client.logic_client.ack_message(frame.sequenceNumber,frame.msgType,frame.userId)
        print "------------------------acknoledge for received message in the room-----------------------"
        
        self.timer_counter =0
        self.sendMessage_ack(message_ack)
    
    def displayUserList(self,userList,movieTitle):
        
        for u in userList:
            print "userlist in display function   "+str(u)
            self.clientProxy.userUpdateReceivedONE(u[0], movieTitle)
        
    
    
    def notAckMovieListTreament(self, frame ):
        
        """ now we will retrieve the movieList sent by the server"""
        self.server_movieList = frame.data
        print "received movie List"+str(self.server_movieList)
        
        
        """ now we call a method to set the movie as desire by initcompleteone method"""
        self.movieList = logic_client.logic_client.movieListCient(frame.data)

        
        print "------------Received Movie list start Acknowledging --------------------------"
        
        """ we can acknoledge now the received movielist"""
        movieList_ack = logic_client.logic_client.ack_message(frame.sequenceNumber,frame.msgType,frame.userId)
        
        
        
        self.timer_counter =0
        """then we set the current satus of the user to waiting for user list """
        self.currentStatus = self.POSSIBLE_STATUS['WAITING_FOR_USERLIST']
        self.sendMessage_ack(movieList_ack)
    
    
    def notAckUserListTreament(self, frame ):
        print"-------------------------treating not room userList received----------------"
        print frame.roomType
        print self.roomType
        if frame.roomType == self.roomType  : #when receiving userlist for the first time roomtype must be 0
            if frame.roomType == 0:
                print"-------------------------treating main room userList received----------------"
                self.server_userList = frame.data
                self.userList = logic_client.logic_client.userListClient(frame.data)
                print "-------------------received userList start Acknowledging ---------------------"
                userList_ack = logic_client.logic_client.ack_message(frame.sequenceNumber,logic_client.logic_client.messageTypeDict['userList'],frame.userId)
                
                self.timer_counter =0
                self.sendMessage_ack(userList_ack)
                
                if self.currentStatus == self.POSSIBLE_STATUS['WAITING_FOR_USERLIST']:
                    if self.init_main == 0 :
                        self.clientProxy.initCompleteONE(self.userList, self.movieList)
                        self.currentStatus = self.POSSIBLE_STATUS['IN_MAIN_ROOM']
                        self.init_main = 1
                    else:
                        print "-----------------------back to main room------------------------------ "
                        print "userlist before back to main room"+str(frame.data)
                        self.userList = logic_client.logic_client.userListClient(frame.data)
                        print "userlist back to main room"+str(self.userList)
                        self.currentStatus = self.POSSIBLE_STATUS['IN_MAIN_ROOM']
                        self.clientProxy.setUserListONE(self.userList)
                        #self.displayUserList(self.userList,"MAIN_ROOM")
                        print "status"+str(self.currentStatus)
                        self.clientProxy.joinRoomOKONE()
                            
                            
                elif self.currentStatus == self.POSSIBLE_STATUS['IN_MAIN_ROOM']:
                    self.server_userList = frame.data
                    self.userList = logic_client.logic_client.userListClient(frame.data)
                    print "the user list updated in the main room is "+str(self.userList)
                    self.clientProxy.setUserListONE(self.userList)
        
            elif frame.roomType == 1:
            
                print"-------------------------treating movie room userList received----------------"
                self.server_userList = frame.data
                self.userList = logic_client.logic_client.userListClient(frame.data)
                
                print "-------------------received userList start Acknowledging ---------------------"
                userList_ack = logic_client.logic_client.ack_message(frame.sequenceNumber,logic_client.logic_client.messageTypeDict['userList'],frame.userId)
                
                self.timer_counter =0
                self.sendMessage_ack(userList_ack)
                
                if self.currentStatus == self.POSSIBLE_STATUS['WAITING_FOR_USERLIST']:
                    
                    print "join room ok one for me"
                    self.currentStatus = self.POSSIBLE_STATUS['IN_MOVIE_ROOM']
                    self.clientProxy.joinRoomOKONE()
                    self.displayUserList(self.userList,self.movie_title_asking)
                    
                            
                elif self.currentStatus == self.POSSIBLE_STATUS['IN_MOVIE_ROOM']:
                    print "displaying userlist"
                    print "userlist displayed"+str(self.userList)
                    
                    self.clientProxy.setUserListONE(self.userList)
                    self.displayUserList(self.userList,self.movie_title_asking)
            
            
        elif frame.roomType != self.roomType : 
            self.userList = logic_client.logic_client.userListClient(frame.data)
            userList_ack = logic_client.logic_client.ack_message(frame.sequenceNumber,logic_client.logic_client.messageTypeDict['userList'],frame.userId)    
            


        
