"use client";

import { Suspense, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
// Add import of the Center component
import { Environment, OrbitControls, useGLTF, Center } from "@react-three/drei";

type PreviewCanvasProps = {
    modelPath: string;
};

function Model({ modelPath }: PreviewCanvasProps) {
    const { scene } = useGLTF(modelPath);
    const clonedScene = useMemo(() => scene.clone(), [scene]);

    return (
        // Component Center automatically calculates the "box" of the object and centers it perfectly
        <Center>
            {/* I removed the hard scale and position so as not to break small models */}
            <primitive object={clonedScene} />
        </Center>
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
                {/* <Environment preset="city" /> */}
                <Model modelPath={modelPath} />
            </Suspense>

            <OrbitControls
                makeDefault
                autoRotate
                autoRotateSpeed={1}
                enablePan={false}  
                enableZoom={true} 
            />
        </Canvas>
    );
}