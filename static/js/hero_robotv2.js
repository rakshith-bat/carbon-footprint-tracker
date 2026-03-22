//## Author Rakshith K

const mouse = { x: 0, y: 0 };
window.addEventListener("mousemove", e => {
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
});

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

// ── Create fixed full-screen canvas behind everything ──
const canvas = document.createElement("canvas");
canvas.id = "bg-canvas";
document.body.prepend(canvas);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
    55,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 0, 7);

const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setClearColor(0x000000, 0);

window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// ── Lighting ──
scene.add(new THREE.AmbientLight(0xffffff, 0.4));

const greenLight = new THREE.DirectionalLight(0x00ff9d, 1.6);
greenLight.position.set(3, 4, 5);
scene.add(greenLight);

const cyanLight = new THREE.DirectionalLight(0x00f3ff, 1.0);
cyanLight.position.set(-4, -2, 3);
scene.add(cyanLight);

// Purple from the left
const purpleLight = new THREE.DirectionalLight(0x9b00ff, 1.8);
purpleLight.position.set(-8, 0, 2);
scene.add(purpleLight);

const rimLight = new THREE.DirectionalLight(0xff00ff, 0.4);
rimLight.position.set(0, -5, -5);
scene.add(rimLight);

// ── Load model ──
const loader = new GLTFLoader();
const modelGroup = new THREE.Group();
scene.add(modelGroup);

let model;

loader.load("/static/walle.glb", (gltf) => {
    model = gltf.scene;

    // Center and auto-scale to fill background nicely
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    model.position.sub(center);

    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = 18 / maxDim;
    model.scale.setScalar(scale);

    // Semi-transparent so UI panels are readable
    model.traverse(child => {
        if (child.isMesh && child.material) {
            const mats = Array.isArray(child.material)
                ? child.material
                : [child.material];
            mats.forEach(mat => {
                mat.transparent = true;
                mat.opacity = 0.78;
            });
        }
    });

    modelGroup.add(model);
}, undefined, (err) => {
    console.warn("GLB load error:", err);
});

// ── Drag + momentum ──
let dragging = false;
let px = 0, py = 0;
let velX = 0, velY = 0; 
window.addEventListener("wheel", e => {
    velX += e.deltaY * 0.0006;
    velX += e.deltaX * 0.0006;
}); // momentum velocity   


window.addEventListener("mousedown", e => {
    const tag = e.target.tagName.toLowerCase();
    const isUI = ["button", "input", "select", "a", "label", "textarea"].includes(tag)
        || e.target.closest(".cyber-panel, .nav-bar, .nav-links, .cyber-btn");
    if (!isUI) {
        dragging = true;
        px = e.clientX;
        py = e.clientY;
        document.body.classList.add("drag-active");
    }
});
window.addEventListener("mousemove", e => {
    if (!dragging) return;
    const dx = (e.clientX - px) * 0.004;
    const dy = (e.clientY - py) * 0.004;
    modelGroup.rotation.y += dx;
    modelGroup.rotation.x += dy;
    velX = dx;   // capture velocity at moment of release
    velY = dy;
    px = e.clientX;
    py = e.clientY;
});
window.addEventListener("mouseup", () => {
    dragging = false;
    document.body.classList.remove("drag-active");
});
// ── Animation loop ──
let t = 0;
function animate() {
    requestAnimationFrame(animate);
    t += 0.008;

    if (model) {
        if (dragging) {
            // While dragging — pure user control, no auto anything
        } else {
            // Apply momentum from last drag, decay it
            modelGroup.rotation.y += velX;
            modelGroup.rotation.x += velY;
            velX *= 0.96;  // friction — change 0.96 for more/less momentum
            velY *= 0.96;

            // Slow base auto-rotation added on top of momentum
            modelGroup.rotation.y += 0.0012;

            // Cursor tracking — adds to current rotation, never resets it
            modelGroup.rotation.x += (mouse.y * 0.3) * 0.08;
            modelGroup.rotation.y += (mouse.x * 0.3) * 0.08;
        }

        // Gentle float — position only, never touches rotation
        modelGroup.position.y = Math.sin(t) * 0.15;
    }

    renderer.render(scene, camera);
}
animate();