#version 460

uniform float t;
uniform float N;
uniform float L;
uniform float w_speed;

layout(location=0) uniform sampler2D noiseTex;

#define PI acos(-1.)

#ifdef VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;

out vec2 uv;

void main(){
    gl_Position = vec4(in_position, 1.0);
    uv = in_texcoord_0;
}

#elif FRAGMENT_SHADER

// float L = 500;

// float w_speed = 5;
float g = 9.81;
vec2 w_dir = normalize(vec2(1.));
float A = pow(w_speed, 2)/g;

in vec2 uv;
layout(location=0) out vec4 fragColor;
layout(location=1) out vec4 fragColor1;
// layout(location=2) out vec4 fragColor2;

vec2 euler(float theta){
    return vec2(cos(theta), sin(theta));
}

vec2 conj(vec2 c){
    return vec2(c.x, -c.y);
}

vec2 multC(vec2 a, vec2 b){
    return vec2(a.x*b.x-a.y*b.y, a.x*b.y+a.y*b.x);
}

float Philips(vec2 K, float L, vec2 w_dir, float V, float g){
    float k = length(K);
    float L_ = V*V/g;
    return L_*exp(-1./pow((k*L), 2))*pow(abs(dot(normalize(K), w_dir)), 2)/pow(k, 4)/L;
}


void main(){
    vec2 K = 2*PI*(uv.xy*N-0.5*N)/L;

    float k = length(K)+0.00001;

    float P_k = Philips(K, L, w_dir, w_speed, g);//V*V*exp(-1./pow((k*L), 2))*pow(dot(normalize(K), w_dir), 2)/pow(k, 4)/g;
    float P_minus_k = Philips(-K, L, w_dir, w_speed, g);

    vec2 h_0_k = vec2(texture(noiseTex, uv).xy)*sqrt(P_k/2.);
    vec2 h_0_minus_k = vec2(texture(noiseTex, uv).zw)*sqrt(P_minus_k/2.);
    
    float omega = sqrt(g*k);

    vec2 h_k_t = multC(h_0_k, euler(-omega*t)) + multC(conj(h_0_minus_k), euler(-omega*t));

    vec2 dx = vec2(0, K.x/k);
    vec2 dy = vec2(0, K.y/k);

    vec2 Dktx = multC(dx, h_k_t);
    vec2 Dkty = multC(dy, h_k_t);

    fragColor = vec4(h_k_t, 0.0, 0.0);
    fragColor1 = vec4(Dktx, Dkty);
    // fragColor2 = vec4(Dkty, 0.0, 0.0);
}

#endif