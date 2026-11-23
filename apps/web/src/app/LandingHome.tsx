"use client";

import React from "react";
import Link from "next/link";
import { Show, UserButton } from "@clerk/nextjs";
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

export default function LandingHome() {
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
          
          <Show when="signed-out">
            <Link
              href="/sign-in"
              className="bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs px-3.5 py-2 rounded-lg border border-slate-700 transition"
            >
              Sign In
            </Link>
            <Link
              href="/sign-up"
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
            >
              Get Started
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </Show>

          <Show when="signed-in">
            <Link
              href="/app"
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
            >
              Go to Workspace
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <UserButton />
          </Show>
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

        <div className="relative z-10 max-w-4xl mx-auto text-center flex flex-col items-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-6 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Deterministic E-Commerce Financial Reconciliation</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-[1.1]">
            Know What You Should Have Received vs.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
              What Marketplaces Actually Paid.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed">
            Stop losing 2–5% of GMV to silent marketplace fee overcharges, uncredited returns, 
            and clawbacks. Automate settlement audits and export reconciled DayBooks straight to TallyPrime.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
            <Show when="signed-out">
              <Link
                href="/sign-up"
                className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-extrabold text-sm px-7 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
              >
                <UploadCloud className="w-4 h-4" />
                Get Started Free
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Show>

            <Show when="signed-in">
              <Link
                href="/app"
                className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-extrabold text-sm px-7 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
              >
                Open Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Show>

            <a
              href="#how-it-works"
              className="w-full sm:w-auto bg-slate-800/80 hover:bg-slate-700/80 text-white font-semibold text-sm px-6 py-3.5 rounded-xl border border-slate-700 transition backdrop-blur-sm flex items-center justify-center gap-2"
            >
              See How It Works
            </a>
          </div>

          {/* Feature Highlights Row */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 text-left w-full max-w-3xl border-t border-slate-800/80 pt-8">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-xs font-semibold text-slate-200">100% Deterministic Math</span>
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-xs font-semibold text-slate-200">Amazon, Flipkart & Meesho</span>
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-xs font-semibold text-slate-200">1-Click Dispute Packages</span>
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-xs font-semibold text-slate-200">TallyPrime XML DayBook</span>
            </div>
          </div>
        </div>
      </section>

      {/* Structured "How It Works" Flow */}
      <section id="how-it-works" className="py-20 px-6 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-extrabold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
            Simple 4-Step Process
          </span>
          <h2 className="text-3xl font-black text-white mt-4 tracking-tight">
            How SellerFlow AI Works
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            From raw flat-file settlements to audit-proof evidence dossiers in seconds.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Step 1 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-black text-sm mb-4">
                01
              </div>
              <h3 className="text-base font-bold text-white mb-2">Drop Your Settlement Sheet</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Drag-and-drop raw Amazon Flat File V2, Flipkart Settlements, or Meesho payments.
                Files are verified via SHA-256 deduplication.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center text-[11px] text-emerald-400/90 font-medium">
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1" />
              Raw TSV / CSV / XLSX
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-black text-sm mb-4">
                02
              </div>
              <h3 className="text-base font-bold text-white mb-2">Deterministic Canonical Parse</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Every line item is normalized into exact Decimal representation, separating Referral,
                Closing, Shipping, and Pick & Pack fees.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center text-[11px] text-emerald-400/90 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              Decimal-Safe Math
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-black text-sm mb-4">
                03
              </div>
              <h3 className="text-base font-bold text-white mb-2">Audit Gaps & Overcharges</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Rule engines evaluate weight handling tiers, category commission rates, and 45-day
                return delivery windows to flag leakage.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center text-[11px] text-emerald-400/90 font-medium">
              <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" />
              Evidence Drawer Lineage
            </div>
          </div>

          {/* Step 4 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-black text-sm mb-4">
                04
              </div>
              <h3 className="text-base font-bold text-white mb-2">Claim Money & Export to Tally</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate pre-filled seller dispute tickets and download single-click TallyPrime XML DayBook
                files with accurate ledger mapping.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center text-[11px] text-emerald-400/90 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" />
              Instant XML & CSV
            </div>
          </div>
        </div>
      </section>

      {/* Feature Deep Dive */}
      <section id="features" className="py-20 px-6 bg-slate-950/50 border-t border-slate-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-extrabold uppercase tracking-widest text-teal-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
              Deterministic Engines
            </span>
            <h2 className="text-3xl font-black text-white mt-4 tracking-tight">
              Built for High-Volume Sellers
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <Calendar className="w-6 h-6 text-emerald-400 mb-4" />
              <h3 className="text-lg font-bold text-white mb-2">Settlement Cycle Tracking</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Track marketplace disbursement cycles, reserve holdbacks, and bank payouts with exact date matching.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <SplitSquareVertical className="w-6 h-6 text-teal-400 mb-4" />
              <h3 className="text-lg font-bold text-white mb-2">Multi-Marketplace Matrix</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Compare payout ratios, commission deductions, and return leakage across Amazon, Flipkart, and Meesho in one unified view.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <Clock className="w-6 h-6 text-indigo-400 mb-4" />
              <h3 className="text-lg font-bold text-white mb-2">Return & RTO Leakage</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Automatically detect returns older than 45 days where inventory was never received back and no reimbursement was credited.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20 px-6 bg-gradient-to-b from-[#0B132B] to-slate-950 border-t border-slate-800 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-black text-white tracking-tight">
            Ready to stop marketplace fee leakage?
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Create your account in 30 seconds and upload your first settlement sheet to audit your payouts.
          </p>
          <div className="mt-8 flex justify-center">
            <Show when="signed-out">
              <Link
                href="/sign-up"
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm px-8 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center gap-2"
              >
                Get Started Free
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Show>
            <Show when="signed-in">
              <Link
                href="/app"
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm px-8 py-3.5 rounded-xl shadow-xl shadow-emerald-500/25 transition transform hover:-translate-y-0.5 flex items-center gap-2"
              >
                Go to Workspace Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Show>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-8 px-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 SellerFlow AI. Deterministic Financial Reconciliation for E-Commerce Sellers.</p>
          <div className="flex gap-4 text-slate-400 font-medium">
            <a href="#how-it-works" className="hover:text-white transition">How It Works</a>
            <a href="#features" className="hover:text-white transition">Features</a>
            <Link href="/sign-in" className="hover:text-white transition">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
