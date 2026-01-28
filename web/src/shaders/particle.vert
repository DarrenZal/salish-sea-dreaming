// Salish Sea Particle Vertex Shader
// Organic movement, presence response, stillness revelation

uniform float uTime;
uniform float uStillness;
uniform float uParticleSize;
uniform vec3 uPresencePos;
uniform float uPresenceStrength;

attribute float aPhase;
attribute float aDepthLayer;
attribute vec3 aBaseColor;

varying vec3 vColor;
varying float vAlpha;
varying float vDepthLayer;

// Smooth noise for organic movement
float noise(vec3 p) {
  return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453);
}

void main() {
  vDepthLayer = aDepthLayer;

  // Base position
  vec3 pos = position;

  // Organic flowing movement (like underwater currents)
  float flowSpeed = 0.3 + aDepthLayer * 0.2;
  float flowScale = 0.5 + aDepthLayer * 0.3;

  // Horizontal current
  pos.x += sin(uTime * flowSpeed + pos.y * 0.1 + aPhase * 6.28) * flowScale;
  pos.z += cos(uTime * flowSpeed * 0.7 + pos.x * 0.1 + aPhase * 3.14) * flowScale * 0.5;

  // Vertical drift (gentle rising/falling)
  pos.y += sin(uTime * flowSpeed * 0.5 + aPhase * 6.28) * flowScale * 0.3;

  // Presence interaction - particles gently move away
  vec3 toPresence = pos - uPresencePos;
  float distToPresence = length(toPresence);
  float presenceInfluence = smoothstep(8.0, 0.0, distToPresence) * uPresenceStrength;

  // Move away from presence, but gently
  if (distToPresence > 0.1) {
    pos += normalize(toPresence) * presenceInfluence * 2.0;
  }

  // Stillness reveals deeper layers
  // When still, deeper particles become more visible and active
  float layerVisibility = smoothstep(aDepthLayer - 0.1, aDepthLayer + 0.1, uStillness);

  // Deeper layers have more pronounced movement when revealed
  float stillnessBoost = uStillness * aDepthLayer;
  pos.x += sin(uTime * 0.8 + aPhase * 12.56) * stillnessBoost * 0.5;
  pos.y += cos(uTime * 0.6 + aPhase * 9.42) * stillnessBoost * 0.3;

  // Color based on depth and stillness
  vec3 baseColor = aBaseColor;

  // Bioluminescence increases with stillness and depth
  float glow = uStillness * aDepthLayer * 0.5;
  vec3 biolumColor = vec3(0.2, 0.8, 0.7); // Cyan bioluminescence
  vColor = mix(baseColor, biolumColor, glow);

  // Brighten when presence is near (curious response)
  vColor += vec3(0.1, 0.2, 0.15) * presenceInfluence;

  // Alpha based on layer visibility
  vAlpha = 0.3 + layerVisibility * 0.7;

  // Surface layer always visible
  if (aDepthLayer < 0.3) {
    vAlpha = 0.6;
  }

  vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);

  // Size based on depth and stillness
  float size = uParticleSize * (1.0 + aDepthLayer * uStillness * 0.5);
  gl_PointSize = size * (300.0 / -mvPosition.z);
  gl_PointSize = clamp(gl_PointSize, 1.0, 32.0);

  gl_Position = projectionMatrix * mvPosition;
}
