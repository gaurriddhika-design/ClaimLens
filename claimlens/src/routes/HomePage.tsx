import { useState } from "react";
import InputPanel from "../components/InputPanel";
interface HomePageProps {
  onVerify: (claim: string) => void;
}

function HomePage({ onVerify }: HomePageProps) {
  const [claim, setClaim] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleVerify = () => {
  if (claim.trim() === "") {
    alert("Please enter a claim first.");
    return;
  }

  setIsLoading(true);
  onVerify(claim.trim());
};

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b bg-white px-8 py-5">
        <h1 className="text-2xl font-bold text-blue-700">
          ClaimLens
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Verify claims. Explore evidence. Think critically.
        </p>
      </header>

     
<main className="mx-auto max-w-5xl space-y-8 px-6 py-10">
  <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-blue-950 to-blue-800 px-6 py-10 text-white shadow-lg sm:px-10 sm:py-14">
    <div className="relative z-10 max-w-3xl">
      <span className="inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium text-blue-100">
        THINK BEFORE YOU SHARE
      </span>

      <h2 className="mt-5 text-3xl font-bold leading-tight tracking-tight sm:text-5xl">
        Truth deserves
        <span className="block text-blue-300">a closer look.</span>
      </h2>

      <p className="mt-4 max-w-xl text-sm leading-7 text-blue-100 sm:text-base">
        Analyze online claims, examine evidence, and make more informed
        decisions before sharing information.
      </p>

      <div className="mt-8 flex flex-wrap gap-3 text-sm">
        <span className="rounded-lg border border-white/15 bg-white/10 px-3 py-2">
          Claim analysis
        </span>
        <span className="rounded-lg border border-white/15 bg-white/10 px-3 py-2">
          Evidence review
        </span>
        <span className="rounded-lg border border-white/15 bg-white/10 px-3 py-2">
          Transparent limitations
        </span>
      </div>
    </div>

    <div
      aria-hidden="true"
      className="absolute -right-16 -top-20 h-64 w-64 rounded-full border border-white/10 sm:h-80 sm:w-80"
    />

    <div
      aria-hidden="true"
      className="absolute -bottom-28 right-16 h-56 w-56 rounded-full border border-white/10"
    />
  </section>

  <InputPanel

          claim={claim}
          setClaim={setClaim}
          onVerify={handleVerify}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

export default HomePage;
