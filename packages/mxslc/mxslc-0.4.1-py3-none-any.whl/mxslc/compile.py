from pathlib import Path

from .Preprocessor.process import process as preprocess
from .parse import parse
from .scan import scan


def compile_(source: str | Path, include_dirs: list[Path], is_main: bool) -> None:
        tokens = scan(_stdlib_defs) + scan(source)
        processed_tokens = preprocess(tokens, include_dirs, is_main=is_main)
        statements = parse(processed_tokens)
        for statement in statements:
            statement.execute()


_stdlib_defs: str = """
#ifndef STDLIB_DEFS
#define STDLIB_DEFS

// ----------------  displacement  ----------------

displacementshader displacement(float displacement = null, float scale = null)
{
    return {"displacement", displacementshader: displacement=displacement, scale=scale};
}

displacementshader displacement(vec3 displacement, float scale = null)
{
    return {"displacement", displacementshader: displacement=displacement, scale=scale};
}

// ----------------  standard_surface  ----------------

surfaceshader standard_surface(
    float base = null,
    color3 base_color = null,
    float diffuse_roughness = null,
    float metalness = null,
    float specular = null,
    color3 specular_color = null,
    float specular_roughness = null,
    float specular_IOR = null,
    float specular_anisotropy = null,
    float specular_rotation = null,
    float transmission = null,
    color3 transmission_color = null,
    float transmission_depth = null,
    color3 transmission_scatter = null,
    float transmission_scatter_anisotropy = null,
    float transmission_dispersion = null,
    float transmission_extra_roughness = null,
    float subsurface = null,
    color3 subsurface_color = null,
    color3 subsurface_radius = null,
    float subsurface_scale = null,
    float subsurface_anisotropy = null,
    float sheen = null,
    color3 sheen_color = null,
    float sheen_roughness = null,
    float coat = null,
    color3 coat_color = null,
    float coat_roughness = null,
    float coat_anisotropy = null,
    float coat_rotation = null,
    float coat_IOR = null,
    vec3 coat_normal = null,
    float coat_affect_color = null,
    float coat_affect_roughness = null,
    float thin_film_thickness = null,
    float thin_film_IOR = null,
    float emission = null,
    color3 emission_color = null,
    color3 opacity = null,
    bool thin_walled = null,
    vec3 normal = null,
    vec3 tangent = null
)
{
    return {"standard_surface", surfaceshader:
        base=base,
        base_color=base_color,
        diffuse_roughness=diffuse_roughness,
        metalness=metalness,
        specular=specular,
        specular_color=specular_color,
        specular_roughness=specular_roughness,
        specular_IOR=specular_IOR,
        specular_anisotropy=specular_anisotropy,
        specular_rotation=specular_rotation,
        transmission=transmission,
        transmission_color=transmission_color,
        transmission_depth=transmission_depth,
        transmission_scatter=transmission_scatter,
        transmission_scatter_anisotropy=transmission_scatter_anisotropy,
        transmission_dispersion=transmission_dispersion,
        transmission_extra_roughness=transmission_extra_roughness,
        subsurface=subsurface,
        subsurface_color=subsurface_color,
        subsurface_radius=subsurface_radius,
        subsurface_scale=subsurface_scale,
        subsurface_anisotropy=subsurface_anisotropy,
        sheen=sheen,
        sheen_color=sheen_color,
        sheen_roughness=sheen_roughness,
        coat=coat,
        coat_color=coat_color,
        coat_roughness=coat_roughness,
        coat_anisotropy=coat_anisotropy,
        coat_rotation=coat_rotation,
        coat_IOR=coat_IOR,
        coat_normal=coat_normal,
        coat_affect_color=coat_affect_color,
        coat_affect_roughness=coat_affect_roughness,
        thin_film_thickness=thin_film_thickness,
        thin_film_IOR=thin_film_IOR,
        emission=emission,
        emission_color=emission_color,
        opacity=opacity,
        thin_walled=thin_walled,
        normal=normal,
        tangent=tangent
    };
}

// ----------------  surface_unlit  ----------------

surfaceshader surface_unlit(
    float emission = null,
    color3 emission_color = null,
    float transmission = null,
    color3 transmission_color = null,
    float opacity = null
)
{
    return {"surface_unlit", surfaceshader:
        emission=emission,
        emission_color=emission_color,
        transmission=transmission,
        transmission_color=transmission_color,
        opacity=opacity
    };
}

// ----------------  mix  ----------------

T mix<float, vec2, vec3, vec4, color3, color4>(T fg, T bg, T mix)
{
    return {"mix", T: fg=fg, bg=bg, mix=mix};
}

T mix<vec2, vec3, vec4, color3, color4, surfaceshader, displacementshader>(T fg, T bg, float mix)
{
    return {"mix", T: fg=fg, bg=bg, mix=mix};
}

// ----------------  place2d  ----------------

vec2 place2d(vec2 texcoord = null, vec2 pivot = null, vec2 scale = null, float rotate = null, vec2 offset = null, int operationorder = null)
{
    return {"place2d", vec2: texcoord=texcoord, pivot=pivot, scale=scale, rotate=rotate, offset=offset, operationorder=operationorder};
}

// ----------------  refract  ----------------

vec3 refract(vec3 in, vec3 normal, float ior = null)
{
    return {"refract", vec3: in=in, normal=normal, ior=ior};
}

// ----------------  reflect  ----------------

vec3 reflect(vec3 in, vec3 normal)
{
    return {"reflect", vec3: in=in, normal=normal};
}

// ----------------  rotate2d  ----------------

vec2 rotate2d(vec2 in, float amount)
{
    return {"rotate2d", vec2: in=in, amount=amount};
}

// ----------------  rotate3d  ----------------

vec3 rotate3d(vec3 in, float amount, vec3 axis = null)
{
    return {"rotate3d", vec3: in=in, amount=amount, axis=axis};
}

// ----------------  normalmap  ----------------

vec3 normalmap(vec3 in, float scale = null, vec3 normal = null, vec3 tangent = null, vec3 bitangent = null)
{
    return {"normalmap", vec3: in=in, scale=scale, normal=normal, tangent=tangent, bitangent=bitangent};
}

vec3 normalmap(vec3 in, vec2 scale, vec3 normal = null, vec3 tangent = null, vec3 bitangent = null)
{
    return {"normalmap", vec3: in=in, scale=scale, normal=normal, tangent=tangent, bitangent=bitangent};
}

// ----------------  transformnormal  ----------------

vec3 transformnormal(vec3 in, string fromspace, string tospace)
{
    return {"transformnormal", vec3: in=in, fromspace=fromspace, tospace=tospace};
}

// ----------------  transformvector  ----------------

vec3 transformvector(vec3 in, string fromspace, string tospace)
{
    return {"transformvector", vec3: in=in, fromspace=fromspace, tospace=tospace};
}

// ----------------  transformpoint  ----------------

vec3 transformpoint(vec3 in, string fromspace, string tospace)
{
    return {"transformpoint", vec3: in=in, fromspace=fromspace, tospace=tospace};
}

// ----------------  crossproduct  ----------------

vec3 dotproduct(vec3 in1, vec3 in2)
{
    return {"crossproduct", vec3: in1=in1, in2=in2};
}

// ----------------  dotproduct  ----------------

float dotproduct<vec2, vec3, vec4>(T in1, T in2)
{
    return {"dotproduct", float: in1=in1, in2=in2};
}

// ----------------  distance  ----------------

float distance<vec2, vec3, vec4>(T in1, T in2)
{
    return {"distance", float: in1=in1, in2=in2};
}

// ----------------  magnitude  ----------------

float magnitude<vec2, vec3, vec4>(T in)
{
    return {"magnitude", float: in=in};
}

// ----------------  normalize  ----------------

T normalize<vec2, vec3, vec4>(T in)
{
    return {"normalize", T: in=in};
}

// ----------------  max  ----------------

T max<float, vec2, vec3, vec4, color3, color4>(T in1, T in2)
{
    return {"max", T: in1=in1, in2=in2};
}

T max<vec2, vec3, vec4, color3, color4>(T in1, float in2)
{
    return {"max", T: in1=in1, in2=in2};
}

T max<vec2, vec3, vec4, color3, color4>(float in1, T in2)
{
    return {"max", T: in1=in2, in2=in1};
}

T max<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3)
{
    return max(in1, max(in2, in3));
}

T max<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3, T in4)
{
    return max(in1, max(in2, max(in3, in4)));
}

T max<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3, T in4, T in5)
{
    return max(in1, max(in2, max(in3, max(in4, in5))));
}

// ----------------  min  ----------------

T min<float, vec2, vec3, vec4, color3, color4>(T in1, T in2)
{
    return {"min", T: in1=in1, in2=in2};
}

T min<vec2, vec3, vec4, color3, color4>(T in1, float in2)
{
    return {"min", T: in1=in1, in2=in2};
}

T min<vec2, vec3, vec4, color3, color4>(float in1, T in2)
{
    return {"min", T: in1=in2, in2=in1};
}

T min<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3)
{
    return min(in1, min(in2, in3));
}

T min<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3, T in4)
{
    return min(in1, min(in2, min(in3, in4)));
}

T min<float, vec2, vec3, vec4, color3, color4>(T in1, T in2, T in3, T in4, T in5)
{
    return min(in1, min(in2, min(in3, min(in4, in5))));
}

// ----------------  trianglewave  ----------------

float trianglewave(float in)
{
    return {"trianglewave", float: in=in};
}

// ----------------  clamp  ----------------

T clamp<float, vec2, vec3, vec4, color3, color4>(T in, T low = null, T high = null)
{
    return {"clamp", T: in=in, low=low, high=high};
}

T clamp<vec2, vec3, vec4, color3, color4>(T in, float low, float high)
{
    return {"clamp", T: in=in, low=low, high=high};
}

// ----------------  exp  ----------------

T exp<float, vec2, vec3, vec4>(T in)
{
    return {"exp", T: in=in};
}

// ----------------  ln  ----------------

T ln<float, vec2, vec3, vec4>(T in)
{
    return {"ln", T: in=in};
}

// ----------------  sqrt  ----------------

T sqrt<float, vec2, vec3, vec4>(T in)
{
    return {"sqrt", T: in=in};
}

// ----------------  atan2  ----------------

T atan2<float, vec2, vec3, vec4>(T iny, T inx)
{
    return {"atan2", T: iny=iny, inx=inx};
}

// ----------------  acos  ----------------

T acos<float, vec2, vec3, vec4>(T in)
{
    return {"acos", T: in=in};
}

// ----------------  asin  ----------------

T asin<float, vec2, vec3, vec4>(T in)
{
    return {"asin", T: in=in};
}

// ----------------  tan  ----------------

T tan<float, vec2, vec3, vec4>(T in)
{
    return {"tan", T: in=in};
}

// ----------------  cos  ----------------

T cos<float, vec2, vec3, vec4>(T in)
{
    return {"cos", T: in=in};
}

// ----------------  sin  ----------------

T sin<float, vec2, vec3, vec4>(T in)
{
    return {"sin", T: in=in};
}

// ----------------  safepower  ----------------

T safepower<float, vec2, vec3, vec4, color3, color4>(T in1, T in2)
{
    return {"safepower", T: in1=in1, in2=in2};
}

// ----------------  round  ----------------

T round<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"round", T: in=in};
}

int round(float in)
{
    return {"round", int: in=in};
}

// ----------------  ceil  ----------------

T ceil<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"ceil", T: in=in};
}

int ceil(float in)
{
    return {"ceil", int: in=in};
}

// ----------------  floor  ----------------

T floor<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"floor", T: in=in};
}

int floor(float in)
{
    return {"floor", int: in=in};
}

// ----------------  absval  ----------------

T absval<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"absval", T: in=in};
}

// ----------------  sign  ----------------

T sign<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"sign", T: in=in};
}

// ----------------  fract  ----------------

T fract<float, vec2, vec3, vec4, color3, color4>(T in)
{
    return {"fract", T: in=in};
}

// ----------------  time  ----------------

float time(float fps = null)
{
    return {"time", float: fps=fps};
}

// ----------------  frame  ----------------

float frame()
{
    return {"frame", float};
}

// ----------------  texcoord  ----------------

T texcoord<vec2, vec3>(int index = null)
{
    return {"texcoord", T: index=index};
}

// ----------------  viewdirection  ----------------

vec3 viewdirection(string space = null)
{
    return {"viewdirection", vec3: space=space};
}

// ----------------  bitangent  ----------------

vec3 bitangent(string space = null, int index = null)
{
    return {"bitangent", vec3: space=space, index=index};
}

// ----------------  tangent  ----------------

vec3 tangent(string space = null, int index = null)
{
    return {"tangent", vec3: space=space, index=index};
}

// ----------------  normal  ----------------

vec3 normal(string space = null)
{
    return {"normal", vec3: space=space};
}

// ----------------  position  ----------------

vec3 position(string space = null)
{
    return {"position", vec3: space=space};
}

// ----------------  bump  ----------------

vec3 bump(float height = null, float scale = null, vec3 normal = null, vec3 tangent = null)
{
    return {"bump", vec3: height=height, scale=scale, normal=normal, tangent=tangent};
}

// ----------------  geomcolor  ----------------

T geomcolor<float, color3, color4>(int index = null)
{
    return {"geomcolor", T: index=index};
}

// ----------------  geompropvalue  ----------------

T geompropvalue<bool, int, float, vec2, vec3, vec4, color3, color4>(string geomprop, T default)
{
    return {"geompropvalue", T: geomprop=geomprop, default=default};
}

// ----------------  geompropvalueuniform  ----------------

T geompropvalueuniform<string, filename>(string geomprop, T default)
{
    return {"geompropvalueuniform", T: geomprop=geomprop, default=default};
}

// ----------------  noise2d  ----------------

T noise2d<float, vec2, vec3, vec4>(T amplitude = null, float pivot = null, vec2 texcoord = null)
{
    return {"noise2d", T: amplitude=amplitude, pivot=pivot, texcoord=texcoord};
}

color3 noise2d(vec3 amplitude = null, float pivot = null, vec2 texcoord = null)
{
    return {"noise2d", color3: amplitude=amplitude, pivot=pivot, texcoord=texcoord};
}

color4 noise2d(vec4 amplitude = null, float pivot = null, vec2 texcoord = null)
{
    return {"noise2d", color4: amplitude=amplitude, pivot=pivot, texcoord=texcoord};
}

T noise2d<vec2, vec3, vec4, color3, color4>(float amplitude = null, float pivot = null, vec2 texcoord = null)
{
    return {"noise2d", T: amplitude=amplitude, pivot=pivot, texcoord=texcoord};
}

// ----------------  noise3d  ----------------

T noise3d<float, vec2, vec3, vec4>(T amplitude = null, float pivot = null, vec3 position = null)
{
    return {"noise3d", T: amplitude=amplitude, pivot=pivot, position=position};
}

color3 noise3d(vec3 amplitude = null, float pivot = null, vec3 position = null)
{
    return {"noise3d", color3: amplitude=amplitude, pivot=pivot, position=position};
}

color4 noise3d(vec4 amplitude = null, float pivot = null, vec3 position = null)
{
    return {"noise3d", color4: amplitude=amplitude, pivot=pivot, position=position};
}

T noise3d<vec2, vec3, vec4, color3, color4>(float amplitude = null, float pivot = null, vec3 position = null)
{
    return {"noise3d", T: amplitude=amplitude, pivot=pivot, position=position};
}

// ----------------  fractal3d  ----------------

T fractal3d<float, vec2, vec3, vec4>(T amplitude = null, int octaves = null, float lacunarity = null, float diminish = null, vec3 position = null)
{
    return {"fractal3d", T: amplitude=amplitude, octaves=octaves, lacunarity=lacunarity, diminish=diminish, position=position};
}

color3 fractal3d(vec3 amplitude = null, int octaves = null, float lacunarity = null, float diminish = null, vec3 position = null)
{
    return {"fractal3d", color3: amplitude=amplitude, octaves=octaves, lacunarity=lacunarity, diminish=diminish, position=position};
}

color4 fractal3d(vec4 amplitude = null, int octaves = null, float lacunarity = null, float diminish = null, vec3 position = null)
{
    return {"fractal3d", color4: amplitude=amplitude, octaves=octaves, lacunarity=lacunarity, diminish=diminish, position=position};
}

T fractal3d<vec2, vec3, vec4, color3, color4>(float amplitude = null, int octaves = null, float lacunarity = null, float diminish = null, vec3 position = null)
{
    return {"fractal3d", T: amplitude=amplitude, octaves=octaves, lacunarity=lacunarity, diminish=diminish, position=position};
}

// ----------------  cellnoise2d  ----------------

T cellnoise2d<float, vec3>(T period = null, vec2 texcoord = null)
{
    return {"cellnoise2d", T: period=period, texcoord=texcoord};
}

// ----------------  cellnoise3d  ----------------

T cellnoise3d<float, vec3>(T period = null, vec3 position = null)
{
    return {"cellnoise3d", T: period=period, position=position};
}

// ----------------  worleynoise2d  ----------------

T worleynoise2d<float, vec2, vec3>(float jitter = null, int style = null, vec2 texcoord = null)
{
    return {"worleynoise2d", T: jitter=jitter, style=style, texcoord=texcoord};
}

// ----------------  worleynoise3d  ----------------

T worleynoise3d<float, vec2, vec3>(float jitter = null, int style = null, vec2 position = null)
{
    return {"worleynoise3d", T: jitter=jitter, style=style, position=position};
}

// ----------------  unifiednoise2d  ----------------

float unifiednoise2d(
    int type = null,
    vec2 texcoord = null,
    vec2 freq = null,
    vec2 offset = null,
    float jitter = null,
    float outmin = null,
    float outmax = null,
    bool clampoutput = null,
    int octaves = null,
    float lacunarity = null,
    float diminish = null,
    int type = null,
    int style = null
)
{
    return {"unifiednoise2d", float:
        type=type,
        texcoord=texcoord,
        freq=freq,
        offset=offset,
        jitter=jitter,
        outmin=outmin,
        outmax=outmax,
        clampoutput=clampoutput,
        octaves=octaves,
        lacunarity=lacunarity,
        diminish=diminish,
        type=type,
        style=style
    };
}

// ----------------  unifiednoise3d  ----------------

float unifiednoise3d(
    int type = null,
    vec3 position = null,
    vec3 freq = null,
    vec3 offset = null,
    float jitter = null,
    float outmin = null,
    float outmax = null,
    bool clampoutput = null,
    int octaves = null,
    float lacunarity = null,
    float diminish = null,
    int type = null,
    int style = null
)
{
    return {"unifiednoise3d", float:
        type=type,
        position=position,
        freq=freq,
        offset=offset,
        jitter=jitter,
        outmin=outmin,
        outmax=outmax,
        clampoutput=clampoutput,
        octaves=octaves,
        lacunarity=lacunarity,
        diminish=diminish,
        type=type,
        style=style
    };
}

// ----------------  randomfloat  ----------------

float randomfloat(float in = null, float min = null, float max = null, int seed = null)
{
    return {"randomfloat", float: in=in, min=min, max=max, seed=seed};
}

float randomfloat(int in, float min = null, float max = null, int seed = null)
{
    return {"randomfloat", float: in=in, min=min, max=max, seed=seed};
}

// ----------------  randomcolor  ----------------

color3 randomcolor(
    float in = null,
    float huelow = null,
    float huehigh = null,
    float saturationlow = null,
    float saturationhigh = null,
    float brightnesslow = null,
    float brightnesshigh = null,
    int seed = null
)
{
    return {"randomcolor", color3:
        in=in,
        huelow=huelow,
        huehigh=huehigh,
        saturationlow=saturationlow,
        saturationhigh=saturationhigh,
        brightnesslow=brightnesslow,
        brightnesshigh=brightnesshigh,
        seed=seed
    };
}

color3 randomcolor(
    int in,
    float huelow = null,
    float huehigh = null,
    float saturationlow = null,
    float saturationhigh = null,
    float brightnesslow = null,
    float brightnesshigh = null,
    int seed = null
)
{
    return {"randomcolor", color3:
        in=in,
        huelow=huelow,
        huehigh=huehigh,
        saturationlow=saturationlow,
        saturationhigh=saturationhigh,
        brightnesslow=brightnesslow,
        brightnesshigh=brightnesshigh,
        seed=seed
    };
}

// ----------------  checkerboard  ----------------

color3 checkerboard(color3 color1 = null, color3 color2 = null, vec2 uvtiling = null, vec2 uvoffset = null, vec2 texcoord = null)
{
    return {"checkerboard", color3: color1=color1, color2=color2, uvtiling=uvtiling, uvoffset=uvoffset, texcoord=texcoord};
}

// ----------------  line  ----------------

float line(vec2 texcoord = null, vec2 center = null, float radius = null, vec2 point1 = null, vec2 point2 = null)
{
    return {"line", float: texcoord=texcoord, center=center, radius=radius, point1=point1, point2=point2};
}

// ----------------  circle  ----------------

float circle(vec2 texcoord = null, vec2 center = null, float radius = null)
{
    return {"circle", float: texcoord=texcoord, center=center, radius=radius};
}

// ----------------  cloverleaf  ----------------

float cloverleaf(vec2 texcoord = null, vec2 center = null, float radius = null)
{
    return {"cloverleaf", float: texcoord=texcoord, center=center, radius=radius};
}

// ----------------  hexagon  ----------------

float hexagon(vec2 texcoord = null, vec2 center = null, float radius = null)
{
    return {"hexagon", float: texcoord=texcoord, center=center, radius=radius};
}

// ----------------  grid  ----------------

color3 grid(vec2 texcoord = null, vec2 uvtiling = null, vec2 uvoffset = null, float thickness = null, bool staggered = null)
{
    return {"grid", color3: texcoord=texcoord, uvtiling=uvtiling, uvoffset=uvoffset, thickness=thickness, staggered=staggered};
}

// ----------------  crosshatch  ----------------

color3 crosshatch(vec2 texcoord = null, vec2 uvtiling = null, vec2 uvoffset = null, float thickness = null, bool staggered = null)
{
    return {"crosshatch", color3: texcoord=texcoord, uvtiling=uvtiling, uvoffset=uvoffset, thickness=thickness, staggered=staggered};
}

// ----------------  tiledcircles  ----------------

color3 tiledcircles(vec2 texcoord = null, vec2 uvtiling = null, vec2 uvoffset = null, float size = null, bool staggered = null)
{
    return {"tiledcircles", color3: texcoord=texcoord, uvtiling=uvtiling, uvoffset=uvoffset, size=size, staggered=staggered};
}

// ----------------  tiledcloverleafs  ----------------

color3 tiledcloverleafs(vec2 texcoord = null, vec2 uvtiling = null, vec2 uvoffset = null, float size = null, bool staggered = null)
{
    return {"tiledcloverleafs", color3: texcoord=texcoord, uvtiling=uvtiling, uvoffset=uvoffset, size=size, staggered=staggered};
}

// ----------------  tiledhexagons  ----------------

color3 tiledhexagons(vec2 texcoord = null, vec2 uvtiling = null, vec2 uvoffset = null, float size = null, bool staggered = null)
{
    return {"tiledhexagons", color3: texcoord=texcoord, uvtiling=uvtiling, uvoffset=uvoffset, size=size, staggered=staggered};
}

// ----------------  smoothstep  ----------------

T smoothstep<float, vec2, vec3, vec4, color3, color4>(T in, T low = null, T high = null)
{
    return {"smoothstep", T: in=in, low=low, high=high};
}

T smoothstep<vec2, vec3, vec4, color3, color4>(T in, float low = null, float high = null)
{
    return {"smoothstep", T: in=in, low=low, high=high};
}

// ----------------  image  ----------------

T image<float, vec2, vec3, vec4, color3, color4>(
    filename file,
    string layer = null,
    T default = null,
    vec2 texcoord = null,
    string uaddressmode = null,
    string vaddressmode = null,
    string filtertype = null
)
{
    return {"image", T:
        file=file,
        layer=layer,
        default=default,
        texcoord=texcoord,
        uaddressmode=uaddressmode,
        vaddressmode=vaddressmode,
        filtertype=filtertype
    };
}

// ----------------  tiledimage  ----------------

T tiledimage<float, vec2, vec3, vec4, color3, color4>(
    filename file,
    T default = null,
    vec2 texcoord = null,
    vec2 uvtiling = null,
    vec2 uvoffset = null,
    vec2 realworldimagesize = null,
    vec2 realworldtilesize = null,
    string filtertype = null
)
{
    return {"tiledimage", T:
        file=file,
        default=default,
        texcoord=texcoord,
        uvtiling=uvtiling,
        uvoffset=uvoffset,
        realworldimagesize=realworldimagesize,
        realworldtilesize=realworldtilesize,
        filtertype=filtertype
    };
}

// ----------------  latlongimage  ----------------

T latlongimage<float, vec2, vec3, vec4, color3, color4>(
    filename file,
    T default = null,
    vec3 viewdir = null,
    float rotation = null
)
{
    return {"latlongimage", T:
        file=file,
        default=default,
        viewdir=viewdir,
        rotation=rotation
    };
}

// ----------------  triplanarprojection  ----------------

T triplanarprojection<float, vec2, vec3, vec4, color3, color4>(
    filename filex,
    filename filey,
    filename filez,
    string layerx = null,
    string layery = null,
    string layerz = null,
    T default = null,
    vec3 position = null,
    vec3 normal = null,
    int upaxis = null,
    float blend = null,
    string filtertype = null
)
{
    return {"triplanarprojection", T:
        filex=filex,
        filey=filey,
        filez=filez,
        layerx=layerx,
        layery=layery,
        layerz=layerz,
        default=default,
        position=position,
        normal=normal,
        upaxis=upaxis,
        blend=blend,
        filtertype=filtertype
    };
}

// ----------------  ramplr  ----------------

T ramplr<float, vec2, vec3, vec4, color3, color4>(T valuel = null, T valuer = null, vec2 texcoord = null)
{
    return {"ramplr", T: valuel=valuel, valuer=valuer, texcoord=texcoord};
}

// ----------------  ramptb  ----------------

T ramptb<float, vec2, vec3, vec4, color3, color4>(T valuet = null, T valueb = null, vec2 texcoord = null)
{
    return {"ramptb", T: valuet=valuet, valueb=valueb, texcoord=texcoord};
}

// ----------------  ramp4  ----------------

T ramp4<float, vec2, vec3, vec4, color3, color4>(T valuetl = null, T valuetr = null, T valuebl = null, T valuebr = null, vec2 texcoord = null)
{
    return {"ramp4", T: valuetl=valuetl, valuetr=valuetr, valuebl=valuebl, valuebr=valuebr, texcoord=texcoord};
}

// ----------------  splitlr  ----------------

T splitlr<float, vec2, vec3, vec4, color3, color4>(T valuel = null, T valuer = null, float center = null, vec2 texcoord = null)
{
    return {"splitlr", T: valuel=valuel, valuer=valuer, center=center, texcoord=texcoord};
}

// ----------------  splittb  ----------------

T splittb<float, vec2, vec3, vec4, color3, color4>(T valuet = null, T valueb = null, float center = null, vec2 texcoord = null)
{
    return {"splittb", T: valuel=valuet, valuer=valueb, center=center, texcoord=texcoord};
}

// ----------------  blur  ----------------

T blur<float, vec2, vec3, vec4, color3, color4>(T in, float size, string filtertype = null)
{
    return {"blur", T: in=in, size=size, filtertype=filtertype};
}

// ----------------  heighttonormal  ----------------

vec3 heighttonormal(float in, float scale = null, vec2 texcoord = null)
{
    return {"heighttonormal", vec3: in=in, scale=scale, texcoord=texcoord};
}

// ----------------  contrast  ----------------

T contrast<float, vec2, vec3, vec4, color3, color4>(T in, T amount, T pivot = null)
{
    return {"contrast", T: in=in, amount=amount, pivot=pivot};
}

T contrast<vec2, vec3, vec4, color3, color4>(T in, float amount, float pivot = null)
{
    return {"contrast", T: in=in, amount=amount, pivot=pivot};
}

// ----------------  remap  ----------------

T remap<float, vec2, vec3, vec4, color3, color4>(T in, T inlow = null, T inhigh = null, T outlow = null, T outhigh = null)
{
    return {"remap", T: in=in, inlow=inlow, inhigh=inhigh, outlow=outlow, outhigh=outhigh};
}

T remap<vec2, vec3, vec4, color3, color4>(T in, float inlow = null, float inhigh = null, float outlow = null, float outhigh = null)
{
    return {"remap", T: in=in, inlow=inlow, inhigh=inhigh, outlow=outlow, outhigh=outhigh};
}

// ----------------  range  ----------------

T range<float, vec2, vec3, vec4, color3, color4>(T in, T inlow = null, T inhigh = null, T gamma = null, T outlow = null, T outhigh = null, bool doclamp = null)
{
    return {"range", T: in=in, inlow=inlow, inhigh=inhigh, gamma=gamma, outlow=outlow, outhigh=outhigh, doclamp=doclamp};
}

T range<vec2, vec3, vec4, color3, color4>(T in, float inlow = null, float inhigh = null, float gamma = null, float outlow = null, float outhigh = null, bool doclamp = null)
{
    return {"range", T: in=in, inlow=inlow, inhigh=inhigh, gamma=gamma, outlow=outlow, outhigh=outhigh, doclamp=doclamp};
}

// ----------------  luminance  ----------------

T luminance<color3, color4>(T in, color3 lumacoeffs = null)
{
    return {"luminance", T: in=in, lumacoeffs=lumacoeffs};
}

// ----------------  rgbtohsv  ----------------

T rgbtohsv<color3, color4>(T in)
{
    return {"rgbtohsv", T: in=in};
}

// ----------------  hsvtorgb  ----------------

T hsvtorgb<color3, color4>(T in)
{
    return {"hsvtorgb", T: in=in};
}

// ----------------  hsvadjust  ----------------

T hsvadjust<color3, color4>(T in, vec3 amount = null)
{
    return {"hsvadjust", T: in=in, amount=amount};
}

// ----------------  saturate  ----------------

T saturate<color3, color4>(T in, float amount = null, color3 lumacoeffs = null)
{
    return {"saturate", T: in=in, amount=amount, lumacoeffs=lumacoeffs};
}

// ----------------  colorcorrect  ----------------

T colorcorrect<color3, color4>(
    T in,
    float hue = null,
    float saturation = null,
    float gamma = null,
    float lift = null,
    float gain = null,
    float contrast = null,
    float contrastpivot = null,
    float exposure = null
)
{
    return {"colorcorrect", T:
        in=in,
        hue=hue,
        saturation=saturation,
        gamma=gamma,
        lift=lift,
        gain=gain,
        contrast=contrast,
        contrastpivot=contrastpivot,
        exposure=exposure
    };
}

// ----------------  premult  ----------------

color4 premult(color4 in)
{
    return {"premult", color4: in=in};
}

// ----------------  unpremult  ----------------

color4 unpremult(color4 in)
{
    return {"unpremult", color4: in=in};
}

// ----------------  plus  ----------------

T plus<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"plus", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  minus  ----------------

T minus<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"minus", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  difference  ----------------

T difference<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"difference", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  burn  ----------------

T burn<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"burn", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  dodge  ----------------

T dodge<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"dodge", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  screen  ----------------

T screen<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"screen", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  overlay  ----------------

T overlay<float, color3, color4>(T bg = null, T fg = null, float mix = null)
{
    return {"overlay", T: bg=bg, fg=fg, mix=mix};
}

// ----------------  disjointover  ----------------

color4 disjointover(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"disjointover", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  in  ----------------

color4 in(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"in", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  mask  ----------------

color4 mask(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"mask", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  matte  ----------------

color4 matte(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"matte", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  out  ----------------

color4 out(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"out", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  over  ----------------

color4 over(color4 bg = null, color4 fg = null, float mix = null)
{
    return {"over", color4: bg=bg, fg=fg, mix=mix};
}

// ----------------  inside  ----------------

T inside<float, color3, color4>(T in = null, float mask = null)
{
    return {"inside", color4: in=in, mask=mask};
}

// ----------------  outside  ----------------

T outside<float, color3, color4>(T in = null, float mask = null)
{
    return {"outside", color4: in=in, mask=mask};
}

#endif // STDLIB_DEFS

"""
