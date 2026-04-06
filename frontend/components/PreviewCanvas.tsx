"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";

// 1. We create a separate part that loads our 3D file
function Model() {
    // We specify the path to one of the files that are already in our public/models folder
    const { scene } = useGLTF("/models/backpack.glb");
    
    // We show this model
    return <primitive object={scene} scale={2} position={[0, -1, 0]} />;
}

export default function PreviewCanvas() {
    return (
        <Canvas
            camera={{ position: [0, 2, 5], fov: 50 }}
            style={{ width: "100%", height: "100%" }}
        >
            {/* 2. Light so that the model is not black */}
            <ambientLight intensity={1} />
            <directionalLight position={[10, 10, 10]} intensity={2} />

            {/* 3. A tool that allows you to rotate the model with the mouse */}
            <OrbitControls makeDefault autoRotate autoRotateSpeed={1} />

            {/* 4. We display our model on the screen */}
            <Model />
        </Canvas>
    );
}