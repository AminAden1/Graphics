from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import math
import sys

angle = 0.0 
tilt_deg = 22.0
vertices = []        
triangles = []             
normals = []               
ZUP_TO_YUP = True           

def load_obj(path: str):
    global vertices, triangles
    raw_vertices = []
    triangles.clear()

    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("v "):
                _, x, y, z = s.split()[:4]
                raw_vertices.append([float(x), float(y), float(z)])
            elif s.startswith("f "):
                parts = s.split()[1:]
                ids = []
                for p in parts:
                    v = p.split("/")[0]
                    if not v:
                        continue
                    vi = int(v)
                    if vi < 0:  
                        vi = len(raw_vertices) + vi + 1
                    ids.append(vi - 1)  
                for j in range(1, len(ids) - 1):
                    triangles.append([ids[0], ids[j], ids[j + 1]])

    if not raw_vertices or not triangles:
        raise RuntimeError("Failed to load teapot.obj (no vertices/faces found).")

    V = np.array(raw_vertices, dtype=np.float32)
    vmin, vmax = V.min(axis=0), V.max(axis=0)
    center = (vmin + vmax) * 0.5
    extent = float((vmax - vmin).max())
    scale = 2.0 / extent if extent > 1e-8 else 1.0
    vertices[:] = ((V - center) * scale).tolist()

def compute_normals():
    normals.clear()
    for a, b, c in triangles:
        v1 = np.array(vertices[a], dtype=np.float32)
        v2 = np.array(vertices[b], dtype=np.float32)
        v3 = np.array(vertices[c], dtype=np.float32)
        n = np.cross(v2 - v1, v3 - v1)
        ln = float(np.linalg.norm(n))
        normals.append((n / ln) if ln > 1e-12 else np.array([0.0, 1.0, 0.0], dtype=np.float32))

def init_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)       
    glEnable(GL_LIGHT1)              
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)           
    glShadeModel(GL_FLAT)           

    glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.0, 0.0, 1.0, 1.0))  
    glLightfv(GL_LIGHT1, GL_DIFFUSE,  (1.0, 0.0, 0.0, 1.0))  
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 1.0, 1.0))
    glLightfv(GL_LIGHT1, GL_SPECULAR, (1.0, 0.0, 0.0, 1.0))

def init_material():
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0.70, 0.70, 0.70, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.30, 0.30, 0.30, 1.0))
    glMaterialf(GL_FRONT, GL_SHININESS, 32.0)

def display():
    global angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Camera
    gluLookAt(0.0, 0.10, 3.5,   0.0, 0.0, 0.0,   0.0, 1.0, 0.0)

    # Lights (camera-relative)
    glLightfv(GL_LIGHT0, GL_POSITION, ( 3.0,  5.0, 5.0, 1.0))   # blue: up-left
    glLightfv(GL_LIGHT1, GL_POSITION, (-3.0, -2.5, 3.0, 1.0))   # red: down-right

    glPushMatrix()

    # Fixed tilt toward the viewer (world X) — stays constant as it spins
    glRotatef(tilt_deg, 1.0, 0.0, 0.0)

    # Turntable spin about WORLD Y
    glRotatef(angle, 0.0, 1.0, 0.0)

    # Reorient OBJ if it's Z-up (closest to the model)
    if ZUP_TO_YUP:
        glRotatef(-90.0, 1.0, 0.0, 0.0)   # use +90.0 if this flips it

    #
    

    glBegin(GL_TRIANGLES)
    for (a, b, c), n in zip(triangles, normals):
        glNormal3fv(n)
        glVertex3fv(vertices[a])
        glVertex3fv(vertices[b])
        glVertex3fv(vertices[c])
    glEnd()

    glPopMatrix()
    glutSwapBuffers()

    angle = (angle + 5.0) % 360.0

def reshape(w, h):
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(w) / float(h), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

def timer(_):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)  

def main():
    load_obj("teapot.obj")
    compute_normals()

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Lighting Teapot - Amin Aden")

    init_lighting()
    init_material()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutTimerFunc(0, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
