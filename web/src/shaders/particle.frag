// Salish Sea Particle Fragment Shader
// Soft, organic particles with bioluminescent glow

uniform float uTime;
uniform float uStillness;

varying vec3 vColor;
varying float vAlpha;
varying float vDepthLayer;

void main() {
  // Circular particle with soft edge
  vec2 center = gl_PointCoord - 0.5;
  float dist = length(center);

  if (dist > 0.5) {
    discard;
  }

  // Soft falloff for organic look
  float alpha = 1.0 - smoothstep(0.2, 0.5, dist);
  alpha *= vAlpha;

  // Subtle pulse for bioluminescence
  float pulse = 1.0 + sin(uTime * 2.0 + vDepthLayer * 10.0) * 0.1 * uStillness;

  vec3 color = vColor * pulse;

  // Add subtle glow halo for deeper layers
  float glow = (1.0 - smoothstep(0.0, 0.5, dist)) * vDepthLayer * uStillness * 0.3;
  color += vec3(0.1, 0.3, 0.25) * glow;

  gl_FragColor = vec4(color, alpha);
}
