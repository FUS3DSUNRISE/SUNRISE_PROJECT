"use client";


export type ModelParameters = {
    category?: string;
    size: {
        width: number;
        height: number;
        depth: number;
    };
    geometry: {
        complexity: number;
        smoothness: number;
    };
    material: {
        type: string;
        roughness: number;
        metallic: number;
    };
};


type ParameterPanelProps = {
    value: ModelParameters;
    onChange: (value: ModelParameters) => void;
};


export default function ParameterPanel({
    value,
    onChange,
}: ParameterPanelProps) {
    const updateSize = (key: keyof ModelParameters["size"], newValue: number) => {
        onChange({
            ...value,
            size: {
                ...value.size,
                [key]: newValue,
            },
        });
    };


    const updateGeometry = (
        key: keyof ModelParameters["geometry"],
        newValue: number
    ) => {
        onChange({
            ...value,
            geometry: {
                ...value.geometry,
                [key]: newValue,
            },
        });
    };


    const updateMaterial = (
        key: keyof ModelParameters["material"],
        newValue: string | number
    ) => {
        onChange({
            ...value,
            material: {
                ...value.material,
                [key]: newValue,
            },
        });
    };


    return (
        <div className="rounded-2xl border border-white/10 bg-[#11131f]/80 p-6 text-white shadow-[0_10px_25px_rgba(0,0,0,0.2)]">


            <div className="space-y-6">
                <section>
                    <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.15em] text-[#ff8a2c]">
                        Size
                    </h3>
                    <div className="space-y-4">
                        <SliderRow
                            label="Width"
                            min={0.5}
                            max={5}
                            step={0.1}
                            value={value.size.width}
                            onChange={(v) => updateSize("width", v)}
                        />
                        <SliderRow
                            label="Height"
                            min={0.5}
                            max={5}
                            step={0.1}
                            value={value.size.height}
                            onChange={(v) => updateSize("height", v)}
                        />
                        <SliderRow
                            label="Depth"
                            min={0.5}
                            max={5}
                            step={0.1}
                            value={value.size.depth}
                            onChange={(v) => updateSize("depth", v)}
                        />
                    </div>
                </section>


                <section>
                    <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.15em] text-[#ff8a2c]">
                        Geometry
                    </h3>
                    <div className="space-y-4">
                        <SliderRow
                            label="Complexity"
                            min={1}
                            max={10}
                            step={1}
                            value={value.geometry.complexity}
                            onChange={(v) => updateGeometry("complexity", v)}
                        />
                        <SliderRow
                            label="Smoothness"
                            min={1}
                            max={100}
                            step={1}
                            value={value.geometry.smoothness}
                            onChange={(v) => updateGeometry("smoothness", v)}
                        />
                    </div>
                </section>


                <section>
                    <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.15em] text-[#ff8a2c]">
                        Material
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-2 block text-sm text-white/75">
                                Material type
                            </label>
                            <select
                                value={value.material.type}
                                onChange={(e) => updateMaterial("type", e.target.value)}
                                className="w-full rounded-xl border border-white/10 bg-[#171927] px-4 py-3 text-white outline-none focus:border-[#ff8a2c]"
                            >
                                <option value="plastic">Plastic</option>
                                <option value="metal">Metal</option>
                                <option value="wood">Wood</option>
                                <option value="glass">Glass</option>
                            </select>
                        </div>


                        <SliderRow
                            label="Roughness"
                            min={0}
                            max={1}
                            step={0.05}
                            value={value.material.roughness}
                            onChange={(v) => updateMaterial("roughness", v)}
                        />
                        <SliderRow
                            label="Metallic"
                            min={0}
                            max={1}
                            step={0.05}
                            value={value.material.metallic}
                            onChange={(v) => updateMaterial("metallic", v)}
                        />
                    </div>
                </section>
            </div>
        </div>
    );
}


type SliderRowProps = {
    label: string;
    min: number;
    max: number;
    step: number;
    value: number;
    onChange: (value: number) => void;
};


function SliderRow({
    label,
    min,
    max,
    step,
    value,
    onChange,
}: SliderRowProps) {
    return (
        <div>
            <div className="mb-2 flex items-center justify-between">
                <label className="text-sm text-white/75">{label}</label>
                <span className="text-sm text-white/60">{value}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
                className="w-full accent-[#ff8a2c]"
            />
        </div>
    );
}
