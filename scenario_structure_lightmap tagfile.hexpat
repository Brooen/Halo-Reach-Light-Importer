#pragma pattern_limit 99999999999
#pragma array_limit 9999999999999
import std.io;
struct header {
    padding [184];
    u32 stringlength;
};

struct strings {
    if ($-parent.beginBlock >= parent.header.stringlength)
        break;
    char string[];
};

struct block1 {
    padding [8];
    u32 size;
    padding [size];
};

struct color {
    float r;
    float g;
    float b;
}  [[static, color(std::format("{:02X}{:02X}{:02X}", u8(255*r), u8(255*g), u8(255*b)))]];

struct xyz {
    float x;
    float y;
    float z;
};

enum lighttype : u32 {
    omni,
    spot,
    directional
};

enum shape : u32 {
    rectangle,
    circle
};

enum bungie_light_type : u16 {
    default_lightmap_light,
    uber_light,
    inlined_light,
    screen_space_light,
    rerender_lights
};

struct reference {
    lighttype type;
    u32 flags;
    shape shape;
    color color;
    float intensity;
    float hotspot_size;
    float hotspot_cutoff_size;
    float hotspot_falloff_speed;
    float near_attenuation_bounds[2]; //low and high
    float far_attenuation_bounds[2]; //low and high
    float aspect;
    u32 clipping_planes[5];// x -x y -y z -z idk why its 5
};

struct instance {
    u32 definition_index;
    u32 shader_reference_index;
    xyz origin;
    xyz forward;
    xyz up;
    bungie_light_type bungie_light_type;
    padding[2];
    u32 screen_space_specular;
    float bounce_light_control;
    float light_volume_distance;
    float fade_out_distance;
    float fade_start_distance;
    padding [64];
};


struct lightdata {
    padding [132];
    u32 referencecount;
    reference reference[referencecount];
    padding [16];
    u32 instancecount;
    padding [4];
    instance instance[instancecount];
};

struct final {
    header header;
    u64 beginBlock = $;
    strings strings[while(true)];
    block1 block1[11];
    lightdata lightdata[[no_unique_address]];
    block1 block2[3];
};

final final @ 0;