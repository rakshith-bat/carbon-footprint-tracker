document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("hero-3d-container");
    if (!container) return; // Stop if container not found

    // ====== THREE.JS SCENE SETUP ======
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f2027);

    const camera = new THREE.PerspectiveCamera(
        75,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );
    camera.position.set(0, 2, 5);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    // ====== LIGHTS ======
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xffffff, 1);
    pointLight.position.set(5, 10, 5);
    scene.add(pointLight);

    // ====== LOW-POLY WALL-E STYLE ROBOT ======
    const robot = new THREE.Group();

    // Body
    const bodyGeometry = new THREE.BoxGeometry(1.2, 1.5, 0.6);
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xffff66 });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    robot.add(body);

    // Head
    const headGeometry = new THREE.BoxGeometry(0.8, 0.6, 0.6);
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0xffff66 });
    const head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.set(0, 1.05, 0);
    robot.add(head);

    // Eyes
    const leftEyeGeometry = new THREE.SphereGeometry(0.15, 16, 16);
    const rightEyeGeometry = new THREE.SphereGeometry(0.15, 16, 16);
    const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff4444 });
    const leftEye = new THREE.Mesh(leftEyeGeometry, eyeMaterial);
    const rightEye = new THREE.Mesh(rightEyeGeometry, eyeMaterial);
    leftEye.position.set(-0.2, 1.1, 0.3);
    rightEye.position.set(0.2, 1.1, 0.3);
    robot.add(leftEye, rightEye);

    // Simple arms
    const armGeometry = new THREE.CylinderGeometry(0.07, 0.07, 0.6);
    const armMaterial = new THREE.MeshStandardMaterial({ color: 0x999999 });
    const leftArm = new THREE.Mesh(armGeometry, armMaterial);
    const rightArm = new THREE.Mesh(armGeometry, armMaterial);
    leftArm.position.set(-0.85, 0.5, 0);
    rightArm.position.set(0.85, 0.5, 0);
    leftArm.rotation.z = Math.PI / 6;
    rightArm.rotation.z = -Math.PI / 6;
    robot.add(leftArm, rightArm);

    scene.add(robot);

    // ====== ANIMATION ======
    let clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        const time = clock.getElapsedTime();

        // Random head tilt
        head.rotation.y = Math.sin(time * 0.5) * 0.3;
        head.rotation.x = Math.sin(time * 0.3) * 0.1;

        // Eyes follow mouse
        if (mouse.x !== undefined && mouse.y !== undefined) {
            const vecX = (mouse.x / container.clientWidth) * 2 - 1;
            const vecY = -(mouse.y / container.clientHeight) * 2 + 1;
            leftEye.rotation.y = vecX * 0.3;
            rightEye.rotation.y = vecX * 0.3;
            leftEye.rotation.x = vecY * 0.3;
            rightEye.rotation.x = vecY * 0.3;
        }

        // Random blinking
        if (Math.random() < 0.01) {
            leftEye.scale.y = 0.1;
            rightEye.scale.y = 0.1;
        } else {
            leftEye.scale.y = 1;
            rightEye.scale.y = 1;
        }

        renderer.render(scene, camera);
    }

    animate();

    // ====== MOUSE TRACKING ======
    let mouse = {};
    container.addEventListener("mousemove", (event) => {
        mouse.x = event.clientX;
        mouse.y = event.clientY;
    });

    // ====== HANDLE RESIZE ======
    window.addEventListener("resize", () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
});
