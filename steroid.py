import copy
import EdgeLaser
import time
import math

game = EdgeLaser.LaserGame('Steroid')

SPACE_X = 1000
SPACE_Y = 1000

game.setResolution(1000).setDefaultColor(EdgeLaser.LaserColor.LIME)

game.setFrameRate(20)

coeff = 0

posx = 450

posy = 450

game_objects = []

class Angle(object):
    def __init__(self, value):
        if isinstance(value, Angle):
            self.value = value.value
        else :
            self.value = value

    def normalize(self):
        if self.value < -math.pi:
            self.value+=2*math.pi
        elif self.value > math.pi:
            self.value-=2*math.pi

    def __add__(self, value):
        self.value+=value
        self.normalize()
        return self

    def __sub__(self, value):
        self.value-=value
        self.normalize()
        return self

    def __str__(self):
        return "Angle({})".format(self.value)

    def add(self, value):
        return self.__add__(value)


class Vector(object):
    def __init__(self, angle,value):
        self.angle=Angle(angle)
        self.value=value

    def apply(self,x,y):
        vx,vy=apply_rot(self.angle.value,self.value,0.0)
        return x+vx,y+vy

    def __add__(self, vector):
        x1,y1=self.apply(0,0)
        x2,y2=vector.apply(0,0)

        xn,yn=x1+x2,y1+y2

        value = math.sqrt(xn**2+yn**2)

        angle = math.atan2(yn,xn)

        return Vector(angle, value)

    def __str__(self):
        x1,y1=self.apply(0,0)
        return "angle={} value={} x={} y={}".format(self.angle, self.value, x1, y1)

class Vector2D(object):
    def __init__(self,x,y):
        self.x=x
        self.y=y

    def __add__(self, other):
        return Vector2D(self.x+other.x,self.y+other.y)

    def __sub__(self, other):
        return Vector2D(self.x-other.x,self.y-other.y)

    def __mul__(self, other):
        if isinstance(other, float):
            return Vector2D(self.x*other,self.y*other)
        raise Exception("Unsupported operation")

    def __rmul__(self, other):
        return self.__mul__(other)



class GameObject(object):
    def __init__(self,ident,x,y,angle):
        self.x=x
        self.y=y
        self.angle=Angle(angle)
        self.clone_of=None
        self.current_clone=None
        self.ident=ident
        self.polygon=[]
        game_objects.append(self)

    def unclone(self):
        game_objects.remove(self.current_clone)
        self.current_clone.clone_of = None
        self.current_clone = None
        print("Uncloned {}".format(self.ident))

    def clone(self):
        if self.current_clone is None :
            cp = copy.copy(self)
            game_objects.append(cp)
            cp.clone_of = self
            self.current_clone = cp

            print("Cloned {}".format(self.ident))

        return self.current_clone

    def is_clone(self):
        return self.clone_of is not None

    def is_visible(self):
        min_x = min(pt[0] for pt in self.polygon)
        if min_x > SPACE_X :
            return False
        max_x = max(pt[0] for pt in self.polygon)
        if max_x < 0 :
            return False
        min_y = min(pt[1] for pt in self.polygon)
        if min_y > SPACE_Y :
            return False
        max_y = max(pt[1] for pt in self.polygon)
        if max_y < 0 :
            return False
        return True

def apply_rot(angle,x,y):
    return x*math.cos(angle)-y*math.sin(angle) , x*math.sin(angle)+y*math.cos(angle)


def apply_trans(obj,x,y):
    return obj.x+x,obj.y+y

def determinant(vec1,vec2):
    return vec1.x*vec2.y-vec1.y*vec2.x


def lines_intersect(a,b,c,d):
    det=determinant(b-a,c-d)
    t=determinant(c-a,c-d)/float(det)
    u=determinant(b-a,c-a)/float(det)

    if ((t<0) or (u<0) or (t>1) or (u>1)) :
        return None
    return a*(1-t)+t*b

class Player(GameObject):
    def __init__(self,ident,*args,**kwargs):
        GameObject.__init__(self,ident,*args,**kwargs)
        self.width=100
        self.speed_vector=Vector(self.angle,0.0)
        self.movement_vector=Vector(self.angle,0.0)
        self.booster = False
        self.polygon=[]

        # print("Angle={}".format(self.angle.value))

    def draw(self, game):
        p1=(0,-self.width/5)
        p2=(self.width,0)
        p3=(0,self.width/5)

        p1=apply_rot(self.angle.value,*p1)
        p2=apply_rot(self.angle.value,*p2)
        p3=apply_rot(self.angle.value,*p3)

        # print(p1)

        p1=apply_trans(self,*p1)
        p2=apply_trans(self,*p2)
        p3=apply_trans(self,*p3)

        # game.addLine(p1[0],p1[1],p2[0],p2[1])
        # game.addLine(p2[0],p2[1],p3[0],p3[1])
        # game.addLine(p3[0],p3[1],p1[0],p1[1])
        # game.addLine(*p2,*p3)
        # game.addLine(*p3,*p1)
        self.polygon=[p1,p2,p3]

    def intersects(self,poly):
        for ptA1,ptA2 in poly_points_closed(self.polygon):
            vA1=Vector2D(*ptA1)
            vA2=Vector2D(*ptA2)
            for ptB1,ptB2 in poly_points_closed(poly):
                vB1=Vector2D(*ptB1)
                vB2=Vector2D(*ptB2)
                if lines_intersect(vA1,vA2,vB1,vB2):
                    return True

        return False



    def apply_movement(self):
        if self.booster:
            self.speed_vector.value=1
            self.speed_vector.angle=self.angle
            self.movement_vector=self.movement_vector + self.speed_vector
            print("movement={} speed={}".format(self.movement_vector, self.speed_vector))
        self.x,self.y=self.movement_vector.apply(self.x,self.y)





while game.isStopped():
    game.receiveServerCommands()
    time.sleep(0.5)


player1 = Player("PLAYER1",500,500,math.pi/2)
# player1.x=500
# player1.y=500
# player1.angle=math.pi/2

dangle=0.1

BORDER_LEFT=[(0.0,0.0),(0.0, SPACE_Y)]
BORDER_RIGHT=[(SPACE_X,0.0),(SPACE_X, SPACE_Y)]
BORDER_BOTTOM=[(0.0,0.0),(SPACE_X, 0.0)]
BORDER_UP=[(0.0,SPACE_Y),(SPACE_X, SPACE_Y)]

def poly_points_closed(points):
    i=0

    while i < len(points) - 1:
        yield points[i],points[i+1]
        i+=1

    yield points[-1],points[0]

def draw_poly(game, game_obj):
    points = game_obj.polygon

    # print(points)
    #
    # i=0
    #
    # while i < len(points) - 1:
    #     game.addLine(points[i][0],points[i][1],points[i+1][0],points[i+1][1])
    #     i+=1
    #
    # i=points[-1]
    # j=points[0]
    # game.addLine(i[0],i[1],j[0],j[1])

    for pt1,pt2 in poly_points_closed(game_obj.polygon):
        game.addLine(pt1[0],pt1[1],pt2[0],pt2[1])

while not game.isStopped():

    game.newFrame()

    game.receiveServerCommands()

    # for cmd in commands:

    if game.player1_keys:
        if game.player1_keys.yp  :
            player1.y-=5
        if game.player1_keys.xn :
            # player1.x-=5
            player1.angle.add(-dangle)
        if game.player1_keys.yn :
            player1.y+=5
        if game.player1_keys.xp :
            # player1.x+=5
            player1.angle.add(dangle)

        player1.booster = game.player1_keys.a

    # print(player1.angle)

    player1.apply_movement()

    for game_obj in game_objects:
        game_obj.draw(game)


    if player1.intersects(BORDER_RIGHT):
        # print("DEAD")
        the_clone = player1.clone()
        the_clone.x = player1.x - SPACE_X
        # the_clone.y = player1.y + player1.y*math.sin(player1.angle.value)
        the_clone.y = player1.y


    if not player1.is_visible() :
        player1.x = player1.current_clone.x
        player1.y = player1.current_clone.y
        player1.unclone()

    for game_obj in game_objects:
        # game_obj.draw(game)
        draw_poly(game, game_obj)

    # player1

    # draw_poly(game, player1)

    game.refresh()

    # time.sleep(0.05)
    # time.sleep(0.5)

    game.endFrame()
