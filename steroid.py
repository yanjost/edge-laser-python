import EdgeLaser
import time
import math

game = EdgeLaser.LaserGame('Steroid')

game.setResolution(1000).setDefaultColor(EdgeLaser.LaserColor.LIME)

game.setFrameRate(20)

coeff = 0

posx = 450

posy = 450

class Vector(object):
    def __init__(self, angle,value):
        self.angle=angle
        self.value=value

    def apply(self,x,y):
        vx,vy=apply_rot(self.angle,self.value,0.0)
        return x+vx,y+vy


class GameObject(object):
    def __init__(self):
        self.x=0
        self.y=0
        self.angle=0.0

def apply_rot(angle,x,y):
    return x*math.cos(angle)-y*math.sin(angle) , x*math.sin(angle)+y*math.cos(angle)


def apply_trans(obj,x,y):
    return obj.x+x,obj.y+y

class Player(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        self.width=100
        self.speed_vector=Vector(self.angle,0.0)
        self.booster = False

    def draw(self, game):
        p1=(-self.width/5,0)
        p2=(self.width/5,0)
        p3=(0,-self.width/2)

        p1=apply_rot(self.angle,*p1)
        p2=apply_rot(self.angle,*p2)
        p3=apply_rot(self.angle,*p3)

        # print(p1)

        p1=apply_trans(self,*p1)
        p2=apply_trans(self,*p2)
        p3=apply_trans(self,*p3)

        game.addLine(p1[0],p1[1],p2[0],p2[1])
        game.addLine(p2[0],p2[1],p3[0],p3[1])
        game.addLine(p3[0],p3[1],p1[0],p1[1])
        # game.addLine(*p2,*p3)
        # game.addLine(*p3,*p1)

    def apply_movement(self):
        if self.booster:
            print("ACCELERATE")
            self.speed_vector.value=5
            self.speed_vector.angle=self.angle-math.pi/2
            print(self.speed_vector.angle)
            self.x,self.y=self.speed_vector.apply(self.x,self.y)





while game.isStopped():
    game.receiveServerCommands()
    time.sleep(0.5)


player1 = Player()
player1.x=500
player1.y=500

dangle=0.1


while not game.isStopped():

    game.newFrame()

    game.receiveServerCommands()

    # for cmd in commands:

    if game.player1_keys:
        if game.player1_keys.yp  :
            player1.y-=5
        if game.player1_keys.xn :
            # player1.x-=5
            player1.angle-=dangle
        if game.player1_keys.yn :
            player1.y+=5
        if game.player1_keys.xp :
            # player1.x+=5
            player1.angle+=dangle

        player1.booster = game.player1_keys.a

    # print(player1.angle)

    player1.apply_movement()

    player1.draw(game)

    game.refresh()

    # time.sleep(0.05)
    # time.sleep(0.5)

    game.endFrame()
