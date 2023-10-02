#version 460

uniform float t;
uniform float N;
uniform float L;
// uniform float w_speed;

layout(location=0) uniform sampler2D noiseTex;

const float PI =  acos(-1.);

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

float w_speed = 5;
float g = 9.81;
vec2 w_dir = normalize(vec2(1.));

in vec2 uv;
layout(location=0) out vec4 fragColor;
// layout(location=1) out vec4 fragColor1;
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

float PiersonMoskowiz(vec2 K, float wind, vec2 wind_dir){
    float g = 9.81;
    float k = length(K)+0.0001;
    float omega = sqrt(g*k);
    float alpha = 0.0081;
    float Sp = alpha*g*g/pow(omega, 5);
    float omega_p = 0.855*g/wind;
    float Spm = Sp*exp(-5*pow(omega_p/omega, 4)/4);
    float D_theta = pow(abs(dot(K/k, wind_dir)), 6);
    return Spm*D_theta*0.5*sqrt(g/k);
}


void main(){
    vec2 K = 2*PI*(uv.xy*N-0.5*N)/L;

    float k = length(K)+0.0001;

    float PM_k = PiersonMoskowiz(K, w_speed, w_dir);//V*V*exp(-1./pow((k*L), 2))*pow(dot(normalize(K), w_dir), 2)/pow(k, 4)/g;
    float PM_minus_k = PiersonMoskowiz(-K, w_speed, w_dir);

    vec2 h_0_k = vec2(texture(noiseTex, uv).xy)*sqrt(2*PM_k)*1e4;
    vec2 h_0_minus_k = vec2(texture(noiseTex, uv).zw)*sqrt(2*PM_minus_k)*1e4;
    
    float omega = sqrt(g*k);

    vec2 h_k_t = 0.5*multC(h_0_k, euler(-omega*t)) + 0.5*multC(conj(h_0_minus_k), euler(omega*t));

    // vec2 dx = vec2(0, K.x/k);
    // vec2 dy = vec2(0, K.y/k);

    // vec2 Dktx = multC(dx, h_k_t);
    // vec2 Dkty = multC(dy, h_k_t);

    fragColor = vec4(h_k_t, 0.0, 0.0);
    // fragColor1 = vec4(Dktx, Dkty);
    // fragColor2 = vec4(Dkty, 0.0, 0.0);
}

#endif