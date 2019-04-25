import bpy
from mathutils import Vector
from mathutils import Matrix
import math

# Constants
STEP   = 15 # 15 is a good value
RADIUS = 1.0 / (256 / STEP) / 4.0
SPHERE_NAME = "RGB_SPHERE"
CUBE_NAME = "RGB_CUBE" 

# Video Animation Constants
DURATION = 15 # [sec]
FPS = 25
ANIM_KEY_1 = 3 # [sec]
ANIM_KEY_2 = 6
ANIM_KEY_3 = 9
ANIM_KEY_4 = 12
ANIM_KEY_END = DURATION

# Derived Animation Constants
ANIM_TOTAL_FRAMES = ANIM_KEY_END * FPS
ANIM_KEY_1_FRAME = ANIM_KEY_1 * FPS
ANIM_KEY_2_FRAME = ANIM_KEY_2 * FPS
ANIM_KEY_3_FRAME = ANIM_KEY_3 * FPS
ANIM_KEY_4_FRAME = ANIM_KEY_4 * FPS

# XYZ = M * RGB - sRGB, D65 illuminant
# http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
M = Matrix([[0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041]])
            
D65 = Vector((0.95047, 1.00, 1.08883))

# http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
EPS = 0.008856
K = 903.3

# Template sphere
sphere = None

def initSphere():
    global sphere
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.surface.primitive_nurbs_surface_sphere_add(radius=RADIUS)
    sphere = bpy.context.object
    sphere.name = SPHERE_NAME
    
def makeMaterial(name, diffuse, specular, alpha):
    # TODO Convert to Nodes based material
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = Vector((diffuse.x, diffuse.y, diffuse.z, 1))
    # mat.diffuse_shader = 'LAMBERT' 
    # mat.diffuse_intensity = 1.0 
    mat.specular_color = specular
    # mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    # mat.alpha = alpha
    # mat.ambient = 1
    return mat
 
def setMaterial(ob, mat):
    me = ob.data
    # Remove the material from the template sphere
    if len(me.materials) > 0:
        me.materials.pop() 
    me.materials.append(mat)
    
def rgb2NormRGB(rgb):
    '''Converts the RGB Vector [0, 255] to normalised RGB [0.0, 1.0] '''
    n = rgb / 255.0
    return n;

def normRGB2ModelSpace(rgb):
    '''Converts the normalised RGB Vector [0, 1.0] to Model space [0.0, 1.0]'''
    return rgb

def rgb2ModelSpace(rgb):
    '''Converts the RGB Vector [0, 255] to Model space [0.0, 1.0]'''
    n = rgb2NormRGB(rgb)
    return normRGB2ModelSpace(n)

def lab2ModelSpace(lab):
    return lab.yzx / 100.0

def linRGB2XYZ(rgb):
    '''Converts linear RGB to XYZ by applying the Matrix M (D65 Illuminant)'''
    xyz = M @ rgb
    return xyz

def XYZ2xyY(xyz):
    '''Converts XYZ to xyY'''
    xyY = Vector()
    
    # http://www.brucelindbloom.com/index.html?Eqn_XYZ_to_xyY.html
    div = xyz.x + xyz.y + xyz.z
    if div != 0:
        xyY.x = xyz.x / div
        xyY.y = xyz.y / div
    else:
        xyY.x = D65.x / (D65.x + D65.y + D65.z)
        xyY.y = D65.y / (D65.x + D65.y + D65.z)
    xyY.z = 1.0
    return xyY

def f(x):
    if x > EPS:
        r = pow(x, 1.0 / 3.0)
    else:
        r = (K * x + 16.0) / 116.0
    return r

def xyz2Lab(xyz):
    xr = xyz.x / D65.x
    yr = xyz.y / D65.y
    zr = xyz.z / D65.z
    L = 116 * f(yr) - 16
    a = 500 * (f(xr) - f(yr))
    b = 200 * (f(yr) - f(zr))
    return Vector((L, a, b))
    
def rgb2Lab(rgb):
    xyz = linRGB2XYZ(rgb)
    lab = xyz2Lab(xyz)
    return lab
    
def createPoint(rgb):
    global sphere
    obj = None
    
    if sphere == None:
        initSphere()
        obj = sphere
    else:
        obj = sphere.copy()
        obj.data = sphere.data.copy()
        bpy.context.scene.collection.objects.link(obj)
    obj.location = rgb2ModelSpace(rgb)    
    mat = makeMaterial('Mat', rgb / 255, (1, 1, 1), 1)
    setMaterial(obj, mat)
    obj.normRGB=rgb2NormRGB(rgb)
    
def s2lin(s):
    a = 0.055
    # http://entropymine.com/imageworsener/srgbformula/
    if s <= 0.04045:
        l = s * (1.0 / 12.92)
    else:
        l = pow((s + a) * (1.0 / (1 + a)), 2.4)
    return l
    
def sRGB2linear(rgb):
    a = 0.055
    lrgb = Vector()
    lrgb.x = s2lin(rgb.x)
    lrgb.y = s2lin(rgb.y)
    lrgb.z = s2lin(rgb.z)
    return lrgb

def createScene():
    scene = bpy.context.scene
    scene.frame_set(0)
    
    # r/g/0 face ("bottom")
    b = 0
    for r in range(0, 256, STEP):
        for g in range(0, 256, STEP):
            rgb = Vector((r, g, b))
            createPoint(rgb)
    # r/g/255 face ("top")
    b = 255
    for r in range(0, 256, STEP):
        for g in range(0, 256, STEP):
            rgb = Vector((r, g, b))
            createPoint(rgb)
    # r/0/b face ("Front")
    g = 0
    for r in range(0, 256, STEP):
        for b in range(0, 256, STEP):
            rgb = Vector((r, g, b))
            createPoint(rgb)
    # r/0/b face ("Back")
    g = 255
    for r in range(0, 256, STEP):
        for b in range(0, 256, STEP):
            rgb = Vector((r, g, b))
            createPoint(rgb)
    # 0/g/b face ("Left")
    r = 0
    for g in range(0, 256, STEP):
        if g > 0 and g < 255:
            for b in range(0, 256, STEP):
                if b > 0 and b < 255:
                    rgb = Vector((r, g, b))
                    createPoint(rgb)
    # 0/g/b face ("Right")
    r = 255
    for g in range(0, 256, STEP):
        if g > 0 and g < 255:
            for b in range(0, 256, STEP):
                if b > 0 and b < 255:
                    rgb = Vector((r, g, b))
                    createPoint(rgb)
    
    #  Store initial locations                
    for obj in bpy.context.selected_objects:
        obj.keyframe_insert(data_path='location', index=-1)
                    
    # Create RGB Cube "handle" ("Empty" object) - center of RGB cube
    loc = normRGB2ModelSpace(Vector((0.5, 0.5, 0.5))) 
    bpy.ops.object.empty_add(type='ARROWS', view_align=False, location=loc)
    # Creating a new object via "operations" makes the newly created object the selected one
    # cube = scene.objects.active
    cube = bpy.context.object
    cube.name = CUBE_NAME
    
    # Create parent-child relationship - make sure the "handle" is de-selected first
    cube.select_set(False)
    
    # Then select all RGB spheres first...
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.name.startswith(SPHERE_NAME))
        
    # ... then the "handle" (parent) again (last)
    cube.select_set(True)
    
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            
    # Update objects in scene        
    scene.update()
                
def clearScene():
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.name.startswith(SPHERE_NAME) or obj.name.startswith(CUBE_NAME))
    bpy.ops.object.delete()
    
def animate():
    scene = bpy.context.scene    
    
    scene.frame_start = 1
    if scene.frame_end < ANIM_TOTAL_FRAMES:
        scene.frame_end = ANIM_TOTAL_FRAMES
    
    # Select the RGB spheresf    
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.name.startswith(SPHERE_NAME))
    
    # linear RGB
    scene.frame_set(ANIM_KEY_1_FRAME)        
    for obj in bpy.context.selected_objects:
        sRGB = obj.normRGB
        linRGB = sRGB2linear(sRGB)
        obj.location = normRGB2ModelSpace(linRGB)
        obj.keyframe_insert(data_path='location', index=-1)

    # XYZ        
    scene.frame_set(ANIM_KEY_2_FRAME)        
    for obj in bpy.context.selected_objects:
        sRGB = obj.normRGB
        linRGB = sRGB2linear(sRGB)
        obj.location = linRGB2XYZ(linRGB)
        obj.keyframe_insert(data_path='location', index=-1)
        
    # xyY        
    scene.frame_set(ANIM_KEY_3_FRAME)        
    for obj in bpy.context.selected_objects:
        sRGB = obj.normRGB
        linRGB = sRGB2linear(sRGB)
        xyz = linRGB2XYZ(linRGB)
        obj.location = XYZ2xyY(xyz)
        obj.keyframe_insert(data_path='location', index=-1)
        
    # L*a*b*, D65    
    scene.frame_set(ANIM_KEY_4_FRAME)        
    for obj in bpy.context.selected_objects:
        sRGB = obj.normRGB
        linRGB = sRGB2linear(sRGB)
        obj.location = lab2ModelSpace(rgb2Lab(linRGB))
        obj.keyframe_insert(data_path='location', index=-1)
        
def getNormRGBProperty(self):
    return self["normRGB"]

def setNormRGBProperty(self, value):
    self["normRGB"] = value
        
def initProperties():
    bpy.types.Object.normRGB = bpy.props.FloatVectorProperty(name="Normalised RGB", description="Original normalised RGB value in range [0.0, 1.0]", subtype="XYZ", size=3, get=getNormRGBProperty, set=setNormRGBProperty)
                
if __name__ == "__main__":
    initProperties()
    clearScene()
    createScene()
    animate()
    
        
        






