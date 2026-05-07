"use client";

import { Suspense, useMemo } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls, useGLTF, Center } from "@react-three/drei";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";

type PreviewCanvasProps = {
    modelPath: string;
    modelType?: string;
};

function GltfModel({ modelPath }: PreviewCanvasProps) {
    const { scene } = useGLTF(modelPath);
    const clonedScene = useMemo(() => scene.clone(), [scene]);

    return (
        <Center>
            <primitive object={clonedScene} />
        </Center>
    );
}

function ObjModel({ modelPath }: PreviewCanvasProps) {
    const object = useLoader(OBJLoader, modelPath);
    const clonedObject = useMemo(() => object.clone(), [object]);

    return (
        <Center>
            <primitive object={clonedObject} />
        </Center>
    );
}

function Model({ modelPath, modelType }: PreviewCanvasProps) {
    if (modelType?.toUpperCase() === "OBJ") {
        return <ObjModel modelPath={modelPath} />;
    }

    return <GltfModel modelPath={modelPath} />;
}

export default function PreviewCanvas({ modelPath, modelType }: PreviewCanvasProps) {
    return (
        <Canvas
            camera={{ position: [0, 2, 5], fov: 50 }}
            style={{ width: "100%", height: "100%" }}
        >
            <ambientLight intensity={1.2} />
            <directionalLight position={[10, 10, 10]} intensity={2.2} />
            <directionalLight position={[-8, 6, 4]} intensity={1.2} />

           <Suspense fallback={null}>
                <Model key={`${modelType ?? "GLB"}:${modelPath}`} modelPath={modelPath} modelType={modelType} />
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
