// ---- Three.js setup ----
const container = document.getElementById("hero-3d-container");
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f2027);

const camera = new THREE.PerspectiveCamera(
  45,
  container.clientWidth / container.clientHeight,
  0.1,
  1000
);
camera.position.set(0, 2, 8);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// ---- Lighting ----
const ambient = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambient);

const directional = new THREE.DirectionalLight(0xffffff, 1);
directional.position.set(5, 10, 7);
scene.add(directional);

// ---- Robot Group ----
const robot = new THREE.Group();
scene.add(robot);

// ---- Colors ----
const yellow = 0xffd44d;
const gray = 0x555555;
const black = 0x000000;
const red = 0xff4444;
const screenColor = 0x00ffcc;

// ---- Torso ----
const torsoGeo = new THREE.BoxGeometry(2, 3, 1);
const torsoMat = new THREE.MeshStandardMaterial({ color: yellow });
const torso = new THREE.Mesh(torsoGeo, torsoMat);
robot.add(torso);

// ---- Screen on torso ----
const screenGeo = new THREE.BoxGeometry(1, 1, 0.05);
const screenMat = new THREE.MeshStandardMaterial({ color: screenColor });
const screen = new THREE.Mesh(screenGeo, screenMat);
screen.position.set(0, 0.2, 0.53);
torso.add(screen);

// ---- Head ----
const headGeo = new THREE.BoxGeometry(1.2, 1, 1);
const headMat = new THREE.MeshStandardMaterial({ color: yellow });
const head = new THREE.Mesh(headGeo, headMat);
head.position.set(0, 2, 0);
robot.add(head);

// ---- Eyes ----
const eyeGeo = new THREE.SphereGeometry(0.2, 16, 16);
const eyeMat = new THREE.MeshStandardMaterial({ color: black });
const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
const rightEye = new THREE.Mesh(eyeGeo, eyeMat);

leftEye.position.set(-0.35, 0.2, 0.6);
rightEye.position.set(0.35, 0.2, 0.6);
head.add(leftEye);
head.add(rightEye);

// ---- Arms ----
function makeArm(x) {
  const armGroup = new THREE.Group();

  const upper = new THREE.CylinderGeometry(0.15, 0.15, 1);
  const upperMat = new THREE.MeshStandardMaterial({ color: yellow });
  const upperMesh = new THREE.Mesh(upper, upperMat);
  upperMesh.rotation.z = Math.PI / 2;
  upperMesh.position.x = 0.5;
  armGroup.add(upperMesh);

  const hand = new THREE.BoxGeometry(0.4, 0.15, 0.15);
  const handMesh = new THREE.Mesh(hand, gray);
  handMesh.position.x = 1.1;
  armGroup.add(handMesh);

  armGroup.position.set(x, 0.5, 0);
  return armGroup;
}
robot.add(makeArm(-1.1));
robot.add(makeArm(1.1));

// ---- Legs / wheels ----
const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.5, 16);
const wheelMat = new THREE.MeshStandardMaterial({ color: gray });
const leftWheel = new THREE.Mesh(wheelGeo, wheelMat);
const rightWheel = new THREE.Mesh(wheelGeo, wheelMat);

leftWheel.rotation.z = Math.PI / 2;
rightWheel.rotation.z = Math.PI / 2;

leftWheel.position.set(-0.7, -1.7, 0);
rightWheel.position.set(0.7, -1.7, 0);

robot.add(leftWheel);
robot.add(rightWheel);

// ---- Animation ----
let clock = new THREE.Clock();
let eyeBlinkTimer = Math.random() * 2 + 1;

// Cursor tracking
let mouse = { x: 0, y: 0 };
window.addEventListener("mousemove", (e) => {
  const rect = container.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
});

function animate() {
  requestAnimationFrame(animate);

  const t = clock.getElapsedTime();

  // Head subtle movement
  head.rotation.y = Math.sin(t * 0.5) * 0.2;
  head.rotation.x = Math.sin(t * 0.3) * 0.1;

  // Eyes follow cursor
  leftEye.lookAt(new THREE.Vector3(mouse.x * 2, mouse.y * 1, 5));
  rightEye.lookAt(new THREE.Vector3(mouse.x * 2, mouse.y * 1, 5));

  // Blinking
  eyeBlinkTimer -= clock.getDelta();
  if (eyeBlinkTimer <= 0) {
    leftEye.scale.y = 0.05;
    rightEye.scale.y = 0.05;
    setTimeout(() => {
      leftEye.scale.y = 1;
      rightEye.scale.y = 1;
    }, 150);
    eyeBlinkTimer = Math.random() * 5 + 2;
  }

  renderer.render(scene, camera);
}
animate();

// Handle resize
window.addEventListener("resize", () => {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});
