import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const container = document.getElementById("robot-canvas");
const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
  75,
  container.clientWidth / container.clientHeight,
  0.1,
  1000
);
camera.position.set(0, 0, 6);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(window.devicePixelRatio);
container.appendChild(renderer.domElement);

window.addEventListener("resize", () => {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});

// Lights
const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
dirLight.position.set(5, 5, 5);
scene.add(dirLight);

// Loader
const loader = new GLTFLoader();
let model, leftEye, rightEye;

// Group for rotation
const modelGroup = new THREE.Group();
scene.add(modelGroup);

loader.load(
  "/static/walle.glb",
  (gltf) => {
    model = gltf.scene;

    // Center model
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);

    // Face center
    model.rotation.y = Math.PI / 2;
    model.scale.set(1.3, 1.3, 1.3);

    // Add to group
    modelGroup.add(model);

    // ADD SIMPLE EYEBALLS (attached to model directly)
    const eyeGeometry = new THREE.SphereGeometry(0.06, 16, 16);
    const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const pupilGeometry = new THREE.SphereGeometry(0.02, 16, 16);
    const pupilMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });

    leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);

    const leftPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
    const rightPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);

    leftEye.add(leftPupil);
    rightEye.add(rightPupil);

    // Put eyes on front area of model (adjust if needed)
    leftEye.position.set(-0.25, 0.25, 0.45);
    rightEye.position.set(0.25, 0.25, 0.45);

    leftPupil.position.set(0, 0, 0.05);
    rightPupil.position.set(0, 0, 0.05);

    model.add(leftEye);
    model.add(rightEye);
  },
  undefined,
  (error) => console.error(error)
);

// Mouse
const mouse = new THREE.Vector2();
document.addEventListener("mousemove", (event) => {
  const rect = container.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
});

// Drag to rotate
let isDragging = false;
let previousMouseX = 0;
let previousMouseY = 0;

container.addEventListener("mousedown", (e) => {
  isDragging = true;
  previousMouseX = e.clientX;
  previousMouseY = e.clientY;
});

container.addEventListener("mousemove", (e) => {
  if (!isDragging) return;

  const deltaX = e.clientX - previousMouseX;
  const deltaY = e.clientY - previousMouseY;

  modelGroup.rotation.y += deltaX * 0.005;
  modelGroup.rotation.x += deltaY * 0.005;

  previousMouseX = e.clientX;
  previousMouseY = e.clientY;
});

container.addEventListener("mouseup", () => (isDragging = false));
container.addEventListener("mouseleave", () => (isDragging = false));

// Animation
let time = 0;
let waveTimer = 0;
let wave = false;

function animate() {
  requestAnimationFrame(animate);
  time += 0.05;

  if (model) {
    // Floating
    const baseY = -3;
    model.position.y = baseY + Math.sin(time) * 0.15;

    // Eye follow cursor
    if (leftEye && rightEye) {
      const lookX = mouse.x * 0.2;
      const lookY = mouse.y * 0.1;

      leftEye.children[0].position.x = lookX;
      leftEye.children[0].position.y = lookY;

      rightEye.children[0].position.x = lookX;
      rightEye.children[0].position.y = lookY;
    }

    // Simple waving (without arm link)
    waveTimer++;
    if (!wave && waveTimer > 200 && Math.random() > 0.75) {
      wave = true;
      waveTimer = 0;
    }
    if (wave) {
      model.rotation.z = Math.sin(time * 3) * 0.05;
      if (waveTimer > 80) wave = false;
    }
  }

  renderer.render(scene, camera);
}

animate();
