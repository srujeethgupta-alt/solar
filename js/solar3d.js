(function() {
  function initSolar3D() {
    var container = document.getElementById('three-container');
    if (!container || !window.THREE) return;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Lights
    var ambient = new THREE.AmbientLight(0x222244, 0.5);
    scene.add(ambient);
    var sunLight = new THREE.DirectionalLight(0xffcc44, 2);
    sunLight.position.set(5, 8, 5);
    scene.add(sunLight);
    var fillLight = new THREE.DirectionalLight(0x0ea5e9, 0.6);
    fillLight.position.set(-3, 2, -4);
    scene.add(fillLight);
    var rimLight = new THREE.DirectionalLight(0x22c55e, 0.3);
    rimLight.position.set(0, -5, 3);
    scene.add(rimLight);

    // Sun sphere
    var sunGeo = new THREE.SphereGeometry(0.9, 32, 32);
    var sunMat = new THREE.MeshStandardMaterial({
      color: 0xffc107,
      emissive: 0xffa000,
      emissiveIntensity: 2,
      roughness: 0.2,
      metalness: 0.1
    });
    var sun = new THREE.Mesh(sunGeo, sunMat);
    sun.position.set(0, 0.5, 0);
    scene.add(sun);

    // Sun glow sprite
    var glowCanvas = document.createElement('canvas');
    glowCanvas.width = 128;
    glowCanvas.height = 128;
    var ctx = glowCanvas.getContext('2d');
    var gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    gradient.addColorStop(0, 'rgba(255, 193, 7, 1)');
    gradient.addColorStop(0.2, 'rgba(255, 160, 0, 0.8)');
    gradient.addColorStop(0.5, 'rgba(255, 100, 0, 0.3)');
    gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 128, 128);
    var glowTexture = new THREE.CanvasTexture(glowCanvas);
    var glowMat = new THREE.SpriteMaterial({
      map: glowTexture,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    var glowSprite = new THREE.Sprite(glowMat);
    glowSprite.scale.set(5, 5, 1);
    sun.add(glowSprite);

    // Solar panel group
    var panelGroup = new THREE.Group();
    panelGroup.position.set(0, -0.3, 0);

    var panelColors = [0x1a1a2e, 0x16213e, 0x0f3460];
    for (var i = 0; i < 8; i++) {
      var panel = new THREE.Mesh(
        new THREE.BoxGeometry(0.8, 0.05, 0.5),
        new THREE.MeshStandardMaterial({
          color: panelColors[i % panelColors.length],
          roughness: 0.3,
          metalness: 0.4,
          emissive: 0x0ea5e9,
          emissiveIntensity: 0.05
        })
      );
      var angle = (i / 8) * Math.PI * 2;
      var radius = 2.4;
      panel.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
      panel.rotation.y = -angle;
      panel.rotation.x = 0.3;
      panelGroup.add(panel);

      // Panel grid lines
      var lineMat = new THREE.LineBasicMaterial({
        color: 0x0ea5e9,
        transparent: true,
        opacity: 0.15
      });
      var gridPoints = [
        new THREE.Vector3(-0.35, 0.03, -0.2),
        new THREE.Vector3(0.35, 0.03, -0.2),
        new THREE.Vector3(0.35, 0.03, 0.2),
        new THREE.Vector3(-0.35, 0.03, 0.2),
        new THREE.Vector3(-0.35, 0.03, -0.2)
      ];
      var lineGeo = new THREE.BufferGeometry().setFromPoints(gridPoints);
      var line = new THREE.Line(lineGeo, lineMat);
      line.position.copy(panel.position);
      line.rotation.copy(panel.rotation);
      panelGroup.add(line);
    }
    scene.add(panelGroup);

    // Orbit ring
    var ringGeo = new THREE.RingGeometry(2.7, 2.85, 64);
    var ringMat = new THREE.MeshBasicMaterial({
      color: 0xffc107,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.08,
      depthWrite: false
    });
    var ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.05;
    scene.add(ring);

    // Particles
    var particleCount = 200;
    var particleGeo = new THREE.BufferGeometry();
    var positions = new Float32Array(particleCount * 3);
    for (var i = 0; i < particleCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 12;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    var particleMat = new THREE.PointsMaterial({
      color: 0xffc107,
      size: 0.03,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    var particles = new THREE.Points(particleGeo, particleMat);
    particles.position.y = 1;
    scene.add(particles);

    camera.position.set(4.5, 3, 5.5);
    camera.lookAt(0, 0.3, 0);

    var mouseX = 0, mouseY = 0;
    var targetRotX = 0, targetRotY = 0;

    function onMouseMove(e) {
      var rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      targetRotY = mouseX * 0.3;
      targetRotX = mouseY * 0.15;
    }

    function onResize() {
      var w = container.clientWidth;
      var h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }

    container.addEventListener('mousemove', onMouseMove);
    window.addEventListener('resize', onResize);

    var time = 0;

    function animate() {
      requestAnimationFrame(animate);
      time += 0.005;

      var rotY = targetRotY + Math.sin(time * 0.3) * 0.05;
      var rotX = targetRotX + Math.sin(time * 0.2) * 0.03;
      var baseY = 0.3;

      var pivot = new THREE.Group();
      pivot.position.set(0, baseY, 0);
      pivot.rotation.x = rotX;
      pivot.rotation.y = rotY;

      var offset = new THREE.Vector3(0, 0, 5.5);
      offset.applyQuaternion(pivot.quaternion);
      camera.position.copy(new THREE.Vector3(0, baseY, 0).add(offset));
      camera.lookAt(0, 0.3, 0);

      // Rotate panel group independently
      panelGroup.rotation.y += 0.002;

      // Animate sun
      sun.scale.setScalar(1 + Math.sin(time * 2) * 0.03);

      // Pulse emissive intensity
      sunMat.emissiveIntensity = 1.5 + Math.sin(time * 3) * 0.8;

      // Animate particles
      var pos = particles.geometry.attributes.position.array;
      for (var i = 0; i < particleCount; i++) {
        pos[i * 3 + 1] += Math.sin(time + i) * 0.0003;
      }
      particles.geometry.attributes.position.needsUpdate = true;

      // Animate ring opacity
      ringMat.opacity = 0.05 + Math.sin(time) * 0.03;

      renderer.render(scene, camera);
    }

    animate();
  }

  // Wait for container and Three.js then init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(initSolar3D, 800);
    });
  } else {
    setTimeout(initSolar3D, 800);
  }
})();
