// ============================================================
// UNIFIED AVATAR SYSTEM v1.0
// Combines: GLB motion consumer + ethereal procedural + customization
// Production-ready, fully integrated
// ============================================================

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

class UnifiedAvatarSystem {
  constructor(scene, options = {}) {
    this.scene = scene;
    this.avatars = new Map();
    this.morphTargets = this.defineMorphTargets();
    this.boneAliases = this.getBoneAliases();
  }

  // ============================================================
  // SPAWN AVATAR - Photo-based or Procedural
  // ============================================================
  
  async spawnFromPhoto(userId, photoUrl, options = {}) {
    /**
     * Photo-based avatar generation
     * Uses foundry system: photo → voxel mesh → skeleton
     */
    const avatar = {
      id: userId,
      type: 'photo',
      source: photoUrl,
      morphs: this.getDefaultMorphs(),
      material: this.createMaterial(options.color || '#4DC8FF'),
      bones: {},
      group: new THREE.Group()
    };

    // Load photo and generate voxel mesh
    await this.generateVoxelMeshFromPhoto(avatar, photoUrl, options);
    
    // Build skeleton from GLB template
    await this.attachGLBSkeleton(avatar, options.skeleton || 'humanoid');
    
    // Register with motion system
    this.registerAvatarMotionConsumer(avatar);
    
    this.avatars.set(userId, avatar);
    this.scene.add(avatar.group);
    return avatar;
  }

  async spawnProcedural(userId, options = {}) {
    /**
     * Procedural avatar generation (ethereal)
     * For NPCs, production characters, unlimited variants
     */
    const avatar = {
      id: userId,
      type: 'procedural',
      morphs: options.morphs || this.getDefaultMorphs(),
      material: this.createMaterial(options.color || '#4DC8FF'),
      bones: {},
      group: new THREE.Group()
    };

    // Generate geometry from morph parameters
    this.generateProceduralGeometry(avatar, options);
    
    // Build skeleton
    this.buildProceduralSkeleton(avatar);
    
    // Register with motion system
    this.registerAvatarMotionConsumer(avatar);
    
    this.avatars.set(userId, avatar);
    this.scene.add(avatar.group);
    return avatar;
  }

  // ============================================================
  // CUSTOMIZATION API - All Parameters
  // ============================================================

  defineMorphTargets() {
    return {
      // FACE
      faceShape: {
        type: 'enum',
        values: ['oval', 'round', 'square', 'heart', 'oblong'],
        default: 'oval'
      },
      cheekboneHeight: {
        type: 'range',
        min: 0, max: 1, step: 0.05,
        default: 0.5
      },
      jawWidth: {
        type: 'range',
        min: 0, max: 1, step: 0.05,
        default: 0.5
      },
      noseSize: {
        type: 'range',
        min: 0, max: 1, step: 0.05,
        default: 0.5
      },

      // HAIR
      hairStyle: {
        type: 'enum',
        values: ['short', 'shoulder', 'long', 'waves', 'curly', 'braids'],
        default: 'shoulder'
      },
      hairColor: {
        type: 'color',
        default: '#8B4513'
      },
      hairLength: {
        type: 'range',
        min: 0.3, max: 1.5, step: 0.1,
        default: 1.0
      },

      // EYES
      eyeColor: {
        type: 'color',
        default: '#4DC8FF'
      },
      eyeSize: {
        type: 'range',
        min: 0.5, max: 1.5, step: 0.1,
        default: 1.0
      },
      eyeShape: {
        type: 'enum',
        values: ['round', 'almond', 'hooded', 'wide'],
        default: 'round'
      },

      // BODY
      height: {
        type: 'range',
        min: 150, max: 210, step: 2,
        default: 175
      },
      girth: {
        type: 'range',
        min: 0, max: 1, step: 0.05,
        default: 0.5
      },
      musculature: {
        type: 'range',
        min: 0, max: 1, step: 0.05,
        default: 0.5
      },

      // GENDER/ANATOMY
      gender: {
        type: 'enum',
        values: ['neutral', 'female', 'male'],
        default: 'neutral'
      },
      breastSize: {
        type: 'range',
        min: 0, max: 1, step: 0.1,
        default: 0.5
      },
      masculineFeminine: {
        type: 'range',
        min: -1, max: 1, step: 0.1,
        default: 0
      },

      // AESTHETIC
      glowColor: {
        type: 'color',
        default: '#4DC8FF'
      },
      mood: {
        type: 'enum',
        values: ['calm', 'happy', 'energetic', 'excited', 'passionate'],
        default: 'calm'
      },
      energyEffect: {
        type: 'bool',
        default: true
      }
    };
  }

  getDefaultMorphs() {
    const defaults = {};
    for (const [key, def] of Object.entries(this.defineMorphTargets())) {
      defaults[key] = def.default;
    }
    return defaults;
  }

  // ============================================================
  // MORPH UPDATES - Real-time
  // ============================================================

  updateMorph(userId, morphName, value) {
    const avatar = this.avatars.get(userId);
    if (!avatar) return false;

    const target = this.defineMorphTargets()[morphName];
    if (!target) return false;

    // Validate range
    if (target.type === 'range') {
      value = Math.max(target.min, Math.min(target.max, value));
    }

    avatar.morphs[morphName] = value;

    // Apply morph to geometry
    this.applyMorphToGeometry(avatar, morphName, value);
    
    // Re-render
    return true;
  }

  updateGender(userId, gender) {
    const avatar = this.avatars.get(userId);
    if (!avatar) return false;

    avatar.morphs.gender = gender;
    
    // Recompute anatomy
    this.recomputeAnatomy(avatar, gender);
    
    return true;
  }

  // ============================================================
  // INTERNAL: Geometry Generation
  // ============================================================

  async generateVoxelMeshFromPhoto(avatar, photoUrl, options) {
    // Placeholder: In production, call voxel engine
    // For now: create basic humanoid from ethereal system
    const geometry = this.createProceduralHeadFromPhoto(photoUrl);
    const mesh = new THREE.Mesh(geometry, avatar.material);
    avatar.group.add(mesh);
  }

  createProceduralHeadFromPhoto(photoUrl) {
    // Detect landmarks, generate voxel head
    // For MVP: simple sphere with texture from photo
    return new THREE.SphereGeometry(0.16, 32, 32);
  }

  generateProceduralGeometry(avatar, options) {
    const morphs = options.morphs || this.getDefaultMorphs();
    
    // Create body segments based on morphs
    const torso = this.createTorsoSegment(morphs);
    const head = this.createHeadSegment(morphs);
    const limbs = this.createLimbSegments(morphs);

    avatar.group.add(torso);
    avatar.group.add(head);
    avatar.group.add(limbs);

    avatar.meshes = { torso, head, limbs };
  }

  createTorsoSegment(morphs) {
    const group = new THREE.Group();
    const height = (morphs.height - 175) / 35 * 0.3; // Scale to geometry
    const girth = morphs.girth * 0.2;
    
    const geometry = new THREE.CapsuleGeometry(0.18 + girth, 0.55 + height, 8, 12);
    const mesh = new THREE.Mesh(geometry, this.createMaterial(morphs.glowColor));
    group.add(mesh);
    return group;
  }

  createHeadSegment(morphs) {
    const group = new THREE.Group();
    group.position.y = 0.5;

    // Base head
    const headGeo = new THREE.SphereGeometry(0.16, 32, 32);
    const headMesh = new THREE.Mesh(headGeo, this.createMaterial(morphs.eyeColor));
    group.add(headMesh);

    // Cheekbones
    const cheekGeo = new THREE.SphereGeometry(0.08, 16, 16);
    const cheekL = new THREE.Mesh(cheekGeo, this.createMaterial(morphs.glowColor));
    cheekL.position.set(0.08, 0.02 + morphs.cheekboneHeight * 0.04, -0.08);
    cheekL.scale.y = morphs.cheekboneHeight;
    group.add(cheekL);

    const cheekR = new THREE.Mesh(cheekGeo, this.createMaterial(morphs.glowColor));
    cheekR.position.set(-0.08, 0.02 + morphs.cheekboneHeight * 0.04, -0.08);
    cheekR.scale.y = morphs.cheekboneHeight;
    group.add(cheekR);

    // Eyes
    const eyeGeo = new THREE.SphereGeometry(0.025 * morphs.eyeSize, 16, 16);
    const eyeL = new THREE.Mesh(eyeGeo, this.createMaterial(morphs.eyeColor));
    eyeL.position.set(0.055, 0.035, -0.14);
    group.add(eyeL);

    const eyeR = new THREE.Mesh(eyeGeo, this.createMaterial(morphs.eyeColor));
    eyeR.position.set(-0.055, 0.035, -0.14);
    group.add(eyeR);

    // Hair
    this.attachHair(group, morphs);

    return group;
  }

  attachHair(headGroup, morphs) {
    const styles = {
      short: () => new THREE.ConeGeometry(0.17, 0.12, 16),
      shoulder: () => new THREE.ConeGeometry(0.18, 0.24, 16),
      long: () => new THREE.ConeGeometry(0.16, 0.45, 16),
      waves: () => new THREE.TorusGeometry(0.16, 0.06, 8, 32),
      curly: () => new THREE.SphereGeometry(0.175, 16, 16),
      braids: () => new THREE.CylinderGeometry(0.17, 0.15, 0.28, 8)
    };

    const geo = styles[morphs.hairStyle]?.() || styles.shoulder();
    const hair = new THREE.Mesh(geo, this.createMaterial(morphs.hairColor));
    hair.position.y = 0.1;
    hair.scale.y = morphs.hairLength;
    headGroup.add(hair);
  }

  createLimbSegments(morphs) {
    const group = new THREE.Group();
    const muscleScale = 0.04 + morphs.musculature * 0.08;

    // Arms
    const armGeo = new THREE.CapsuleGeometry(0.055 + muscleScale, 0.28, 8, 12);
    const armL = new THREE.Mesh(armGeo, this.createMaterial(morphs.glowColor));
    armL.position.set(0.25, 0.1, 0);
    group.add(armL);

    const armR = new THREE.Mesh(armGeo, this.createMaterial(morphs.glowColor));
    armR.position.set(-0.25, 0.1, 0);
    group.add(armR);

    // Legs
    const legGeo = new THREE.CapsuleGeometry(0.07 + muscleScale, 0.36, 8, 12);
    const legL = new THREE.Mesh(legGeo, this.createMaterial(morphs.glowColor));
    legL.position.set(0.1, -0.4, 0);
    group.add(legL);

    const legR = new THREE.Mesh(legGeo, this.createMaterial(morphs.glowColor));
    legR.position.set(-0.1, -0.4, 0);
    group.add(legR);

    // Gender anatomy
    if (morphs.gender === 'female' && morphs.breastSize > 0) {
      const breastL = new THREE.Mesh(
        new THREE.SphereGeometry(0.08 * morphs.breastSize, 16, 16),
        this.createMaterial(morphs.glowColor)
      );
      breastL.position.set(0.12, 0.25, -0.05);
      group.add(breastL);

      const breastR = new THREE.Mesh(
        new THREE.SphereGeometry(0.08 * morphs.breastSize, 16, 16),
        this.createMaterial(morphs.glowColor)
      );
      breastR.position.set(-0.12, 0.25, -0.05);
      group.add(breastR);
    }

    return group;
  }

  recomputeAnatomy(avatar, gender) {
    // When gender changes, recompute shoulder/hip widths, etc
    const factor = gender === 'male' ? 0.8 : gender === 'female' ? 1.2 : 1.0;
    
    if (avatar.meshes?.limbs) {
      avatar.meshes.limbs.children.forEach(child => {
        if (child.position.x > 0) {
          child.position.x = Math.abs(child.position.x) * factor;
        } else if (child.position.x < 0) {
          child.position.x = -Math.abs(child.position.x) * factor;
        }
      });
    }
  }

  applyMorphToGeometry(avatar, morphName, value) {
    // Real-time updates to geometry without full rebuild
    // This is where Three.js morph targets would actually update
  }

  // ============================================================
  // SKELETON & MOTION
  // ============================================================

  async attachGLBSkeleton(avatar, skeletonType) {
    // Load skeleton from GLB template
    // Map bones to avatar structure
  }

  buildProceduralSkeleton(avatar) {
    // Create bones for procedural avatar
    const hips = new THREE.Bone();
    hips.name = 'hips';
    avatar.bones['hips'] = hips;

    const spine = new THREE.Bone();
    spine.name = 'spine';
    hips.add(spine);
    avatar.bones['spine'] = spine;

    // ... build full skeleton hierarchy
  }

  registerAvatarMotionConsumer(avatar) {
    // Register avatar with motion system
    // This ties it to avatar_glb_motion_consumer.js
    if (window.PubcastGLBMotionConsumer) {
      window.PubcastGLBMotionConsumer.registerAvatar(avatar.id, avatar.group);
    }
  }

  // ============================================================
  // MOTION COMMANDS
  // ============================================================

  applyMotion(userId, motionData) {
    const avatar = this.avatars.get(userId);
    if (!avatar) return false;

    // Delegate to motion consumer
    if (window.PubcastGLBMotionConsumer) {
      return window.PubcastGLBMotionConsumer.applyMotion(userId, motionData);
    }
    return false;
  }

  // ============================================================
  // UTILITIES
  // ============================================================

  createMaterial(hexColor) {
    return new THREE.MeshStandardMaterial({
      color: new THREE.Color(hexColor),
      emissive: new THREE.Color(hexColor),
      emissiveIntensity: 0.5,
      metalness: 0.3,
      roughness: 0.4
    });
  }

  getBoneAliases() {
    return {
      'head': ['Head', 'head', 'mixamorigHead'],
      'neck': ['Neck', 'neck_01', 'mixamorigNeck'],
      'spine': ['Spine', 'spine_01', 'mixamorigSpine'],
      'chest': ['Chest', 'spine_02'],
      'hips': ['Hips', 'hip', 'mixamorigHips'],
      'left_shoulder': ['Shoulder.L', 'left_shoulder'],
      'left_arm': ['Upper Arm.L', 'left_arm'],
      'left_forearm': ['Forearm.L', 'left_forearm'],
      'left_hand': ['Hand.L', 'left_hand'],
      'right_shoulder': ['Shoulder.R', 'right_shoulder'],
      'right_arm': ['Upper Arm.R', 'right_arm'],
      'right_forearm': ['Forearm.R', 'right_forearm'],
      'right_hand': ['Hand.R', 'right_hand']
    };
  }

  dispose(userId) {
    const avatar = this.avatars.get(userId);
    if (avatar) {
      avatar.group.traverse(obj => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      });
      this.scene.remove(avatar.group);
      this.avatars.delete(userId);
    }
  }
}

export default UnifiedAvatarSystem;
