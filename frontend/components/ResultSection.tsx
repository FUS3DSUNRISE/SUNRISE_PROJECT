"use client";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white">
      
      {/* HEADER */}
      <header className="flex justify-between items-center p-4 border-b border-gray-800">
        <h1 className="text-xl font-bold">SUNRISE</h1>
        <button className="border px-4 py-1 rounded">Login</button>
      </header>

      {/* HERO */}
      <section className="flex items-center justify-center h-[80vh] px-10">
        
        {/* LEFT (3D placeholder) */}
        <div className="w-1/2 h-96 border border-gray-700 flex items-center justify-center">
          3D Preview
        </div>

        {/* RIGHT (text) */}
        <div className="w-1/2 pl-10">
          <h2 className="text-4xl font-bold mb-4">
            The Easiest Way to Create 3D Models
          </h2>

          <p className="text-gray-400 mb-6">
            Type a prompt and generate 3D models instantly.
          </p>

          <button className="bg-purple-600 px-6 py-3 rounded">
            Get Started
          </button>
        </div>

      </section>
    </main>
  );
}