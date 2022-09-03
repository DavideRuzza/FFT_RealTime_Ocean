
#version 460

uniform mat4 proj;
uniform mat4 view;
uniform mat4 model;
uniform mat4 scale_model;
uniform vec3 eye;
uniform float wave_scale;

layout(binding=0) uniform sampler2D h_z;
layout(binding=1) uniform sampler2D d_xy;
layout(binding=2) uniform sampler2D norm_tex;

uniform float choppy;

#ifdef VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;


out vec2 uv;
out vec3 pos;

void main(){
    uv = in_texcoord_0;
    
    vec3 delta = vec3(choppy*-texture(d_xy, uv).rg, texture(h_z, uv).r*wave_scale);
    pos = (scale_model*model*vec4(in_position, 1.0)+model*vec4(delta, 1.0)).xyz;

    gl_Position = proj*view*(scale_model*model*vec4(in_position, 1.0)+model*vec4(delta, 1.0));

    
}

#elif FRAGMENT_SHADER

in vec2 uv;
in vec3 pos;

layout(location=0) out vec4 fragColor;

void main(){
    vec3 dir = normalize(pos-eye);
    vec3 sun_dir = normalize(vec3(1, 1, -0.8));
    vec3 N = normalize(texture(norm_tex, uv).xyz);

    float fresnel = pow(1-max(0, dot(-N, dir)), 3);
    float specular = max(0., dot(-N, sun_dir));
    vec3 color = mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), 1-fresnel);
    fragColor = vec4(vec3(specular), 0.0);
}

#endif