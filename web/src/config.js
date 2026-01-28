// Salish Sea Dreaming - Configuration
// Stillness is rewarded, not performance

export const CONFIG = {
  // Particle system
  particles: {
    count: 50000,
    size: 2.0,
    spread: 40,
    depth: 30
  },

  // Stillness detection
  stillness: {
    threshold: 0.002,      // Movement below this = still
    timeToDeepen: 2000,    // ms of stillness before deepening
    maxDepth: 1.0          // Maximum revelation level
  },

  // Visual layers (revealed through stillness)
  layers: {
    surface: {
      // Always visible - gentle movement
      speed: 0.3,
      amplitude: 0.5
    },
    middle: {
      // Revealed after some stillness
      speed: 0.5,
      amplitude: 0.8,
      stillnessRequired: 0.3
    },
    deep: {
      // Revealed after sustained stillness
      speed: 0.8,
      amplitude: 1.2,
      stillnessRequired: 0.7
    }
  },

  // Colors - bioluminescent Salish Sea palette
  colors: {
    surface: [
      [0.1, 0.3, 0.5],   // Deep blue
      [0.05, 0.2, 0.4],  // Darker blue
      [0.15, 0.35, 0.45] // Teal hint
    ],
    bioluminescence: [
      [0.2, 0.8, 0.7],   // Cyan glow
      [0.3, 0.9, 0.6],   // Green glow
      [0.4, 0.6, 0.9],   // Soft blue glow
      [0.6, 0.4, 0.8]    // Purple hint
    ]
  },

  // Presence interaction
  presence: {
    radius: 8,           // How far presence affects particles
    strength: 0.3,       // How strongly particles respond
    gentleness: 0.95     // Smoothing factor (higher = gentler)
  }
};
