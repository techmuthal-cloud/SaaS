"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useUser, useAuth } from "@clerk/nextjs";
import { fetchWithAuth } from "../../lib/api";
import {
  ShieldCheck,
  Store,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Building2,
  CheckCircle2
} from "lucide-react";

function OnboardingContent() {
  const router = useRouter();
  const { user, isLoaded: userLoaded } = useUser();
  const { getToken, isLoaded: authLoaded, isSignedIn } = useAuth();

  const [workspaceName, setWorkspaceName] = useState("");
  const [selectedMarketplace, setSelectedMarketplace] = useState<"amazon_in" | "flipkart" | "meesho">("amazon_in");
  const [storeName, setStoreName] = useState("Amazon India Primary");

  const [checkingWorkspaces, setCheckingWorkspaces] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Update default store name when marketplace changes if user hasn't heavily customized it
  const handleMarketplaceChange = (mp: "amazon_in" | "flipkart" | "meesho") => {
    setSelectedMarketplace(mp);
    if (mp === "amazon_in") setStoreName("Amazon India Primary");
    else if (mp === "flipkart") setStoreName("Flipkart Main Account");
    else if (mp === "meesho") setStoreName("Meesho Hub");
  };

  // Check if user already has a workspace. If so, go straight to /app
  useEffect(() => {
    if (!authLoaded || !userLoaded) return;
    if (!isSignedIn) {
      router.push("/sign-in");
      return;
    }

    let isMounted = true;
    fetchWithAuth("/workspaces", {}, getToken)
      .then((data) => {
        if (!isMounted) return;
        if (data && data.length > 0) {
          // Returning seller: redirect directly to workspace dashboard
          router.push("/app");
        } else {
          setCheckingWorkspaces(false);
        }
      })
      .catch((err) => {
        console.error("Failed to check workspaces:", err);
        if (isMounted) setCheckingWorkspaces(false);
      });

    return () => {
      isMounted = false;
    };
  }, [authLoaded, userLoaded, isSignedIn, router, getToken]);

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalWsName = workspaceName.trim() || (user?.firstName ? `${user.firstName}'s Operations` : "My Seller Operations");
    if (!finalWsName) {
      setErrorMessage("Please enter a workspace name.");
      return;
    }
    if (!storeName.trim()) {
      setErrorMessage("Please enter an initial store name.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      // 1. Create Workspace
      const wsForm = new FormData();
      wsForm.append("name", finalWsName);
      const newWs = await fetchWithAuth("/workspaces", {
        method: "POST",
        body: wsForm,
      }, getToken);

      if (!newWs || !newWs.id) {
        throw new Error("Failed to receive valid workspace details from the server.");
      }

      // 2. Create Initial Store
      const storeForm = new FormData();
      storeForm.append("store_name", storeName.trim());
      storeForm.append("marketplace", selectedMarketplace);
      await fetchWithAuth(`/workspaces/${newWs.id}/stores`, {
        method: "POST",
        body: storeForm,
      }, getToken);

      // 3. Transition to /app with first upload trigger
      router.push("/app?first_upload=true");
    } catch (err: any) {
      console.error("Onboarding error:", err);
      setErrorMessage(err.message || "Failed to create workspace. Please check your connection and retry.");
      setIsSubmitting(false);
    }
  };

  if (!authLoaded || !userLoaded || checkingWorkspaces) {
    return (
      <div className="min-h-screen bg-[#0B132B] flex flex-col items-center justify-center p-6 text-slate-100 font-sans">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
        <p className="text-sm text-slate-400">Loading your account details...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B132B] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <nav className="border-b border-slate-800 bg-[#0B132B]/90 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-2 rounded-xl font-bold flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="tracking-tight text-lg text-white font-black">SellerFlow AI</span>
          </div>
          <span className="hidden sm:inline-block bg-slate-800/80 text-slate-300 text-xs font-semibold px-2.5 py-1 rounded-full border border-slate-700">
            Account Setup
          </span>
        </div>
        <div className="text-xs text-slate-400">
          Step 1 of 2: Workspace Setup
        </div>
      </nav>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-xl w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold mb-3">
              <Building2 className="w-3.5 h-3.5" />
              Initial Setup
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">
              Welcome, {user?.firstName || "Seller"}!
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Configure your reconciliation workspace and connect your primary e-commerce channel.
            </p>
          </div>

          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-rose-200">Setup Encountered an Issue</p>
                <p className="text-xs text-rose-300/90 mt-1">{errorMessage}</p>
                <button
                  type="button"
                  onClick={handleCreateWorkspace}
                  className="mt-3 text-xs bg-rose-600 hover:bg-rose-500 text-white font-bold px-3 py-1.5 rounded-lg transition inline-flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retry Setup
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleCreateWorkspace} className="space-y-6">
            {/* Workspace Name Input */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                1. Workspace / Business Name
              </label>
              <input
                type="text"
                required
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                placeholder="e.g. Acme Brands Operations"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
              />
              <p className="text-[11px] text-slate-500 mt-1.5">
                All settlement sheets, reconciliation reports, and Tally exports will be grouped under this entity.
              </p>
            </div>

            {/* Marketplace Selection */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                2. Select Primary Marketplace
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => handleMarketplaceChange("amazon_in")}
                  className={`p-3.5 rounded-xl border text-left transition flex flex-col justify-between ${
                    selectedMarketplace === "amazon_in"
                      ? "bg-emerald-500/10 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm">Amazon India</span>
                    {selectedMarketplace === "amazon_in" && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400 leading-tight">
                    Flat File V2, Easy Ship & Ad Fees
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleMarketplaceChange("flipkart")}
                  className={`p-3.5 rounded-xl border text-left transition flex flex-col justify-between ${
                    selectedMarketplace === "flipkart"
                      ? "bg-emerald-500/10 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm">Flipkart</span>
                    {selectedMarketplace === "flipkart" && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400 leading-tight">
                    Settlements & Commission Audits
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleMarketplaceChange("meesho")}
                  className={`p-3.5 rounded-xl border text-left transition flex flex-col justify-between ${
                    selectedMarketplace === "meesho"
                      ? "bg-emerald-500/10 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm">Meesho</span>
                    {selectedMarketplace === "meesho" && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400 leading-tight">
                    0% Commission & RTO Attribution
                  </span>
                </button>
              </div>
            </div>

            {/* Store Name Input */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                3. Store / Account Display Name
              </label>
              <div className="relative">
                <Store className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  placeholder="e.g. Amazon India Main"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1.5">
                You can add more stores and marketplaces anytime from the Settings tab.
              </p>
            </div>

            {/* Submit Action */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-extrabold text-sm py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition flex items-center justify-center gap-2 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Creating Workspace & Channel...
                </>
              ) : (
                <>
                  Confirm & Launch Workspace
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#0B132B] flex flex-col items-center justify-center p-6 text-slate-100 font-sans">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
          <p className="text-sm text-slate-400">Loading your account details...</p>
        </div>
      }
    >
      <OnboardingContent />
    </Suspense>
  );
}
