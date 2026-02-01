//## Author Rakshith K

const mouse = { x: 0, y: 0 };
window.addEventListener("mousemove", e => {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
});

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
scene.add(new THREE.AmbientLight(0xffffff, 1.2));
const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
dirLight.position.set(0, 2, 4);
scene.add(dirLight);


// Loader
const loader = new GLTFLoader();
let model;

// Group for rotation
const modelGroup = new THREE.Group();
scene.add(modelGroup);

loader.load("/static/walle.glb", (gltf) => {
  model = gltf.scene;

  // Center model
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  model.position.sub(center);

  model.rotation.y = Math.PI / 2;
  model.scale.set(1.3, 1.3, 1.3);

  modelGroup.add(model);
});

// Mouse drag rotate
let dragging = false;
let px = 0, py = 0;

container.addEventListener("mousedown", e => {
  dragging = true;
  px = e.clientX;
  py = e.clientY;
});
container.addEventListener("mousemove", e => {
  if (!dragging) return;
  modelGroup.rotation.y += (e.clientX - px) * 0.005;
  modelGroup.rotation.x += (e.clientY - py) * 0.005;
  px = e.clientX;
  py = e.clientY;
});
container.addEventListener("mouseup", () => dragging = false);
container.addEventListener("mouseleave", () => dragging = false);

// Animation
let t = 0;
function animate() {
  requestAnimationFrame(animate);
  t += 0.04;
// Light reacts to cursor (alive feel)
  
  if (model) {
    // Gentle floating (alive feel)
    model.position.y = -3 + Math.sin(t) * 0.12;

    // Subtle idle sway
    model.rotation.z = Math.sin(t * 0.5) * 0.03;
    model.rotation.y = mouse.x * 0.25;
    model.rotation.x = mouse.y * 0.15;

  }

  renderer.render(scene, camera);
}
animate();
