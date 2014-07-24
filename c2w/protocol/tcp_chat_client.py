# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
import logic_client
import logic
import c2w.main.view
import clientClass

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')


class c2wTcpChatClientProtocol(Protocol):
    """
        On definit des variables qui seront mises a jour au fur et a mesure de notre potocool
    """

    global sequenceNumber
    global userId
    global destinationId
    def __init__(self, clientProxy, serverAddress, serverPort):
        """
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: serverAddress

            The IP address (or the name) of the c2w server.

        .. attribute:: serverPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
        
        self.serverAddress = serverAddress
        self.serverPort = serverPort
        self.clientProxy = clientProxy
        self.client = clientClass.client(self.clientProxy, self, (self.serverAddress,self.serverPort))
        
        
    def sendMessage(self, message):
        self.transport.write(message.raw)

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The controller calls this function as soon as the user clicks on
        the login button.
        """
        """
            On cree un header avec les parametres suivants frg ='0' ack ='0' rt ='11' ty='0000'
        """
        self.client.sendLoginRequest(userName)
        moduleLogger.debug('loginRequest called with username=%s', userName)
        
    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called **by the controller**  when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or to the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        self.client.sendChatMessageOIE(message)

    def sendJoinRoomRequestOIE(self, roomName):
        """
       
        :param roomName: The room name (or movie title.)

        Called **by the controller**  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        self.client.sendJoinRoomRequest(roomName)
        print "--------------------launching timer------------------------------"
        moduleLogger.debug('RoomRequest called with roomName=%s', roomName)

    def sendLeaveSystemRequestOIE(self):
        """
        Called **by the controller**  when the user
        has clicked on the leave button in the main room.
        """
        self.client.sendLeaveRoomMessage()

    def dataReceived(self, data):
        
        
        """
        :param data: The message received from the server
        :type data: A string of indeterminate length

        Twisted calls this method whenever new data is received on this
        connection.
        """
        print "----------------------------------Receiving tcp message-------------------------------"
        self.client.testingFragmentation(data)

        #problème de lose connection
        #self.transport.loseConnection()
                
