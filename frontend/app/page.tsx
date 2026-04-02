export default function Home() {
  return (
    <main className="min-h-screen bg-[#07070b] text-white">
      <div className="mx-auto max-w-[1600px] px-6 py-6">
        <div className="rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(76,76,140,0.22),rgba(7,7,11,0.96)_55%)] shadow-[0_0_40px_rgba(0,0,0,0.35)]">
          <header className="flex items-center justify-between border-b border-white/10 px-8 py-6">
            <div className="flex items-center gap-3">
              <span className="text-[42px] font-extrabold tracking-tight text-[#ff8c2b]">
                &gt;&gt;
              </span>
              <span className="text-[42px] font-extrabold tracking-tight text-white">
                SCAI<span className="text-[#ff8c2b]">LAB</span>
              </span>
            </div>

            <nav className="flex items-center gap-8 text-[18px] text-white/90">
              <a href="#" className="transition hover:text-white">
                Contact
              </a>
              <a href="#" className="transition hover:text-white">
                Login
              </a>
              <a
                href="#"
                className="rounded-xl border border-[#8a5b22] px-5 py-3 text-[#f2c27c] transition hover:bg-white/5"
              >
                Sign Up Free
              </a>
            </nav>
          </header>

          <section className="grid grid-cols-1 gap-10 px-8 py-10 lg:grid-cols-[1.05fr_1.35fr]">
            <div className="flex flex-col">
              <div className="relative overflow-hidden rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(35,35,70,0.45),rgba(7,7,11,0.98)_75%)] p-6 min-h-[600px]">
                <div className="absolute left-1/2 top-12 -translate-x-1/2 rounded-xl border border-white/10 bg-[#2b2d42]/80 px-5 py-3 text-[16px] text-white/80 shadow-lg">
                  Hover to preview 3D model
                </div>

                <div className="flex h-full items-center justify-center">
                 <div className="text-white/50 text-2xl">3D Model Preview</div>
                </div>

                <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:60px_60px] opacity-25 pointer-events-none" />
              </div>

              <div className="pt-5">
                <h3 className="text-[28px] font-bold tracking-tight">
                  Shows example 3D preview
                </h3>
                <p className="mt-3 text-[18px] text-white/70">
                  Type a prompt and generate 3D model instantly.
                </p>
              </div>
            </div>

            <div className="flex flex-col justify-center">
              <h1 className="max-w-[900px] text-[64px] font-extrabold leading-[0.98] tracking-tight xl:text-[76px]">
                The Easiest Way to
                <br />
                Create 3D Models
              </h1>

              <p className="mt-6 text-[24px] text-white/80">
                Type a prompt and generate 3D models instantly.
              </p>

              <div className="mt-10">
                <label htmlFor="prompt" className="sr-only">
                  Text prompt
                </label>
                <input
                  id="prompt"
                  type="text"
                  placeholder="Describe the 3D model you'd like to create..."
                  className="w-full rounded-[20px] border border-white/10 bg-[#11131f]/80 px-6 py-5 text-[22px] text-white placeholder:text-white/35 outline-none transition focus:border-[#4d58ff] focus:ring-2 focus:ring-[#4d58ff]/30"
                />
              </div>

              <div className="mt-10 flex justify-center">
                <button className="min-w-[560px] rounded-[20px] bg-[#4f5dff] px-10 py-5 text-[24px] font-semibold text-white shadow-[0_12px_30px_rgba(79,93,255,0.35)] transition hover:bg-[#5d69ff]">
                  Generate 3D Model
                </button>
              </div>

              <div className="mt-12 flex justify-center">
                <div className="w-full max-w-[500px] rounded-[20px] border border-white/10 bg-[#11131f]/70 px-8 py-7 text-center shadow-[0_10px_25px_rgba(0,0,0,0.25)]">
                  <button className="w-full rounded-[14px] border border-white/10 bg-[#171927] px-6 py-4 text-[22px] font-medium text-white transition hover:bg-white/5">
                    ↓ Download Model (glb)
                  </button>

                  <p className="mt-6 text-[20px] text-white/75">
                    Formats: GLB / FBX / OBJ
                  </p>
                  <p className="mt-3 text-[20px] text-white/75">
                    Estimated Time: 3-5 min
                  </p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}