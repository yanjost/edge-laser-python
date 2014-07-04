from __future__ import print_function
import sys
import socket
import math
import struct
import itertools
import time

from construct import *
from construct import macros

import datetime

# HOST="192.168.1.29"
HOST="localhost"
PORT=4242

OneChar = Struct("OneChar", String("one",1))


def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk

def str_to_ord(s):
    return " ".join(str(ord(c)) for c in s)

class Socket(object):
    def __init__(self, socket):
        self.sock = socket
        self.internalbuffer = ""

    def bytesAvail(self):
        self.getFromSocket()
        return len(self.internalbuffer)

    def getFromSocket(self):
        tmp=None
        data=None
        try :
            data, address = self.sock.recvfrom(65535, socket.MSG_DONTWAIT)
            self.internalbuffer+=data
        except socket.error as exc:
            if exc.errno == 35:
                pass

        # if data:
        #     print("Got '{}' ({}) from socket, internal buffer '{}' ({})".format(data
        #                                                                         , str_to_ord(data)
        #                                                                         , self.internalbuffer
        #                                                                         , str_to_ord(self.internalbuffer))
        #     )

    def read(self, byteCount):
        buffer=''
        size=0
        while self.bytesAvail() < byteCount:
            pass

        buffer = self.internalbuffer[0:byteCount]
        self.internalbuffer=self.internalbuffer[byteCount:]
        # print("Buffer {}".format(self.internalbuffer))
        return buffer

    def peek(self, byteCount):
        buffer=''
        size=0
        while self.bytesAvail() < byteCount:
            pass

        buffer = self.internalbuffer[0:byteCount]
        return buffer


class AbstractCommand(object):
    def parse_type(self, data):
        parsed = OneChar.parse(data)

        # print ("Parsed : {}".format(parsed.one))

        return parsed.one

    def parse(self, socket, game):
        pass

class PlayerKeyCommand(AbstractCommand):

    def __init__(self):
        self.key = None
        self.player = None
        self.type = None


    def parse(self, socket, game):
        # print("Try to parse PlayerKey")
        if not self.parse_type(socket.peek(1)) == 'I' :
            return False

        # print("Parsed PlayerKey")

        socket.read(1)

        data = socket.read(2)

        packet = PlayerKeyPacket.parse(data)

        self.player1 = packet.player1
        self.player2 = packet.player2

        # print("Player {} key {}".format(self.player, self.key))
        # print("Player 1 {}".format(self.player1))
        # print("Player 2 {}".format(self.player2))

        game.player1_keys = self.player1
        game.player2_keys = self.player2

        return True

AckPacket = Struct("AckPacket",
                                   ULInt8("id"),
)

class AckCommand(AbstractCommand):



    def __init__(self):
        self.id = None

    def parse(self, socket, game):
        if not self.parse_type(socket.peek(1)) == 'A' :
            return False

        socket.read(1)

        data = socket.read(1)

        packet = AckPacket.parse(data)

        self.id = packet.id

        print("Game ID {}".format(self.id))

        game.gameid = self.id

        return True


class GoCommand(AbstractCommand):

    def parse(self, socket, game):
        if not self.parse_type(socket.peek(1)) == 'G' :
            return False

        # socket.read(2)
        socket.read(1)

        game.stopped = False

        return True

class StopCommand(AbstractCommand):

    def parse(self, socket, game):
        if not self.parse_type(socket.peek(1)) == 'S' :
            return False

        # socket.read(2)
        socket.read(1)

        game.stopped = True

        return True

HelloPacket = Struct("HelloPacket",
     Const(Bytes("id", 1), '\x00'),
     Magic('H'),
     macros.CString("gamename"),
)

LinePacket = Struct("LinePacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("L"),
    ULInt16("x1"),
    ULInt16("y1"),
    ULInt16("x2"),
    ULInt16("y2"),
    ULInt8("color"),
)

CirclePacket = Struct("CirclePacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("C"),
    ULInt16("x"),
    ULInt16("y"),
    ULInt16("diam"),
    ULInt8("color"),
)

RectPacket = Struct("RectPacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("D"),
    ULInt16("x1"),
    ULInt16("y1"),
    ULInt16("x2"),
    ULInt16("y2"),
    ULInt8("color"),
)

RefreshPacket = Struct("RefreshPacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("R"),
)

PausePacket = Struct("PausePacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("S"),
)

KinectPacket = Struct("KinectPacket",
    # Magic("C"),
    ULInt8("gameid"),
    Magic("K"),
)

PlayerKeyPacket = Struct("PlayerKeyPacket",
    # Magic("I"),
    BitStruct("player2",
              Flag("xp"),
              Flag("xn"),
              Flag("yp"),
              Flag("yn"),
              Flag("x"),
              Flag("y"),
              Flag("a"),
              Flag("b"),
              ),
    BitStruct("player1",
              Flag("xp"),
              Flag("xn"),
              Flag("yp"),
              Flag("yn"),
              Flag("x"),
              Flag("y"),
              Flag("a"),
              Flag("b"),
              ),
)


class LaserGame(object):
    HOST = '127.0.0.1'
    PORT = 4242

    def __init__(self,gamename):
        self.gameid = 0
        self.gamename = gamename
        self.sock = None
        self.stopped = True
        self.resolution = 65536
        self.multiplicator = 0.0
        self.color = LaserColor.LIME # Because it's REALLY awesome

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.connect((HOST, PORT))
        self.sock.setblocking(0)

        self.sendCmd(HelloPacket.build(Container(id='\x00', gamename=gamename)))

        self.socket = Socket(self.sock)
        self.player1_keys = None
        self.player2_keys = None


    def sendCmd(self, data):
        # print("Sending '{}'".format(str(data)))
        try:
            return self.sock.send(data)
        except Exception as e:
            print("Exception ignored in sendCmd: {}".format(e))

    def sendPacket(self, cls, **kwargs):
        # print("Sending {} {}".format(cls.name, ", ".join(["{}={}".format(k,v) for k,v in kwargs.iteritems()])))
        self.sendCmd(cls.build(Container(**kwargs)))

    def setResolution(self, px):
        self.resolution = px
        self.multiplicator = math.floor(65535.0/px);

        return self

    def setDefaultColor(self, color):
        self.color = color
        return self

    def setFrameRate(self,fps):
        self.fps=fps

    def newFrame(self):
        self.last_frame_start = datetime.datetime.now()

    def endFrame(self):
        try:
            time.sleep(1.0/self.fps-(datetime.datetime.now()-self.last_frame_start).total_seconds())
        except:
            pass

    def isStopped(self):
        return self.stopped

    def useKinect(self):
        self.sendPacket(KinectPacket, gameid=self.gameid)

    def receiveServerCommands(self):
        commands = []

        # print("Game id = {}".format(self.gameid))


        if not self.socket.bytesAvail():
            return commands

        for cls in [ PlayerKeyCommand, GoCommand, StopCommand, AckCommand ]:
            inst = cls()

            if inst.parse(self.socket, self):
                # print(str(inst))
                break

        return commands

    def liangbarsky(self, x1, y1, x2, y2):
        res = self.resolution
        dx = x2 - x1
        dy = y2 - y1
        dt0, dt1 = 0, 1
        c_x1 = x1; c_x2 = x2; c_y1 = y1; c_y2 = y2

        checks = ((-dx, x1 - 0),   # left
                 (dx, res - x1),   # right
                 (-dy, y1 - 0),  # top
                 (dy, res - y1))     # bottom

        for p, q in checks:
            if p == 0 and q < 0:
                return None, None, None, None
            if p != 0:
                dt = q / (p * 1.0)
                if p < 0:
                    if dt > dt1:
                        return None, None, None, None
                    dt0 = max(dt0, dt)
                else:
                    if dt < dt0:
                        return None, None, None, None
                    dt1 = min(dt1, dt)
        if dt0 > 0:
            c_x1 = x1 + dt0 * dx
            c_y1 = y1 + dt0 * dy
        if dt1 < 1:
            c_x2 = x1 + dt1 * dx
            c_y2 = y1 + dt1 * dy

        return c_x1, c_y1, c_x2, c_y2


    def addLine(self, x1, y1, x2, y2, color = None):
        m = self.multiplicator

        #make sure coordinates are in the correct range
        x1, y1, x2, y2 = self.liangbarsky(x1, y1, x2, y2)

        if x1 is not None:
            self.sendPacket(LinePacket, gameid=self.gameid, x1=x1*m, y1=y1*m, x2=x2*m, y2=y2*m, color=color or self.color)

        return self


    def addCircle(self, x, y, dim, color = None):
        m = self.multiplicator

        self.sendPacket(CirclePacket, gameid=self.gameid, x=x*m, y=y*m, diam=dim*m, color=color or self.color)

        return self


    def addRectangle(self, x1, y1, x2, y2, color = None):
        m = self.multiplicator

        # if completely outside, do nothing
        if ((x1 < 0) and (x2 < 0)) or ((y1 < 0) and (y2 < 0)) or \
              ((x1 > self.resolution - 1) and (x2 > self.resolution -1)) or \
              ((y1 > self.resolution - 1) and (y2 > self.resolution - 1)):
            return self

        # clip the rectangle if needed
        (x1, y1, x2, y2) = tuple(map(lambda i: min(max(i, 0), self.resolution - 1), [x1, y1, x2, y2]))

        self.sendPacket(RectPacket, gameid=self.gameid, x1=x1*m, y1=y1*m, x2=x2*m, y2=y2*m, color=color or self.color)

        return self

    def refresh(self):

        self.sendPacket(RefreshPacket, gameid=self.gameid)

        return self

    def pause(self):

        self.sendPacket(PausePacket, gameid=self.gameid)
        self.stopped = True

        return self



class LaserColor(object):
    RED = 0x1
    LIME = 0x2
    GREEN = 0x2
    YELLOW = 0x3
    BLUE = 0x4
    FUCHSIA = 0x5
    CYAN = 0x6
    WHITE = 0x7


class LaserFont(object):
    def __init__(self, file):
        self.letters = {}
        self.name = file.split('.')[0]
        zipdata = open(file, 'rb').read()
        zipdata = zipdata.decode('zlib').strip()
        header = True

        for data in zipdata.split('\0'):
            if header:
                self.spacing = struct.unpack('B', data[0])[0]
                header = False
            else:
                if len(data) == 0:
                    continue
                char = chr(struct.unpack('B', data[0])[0])
                coordlist = []
                for val in data[1:]:
                    coordlist.append(struct.unpack('B', val)[0])
                self.letters[char] = coordlist

    def render(self, game, text, x, y, color=LaserColor.LIME, coeff=1, spacing_factor=8):
        offset_x = x
        offset_y = y

        if coeff < 1:
            coeff = 1

        if coeff == 1:
            scaledletters = self.letters
        else:
            scaledletters = {}
            for char in self.letters.keys():
                scaledvals = []
                for val in self.letters[char]:
                    scaledvals.append(val * coeff)
                scaledletters[char] = scaledvals

        for char in text:
            tmp_offset = 0
            if char == ' ':
                tmp_offset = spacing_factor * coeff
            else:
                for line in grouper(4, scaledletters[char]):
                    game.addLine(line[0] + offset_x, line[1] + offset_y, line[2] + offset_x, line[3] + offset_y, color)
                    tmp_offset = max(tmp_offset, max(line[0], line[2]))
            offset_x += tmp_offset + self.spacing * coeff


if __name__ == '__main__':
    font = LaserFont('lcd.elfc')
    print('[EdgeLaser] loaded font %s' % font.name)
    print('[EdgeLaser] font spacing: %s' % font.spacing)
    print('[EdgeLaser] font contains %s chars' % len(font.letters))
