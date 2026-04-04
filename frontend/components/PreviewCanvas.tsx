"use client";

import { Canvas } from "@react-three/fiber";

export default function PreviewCanvas() {
    return (
        <Canvas
            camera={{ position: [2, 2, 2], fov: 60 }}
            style={{ width: "100%", height: "100%" }}
        >
            {/* simple light so scene is not black */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 5, 5]} />

            {/* TEMP object just to verify rendering */}
            <mesh>
                <boxGeometry />
                <meshStandardMaterial color="#4f5dff" />
            </mesh>
        </Canvas>
    );
}