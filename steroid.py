import copy
import EdgeLaser
import time
import math

game = EdgeLaser.LaserGame('Steroid')

SPACE_X = 1000
SPACE_Y = 1000

game.setResolution(1000).setDefaultColor(EdgeLaser.LaserColor.LIME)

game.setFrameRate(20)



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
    def __init__(self,ident,x,y,angle,color=EdgeLaser.LaserColor.LIME):
        self.x=x
        self.y=y
        self.angle=Angle(angle)
        self.clone_of=None
        self.current_clone=None
        self.ident=ident
        self.polygon=[]
        self.color=color
        self.movement_vector=Vector(self.angle,0.0)
        game_objects.append(self)

    def unclone(self):
        game_objects.remove(self.current_clone)
        self.current_clone.clone_of = None
        self.current_clone = None
        # print("Uncloned {}".format(self.ident))

    def clone(self):
        if self.current_clone is None :
            cp = copy.copy(self)
            game_objects.append(cp)
            cp.clone_of = self
            self.current_clone = cp

            # print("Cloned {}".format(self.ident))

        return self.current_clone

    def stop(self):
        self.movement_vector=Vector(self.angle,0.0)

    def is_clone(self):
        return self.clone_of is not None

    def has_clone(self):
        return self.current_clone is not None

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

    def intersects(self,poly):
        assert poly is not None, "{} polygon is empty".format(poly)
        for ptA1,ptA2 in poly_points_closed(self.polygon):
            vA1=Vector2D(*ptA1)
            vA2=Vector2D(*ptA2)
            for ptB1,ptB2 in poly_points_closed(poly):
                vB1=Vector2D(*ptB1)
                vB2=Vector2D(*ptB2)
                if lines_intersect(vA1,vA2,vB1,vB2):
                    return True

        return False

    def is_colliding(self, other):
        assert other.polygon is not None, "{} polygon is None".format(other.ident)
        assert len(other.polygon) > 0, "{} polygon is empty".format(other.ident)
        return self.intersects(other.polygon)

    def apply_movement(self):
        self.x,self.y=self.movement_vector.apply(self.x,self.y)

    def collide(self, other):
        pass

    def destroy(self):
        game_objects.remove(self)


def apply_rot(angle,x,y):
    return x*math.cos(angle)-y*math.sin(angle) , x*math.sin(angle)+y*math.cos(angle)


def apply_trans(obj,x,y):
    return obj.x+x,obj.y+y

def determinant(vec1,vec2):
    return vec1.x*vec2.y-vec1.y*vec2.x


def lines_intersect(a,b,c,d):
    det=determinant(b-a,c-d)
    if det == 0 :
        return None
    t=determinant(c-a,c-d)/float(det)
    u=determinant(b-a,c-a)/float(det)

    if ((t<0) or (u<0) or (t>1) or (u>1)) :
        return None
    return a*(1-t)+t*b

class Fire(GameObject):
    def __init__(self,ident,player,*args,**kwargs):
        GameObject.__init__(self,ident,*args,**kwargs)
        self.width=10
        self.player=player
        self.movement_vector=Vector(player.angle,player.movement_vector.value+5.0)
        self.polygon=[]

    def draw(self, game):
        p1=(0,-self.width/2)
        p2=(self.width/2,0)
        p3=(0,self.width/2)

        p1=apply_rot(self.angle.value,*p1)
        p2=apply_rot(self.angle.value,*p2)
        p3=apply_rot(self.angle.value,*p3)

        p1=apply_trans(self,*p1)
        p2=apply_trans(self,*p2)
        p3=apply_trans(self,*p3)

        self.polygon=[p1,p2,p3]

    def collide(self, other):
        if isinstance(other, Player):
            other.die()
            self.destroy()

    def destroy(self):
        self.player.current_fire=None
        GameObject.destroy(self)

STATUS_ALIVE=1
STATUS_DYING=2
STATUS_RESPAWN=3

class Player(GameObject):
    def __init__(self,ident,*args,**kwargs):
        GameObject.__init__(self,ident,*args,**kwargs)
        self.width=100
        self.speed_vector=Vector(self.angle,0.0)
        self.booster = False
        self.fire = False
        self.current_fire = None
        self.polygon=[]
        self.original_width=self.width
        self.status=STATUS_ALIVE
        # self.timecode=0

    # def get_poly(self):
    #     if

    def die(self):
        self.status=STATUS_DYING
        self.stop()

    def draw(self, game):
        if self.status==STATUS_DYING :
            if self.width > 0:
                self.width-=3
            else:
                self.status=STATUS_ALIVE

        p1=(0,-self.width/5)
        p2=(self.width/2,0)
        p3=(0,self.width/5)

        p1=apply_rot(self.angle.value,*p1)
        p2=apply_rot(self.angle.value,*p2)
        p3=apply_rot(self.angle.value,*p3)

        p1=apply_trans(self,*p1)
        p2=apply_trans(self,*p2)
        p3=apply_trans(self,*p3)

        self.polygon=[p1,p2,p3]


    def apply_movement(self):
        if self.booster:
            self.speed_vector.value=1
            self.speed_vector.angle=self.angle
            self.movement_vector=self.movement_vector + self.speed_vector
            # print("movement={} speed={}".format(self.movement_vector, self.speed_vector))
        GameObject.apply_movement(self)

    def do_fire(self):
        if self.fire and not self.current_fire :
            x = self.x + self.width*math.cos(self.angle.value)
            y = self.y + self.width*math.sin(self.angle.value)
            self.current_fire = Fire("FIRE_P1",self,x,y,self.angle.value,color=EdgeLaser.LaserColor.YELLOW)

    def collide(self, other):
        if isinstance(other, Player):
            self.die()
            other.die()

def poly_points_closed(points):
    if len(points) == 0:
        yield None

    if len(points) == 1:
        yield points[0]

    i=0

    while i < len(points) - 1:
        yield points[i],points[i+1]
        i+=1

    yield points[-1],points[0]

def draw_poly(game, game_obj):
    for pt1,pt2 in poly_points_closed(game_obj.polygon):
        game.addLine(pt1[0],pt1[1],pt2[0],pt2[1], game_obj.color)

game_objects = None

while True:
    game_objects = []

    while game.isStopped():
        game.receiveServerCommands()
        time.sleep(0.5)


    player1 = Player("PLAYER1",300,500,math.pi/2,color=EdgeLaser.LaserColor.LIME)
    player2 = Player("PLAYER2",600,500,math.pi/2,color=EdgeLaser.LaserColor.RED)

    dangle=0.1

    BORDER_LEFT=[(0.0,0.0),(0.0, SPACE_Y)]
    BORDER_RIGHT=[(SPACE_X,0.0),(SPACE_X, SPACE_Y)]
    BORDER_BOTTOM=[(0.0,0.0),(SPACE_X, 0.0)]
    BORDER_TOP=[(0.0,SPACE_Y),(SPACE_X, SPACE_Y)]



    while not game.isStopped():

        game.newFrame()

        game.receiveServerCommands()

        if game.player1_keys:
            if game.player1_keys.xn :
                player1.angle.add(-dangle)
            elif game.player1_keys.xp :
                player1.angle.add(dangle)

            player1.booster = game.player1_keys.a
            player1.fire =    game.player1_keys.b

        if game.player2_keys:
            if game.player2_keys.xn :
                player2.angle.add(-dangle)
            elif game.player2_keys.xp :
                player2.angle.add(dangle)

            player2.booster = game.player2_keys.a
            player2.fire =    game.player2_keys.b

        for player in [player1, player2] :
            player.do_fire()

        for game_obj in game_objects:
            game_obj.apply_movement()


        for game_obj in game_objects:
            game_obj.draw(game)

        for go1 in game_objects:
            assert(go1.polygon is not None)
            for go2 in game_objects:
                assert(go2.polygon is not None)
                if go1 is not go2 :
                    if go1.is_colliding(go2):
                        go1.collide(go2)

        no_clone_objects = [obj for obj in game_objects if not obj.is_clone()]

        for game_obj in no_clone_objects:

            if game_obj.intersects(BORDER_RIGHT):
                the_clone = game_obj.clone()
                the_clone.x = game_obj.x - SPACE_X
                the_clone.y = game_obj.y

            elif game_obj.intersects(BORDER_LEFT):
                the_clone = game_obj.clone()
                the_clone.x = game_obj.x + SPACE_X
                the_clone.y = game_obj.y

            elif game_obj.intersects(BORDER_TOP):
                the_clone = game_obj.clone()
                the_clone.x = game_obj.x
                the_clone.y = game_obj.y - SPACE_Y

            elif game_obj.intersects(BORDER_BOTTOM):
                the_clone = game_obj.clone()
                the_clone.x = game_obj.x
                the_clone.y = game_obj.y + SPACE_Y

            if not game_obj.is_visible() and game_obj.has_clone() :
                game_obj.x = game_obj.current_clone.x
                game_obj.y = game_obj.current_clone.y
                game_obj.unclone()

        for game_obj in game_objects:
            draw_poly(game, game_obj)

        game.refresh()

        game.endFrame()
