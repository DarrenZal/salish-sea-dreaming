// Salish Sea Dreaming - Interactive Web Prototype
// "We are the Salish Sea, dreaming itself awake."

import * as THREE from 'three';
import { CONFIG } from './config.js';

// Shader imports (Vite handles these)
import vertexShader from './shaders/particle.vert?raw';
import fragmentShader from './shaders/particle.frag?raw';

// ============================================================================
// State
// ============================================================================

const state = {
  mouse: new THREE.Vector2(0, 0),
  mouseWorld: new THREE.Vector3(0, 0, 0),
  lastMouseMove: Date.now(),
  stillness: 0,
  stillnessTarget: 0,
  lastMousePos: new THREE.Vector2(0, 0)
};

// ============================================================================
// Scene Setup
// ============================================================================

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020408); // Deep ocean dark

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.z = 30;

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

// ============================================================================
// Particle System
// ============================================================================

function createParticleSystem() {
  const { count, spread, depth } = CONFIG.particles;

  const geometry = new THREE.BufferGeometry();

  // Position particles in a volume
  const positions = new Float32Array(count * 3);
  const phases = new Float32Array(count);
  const depthLayers = new Float32Array(count);
  const baseColors = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    const i3 = i * 3;

    // Distribute in a spherical volume
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = Math.pow(Math.random(), 0.5) * spread; // Square root for even distribution

    positions[i3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.6; // Flatten slightly
    positions[i3 + 2] = r * Math.cos(phi) * (depth / spread);

    // Random phase for varied animation
    phases[i] = Math.random();

    // Depth layer (0 = surface, 1 = deep)
    // More particles at surface, fewer in deep
    depthLayers[i] = Math.pow(Math.random(), 2);

    // Base color - deeper = more varied
    const layer = depthLayers[i];
    const colorSet = CONFIG.colors.surface;
    const colorIndex = Math.floor(Math.random() * colorSet.length);
    const color = colorSet[colorIndex];

    // Slight variation
    baseColors[i3] = color[0] + (Math.random() - 0.5) * 0.1;
    baseColors[i3 + 1] = color[1] + (Math.random() - 0.5) * 0.1;
    baseColors[i3 + 2] = color[2] + (Math.random() - 0.5) * 0.1;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));
  geometry.setAttribute('aDepthLayer', new THREE.BufferAttribute(depthLayers, 1));
  geometry.setAttribute('aBaseColor', new THREE.BufferAttribute(baseColors, 3));

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uStillness: { value: 0 },
      uParticleSize: { value: CONFIG.particles.size },
      uPresencePos: { value: new THREE.Vector3(0, 0, 0) },
      uPresenceStrength: { value: 0 }
    },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });

  const particles = new THREE.Points(geometry, material);
  scene.add(particles);

  return { geometry, material, particles };
}

const particleSystem = createParticleSystem();

// ============================================================================
// Interaction
// ============================================================================

function onMouseMove(event) {
  // Normalized mouse position
  state.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  state.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  // Track movement for stillness detection
  const dx = state.mouse.x - state.lastMousePos.x;
  const dy = state.mouse.y - state.lastMousePos.y;
  const movement = Math.sqrt(dx * dx + dy * dy);

  if (movement > CONFIG.stillness.threshold) {
    state.lastMouseMove = Date.now();
    state.stillnessTarget = 0;
  }

  state.lastMousePos.copy(state.mouse);

  // Project mouse to world space (on a plane at z=0)
  const vector = new THREE.Vector3(state.mouse.x, state.mouse.y, 0.5);
  vector.unproject(camera);
  const dir = vector.sub(camera.position).normalize();
  const distance = -camera.position.z / dir.z;
  state.mouseWorld = camera.position.clone().add(dir.multiplyScalar(distance));
}

function onTouchMove(event) {
  if (event.touches.length > 0) {
    onMouseMove({
      clientX: event.touches[0].clientX,
      clientY: event.touches[0].clientY
    });
  }
}

window.addEventListener('mousemove', onMouseMove);
window.addEventListener('touchmove', onTouchMove);

// ============================================================================
// Resize Handler
// ============================================================================

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

window.addEventListener('resize', onResize);

// ============================================================================
// UI Updates
// ============================================================================

const stillnessIndicator = document.getElementById('stillness-indicator');
const info = document.getElementById('info');

function updateUI() {
  if (state.stillness > 0.1) {
    const depth = Math.floor(state.stillness * 100);
    stillnessIndicator.textContent = `Depth: ${depth}%`;
    stillnessIndicator.style.opacity = state.stillness;
  } else {
    stillnessIndicator.textContent = '';
  }

  // Fade out info after first interaction
  if (state.stillness > 0.5) {
    info.classList.add('hidden');
  }
}

// ============================================================================
// Animation Loop
// ============================================================================

function animate() {
  requestAnimationFrame(animate);

  const time = performance.now() * 0.001;

  // Update stillness
  const timeSinceMove = Date.now() - state.lastMouseMove;
  if (timeSinceMove > CONFIG.stillness.timeToDeepen) {
    // Gradually increase stillness
    const progress = (timeSinceMove - CONFIG.stillness.timeToDeepen) / 5000;
    state.stillnessTarget = Math.min(CONFIG.stillness.maxDepth, progress);
  }

  // Smooth stillness transitions
  state.stillness += (state.stillnessTarget - state.stillness) * 0.02;

  // Update shader uniforms
  const uniforms = particleSystem.material.uniforms;
  uniforms.uTime.value = time;
  uniforms.uStillness.value = state.stillness;
  uniforms.uPresencePos.value.copy(state.mouseWorld);
  uniforms.uPresenceStrength.value = CONFIG.presence.strength;

  // Gentle camera drift (the sea is never truly still)
  camera.position.x = Math.sin(time * 0.1) * 2;
  camera.position.y = Math.cos(time * 0.08) * 1;
  camera.lookAt(0, 0, 0);

  updateUI();

  renderer.render(scene, camera);
}

animate();

// ============================================================================
// Debug info (remove for production)
// ============================================================================

console.log('Salish Sea Dreaming - Web Prototype');
console.log('Move slowly. Be still. The sea reveals itself to those who wait.');
