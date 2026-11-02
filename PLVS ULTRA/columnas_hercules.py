"""
Columnas de Hércules con el lema PLVS VLTRA — generador procedural para Blender.

Uso:
  • Desde Blender: pestaña "Scripting" → Abrir este archivo → "Run Script".
  • Sin interfaz:  blender -b -P columnas_hercules.py
  • Con el módulo bpy de PyPI:  python columnas_hercules.py

Genera en la misma carpeta:
  columnas_hercules.blend   (escena editable)
  columnas_hercules.glb     (para CesiumJS / web)
  columnas_hercules.png     (render de vista previa, solo en modo sin interfaz)

Unidades: 1 unidad = 1 metro. El origen está en el centro de la base, al nivel
del suelo (Z = 0), igual que el galeón: altura 0 = apoyado en la superficie.
"""

import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

# ─────────────────────────── Parámetros ───────────────────────────
SEPARACION     = 4.4    # distancia entre los ejes de las dos columnas
RADIO_FUSTE    = 0.62   # radio del fuste en la base
ALTO_FUSTE     = 6.4
ESTRIAS        = 20     # acanaladuras del fuste
INCLUIR_MAR    = True   # olas estilizadas bajo las columnas (como en el escudo)
LEMA           = ("PLVS", "VLTRA")
FUENTES = [             # se usa la primera que exista
    "Cinzel.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]


def carpeta_salida():
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(d) and not d == os.path.sep:
            return d
    except NameError:
        pass
    return bpy.path.abspath("//") or os.getcwd()


OUT = carpeta_salida()


# ─────────────────────────── Utilidades ───────────────────────────
def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(nombre, color, metal=0.0, rugosidad=0.5):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1.0)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rugosidad
    return m


def objeto_desde_bmesh(nombre, bm, mat, suave=True):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    if suave:
        me.shade_smooth()
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def torno(nombre, perfil, mat, segmentos=96, x=0.0, z=0.0):
    """Revoluciona un perfil [(radio, altura), ...] alrededor del eje Z."""
    bm = bmesh.new()
    anillos = []
    for r, h in perfil:
        anillo = []
        for i in range(segmentos):
            a = 2 * math.pi * i / segmentos
            anillo.append(bm.verts.new((x + r * math.cos(a), r * math.sin(a), z + h)))
        anillos.append(anillo)
    for a0, a1 in zip(anillos, anillos[1:]):
        for i in range(segmentos):
            j = (i + 1) % segmentos
            bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
    # tapas
    for anillo, invertir in ((anillos[0], True), (anillos[-1], False)):
        if perfil[0 if invertir else -1][0] > 1e-4:
            bm.faces.new(list(reversed(anillo)) if invertir else anillo)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return objeto_desde_bmesh(nombre, bm, mat)


def caja(nombre, cx, cy, cz, sx, sy, sz, mat, bisel=0.03):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((cx + v.co.x * sx, cy + v.co.y * sy, cz + v.co.z * sz))
    ob = objeto_desde_bmesh(nombre, bm, mat, suave=False)
    if bisel:
        mod = ob.modifiers.new("Bisel", "BEVEL")
        mod.width = bisel
        mod.segments = 3
    return ob


def toro(bm, centro, R, r, seg=48, seg_r=12, arco=2 * math.pi, eje="z"):
    """Toro (o arco de toro) añadido a un bmesh existente."""
    filas = []
    abierto = arco < 2 * math.pi - 1e-6
    n = seg + 1 if abierto else seg
    for i in range(n):
        u = arco * i / seg
        fila = []
        for k in range(seg_r):
            w = 2 * math.pi * k / seg_r
            d = R + r * math.cos(w)
            if eje == "z":
                p = (d * math.cos(u), d * math.sin(u), r * math.sin(w))
            else:  # arco vertical en el plano XZ
                p = (d * math.cos(u), r * math.sin(w), d * math.sin(u))
            fila.append(bm.verts.new(Vector(centro) + Vector(p)))
        filas.append(fila)
    pares = zip(filas, filas[1:] + ([] if abierto else [filas[0]]))
    for f0, f1 in pares:
        for k in range(seg_r):
            j = (k + 1) % seg_r
            bm.faces.new((f0[k], f0[j], f1[j], f1[k]))


def esfera(bm, centro, r):
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    bmesh.ops.translate(bm, verts=res["verts"], vec=Vector(centro))


# ─────────────────────────── Piezas ───────────────────────────
def fuste_estriado(nombre, x, z0, mat):
    """Fuste con éntasis y acanaladuras cóncavas."""
    seg = ESTRIAS * 8
    pisos = 48
    prof = 0.045
    bm = bmesh.new()
    anillos = []
    for k in range(pisos + 1):
        t = k / pisos
        # éntasis: ligero abombamiento a 1/3 y estrechamiento hacia arriba
        R = RADIO_FUSTE * (1.0 - 0.16 * t + 0.03 * math.sin(math.pi * t))
        anillo = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            f = (i % 8) / 8.0  # posición dentro de la estría
            canal = math.sin(math.pi * min(1, max(0, (f - 0.1) / 0.8))) ** 0.6
            r = R - prof * canal
            anillo.append(bm.verts.new((x + r * math.cos(a), r * math.sin(a), z0 + t * ALTO_FUSTE)))
        anillos.append(anillo)
    for a0, a1 in zip(anillos, anillos[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = objeto_desde_bmesh(nombre, bm, mat)
    return ob, RADIO_FUSTE * 0.84  # radio superior


def corona(nombre, x, z0, R, mat_oro, mat_gema, mat_gorro, imperial=False):
    """Corona simplificada: aro, florones, diademas (arcos), orbe y cruz.
    La imperial (columna izquierda) es más alta y lleva mitra central."""
    bm = bmesh.new()
    alto_aro = 0.32
    # aro ligeramente acampanado
    perfil = [(R * 0.92, 0), (R, alto_aro * 0.15), (R * 1.04, alto_aro), (R * 0.98, alto_aro)]
    seg = 64
    anillos = []
    for r, h in perfil:
        anillos.append([bm.verts.new((r * math.cos(2 * math.pi * i / seg),
                                      r * math.sin(2 * math.pi * i / seg), h)) for i in range(seg)])
    for a0, a1 in zip(anillos, anillos[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
    toro(bm, (0, 0, 0.02), R * 0.95, 0.04)
    toro(bm, (0, 0, alto_aro), R * 1.02, 0.035)
    # florones
    for i in range(8):
        a = 2 * math.pi * i / 8
        p = Vector((R * 1.02 * math.cos(a), R * 1.02 * math.sin(a), alto_aro + 0.1))
        esfera(bm, p, 0.07 if i % 2 == 0 else 0.05)
    # diademas: arcos que suben del aro al centro
    altura_arcos = R * (1.25 if imperial else 1.0)
    n_arcos = 4
    for i in range(n_arcos):
        a = math.pi * i / n_arcos
        arco = bmesh.new()
        # semielipse construida como arco de toro y luego escalada en Z
        toro(arco, (0, 0, 0), R, 0.05, seg=32, seg_r=8, arco=math.pi, eje="xz")
        for v in arco.verts:
            v.co.z = v.co.z * (altura_arcos / R) + alto_aro
            v.co.x, v.co.y = (v.co.x * math.cos(a) - v.co.y * math.sin(a),
                              v.co.x * math.sin(a) + v.co.y * math.cos(a))
        me_tmp = bpy.data.meshes.new("tmp")
        arco.to_mesh(me_tmp)
        arco.free()
        bm.from_mesh(me_tmp)
        bpy.data.meshes.remove(me_tmp)
    cima = alto_aro + altura_arcos
    if imperial:  # mitra central
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=R * 0.55,
                                    radius2=R * 0.15, depth=altura_arcos * 0.85)
        bmesh.ops.translate(bm, verts=res["verts"],
                            vec=Vector((0, 0, alto_aro + altura_arcos * 0.425)))
    # orbe y cruz
    esfera(bm, (0, 0, cima + 0.14), 0.15)
    for (sx, sy, sz, dz) in ((0.06, 0.06, 0.36, 0.42), (0.24, 0.06, 0.06, 0.46)):
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + cima + dz))
    for v in bm.verts:
        v.co += Vector((x, 0, z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = objeto_desde_bmesh(nombre, bm, mat_oro)
    # gemas en el aro
    bm = bmesh.new()
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        esfera(bm, (x + R * 1.04 * math.cos(a), R * 1.04 * math.sin(a), z0 + alto_aro * 0.55), 0.055)
    objeto_desde_bmesh(nombre + "_gemas", bm, mat_gema)
    # gorro de terciopelo bajo las diademas
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), 1.0)
    for v in bm.verts:
        v.co = Vector((x + v.co.x * R * 0.93, v.co.y * R * 0.93,
                       z0 + alto_aro * 0.5 + max(v.co.z, -0.2) * altura_arcos * 0.92))
    objeto_desde_bmesh(nombre + "_gorro", bm, mat_gorro)
    return ob


def helice(theta, z_centro, paso):
    """Altura de la cinta según el ángulo (0 rad = frente, mirando hacia -Y)."""
    return z_centro + paso * theta / (2 * math.pi) + 0.08 * math.sin(2 * theta)


def cinta_con_lema(nombre, x, z_centro, radio, texto, fuente, mat_cinta, mat_letras, sentido):
    """Cinta que se enrolla alrededor del fuste con el texto curvado sobre ella."""
    ancho = 0.78
    grosor = 0.025
    paso = 1.1 * sentido
    frente = -math.pi / 2  # dirección -Y

    def radio_en(theta):
        # delante la cinta se separa del fuste para que el lema se lea entero
        return radio + 0.42 * max(0.0, math.cos(theta)) ** 2

    def punto(theta, h, extra=0.0):
        a = frente + theta
        r = radio_en(theta) + extra
        return Vector((x + r * math.cos(a), r * math.sin(a), helice(theta, z_centro, paso) + h))

    # ── cinta (con extremos que se separan del fuste, a modo de banderola)
    n = 200
    t0, t1 = -1.15 * math.pi, 1.15 * math.pi

    def sale(th):
        return max(0.0, abs(th) - 0.8 * math.pi) * 0.5  # extremos al aire

    bm = bmesh.new()
    filas = []
    for i in range(n + 1):
        th = t0 + (t1 - t0) * i / n
        filas.append([bm.verts.new(punto(th, -ancho / 2, sale(th))),
                      bm.verts.new(punto(th, ancho / 2, sale(th)))])
    for f0, f1 in zip(filas, filas[1:]):
        bm.faces.new((f0[0], f1[0], f1[1], f0[1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob_cinta = objeto_desde_bmesh(nombre + "_cinta", bm, mat_cinta)
    sol = ob_cinta.modifiers.new("Grosor", "SOLIDIFY")
    sol.thickness = grosor
    sol.offset = 0
    # ribetes dorados
    bm = bmesh.new()
    for borde in (-ancho / 2, ancho / 2):
        tubo(bm, [punto(t0 + (t1 - t0) * i / n, borde, sale(t0 + (t1 - t0) * i / n))
                  for i in range(n + 1)], 0.022)
    objeto_desde_bmesh(nombre + "_ribete", bm, mat_letras)

    # tabla longitud de arco (en planta) → ángulo, para colocar las letras
    tabla = [(0.0, 0.0)]
    pasos = 2000
    for signo in (1, -1):
        s_acum, prev = 0.0, punto(0.0, 0.0)
        for i in range(1, pasos + 1):
            th = signo * math.pi * i / pasos
            q = punto(th, 0.0)
            d = Vector((q.x - prev.x, q.y - prev.y)).length
            s_acum += d
            tabla.append((signo * s_acum, th))
            prev = q
    tabla.sort()

    def angulo_por_arco(sv):
        lo, hi = 0, len(tabla) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if tabla[m][0] <= sv:
                lo = m
            else:
                hi = m
        (s0, a0), (s1, a1) = tabla[lo], tabla[hi]
        return a0 if s1 == s0 else a0 + (a1 - a0) * (sv - s0) / (s1 - s0)

    # ── texto: se crea plano, se subdivide y se dobla sobre la cinta
    cu = bpy.data.curves.new(nombre + "_txt", "FONT")
    cu.body = texto
    if fuente:
        cu.font = bpy.data.fonts.load(fuente)
    cu.size = 0.44
    cu.extrude = 0.018
    cu.space_character = 1.05
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob_txt = bpy.data.objects.new(nombre + "_lema", cu)
    bpy.context.collection.objects.link(ob_txt)
    bpy.context.view_layer.objects.active = ob_txt
    ob_txt.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob_txt = bpy.context.active_object
    me = ob_txt.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # cortes verticales para que las caras sigan la curvatura
    xs = [v.co.x for v in bm.verts]
    paso_corte = 0.03
    c = min(xs)
    while c < max(xs):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(c, 0, 0), plane_no=(1, 0, 0))
        c += paso_corte
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for v in bm.verts:
        lx, ly, lz = v.co
        v.co = punto(angulo_por_arco(lx), ly, grosor / 2 + 0.002 + lz)
    bm.to_mesh(me)
    bm.free()
    ob_txt.select_set(False)
    me.materials.clear()
    me.materials.append(mat_letras)
    return ob_cinta, ob_txt


def tubo(bm, puntos, r, seg=8):
    anillos = []
    for i, p in enumerate(puntos):
        t = (puntos[min(i + 1, len(puntos) - 1)] - puntos[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized()
        b = t.cross(a)
        anillos.append([bm.verts.new(p + r * (math.cos(2 * math.pi * k / seg) * a +
                                               math.sin(2 * math.pi * k / seg) * b))
                        for k in range(seg)])
    for a0, a1 in zip(anillos, anillos[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((a0[k], a0[j], a1[j], a1[k]))


def mar(mat):
    """Losa de olas estilizadas bajo las columnas."""
    bm = bmesh.new()
    nx, ny = 120, 40
    sx, sy = SEPARACION + 4.5, 3.6
    grid = []
    for j in range(ny + 1):
        fila = []
        for i in range(nx + 1):
            x = -sx / 2 + sx * i / nx
            y = -sy / 2 + sy * j / ny
            z = 0.12 * math.sin(x * 3.2 + y * 1.3) + 0.07 * math.sin(y * 4.1 - x * 0.7)
            fila.append(bm.verts.new((x, y, z)))
        grid.append(fila)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    ob = objeto_desde_bmesh("Mar", bm, mat)
    sol = ob.modifiers.new("Grosor", "SOLIDIFY")
    sol.thickness = 0.35
    return ob


# ─────────────────────────── Escena ───────────────────────────
def construir():
    limpiar_escena()
    marmol = material("Marmol", (0.90, 0.88, 0.83), rugosidad=0.35)
    oro = material("Oro", (0.83, 0.62, 0.22), metal=1.0, rugosidad=0.28)
    rojo = material("Cinta_Roja", (0.55, 0.04, 0.05), rugosidad=0.55)
    gema = material("Gemas", (0.05, 0.25, 0.65), rugosidad=0.1)
    agua = material("Mar", (0.03, 0.12, 0.28), rugosidad=0.15)
    terciopelo = material("Terciopelo", (0.35, 0.02, 0.04), rugosidad=0.8)

    fuente = next((f if os.path.isabs(f) else os.path.join(OUT, f)
                   for f in FUENTES
                   if os.path.exists(f if os.path.isabs(f) else os.path.join(OUT, f))), None)
    print("Fuente del lema:", fuente or "Bfont (por defecto de Blender)")

    z_suelo = 0.1 if INCLUIR_MAR else 0.0
    if INCLUIR_MAR:
        mar(agua)

    for idx, (lado, texto) in enumerate(zip((-1, 1), LEMA)):
        x = lado * SEPARACION / 2
        nombre = "Columna_" + ("Izq" if lado < 0 else "Der")
        R = RADIO_FUSTE
        # plinto
        caja(nombre + "_plinto", x, 0, z_suelo + 0.2, 1.9, 1.9, 0.4, marmol)
        z = z_suelo + 0.4
        # basa ática: toro – escocia – toro
        basa = [(0.0, 0), (R * 1.45, 0), (R * 1.5, 0.08), (R * 1.45, 0.22), (R * 1.25, 0.28),
                (R * 1.12, 0.30), (R * 1.08, 0.38), (R * 1.15, 0.45), (R * 1.22, 0.52),
                (R * 1.18, 0.60), (R * 1.04, 0.64), (R, 0.70)]
        torno(nombre + "_basa", basa, marmol, x=x, z=z)
        z += 0.70
        _, r_sup = fuste_estriado(nombre + "_fuste", x, z, marmol)
        z_fuste = z
        z += ALTO_FUSTE
        # capitel: astrágalo dorado + equino + ábaco
        astragalo = [(0.0, 0), (r_sup * 1.02, 0), (r_sup * 1.12, 0.06), (r_sup * 1.02, 0.12),
                     (r_sup, 0.14), (0.0, 0.14)]
        torno(nombre + "_astragalo", astragalo, oro, x=x, z=z)
        z += 0.14
        equino = [(0.0, 0), (r_sup, 0), (r_sup * 1.05, 0.12), (r_sup * 1.25, 0.32),
                  (r_sup * 1.45, 0.42), (r_sup * 1.5, 0.46), (0.0, 0.46)]
        torno(nombre + "_capitel", equino, marmol, x=x, z=z)
        z += 0.46
        caja(nombre + "_abaco", x, 0, z + 0.12, 1.75, 1.75, 0.24, marmol)
        caja(nombre + "_abaco_oro", x, 0, z + 0.25, 1.82, 1.82, 0.04, oro, bisel=0.01)
        z += 0.27
        corona(nombre + "_corona", x, z, 0.62, oro, gema, terciopelo, imperial=(lado < 0))
        # cinta con el lema, a media altura del fuste
        t = 0.55
        r_cinta = RADIO_FUSTE * (1.0 - 0.16 * t + 0.03 * math.sin(math.pi * t)) + 0.04
        cinta_con_lema(nombre, x, z_fuste + ALTO_FUSTE * t, r_cinta, texto, fuente,
                       rojo, oro, sentido=-lado)

    # agrupar todo bajo un empty para moverlo como una pieza
    raiz = bpy.data.objects.new("Columnas_de_Hercules", None)
    bpy.context.collection.objects.link(raiz)
    for ob in bpy.context.collection.objects:
        if ob is not raiz:
            ob.parent = raiz
    return raiz


def iluminar_y_camara():
    sc = bpy.context.scene
    world = bpy.data.worlds.new("Cielo")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.04, 0.035, 0.03, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = world
    for nombre, energia, rot in (("Sol", 4.0, (math.radians(50), 0, math.radians(-30))),
                                 ("Relleno", 1.2, (math.radians(70), 0, math.radians(140)))):
        luz = bpy.data.lights.new(nombre, "SUN")
        luz.energy = energia
        ob = bpy.data.objects.new(nombre, luz)
        ob.rotation_euler = rot
        sc.collection.objects.link(ob)
    cam = bpy.data.cameras.new("Camara")
    cam.lens = 50
    ob = bpy.data.objects.new("Camara", cam)
    ob.location = (0, -21, 6.5)
    sc.collection.objects.link(ob)
    objetivo = Vector((0, 0, 5.0))
    ob.rotation_euler = (objetivo - ob.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = ob


def exportar(render=False):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "columnas_hercules.blend"))
    # solo la geometría (sin cámara ni luces); modificadores aplicados
    bpy.ops.object.select_all(action="DESELECT")
    for ob in bpy.context.scene.objects:
        if ob.type in {"MESH", "EMPTY"}:
            ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "columnas_hercules.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    # versión para el visor Cesium: sin olas (el mar ya lo pone el globo)
    mar_ob = bpy.data.objects.get("Mar")
    if mar_ob:
        mar_ob.select_set(False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "columnas_hercules_mapa.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    if render:
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = 48
        sc.render.resolution_x, sc.render.resolution_y = 1100, 900
        sc.render.filepath = os.path.join(OUT, "columnas_hercules.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    construir()
    iluminar_y_camara()
    exportar(render=bpy.app.background)
    print("Listo →", OUT)
