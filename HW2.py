import math
import sys
import pygame
from pygame.locals import (
    DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_UP, K_DOWN
)
from OpenGL.GL import *
from OpenGL.GLU import *


WINDOW_SIZE = (1280, 720)
FOV_Y = 45.0
Z_NEAR, Z_FAR = 0.1, 1000.0

EARTH_DEG_PER_UPDATE = 1.0

AU_TO_UNITS = 10.0


TILT_MIN = 0.0
TILT_MAX = 90.0
TILT_STEP = 2.0  


SPHERE_SLICES = 32
SPHERE_STACKS = 24


YELLOW = (1.0, 1.0, 0.0)
BLUE   = (0.2, 0.5, 1.0)
GREEN  = (0.1, 0.8, 0.2)
RED    = (1.0, 0.2, 0.2)
GREY   = (0.8, 0.8, 0.85)

CAMERA_BACK = 60.0


PLANETS = [
    
    ("Mercury", RED,   1.0 * 0.38, AU_TO_UNITS * 0.39,  87.97),
    ("Venus",   GREEN, 1.0 * 0.95, AU_TO_UNITS * 0.72, 224.70),
    ("Earth",   BLUE,  1.0 * 1.00, AU_TO_UNITS * 1.00, 365.26),
    ("Mars",    RED,   1.0 * 0.53, AU_TO_UNITS * 1.50, 686.98),
]
SUN_RADIUS = 2.0

MOON_ORBIT_RADIUS = 1.5
MOON_RADIUS = 1.0 * 0.27
MOON_PERIOD_DAYS = 27.3  

_quadric_cache = None
def get_quadric():
    global _quadric_cache
    if _quadric_cache is None:
        _quadric_cache = gluNewQuadric()
        gluQuadricNormals(_quadric_cache, GLU_SMOOTH)
    return _quadric_cache

def draw_sphere(radius, color, slices=SPHERE_SLICES, stacks=SPHERE_STACKS):
    glColor3f(*color)
    gluSphere(get_quadric(), radius, slices, stacks)

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)

    glShadeModel(GL_SMOOTH)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 1.0, 0.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.2, 0.2, 0.2, 1.0))

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glClearColor(0.02, 0.02, 0.05, 1.0)

def set_viewport(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = w / float(h if h != 0 else 1)
    gluPerspective(FOV_Y, aspect, Z_NEAR, Z_FAR)
    glMatrixMode(GL_MODELVIEW)


def planet_angle_delta_deg(planet_period_days, earth_deg_per_update=EARTH_DEG_PER_UPDATE):
    EARTH_PERIOD = 365.26
    return earth_deg_per_update * (EARTH_PERIOD / planet_period_days)

def draw_orbit_ring(radius, segments=200):
    glDisable(GL_LIGHTING)
    glPushAttrib(GL_ENABLE_BIT | GL_LINE_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT)
    glDepthMask(GL_FALSE)
    glColor3f(0.5, 0.5, 0.6)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        theta = (i / float(segments)) * 2.0 * math.pi
        glVertex3f(radius * math.cos(theta), radius * math.sin(theta), 0.0)
    glEnd()
    glDepthMask(GL_TRUE)
    glPopAttrib()
    glEnable(GL_LIGHTING)


def main():
    pygame.init()
    pygame.display.set_caption("COSC 4370 HW2 - Inner Solar System")
    screen = pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)
    init_gl()
    set_viewport(*WINDOW_SIZE)

    clock = pygame.time.Clock()

    tilt_deg = 90.0 
    angles = {name: 0.0 for (name, *_rest) in PLANETS}
    moon_angle = 0.0

    
    planet_speeds = {
        name: planet_angle_delta_deg(period_days)
        for (name, _color, _r, _orbit, period_days) in PLANETS
    }
    moon_speed = EARTH_DEG_PER_UPDATE * (365.26 / MOON_PERIOD_DAYS)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_UP:
                    tilt_deg = min(TILT_MAX, tilt_deg + TILT_STEP)
                elif event.key == K_DOWN:
                    tilt_deg = max(TILT_MIN, tilt_deg - TILT_STEP)

        for (name, _c, _r, _o, _p) in PLANETS:
            angles[name] = (angles[name] + planet_speeds[name]) % 360.0
        moon_angle = (moon_angle + moon_speed) % 360.0

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0.0, 0.0, -CAMERA_BACK)
        glRotatef(tilt_deg, 1.0, 0.0, 0.0)

        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 1.0, 0.0))

        glPushMatrix()
        draw_sphere(SUN_RADIUS, YELLOW)
        glPopMatrix()

        for (name, _color, _radius, orbit_radius, _period) in PLANETS:
            draw_orbit_ring(orbit_radius)

        
        earth_world_pos = (0.0, 0.0, 0.0)

        for (name, color, radius, orbit_radius, _period) in PLANETS:
            glPushMatrix()

            glRotatef(angles[name], 0.0, 0.0, 1.0)
            glTranslatef(orbit_radius, 0.0, 0.0)

            if name == "Earth":
                m = glGetFloatv(GL_MODELVIEW_MATRIX).T 
                earth_world_pos = (m[3][0], m[3][1], m[3][2])

            draw_sphere(radius, color)
            glPopMatrix()

        glPushMatrix()
        glRotatef(angles["Earth"], 0.0, 0.0, 1.0)
        glTranslatef(AU_TO_UNITS * 1.0, 0.0, 0.0)

        glRotatef(moon_angle, 0.0, 0.0, 1.0)
        glTranslatef(MOON_ORBIT_RADIUS, 0.0, 0.0)
        draw_sphere(MOON_RADIUS, GREY)
        glPopMatrix()

        pygame.display.set_caption(
            f"COSC 4370 HW2 - Inner Solar System | Tilt: {tilt_deg:.0f}° (Up/Down)"
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
