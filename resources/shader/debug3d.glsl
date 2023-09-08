#version 460

#ifdef VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;
in vec3 in_normal;

uniform mat4 Proj;
uniform mat4 View;

out vec3 N;

void main(){
    gl_Position = Proj * View * vec4(in_position, 1.0);
    N = in_normal;
}

#elif FRAGMENT_SHADER

in vec3 N;
layout(location=0) out vec4 fragColor;

void main(){
    fragColor = vec4(N, 1.0);
}

#endif