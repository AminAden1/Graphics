import math
import os
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from PIL import Image, ImageDraw, ImageFont

def v_add(a,b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def v_sub(a,b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def v_dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def v_cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def v_len(a): return math.sqrt(v_dot(a,a))
def v_norm(a):
    L=v_len(a)
    return (0,0,0) if L==0 else (a[0]/L,a[1]/L,a[2]/L)
def v_scale(a,s): return (a[0]*s, a[1]*s, a[2]*s)

def face_normal(V,F):
    a,b,c = V[F[0]], V[F[1]], V[F[2]]
    return v_norm(v_cross(v_sub(b,a), v_sub(c,a)))

def face_center(V,F):
    c=(0.0,0.0,0.0)
    for i in F: c=v_add(c,V[i])
    return v_scale(c, 1.0/len(F))

def build_axes(n):
    n=v_norm(n)
    up=(0,1,0) if abs(n[1])<0.9 else (1,0,0)
    u=v_norm(v_cross(up,n))
    v=v_norm(v_cross(n,u))
    return u,v,n

def ensure_number_png(n, size=512):
    """Create num_n.png with transparent background and black digit if missing."""
    fname = f"num_{n}.png"
    if os.path.exists(fname): return fname

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", int(size * 0.7))
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", int(size * 0.7))
        except:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.7))
            except:
                font = ImageFont.load_default()

    text = str(n)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        w, h = draw.textsize(text, font=font)

    draw.text(((size - w) / 2, (size - h) / 2), text, fill=(0, 0, 0, 255), font=font)
    img.save(fname)
    return fname

def upload_texture_from_path(path):
    img=Image.open(path).convert("RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    data = img.tobytes("raw","RGBA",0,-1)
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, img.size[0], img.size[1],
                      GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tex

_tex_cache = {}
def get_textures(nfaces):
    if nfaces in _tex_cache: return _tex_cache[nfaces]
    tex=[]
    for i in range(1, nfaces+1):
        fname = ensure_number_png(i)
        tex.append(upload_texture_from_path(fname))
    _tex_cache[nfaces]=tex
    return tex

def pair_faces(V,F):
    N=[face_normal(V,f) for f in F]
    n=len(F)
    used=[False]*n
    pairs=[-1]*n
    for i in range(n):
        if used[i]: continue
        best=-1; bestv=1e9
        for j in range(n):
            if i==j or used[j]: continue
            d=abs(v_dot(N[i],N[j])+1.0)
            if d<bestv:
                bestv=d; best=j
        if best==-1:
            pairs[i]=i; used[i]=True
        else:
            pairs[i]=best; pairs[best]=i
            used[i]=used[best]=True
    return pairs

def labels_opposite_sum(nfaces, pairs):
    labels=[0]*nfaces
    low, high = 1, nfaces
    for i in range(nfaces):
        if labels[i]!=0: continue
        j=pairs[i]
        if j==i:
            labels[i]=low; low+=1
        else:
            labels[i], labels[j] = low, high
            low+=1; high-=1
    return labels

def tetrahedron():
    d=math.sqrt(3)/3
    V=[(d,d,-d), (-d,-d,-d), (d,-d,d), (-d,d,d)]
    F=[(0,1,2),(0,1,3),(0,2,3),(1,2,3)]
    return V,F

def cube():
    d=math.sqrt(3)/3
    V=[(d,-d,-d),(d,d,-d),(-d,d,-d),(-d,-d,-d),
       (d,-d,d),(d,d,d),(-d,-d,d),(-d,d,d)]
    F=[(0,1,2,3),(4,5,7,6),(0,1,5,4),(2,3,6,7),(1,2,7,5),(0,3,6,4)]
    return V,F

def octahedron():
    V=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
    F=[(0,2,4),(1,2,4),(1,3,4),(0,3,4),(0,2,5),(0,3,5),(1,3,5),(1,2,5)]
    return V,F

def icosahedron():
    t=(1+math.sqrt(5))/2
    V=[(-1,t,0),(1,t,0),(-1,-t,0),(1,-t,0),(0,-1,t),(0,1,t),
       (0,-1,-t),(0,1,-t),(t,0,-1),(t,0,1),(-t,0,-1),(-t,0,1)]
    V=[v_norm(p) for p in V]
    F=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
       (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
       (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
       (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
    return V,F

def dodecahedron():
    iV, iF = icosahedron()
    dV=[]
    for f in iF:
        c=(0,0,0)
        for vi in f: c=v_add(c, iV[vi])
        c=v_norm(c)
        dV.append(c)
    adj=[[] for _ in range(len(iV))]
    for fi,f in enumerate(iF):
        for vi in f: adj[vi].append(fi)
    dF=[]
    for vi,faces in enumerate(adj):
        center=iV[vi]; n=v_norm(center)
        u,v,_=build_axes(n)
        with_angles=[]
        for fi in faces:
            p=dV[fi]
            q=v_sub(p, v_scale(n, v_dot(p,n)))
            x=v_dot(q,u); y=v_dot(q,v)
            ang=math.atan2(y,x)
            with_angles.append((ang,fi))
        with_angles.sort()
        dF.append(tuple(fi for ang,fi in with_angles))
    return dV,dF

def draw_solid(V,F,color):
    glColor3fv(color)
    for face in F:
        n=face_normal(V,face)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3fv(n)
        for idx in face:
            glVertex3fv(V[idx])
        glEnd()

def draw_numbers(V, F, labels, texs, scale=0.33, lift=0.01):
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)

    for fi, face in enumerate(F):
        n = face_normal(V, face)
        c = face_center(V, face)

        to_center = v_norm(c)
        if v_dot(n, to_center) < 0:
            n = v_scale(n, -1)

        u, v, _ = build_axes(n)
        h = scale

        p00 = v_add(c, v_add(v_scale(u, -h), v_scale(v, -h)))
        p10 = v_add(c, v_add(v_scale(u,  h), v_scale(v, -h)))
        p11 = v_add(c, v_add(v_scale(u,  h), v_scale(v,  h)))
        p01 = v_add(c, v_add(v_scale(u, -h), v_scale(v,  h)))

        liftv = v_scale(n, lift)
        quad = [v_add(p, liftv) for p in (p00, p10, p11, p01)]

        glBindTexture(GL_TEXTURE_2D, texs[labels[fi] - 1])
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(1, 0); glVertex3fv(quad[0])
        glTexCoord2f(0, 0); glVertex3fv(quad[1])
        glTexCoord2f(0, 1); glVertex3fv(quad[2])
        glTexCoord2f(1, 1); glVertex3fv(quad[3])
        glEnd()

    glEnable(GL_LIGHTING)
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)


def get_shape(shape_id):
    if shape_id==1: return tetrahedron()
    if shape_id==2: return cube()
    if shape_id==3: return octahedron()
    if shape_id==4: return dodecahedron()
    return icosahedron()

def main():
    pygame.init()
    display=(800,800)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption("COSC 4370 HW4 – Amin Aden")

    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)  

    glMatrixMode(GL_PROJECTION)
    gluPerspective(70, display[0]/display[1], 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(0,-3.6,1.2, 0,0,0, 0,0,1)

    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [1.5,-2.0,3.0,0.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0,1.0,1.0,1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.25,0.25,0.25,1.0])
    glShadeModel(GL_SMOOTH)

    current=2
    angle=0.0
    clock=pygame.time.Clock()
    colors=[(0.90,0.35,0.35),(0.35,0.85,0.45),(0.35,0.55,0.95),
            (0.75,0.55,0.90),(0.95,0.85,0.35)]

    while True:
        dt=clock.tick(60)/1000.0
        for e in pygame.event.get():
            if e.type==QUIT: pygame.quit(); return
            if e.type==KEYDOWN:
                if e.key in (K_ESCAPE,K_RETURN): pygame.quit(); return
                if e.key in (K_1,K_2,K_3,K_4,K_5): current=e.key-K_0

        glClearColor(0.06,0.06,0.08,1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        V,F=get_shape(current)

        if len(F)<=6:
            labels=list(range(1,len(F)+1))
        else:
            pairs=pair_faces(V,F)
            labels=labels_opposite_sum(len(F),pairs)

        texs=get_textures(len(F))

        glPushMatrix()
        tilt=18+10*math.cos(math.radians(angle))
        glRotatef(tilt,1,0,0)
        angle=(angle+40*dt)%360
        glRotatef(angle,0,0,1)

        draw_solid(V,F,colors[current-1])
        draw_numbers(V,F,labels,texs,scale=0.32 if current!=5 else 0.28,lift=0.01)

        glPopMatrix()
        pygame.display.flip()

if __name__=="__main__":
    main()
