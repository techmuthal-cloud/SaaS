import { Suspense } from "react";
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-[#0B132B] flex flex-col items-center justify-center p-4 font-sans text-slate-100">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-black tracking-tight text-white">
          SellerFlow <span className="text-emerald-400">AI</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Sign in to your e-commerce financial reconciliation workspace
        </p>
      </div>
      <Suspense fallback={<div className="text-xs text-slate-400">Loading sign in...</div>}>
        <SignIn
          fallbackRedirectUrl="/app"
          signUpUrl="/sign-up"
        />
      </Suspense>
    </div>
  );
}
