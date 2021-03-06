# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol

import logging
import frame
import logic
import ctypes
import struct
import time

from c2w.main.user import c2wUser
from c2w.main.user import c2wUserStore
from c2w.main.movie import c2wMovie
from c2w.main.movie import c2wMovieStore
from c2w.main.server_proxy import c2wServerProxy

from twisted.internet import reactor

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_server_protocol')


class c2wTcpChatServerProtocol(Protocol):

    def __init__(self, serverProxy, clientAddress, clientPort):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
    
	:param clientAddress: The IP address (or the name) of the c2w server,
	    given by the user.
    
        :param clientPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: clientAddress

            The IP address (or the name) of the c2w server.

        .. attribute:: clientPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.

        .. note::
            The IP address and port number of the client are provided
            only for the sake of completeness, you do not need to use
            them, as a TCP connection is already associated with only
            one client.
        """
        #self.buf
	################ global variable #######################self.new_userId = 0
	self.telegramme = ''
	self.sequenceNumber=0
        self.utilisateur = c2wUser(None,None,None,None) # nous permettra de recuperer les informations de lutilisateur courant
        self.UserMaxNumber = 255
	
	self.ReturnMainRoom = False
	self.MovieOpen = [False, 0]
	self.flag_broadcast = [False,0]	# by default roomId is 0 for main-room
	
	
	self.timer = None
	self.timer_counter = 0	#if it exceed num_limit, stop!! 
	self.timer_num_limit = 3
	
	self.delay = 2		# pour passer le test, faut qu'on ait un delai moins de 2
	
	
	################ variable of system ################
	self.clientAddress = clientAddress
	self.clientPort = clientPort
	self.serverProxy = serverProxy
	self.userStore = c2wUserStore()
	#self.communication = communication(serverProxy, self)

    def dataReceived(self, data):
        """
        :param data: The message received from the server
        :type data: A string of indeterminate length

        Twisted calls this method whenever new data is received on this
        connection.
        """
	print "-----------------------------Framing process------------------------------"
	print "received data: %r" % (data)
	self.telegramme = self.telegramme + data
	
	if len(self.telegramme) >= 6:	
	    info = struct.unpack_from('!BBBBH', self.telegramme)
	    dataLength = info [4]
	    
	    
	    limit = dataLength + 6
	    print 'limit:' + str(limit) 

	    self.response = []
	    while len(self.telegramme) >= limit:
		i = 0
		print 'telegramme1 %r' % self.telegramme

		Frame_receive = logic.logic.binaryToObject(self.telegramme)  # True means framing statement
		self.process_dataReceived(Frame_receive)
		self.telegramme = self.telegramme[limit:]
		print 'Frame_receive = ' + str(Frame_receive)
		print 'telegramme %r' % self.telegramme 

		if len(self.telegramme) >= 6:			    	
		    info = struct.unpack_from('!BBBBH', self.telegramme)
		    dataLength = info [4]
		    limit = dataLength + 6
		    print 'limit:' + str(limit)
		    
		else:
		    break
        
    def process_dataReceived(self, Frame_receive):	
	print "-----------------------------SERVER Receive data------------------------------"
        #Frame_receive = logic.logic.binaryToObject(datagram)
	
        #--------------------------------------Receive requete and return an ACK------------------------------------------"
	if Frame_receive.ack == 0:	                  #it needs an ACK
            print "---------------------------Receive a request no ACK------------------------------"
	    print "Received Message Type : "+ str(Frame_receive.msgType)
	    print "Received Message Data : "+ str(Frame_receive.data)
	    # ici, self est utilise pour propos d'appeler le ackFunDict. c'est la raison pourquoi on devra alors visuellement mettre en place self"
	    # le sequenceNumber of ACK egale toujour que trame d'aller
	    #********************************Login request********************************************
	    if Frame_receive.msgType == int('0000', 2):
		self.ACK_Login(Frame_receive)
		
	    #********************************Leave to Main Room Request**************************************
	    elif (Frame_receive.msgType == int('1000', 2)) & (Frame_receive.roomType == 00):
		print "*********************Leave to Main Room Request**********************"
		self.ACK_LeaveToMainRoom(Frame_receive)
	    
	    #********************************Room Request--Movie Room********************************************
	    elif (Frame_receive.msgType == int('1000', 2)) & (Frame_receive.roomType == 01):
		print "*********************Movie Room Request**********************"
		self.ACK_RoomRequest(Frame_receive)
		
	    #********************************Room Request--Private Room********************************************
	    elif (Frame_receive.msgType == int('1000', 2)) & (Frame_receive.roomType == 02):
		print "*********************Private Room Request**********************"
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		TCP_Instance = UserInstance.userChatInstance
		TCP_Instance.timer_counter[Frame_receive.userId] = 0
		self.Forward_PrivateChat_sign(Frame_receive)
		
	    #********************************Private Message send********************************************
	    elif Frame_receive.msgType == int('0001',2) | Frame_receive.roomType == 2:
		print "********************* Private Message send**********************"
		self.ACK_PrivateChat_msg(Frame_receive)
		
	    #********************************Broadcast Room Message send*************************************
	    elif Frame_receive.msgType == int('0001',2) | Frame_receive.roomType != 2:
		print "*********************Broadcast Room Message send**********************"
		self.ACK_RoomChatMessage(Frame_receive)
		self.BroadCast_Message(Frame_receive)
		
	    #********************************Message send********************************************
	    elif Frame_receive.msgType == int('1111',2):
		print "*********************Disconnection Request**********************"
		self.ACK_Disconnection(Frame_receive)
	    
	else:
	    print "-----------------------Receive an ACK and response------------------------------"
	    print "Received Message Type : "+ str(Frame_receive.msgType)
	    print "Received Message Data : "+ str(Frame_receive.data)
	    
	    
	    # ********************after Movie List ACK**********************************
	    if Frame_receive.msgType == int('0011', 2):
		print "********************after Movie List ACK**********************************"
		print "increment the seq num!!!"
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		TCP_Instance = UserInstance.userChatInstance

		
		TCP_Instance.sequenceNumber += 1
		print "ACK MovieList sequenceNumber: "+str(TCP_Instance.sequenceNumber)
		TCP_Instance.timer.cancel()
		
		TCP_Instance.timer_counter = 0
		self.sendUserList(Frame_receive.userId, self, 0) # 0 is main-room

	    # ********************after User List ACK**********************************	
	    elif Frame_receive.msgType == int('0101', 2):
		print "********************after User List ACK**********************************"
		print "increment the seq num!!!"
		
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		TCP_Instance = UserInstance.userChatInstance

		
		TCP_Instance.sequenceNumber += 1
		print "ACK UserList sequenceNumber: "+str(TCP_Instance.sequenceNumber)
		TCP_Instance.timer.cancel()
		
		if self.MovieOpen[0]:
		    MovieInstance = self.serverProxy.getMovieById(self.MovieOpen[1])
		    self.serverProxy.startStreamingMovie(MovieInstance.movieTitle)
		
		
		if self.flag_broadcast[0] == True:
		    print "begin the broadcast"
		    self.BroadCast_UserList(Frame_receive.userId, self.flag_broadcast[1])	# flag_broadcast[1] is roomId for userlist
		    
		    if self.MovieOpen[0]:
			self.BroadCast_UserList(Frame_receive.userId, 0)	# flag_broadcast[1] is roomId for userlist
		    
                    print "ReturnMainRoom" + str(self.ReturnMainRoom)  
                    if self.ReturnMainRoom:
			self.BroadCast_UserList(Frame_receive.userId, 0)
			
		    self.flag_broadcast[0] = False
		    self.flag_broadcast[1] = 0
		 
		self.ReturnMainRoom = False  
		self.MovieOpen = [False, 0]
		    
	    elif Frame_receive.msgType == int('1010', 2):
		print "********************after signalisation PrivateChat ACK**********************************"
		print "increment the seq num!!!"
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		TCP_Instance = UserInstance.userChatInstance

		
		TCP_Instance.sequenceNumber += 1
		print "ACK UserList sequenceNumber: "+str(TCP_Instance.sequenceNumber)
		
		TCP_Instance.timer.cancel()
		self.ACK_PrivateChat_sign(Frame_receive)
		
	    elif Frame_receive.msgType == int('1100', 2):
		print "********************after message PrivateChat ACK**********************************"
		print "increment the seq num!!!"
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		TCP_Instance = UserInstance.userChatInstance

		
		TCP_Instance.sequenceNumber += 1
		print "ACK UserList sequenceNumber: "+str(TCP_Instance.sequenceNumber)
		
		TCP_Instance.timer.cancel()
		
	    elif Frame_receive.msgType == int('0001', 2):
		print "********************after send-msg to destinataire ACK**********************************"
		print "increment the seq num!!!"
		
		UserInstance = self.serverProxy.getUserById(Frame_receive.userId)
		
		print "userId on this message is"+str(Frame_receive.userId)
		print "user Instance is "+str(UserInstance.userName)
		TCP_Instance = UserInstance.userChatInstance
		
		print "userchatInstance"+str(TCP_Instance)
		
		
		TCP_Instance.sequenceNumber += 1
		print "ACK UserList sequenceNumber: "+str(TCP_Instance.sequenceNumber)
		
		TCP_Instance.timer.cancel()
		
		
		
    
    def ACK_Login(self, Frame_receive):
        
        # 1  premier ACK destine au client
	print "----------------------ACK Login-------------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 3		                        # change the value of roomType to 11(binary)/3(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0
	destinationId = 0		# except Movie Room User list, Message broadcasted to a room, Private message, the others must be 
	
	flag = self.serverProxy.getUserByName(Frame_receive.data)
	
	if flag == None:    
	    sequenceNumber = Frame_receive.sequenceNumber
	    msgType = Frame_receive.msgType 
	    #print "distribution of New userId in condition of LoginIn et creation de l'utiisateur"
	    userId = self.serverProxy.addUser(Frame_receive.data, "MAIN_ROOM", self) # add the new user to the list
	    print ' the new userId is '+ str(userId)
	    self.sequenceNumber=0
	    # List of userStore
	    self.userStore.createAndAddUser(Frame_receive.data, "MAIN_ROOM",self,None,userId)
	    self.flag_broadcast[0] = True
	    self.flag_broadcast[1] = 0
	    
	    dataLength = 0		# in case of ACK, it's thought as zero
	
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    
	    # 2  l'envoi de Movie List
	    self.timer_counter = 0
	    self.sendMovieList(userId)
	    
	elif Frame_receive.sequenceNumber == 0:			# First ACK of Login is lost and resend the this ack
	    sequenceNumber = Frame_receive.sequenceNumber
	    msgType = Frame_receive.msgType 
	    #print "distribution of New userId in condition of LoginIn et creation de l'utiisateur"
	    userId = flag.userId
	    print ' the new userId is '+ str(userId)
	    self.sequenceNumber=0
	    # List of userStore
	    #self.userStore.createAndAddUser(Frame_receive.data, "MAIN_ROOM",None,None,userId)
	    #self.flag_broadcast[0] = True
	    #self.flag_broadcast[1] = 0
	    
	    dataLength = 0		# in case of ACK, it's thought as zero
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    
	    # 2  l'envoi de Movie List
	    self.timer.cancel()
	    self.timer_counter = 0
	    self.sendMovieList(userId)
	else:
	    sequenceNumber = 0			#  duplicate the UserName error
	    msgType = 14			#  error messageType
	    dataLength = 1
	    data = 6	# Invalid Message
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, Frame_receive.userId+1, destinationId, dataLength, data)
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
    
    def ACK_Disconnection(self,Frame_receive):
	
	
	
	print"-------------------------------------acknoledging disconnection----------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 3		                        # change the value of roomType to 11(binary)/3(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0
	
	for user in self.serverProxy.getUserList():
		if user.userId == Frame_receive.userId:
		    name_update = user.userName
		    break
		
	self.serverProxy.removeUser(name_update)
	
	#self.serverProxy.updateUserChatroom(name_update, "OUT_OF_THE_SYSTEM_ROOM")
	self.userStore.updateUserChatRoom(name_update, "OUT_OF_THE_SYSTEM_ROOM")
	
	#print "Rest of the UserList: ",self.serverProxy.getUserList()
	
	sequenceNumber = Frame_receive.sequenceNumber
	msgType = Frame_receive.msgType
	userId = Frame_receive.userId
	destinationId = 0
	dataLength = 0
	Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	   
	
	print "------------------Broadcast User list update--------------------"
	UserList = self.serverProxy.getUserList()
	new_userList = []
	
	
	print "------------------Broadcast User list in main room update--------------------"
	print "userList: " + str(UserList)
	
	for user in UserList:
	    if (user.userChatRoom == 'MAIN_ROOM'):
		new_userList.append(user)
		    
	print "len MainRoom_BroadCast" + str(new_userList)
	for user in new_userList:
	    UserInstance = self.serverProxy.getUserById(user.userId)
	    TCP_Instance = UserInstance.userChatInstance
		    
	    TCP_Instance.timer_counter = 0
	    self.sendUserList(user.userId ,user.userChatInstance, 0)
	
	
    
    
    
    
	
    def ACK_RoomRequest(self, Frame_receive):
        
        # 1  premier ACK destine au client
	print "----------------------ACK RoomRequest-------------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 3		                        # change the value of roomType to 11(binary)/3(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0

	Movie = self.serverProxy.getMovieById(Frame_receive.destinationId)
	print "destinationId"+str(Frame_receive.destinationId)
	 
	if Movie == None:
	    sequenceNumber = Frame_receive.sequenceNumber
	    msgType = 14		#error message  movieNumber is wrong
	    destinationId = 0
	    dataLength = 1
	    data = 6 		# Invalid Message 
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, Frame_receive.userId+1, destinationId, dataLength, data)
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    
	else:
	    self.MovieOpen = [True,Frame_receive.destinationId]
	    #Find the source UserName correspond to UserId in sake of using udateChatroom()
	    for user in self.serverProxy.getUserList():
		if user.userId == Frame_receive.userId:
		    name_update = user.userName
		    break
		
	    # modify(serverProxy) Room status of User to Movie_Room
	    self.serverProxy.updateUserChatroom(name_update, Movie.movieTitle)
	    print "userlist mis a jour dans le serveur proxy"+str(self.serverProxy.getUserList())
	    # modify(userStore) Ro+om status of User to certain Movie_Room Title
	    
	    
	    self.userStore.updateUserChatRoom(name_update, Movie.movieTitle)
	    print "movie Title"+str(Movie.movieTitle)
	    print "userlist mis a jour dans le user store"+str(self.userStore.getChatRoomUsersList(Movie.movieTitle))
	    self.flag_broadcast[0] = True
	    self.flag_broadcast[1] = Frame_receive.destinationId
	    
	    sequenceNumber = Frame_receive.sequenceNumber
	    msgType = Frame_receive.msgType
	    
	    #print "distribution of New userId in condition of LoginIn et creation de l'utiisateur"
	    userId = Frame_receive.userId
	    print 'movieIpAddress '+ str(Movie.movieIpAddress)
	    destinationId = Frame_receive.destinationId
	    data = [Movie.moviePort, Movie.movieIpAddress]
	    dataLength = 2+len(Movie.movieIpAddress)		# in case of ACK_RoomRequest, it has the content
	    
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength, data)
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    
	    # 2  l'envoi de Movie List
	    self.timer_counter = 0
	    self.sendUserList(userId ,self, destinationId)
	    
    def ACK_LeaveToMainRoom(self, Frame_receive):
	print "----------------------ACK_LeaveToMainRoom-------------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 0		                        # change the value of roomType to 11(binary)/3(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0
	
	for user in self.serverProxy.getUserList():
		if user.userId == Frame_receive.userId:
		    name_update = user.userName
		    stopStreamingMovie = user.userChatRoom
		    break
	Movie = self.serverProxy.getMovieByTitle(stopStreamingMovie)
        
        self.flag_broadcast[0] = True
	self.flag_broadcast[1] = Movie.movieId
        
	self.serverProxy.stopStreamingMovie(stopStreamingMovie)
	
	self.serverProxy.updateUserChatroom(name_update, "MAIN_ROOM")
	self.userStore.updateUserChatRoom(name_update, "MAIN_ROOM")
	sequenceNumber = Frame_receive.sequenceNumber
	msgType = Frame_receive.msgType
	userId = Frame_receive.userId
	destinationId = 0
	dataLength = 0
	Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	
	print "the server has sent for leaving room "+str(roomType)
	
	self.sendUserList(userId ,self, destinationId)
	self.ReturnMainRoom = True
	# 2  l'envoi de User List
	#self.timer_counter_List[userId] = 0
	
    def ACK_RoomChatMessage(self, Frame_receive):
        """
        :param Frame_receive: the payload after processing by binaryToObject
                              in logic.py
        :param host: the IP address of the source.
        :param port: the source port.
        
        called by datagramReceived when it receives a msgType 0001 Message
               or the roomType is not 02
        """ 
        print "----------------------ACK_RoomChatMessage-------------------------"
        ack = 1			        # change the value of ack to 1
        """ set the roomType to whatever the current room is
        """
        roomType = Frame_receive.roomType
        fragment = 0            # usually the ACK frame is too short to be cut, so it's always 0
        msgType = Frame_receive.msgType           
        sequenceNumber = Frame_receive.sequenceNumber
       
        userId = Frame_receive.userId
        destinationId = Frame_receive.destinationId
        dataLength = 0
        Frame_send = frame.frame(fragment, ack, msgType, roomType,
                                 sequenceNumber, userId, destinationId,
                                 dataLength)
	self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
    
    
	    
    def ACK_PrivateChat_sign(self, Frame_receive):
        
        # 1  premier ACK destine au client
	print "----------------------ACK_PrivateChat-------------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 2		                        # change the value of roomType to 10(binary)/1(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0

	UserInstance = self.serverProxy.getUserById(Frame_receive.destinationId)
	print "UserInstance"+str(UserInstance)
	TCP_Instance = UserInstance.userChatInstance

	sequenceNumber = Frame_receive.sequenceNumber
	msgType = 8
	    
	userId = Frame_receive.destinationId
	destinationId = Frame_receive.userId
	dataLength = 0
	    
	Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	TCP_Instance.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	
	    
    def ACK_PrivateChat_msg(self, Frame_receive):
        
        # 1  premier ACK destine au client
	print "----------------------ACK_PrivateChat-------------------------"
	ack = 1					        # change the value of ack to 1
	roomType = 2		                        # change the value of roomType to 10(binary)/1(decimal)  except Chat messages and user lists, all the others should be made 11
	fragment = 0		                        # usually the ACK frame is too short to be cut, so it's always 0

	sequenceNumber = Frame_receive.sequenceNumber
	msgType = Frame_receive.msgType
	    
	userId = Frame_receive.userId
	destinationId = Frame_receive.destinationId
	dataLength = 0
	    
	Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
	self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	
	self.Forward_PrivateChat_msg(Frame_receive)
	
    
	


    def sendMovieList(self, userId):
	
	UserInstance = self.serverProxy.getUserById(userId)
	print "UserInstance"+str(UserInstance)
		
	TCP_Instance = UserInstance.userChatInstance
	
	if TCP_Instance.timer_counter< self.timer_num_limit:
	    
	    print "------------------sending Movie list data to the client--------------------"
	    MovieList = self.serverProxy.getMovieList()
	    fragment = 0
	    ack = 0
	    msgType = 3
	    roomType = 3
	    data = []
	    
	    dataLength = 0
	    roomId=1
	    for movie in MovieList:
		nameLength = len(movie.movieTitle)
		data.append([nameLength, movie.movieId, movie.movieTitle])
		dataLength = dataLength + 2 + nameLength
	    
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, 0, userId, 0, dataLength, data)	# sequenceNumber = 0
	    self.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    
	    
	    a = reactor.callLater(self.delay, self.sendMovieList, userId)
	    TCP_Instance.timer = a
	    TCP_Instance.timer_counter += 1
	
	
	
	
    def sendUserList(self , userId, userChatInstance, RoomId):
	
	
	if userChatInstance.timer_counter< self.timer_num_limit:
	    print "------------------sending User list data to the client--------------------"
	    
	    fragment = 0
	    ack = 0
	    msgType = 5
	    
	    if  RoomId == 0:
		
		#UserList = self.userStore.getChatRoomUsersList("MAIN_ROOM")
		UserList = self.serverProxy.getUserList()
		destinationId=0
		roomType = 0   		# at the moment, roomtype is 00 for main room
		data = []
		
		dataLength = 0
		for user in UserList:
		    print "userAddress" + str(user.userAddress)
		    nameLength = len(user.userName)
		    data.append([nameLength, user.userId , user.userChatRoom,  user.userName])
		    dataLength = dataLength + 3 + nameLength
	    else:
		Movie= self.serverProxy.getMovieById(RoomId)
		print "MovieIP: "+ Movie.movieIpAddress
		UserList_global = self.serverProxy.getUserList()
		UserList = []
		for user in UserList_global:
		    if user.userChatRoom == Movie.movieTitle:
			UserList.append(user)
		
		
		#UserList = self.userStore.getChatRoomUsersList(Movie.movieTitle)
		
		destinationId=RoomId
		roomType = 1   		# at the moment, roomtype is 01 for movie room
		data = []
		
		dataLength = 0
		for user in UserList:
		    print "user" + str(user)
		    nameLength = len(user.userName)
		    data.append([nameLength, user.userId, user.userChatRoom , user.userName])
		    dataLength = dataLength + 3 + nameLength	

	    TCP_Instance = userChatInstance
	    
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, TCP_Instance.sequenceNumber, userId, destinationId, dataLength, data)
	    TCP_Instance.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    a = reactor.callLater(self.delay, self.sendUserList ,userId, userChatInstance,RoomId)
	    
	    userChatInstance.timer = a
	    userChatInstance.timer_counter += 1
    
    def BroadCast_UserList(self, userId, RoomId):
	print "------------------Broadcast User list update--------------------"
	UserList = self.serverProxy.getUserList()
	new_userList = []
	
	if RoomId == 0:
	    print "------------------Broadcast User list in main room update--------------------"
	    print "userList: " + str(UserList)
	    if len(UserList) > 1:
		for user in UserList:
		    if (user.userChatRoom == 'MAIN_ROOM') & (user.userId != userId):
			new_userList.append(user)
		    
		print "len MainRoom_BroadCast" + str(new_userList)
		for user in new_userList:
		    UserInstance = self.serverProxy.getUserById(user.userId)
		    TCP_Instance = UserInstance.userChatInstance
		    
		    TCP_Instance.timer_counter = 0
		    self.sendUserList(user.userId ,user.userChatInstance, RoomId)
	    else:
		print "No BroadCast"
		
	else:	# Movie Room update UserList
	    print "------------------Broadcast User list in movie room update--------------------"
	    print "userList: " + str(UserList)
	    Movie = self.serverProxy.getMovieById(RoomId)	
	    if len(UserList) > 1:
		for user in UserList:
		    if (user.userChatRoom == Movie.movieTitle) & (user.userId != userId):
			new_userList.append(user)
		    
		print "len MovieRoom_BroadCast: " + str(new_userList)
		print "MovieTitle"+ Movie.movieTitle
		for user in new_userList:
		    UserInstance = self.serverProxy.getUserById(user.userId)
		    TCP_Instance = UserInstance.userChatInstance
		    
		    TCP_Instance.timer_counter = 0
		    self.sendUserList(user.userId ,user.userChatInstance, RoomId)
		
	    else:
		print "No BroadCast"
		
    def Send_msg( self , Frame_receive, finishId):			# msg-type is 0001
        
	UserInstance = self.serverProxy.getUserById(finishId)
	
	print "UserInstance"+str(UserInstance.userName)
		
	TCP_Instance = UserInstance.userChatInstance
	
	if TCP_Instance.timer_counter< self.timer_num_limit:
	    print "----------------------Send_msg one to one-------------------------"
    	    RoomId = Frame_receive.destinationId
	    
	    if RoomId == 0:
	        roomType = 00
	    else:
		roomType = 01
		    
	    fragment = 0
	    
	    ack = 0
	    msgType = 1  #0001  0x01
	    userId = finishId
	    
	    sequenceNumber = TCP_Instance.sequenceNumber
	    destinationId = Frame_receive.userId
	    dataLength = Frame_receive.dataLength
	    data = Frame_receive.data
		       
	    Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength, data)
	    TCP_Instance.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
	    a = reactor.callLater(self.delay, self.Send_msg, Frame_receive, finishId)
	    TCP_Instance.timer = a
	    TCP_Instance.timer_counter += 1
		
    def BroadCast_Message(self, Frame_receive):
	print "------------------Broadcast Message update--------------------"
	UserList = self.serverProxy.getUserList()
	new_userList = []
	RoomId = Frame_receive.destinationId
	userId = Frame_receive.userId
	
	if RoomId == 0:
	    print "userList: " + str(UserList)
	    if len(UserList) > 1:
		for user in UserList:
		    if (user.userChatRoom == 'MAIN_ROOM') & (user.userId != userId):
			new_userList.append(user)
		    
		print "len MainRoom_BroadCast" + str(new_userList)
	    else:
		print "No BroadCast"
		
	else:	# Movie Room update UserList
	    print "userList: " + str(UserList)
	    Movie = self.serverProxy.getMovieById(RoomId)	
	    if len(UserList) > 1:
		for user in UserList:
		    if (user.userChatRoom == Movie.movieTitle) & (user.userId != userId):
			new_userList.append(user)
		    
		print "len MovieRoom_BroadCast: " + str(new_userList)
		print "MovieTitle"+ Movie.movieTitle
	    else:
		print "No BroadCast"
	    
	for user in new_userList:
	    UserInstance = self.serverProxy.getUserById(user.userId)
	    TCP_Instance = UserInstance.userChatInstance
	    
	    TCP_Instance.timer_counter = 0
	    self.Send_msg(Frame_receive, user.userId)


	def Forward_PrivateChat_sign(self, Frame_receive):			# msg-type is 1010
	    UserInstance = self.serverProxy.getUserById(Frame_receive.destinationId)
	    TCP_Instance = UserInstance.userChatInstance
	    
	    
	    if TCP_Instance.timer_counter< self.timer_num_limit:
		print "----------------------Forward_PrivateChat-------------------------"
		
		roomType = 2
		fragment = 0
		
		
		ack = 0
		msgType = 10
		userId = Frame_receive.destinationId
		
		sequenceNumber = TCP_Instance.sequenceNumber
		destinationId = Frame_receive.userId
		dataLength = 0
		    
		    
		Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength)
		TCP_Instance.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
		a = reactor.callLater(self.delay, self.Forward_PrivateChat, Frame_receive)
		TCP_Instance.timer = a
		TCP_Instance.timer_counter += 1
		
	def Forward_PrivateChat_msg(self, Frame_receive):			# msg-type is 1100
	    
	    UserInstance = self.serverProxy.getUserById(Frame_receive.destinationId)
	    print "UserInstance"+str(UserInstance)
		
	    TCP_Instance = UserInstance.userChatInstance

	    
	    if TCP_Instance.timer_counter[userId]< self.timer_num_limit:
		print "----------------------Forward_PrivateChat-------------------------"
		
		roomType = 2
		fragment = 0
		
		ack = 0
		msgType = 12  #1100  0x0c
		userId = Frame_receive.destinationId
		sequenceNumber = TCP_Instance.sequenceNumber
		
		
		
		destinationId = Frame_receive.userId
		dataLength = Frame_receive.dataLength
		data = Frame_receive.data
		    
		    
		Frame_send = frame.frame(fragment, ack, msgType, roomType, sequenceNumber, userId, destinationId, dataLength, data)
		
		TCP_Instance.transport.write(logic.logic.ObjectToBinary(Frame_send, "TCP"))
		a = reactor.callLater(self.delay, self.Forward_PrivateChat, Frame_receive)
		TCP_Instance.timer= a
		TCP_Instance.timer_counter += 1
