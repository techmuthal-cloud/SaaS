"use client";

import React from "react";
import {
  ShieldCheck,
  TrendingUp,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  UploadCloud,
  SplitSquareVertical,
  Calendar,
  Layers,
  Clock,
  Sparkles,
  IndianRupee,
  FileCode,
  DollarSign
} from "lucide-react";

interface LandingHomeProps {
  onGoToApp: () => void;
}

export default function LandingHome({ onGoToApp }: LandingHomeProps) {
  return (
    <div className="min-h-screen bg-[#0B132B] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <nav className="border-b border-slate-800 bg-[#0B132B]/90 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-2 rounded-xl font-bold flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="tracking-tight text-lg text-white font-black">SellerFlow AI</span>
          </div>
          <span className="hidden sm:inline-block bg-slate-800/80 text-slate-300 text-xs font-semibold px-2.5 py-1 rounded-full border border-slate-700">
            For Amazon, Flipkart & Meesho Sellers
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <a href="#how-it-works" className="text-xs text-slate-300 hover:text-white font-medium transition hidden md:inline-block">
            How It Works
          </a>
          <a href="#features" className="text-xs text-slate-300 hover:text-white font-medium transition hidden md:inline-block">
            Dispute Engine
          </a>
          <button
            onClick={onGoToApp}
            className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
          >
            Launch Free Workspace
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </nav>

      {/* Hero Section with Logistics & Delivery Warehouse Background */}
      <section className="relative min-h-[580px] flex items-center justify-center px-6 py-20 overflow-hidden">
        {/* Background Overlay with Delivery / Logistics Imagery */}
        <div 
          className="absolute inset-0 z-0 bg-cover bg-center filter brightness-[0.25] saturate-150 transform scale-105"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=2000&q=80')`
          }}
        />
        {/* Gradient Overlay for high readability */}
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#0B132B]/80 via-[#0B132B]/60 to-[#0B132B]" />

        <div className="relative z-10 max-w-5xl mx-auto text-center flex flex-col items-center">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-1.5 rounded-full text-xs font-semibold text-emerald-400 mb-6 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            Deterministic E-Commerce Financial Reconciliation
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-[1.15] max-w-4xl">
            Know What You Should Have Received vs.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              What Marketplaces Actually Paid.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed font-normal">
            Automate settlement auditing for <strong className="text-white">Amazon India</strong>, <strong className="text-white">Flipkart</strong>, and <strong className="text-white">Meesho</strong>. Stop fee overcharges, recover unreturned RTO stock, and match bank NEFT deposits in seconds.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
            <button
              onClick={onGoToApp}
              className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-extrabold text-sm px-7 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
            >
              Upload Settlement & Reconcile Free
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#how-it-works"
              className="w-full sm:w-auto bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 text-sm font-semibold px-6 py-3.5 rounded-xl transition flex items-center justify-center gap-2"
            >
              See How It Works
            </a>
          </div>

          {/* Social Proof Metric Badges */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-3xl border-t border-slate-800/80 pt-8 text-left">
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Reconciliation Math</span>
              <p className="text-lg font-bold text-white mt-0.5">100% Deterministic</p>
              <span className="text-[11px] text-emerald-400">Zero LLM Guesswork</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Multi-Marketplace</span>
              <p className="text-lg font-bold text-white mt-0.5">Unified Matrix</p>
              <span className="text-[11px] text-teal-400">AMZ + FK + Meesho</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Dispute Automation</span>
              <p className="text-lg font-bold text-white mt-0.5">1-Click Claims</p>
              <span className="text-[11px] text-amber-400">SAFE-T & Weight Slabs</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Accounting Sync</span>
              <p className="text-lg font-bold text-white mt-0.5">TallyPrime XML</p>
              <span className="text-[11px] text-cyan-400">5-Second DayBook Import</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 px-6 bg-[#0E1738] border-t border-slate-800 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              Simple 4-Step Process
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-3 tracking-tight">
              How SellerFlow AI Works
            </h2>
            <p className="text-sm text-slate-300 mt-2">
              Transform chaotic, conflicting marketplace settlement sheets into clear, auditable bank-matched figures in minutes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-emerald-500/50 p-6 rounded-2xl transition duration-300 relative group flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-black text-sm mb-4">
                  01
                </div>
                <h3 className="font-bold text-lg text-white mb-2">Drop Your Settlement Sheet</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Upload raw settlement exports (CSV, TSV, or XLSX) from Amazon Seller Central, Flipkart Payment Desk, or Meesho Supplier Panel.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                Auto-checksum & Deduplication
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-teal-500/50 p-6 rounded-2xl transition duration-300 relative group flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 flex items-center justify-center font-black text-sm mb-4">
                  02
                </div>
                <h3 className="font-bold text-lg text-white mb-2">Deterministic Canonical Parse</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  The engine standardizes fragmented fee names into universal buckets: Referral, Pick-Pack, Shipping, Returns, and Rolling Reserves.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                Decimal Precision Math
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-amber-500/50 p-6 rounded-2xl transition duration-300 relative group flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center font-black text-sm mb-4">
                  03
                </div>
                <h3 className="font-bold text-lg text-white mb-2">Audit Gaps & Overcharges</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  The engine compares expected payouts against bank deposits, highlights volumetric overcharges, and flags refunds where inventory was never restocked.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                Evidence Drawer Row Lineage
              </div>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 p-6 rounded-2xl transition duration-300 relative group flex flex-col justify-between">
              <div>
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center font-black text-sm mb-4">
                  04
                </div>
                <h3 className="font-bold text-lg text-white mb-2">Claim Money & Export to Tally</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Generate copy-pasteable 1-Click dispute tickets for Seller Central or download TallyPrime XML vouchers for instantaneous accounting entry.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                1-Click Ticket & Tally XML
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Showcase Grid */}
      <section id="features" className="py-20 px-6 bg-[#0B132B] relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
              Built for High-Volume Sellers
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-3 tracking-tight">
              Everything Needed to Protect Settlement Cash Flow
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl w-fit mb-4">
                <Calendar className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-2">Settlement Period Recon</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Stop reconciling by calendar months. Reconcile by exact marketplace disbursement cycles (Settlement ID) with explicit rolling reserve releases.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
              <div className="p-3 bg-rose-500/10 text-rose-400 rounded-xl w-fit mb-4">
                <Clock className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-2">RTO Return Leakage Tracker</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Cross-references refunds with inventory restocks. Identifies customers refunded over 45 days ago where you never received physical stock back.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl w-fit mb-4">
                <SplitSquareVertical className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-2">Unified Multi-Store Pivot</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Stack Amazon, Flipkart, and Meesho side-by-side. See total net cash and total commissions across all sales channels in one unified matrix.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call To Action Banner */}
      <section className="py-16 px-6 bg-gradient-to-r from-emerald-950 via-slate-900 to-[#0B132B] border-t border-slate-800 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-extrabold text-white">
            Find Your Discrepancies in the Next 5 Minutes
          </h2>
          <p className="text-sm text-slate-300 mt-2 max-w-xl mx-auto">
            Get started on our free early-access tier. Reconcile up to 10,000 orders/month without entering a credit card.
          </p>
          <div className="mt-6 flex justify-center">
            <button
              onClick={onGoToApp}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm px-8 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center gap-2"
            >
              Open Live Seller Workspace
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-8 px-6 text-center text-xs text-slate-500 bg-[#080E21]">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 SellerFlow AI. Financial Operations & Settlement Reconciliation for E-Commerce Sellers.</p>
          <div className="flex gap-4 text-slate-400 font-medium">
            <button onClick={onGoToApp} className="hover:text-white transition">Workspace</button>
            <a href="#how-it-works" className="hover:text-white transition">How It Works</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
