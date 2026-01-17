// Three.js Robot Mascot
// Uses global THREE variable from CDN

const container = document.getElementById('robot-canvas');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); // Brighter ambient
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0x10b981, 2.5); // Emerald, stronger
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);

const pointLight = new THREE.PointLight(0x06b6d4, 1.5, 100); // Cyan, stronger
pointLight.position.set(-5, 5, 5);
scene.add(pointLight);

// Robot Group
const robot = new THREE.Group();
scene.add(robot);

// Materials
const metalMat = new THREE.MeshStandardMaterial({ 
    color: 0xffffff, // Pure White
    roughness: 0.2, 
    metalness: 0.5 // Reduced metalness for brighter look
});
const glowMat = new THREE.MeshBasicMaterial({ color: 0x10b981 }); // Emerald
const eyeMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 }); // Cyan

// Head
const headGeo = new THREE.BoxGeometry(1.2, 1, 1);
const head = new THREE.Mesh(headGeo, metalMat);
robot.add(head);

// Eyes
const eyeGeo = new THREE.SphereGeometry(0.15, 16, 16);
const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
leftEye.position.set(-0.3, 0.1, 0.5);
head.add(leftEye);

const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
rightEye.position.set(0.3, 0.1, 0.5);
head.add(rightEye);

// Antenna
const antStemGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.5);
const antStem = new THREE.Mesh(antStemGeo, metalMat);
antStem.position.set(0, 0.75, 0);
head.add(antStem);

const antBulbGeo = new THREE.SphereGeometry(0.1);
const antBulb = new THREE.Mesh(antBulbGeo, glowMat);
antBulb.position.set(0, 1, 0);
head.add(antBulb);

// Body
const bodyGeo = new THREE.CylinderGeometry(0.8, 0.6, 1.5, 8);
const body = new THREE.Mesh(bodyGeo, metalMat);
body.position.y = -1.4;
robot.add(body);

// Core (Glowing Heart)
const coreGeo = new THREE.OctahedronGeometry(0.3);
const core = new THREE.Mesh(coreGeo, glowMat);
core.position.set(0, 0, 0.6);
body.add(core);

camera.position.z = 4;

// Animation Variables
let time = 0;
const mouse = new THREE.Vector2();
const targetRotation = new THREE.Vector2();

// Mouse Tracking
document.addEventListener('mousemove', (event) => {
    // Normalize mouse position relative to canvas center
    const rect = container.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    mouse.set(x, y);
});

// Animation Loop
function animate() {
    requestAnimationFrame(animate);
    time += 0.05;

    // Breathing Animation (Scale & Position)
    robot.position.y = Math.sin(time) * 0.1;
    body.scale.x = 1 + Math.sin(time) * 0.02;
    body.scale.z = 1 + Math.sin(time) * 0.02;

    // Head Tracking (Smooth Lerp)
    targetRotation.x = mouse.y * 0.5;
    targetRotation.y = mouse.x * 0.5;

    head.rotation.x += (targetRotation.x - head.rotation.x) * 0.1;
    head.rotation.y += (targetRotation.y - head.rotation.y) * 0.1;

    // Eye Movement (Subtle offset from head)
    leftEye.position.x = -0.3 + mouse.x * 0.05;
    leftEye.position.y = 0.1 + mouse.y * 0.05;
    rightEye.position.x = 0.3 + mouse.x * 0.05;
    rightEye.position.y = 0.1 + mouse.y * 0.05;

    // Core Pulse
    core.scale.setScalar(1 + Math.sin(time * 2) * 0.2);

    renderer.render(scene, camera);
}

// Handle Resize
window.addEventListener('resize', () => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
});

animate();
