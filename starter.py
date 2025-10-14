#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COSC 4370 Homework #1
This is the starter code for the first homework assignment.
It should run as is and will serve as the starting point for development.
"""

import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


def Cube():
    d = 1.0 / math.sqrt(3.0) #ToDo: This is the default but is too large and needs to be changed
    verticies = (
        (d, -d, -d),
        (d, d, -d),
        (-d, d, -d),
        (-d, -d, -d),
        (d, -d, d),
        (d, d, d),
        (-d, -d, d),
        (-d, d, d)
        )

    edges = (
        (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
        (6,3), (6,4), (6,7), (5,1), (5,4), (5,7)
        )
    glColor(1,1,1) # Draw the cube in white
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(verticies[vertex])
    glEnd()


def Axes():
    glBegin(GL_LINES)
    glColor(1,0,0) # Red for the x-axis
    glVertex3fv((0,0,0))
    glVertex3fv((1.5,0,0))
    glColor(0,1,0) # Green for the y-axis
    glVertex3fv((0,0,0))
    glVertex3fv((0,1.5,0))
    glColor(0,0,1) # Blue for the z-axis
    glVertex3fv((0,0,0))
    glVertex3fv((0,0,1.5))
    glEnd()


def Circle():
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-2, 2, -2, 2, -2, 2)
    glColor(1,0,1) # Purple for the limits
    glBegin(GL_LINE_LOOP)
    for i in range(36):
        angle = 2.0 * math.pi * i / 36
        x = math.cos(angle)
        y = math.sin(angle)
        glVertex3fv((x, y, 0))
    glEnd()
    glPopMatrix()


def normalize_vertices(vertices):
    m = max((x*x+y*y+z*z)**0.5 for x,y,z in vertices)
    s = 1.0/m if m else 1.0
    return [(x*s, y*s, z*s) for x,y,z in vertices]

def unique_edges_from_faces(faces):
    seen = set(); out = []
    for f in faces:
        n = len(f)
        for i in range(n):
            a,b = f[i], f[(i+1)%n]
            e = (a,b) if a<b else (b,a)
            if e not in seen:
                seen.add(e); out.append(e)
    return out

def draw_edges(vertices, edges):
    glColor(1,1,1)
    glBegin(GL_LINES)
    for a,b in edges:
        glVertex3fv(vertices[a]); glVertex3fv(vertices[b])
    glEnd()

_TV = normalize_vertices([(1,1,1), (-1,-1,1), (-1,1,-1), (1,-1,-1)])
_TF = [(0,1,2), (0,3,1), (0,2,3), (1,3,2)]
_TE = unique_edges_from_faces(_TF)
def Tetrahedron():
    draw_edges(_TV, _TE)

_OV = normalize_vertices([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
_OF = [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]
_OE = unique_edges_from_faces(_OF)
def Octahedron():
    draw_edges(_OV, _OE)

phi = (1+5**0.5)/2.0
_IV = normalize_vertices([
    (-1, phi, 0), (1, phi, 0), (-1,-phi,0), (1,-phi,0),
    (0,-1, phi), (0, 1, phi), (0,-1,-phi), (0, 1,-phi),
    ( phi,0,-1), ( phi,0, 1), (-phi,0,-1), (-phi,0,1)
])
_IF = [
    (0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
    (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
    (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
    (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)
]
_IE = unique_edges_from_faces(_IF)
def Icosahedron():
    draw_edges(_IV, _IE)

_DV = []
for sx in (-1,1):
    for sy in (-1,1):
        for sz in (-1,1):
            _DV.append((sx,sy,sz))
for sy in (-1,1):
    for sz in (-1,1):
        _DV.append((0.0, sy/phi, sz*phi))
for sx in (-1,1):
    for sy in (-1,1):
        _DV.append((sx/phi, sy*phi, 0.0))
for sx in (-1,1):
    for sz in (-1,1):
        _DV.append((sx*phi, 0.0, sz/phi))
_DV = normalize_vertices(_DV)

def _edges_from_shortest_dist(vertices):
    n = len(vertices)
    pairs = []
    md = None
    for i in range(n):
        xi,yi,zi = vertices[i]
        for j in range(i+1, n):
            xj,yj,zj = vertices[j]
            dx = xi - xj; dy = yi - yj; dz = zi - zj
            d = (dx*dx + dy*dy + dz*dz) ** 0.5
            if md is None or d < md:
                md = d
            pairs.append((d, i, j))
    thr = md * (1.0 + 1e-5)
    return [(i, j) for d, i, j in pairs if d <= thr]

_DE = _edges_from_shortest_dist(_DV)
def Dodecahedron():
    draw_edges(_DV, _DE)
    

def main():
    pygame.init()
    display = (800,800)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption('Homework #1 - Amin Aden') #ToDo: Change this 
    glOrtho(-2, 2, -2, 2, -2, 2)
    glMatrixMode(GL_MODELVIEW)
    
    current = 2

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                key_to_shape = {
                    K_1: 1, K_2: 2, K_3: 3, K_4: 4, K_5: 5,
                    K_KP1: 1, K_KP2: 2, K_KP3: 3, K_KP4: 4, K_KP5: 5,
                }
                if event.key in key_to_shape:
                    current = key_to_shape[event.key]

        glRotatef(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        Axes()
        if current == 1:
            Tetrahedron()
        elif current == 2:
            Cube()
        elif current == 3:
            Octahedron()
        elif current == 4:
            Dodecahedron()
        else:
            Icosahedron()
        Circle()
        
        pygame.display.flip()
        pygame.time.wait(10)


main()
