"use client";

import { Suspense, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, useGLTF } from "@react-three/drei";

type PreviewCanvasProps = {
    modelPath: string;
};

function Model({ modelPath }: PreviewCanvasProps) {
    const { scene } = useGLTF(modelPath);
    const clonedScene = useMemo(() => scene.clone(), [scene]);

    return (
        <primitive
            object={clonedScene}
            scale={2.2}
            position={[0, -1.5, 0]}
        />
    );
}

export default function PreviewCanvas({ modelPath }: PreviewCanvasProps) {
    return (
        <Canvas
            camera={{ position: [0, 2, 5], fov: 50 }}
            style={{ width: "100%", height: "100%" }}
        >
            <ambientLight intensity={1.2} />
            <directionalLight position={[10, 10, 10]} intensity={2.2} />
            <directionalLight position={[-8, 6, 4]} intensity={1.2} />

            <Suspense fallback={null}>
                <Environment preset="city" />
                <Model modelPath={modelPath} />
            </Suspense>

            <OrbitControls
                makeDefault
                autoRotate
                autoRotateSpeed={1}
                enablePan={false}
            />
        </Canvas>
    );
}