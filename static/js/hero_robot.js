// === Basic Three.js setup ===
const container = document.getElementById("hero-3d-container");
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a1f);

const camera = new THREE.PerspectiveCamera(
  50,
  container.clientWidth / container.clientHeight,
  0.1,
  1000
);
camera.position.set(0, 1, 5);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// === Lights ===
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const spotLight = new THREE.SpotLight(0xffffff, 0.8);
spotLight.position.set(10, 15, 10);
scene.add(spotLight);

// === Robot (low-poly) ===
const robot = new THREE.Group();

// Body
const bodyGeom = new THREE.BoxGeometry(1, 1.5, 0.7);
const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffff00 });
const body = new THREE.Mesh(bodyGeom, bodyMat);
robot.add(body);

// Head
const headGeom = new THREE.BoxGeometry(0.7, 0.7, 0.5);
const headMat = new THREE.MeshStandardMaterial({ color: 0xffff00 });
const head = new THREE.Mesh(headGeom, headMat);
head.position.set(0, 1.1, 0);
robot.add(head);

// Eyes (glowing)
const eyeLeft = new THREE.Mesh(
  new THREE.SphereGeometry(0.1, 16, 16),
  new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000 })
);
const eyeRight = eyeLeft.clone();
eyeLeft.position.set(-0.2, 1.1, 0.26);
eyeRight.position.set(0.2, 1.1, 0.26);
robot.add(eyeLeft);
robot.add(eyeRight);

scene.add(robot);

// === Cursor Tracking ===
document.addEventListener("mousemove", (e) => {
    const x = (e.clientX / window.innerWidth) * 2 - 1;
    const y = -(e.clientY / window.innerHeight) * 2 + 1;

    // head rotation
    head.rotation.y = x * 0.5; // horizontal
    head.rotation.x = y * 0.2; // vertical

    // eyes follow cursor
    eyeLeft.lookAt(new THREE.Vector3(x*5, y*5 + 1.1, 1));
    eyeRight.lookAt(new THREE.Vector3(x*5, y*5 + 1.1, 1));
});

// === Random Blink Animation ===
setInterval(() => {
    const scale = Math.random() < 0.1 ? 0.1 : 1;
    eyeLeft.scale.y = scale;
    eyeRight.scale.y = scale;
}, 300 + Math.random() * 2000);

// === Random Head Movement (idle) ===
setInterval(() => {
    head.rotation.y += (Math.random() - 0.5) * 0.2;
    head.rotation.x += (Math.random() - 0.5) * 0.1;
}, 3000);

// === Animate ===
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// === Handle Window Resize ===
window.addEventListener("resize", () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});
