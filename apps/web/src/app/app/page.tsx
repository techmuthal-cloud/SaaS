"use client";

import React, { useState, useEffect, useMemo, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser, useAuth, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { fetchWithAuth, API_BASE } from "../../lib/api";
import {
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  HelpCircle,
  IndianRupee,
  Sparkles,
  Download,
  Package,
  Plus,
  FileText,
  Copy,
  Clock,
  Layers,
  Store as StoreIcon,
  Search,
  Filter,
  Eye,
  X,
  FileCode,
  DollarSign,
  ArrowRight,
  Calendar,
  SplitSquareVertical,
  History,
  Home,
  Settings as SettingsIcon,
  Check,
  Landmark
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";

function WorkspaceAppContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoaded: userLoaded } = useUser();
  const { getToken, isLoaded: authLoaded, isSignedIn } = useAuth();

  // Workspace & Store State
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [currentWs, setCurrentWs] = useState<any>(null);
  const [stores, setStores] = useState<any[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string>("all");
  const [selectedMarketplace, setSelectedMarketplace] = useState<string>("amazon_in");

  // Core Data State
  const [imports, setImports] = useState<any[]>([]);
  const [reconciliation, setReconciliation] = useState<any>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [returnLeakages, setReturnLeakages] = useState<any>(null);
  const [waterfallData, setWaterfallData] = useState<any>(null);
  const [settlementCycle, setSettlementCycle] = useState<any>(null);
  const [multiMarketplacePivot, setMultiMarketplacePivot] = useState<any>(null);
  const [cohortReturns, setCohortReturns] = useState<any>(null);

  // Navigation State: Overview, Imports, Reconciliation, Settings
  const [activeTab, setActiveTab] = useState<"overview" | "imports" | "reconciliation" | "settings">("overview");
  const [reconSubTab, setReconSubTab] = useState<"discrepancies" | "cycles" | "pivot" | "cohorts" | "leakage">("discrepancies");

  // Guided Upload Wizard State
  const [showUploadWizard, setShowUploadWizard] = useState(
    () => searchParams.get("first_upload") === "true"
  );
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3 | 4>(1);
  const [wizardStoreId, setWizardStoreId] = useState<string>("");
  const [wizardReportType, setWizardReportType] = useState<string>("settlement");
  const [wizardFile, setWizardFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Bank Statement Matching Modal
  const [showBankModal, setShowBankModal] = useState(false);
  const [bankFile, setBankFile] = useState<File | null>(null);
  const [bankUploading, setBankUploading] = useState(false);
  const [bankMessage, setBankMessage] = useState<string | null>(null);

  // Export State
  const [exportingTally, setExportingTally] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Evidence Drawer State
  const [drawerOrderId, setDrawerOrderId] = useState<string | null>(null);
  const [evidenceData, setEvidenceData] = useState<any>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

  // Single Order Dispute Modal
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<any>(null);
  const [disputePackage, setDisputePackage] = useState<any>(null);
  const [generatingDispute, setGeneratingDispute] = useState(false);

  // New Store Modal
  const [showAddStoreModal, setShowAddStoreModal] = useState(false);
  const [newStoreName, setNewStoreName] = useState("");
  const [newStoreMarketplace, setNewStoreMarketplace] = useState<"amazon_in" | "flipkart" | "meesho">("amazon_in");
  const [addingStore, setAddingStore] = useState(false);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [reconciling, setReconciling] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Load all Workspace Data
  const loadWorkspaceData = useCallback(async (wsId: string, storeFilter: string = "all") => {
    try {
      const st = await fetchWithAuth(`/workspaces/${wsId}/stores`, {}, getToken);
      setStores(st || []);
      if (st && st.length > 0) {
        setWizardStoreId((prev) => prev || st[0].id);
      }

      const imp = await fetchWithAuth(`/workspaces/${wsId}/imports`, {}, getToken);
      setImports(imp || []);

      const reconUrl = storeFilter && storeFilter !== "all"
        ? `/workspaces/${wsId}/reconciliation/latest?store_id=${storeFilter}`
        : `/workspaces/${wsId}/reconciliation/latest`;
      const recon = await fetchWithAuth(reconUrl, {}, getToken);
      setReconciliation(recon);

      const prods = await fetchWithAuth(`/workspaces/${wsId}/products`, {}, getToken);
      setProducts(prods || []);

      const leak = await fetchWithAuth(`/workspaces/${wsId}/returns-leakage`, {}, getToken);
      setReturnLeakages(leak);

      const wf = await fetchWithAuth(`/workspaces/${wsId}/waterfall`, {}, getToken);
      setWaterfallData(wf);

      const sc = await fetchWithAuth(`/workspaces/${wsId}/settlement-cycle-recon`, {}, getToken);
      setSettlementCycle(sc);

      const mp = await fetchWithAuth(`/workspaces/${wsId}/multi-marketplace-pivot`, {}, getToken);
      setMultiMarketplacePivot(mp);

      const cr = await fetchWithAuth(`/workspaces/${wsId}/cohort-returns`, {}, getToken);
      setCohortReturns(cr);
    } catch (err) {
      console.error("Error loading workspace data:", err);
    }
  }, [getToken]);

  // 1. Authentication & Tenant Authorization Check
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
        if (!data || data.length === 0) {
          // If signed in but no workspace exists, route to dedicated onboarding
          router.push("/onboarding");
        } else {
          setWorkspaces(data);
          const active = data[0];
          setCurrentWs(active);
          loadWorkspaceData(active.id, "all");
        }
      })
      .catch((err) => {
        console.error("Failed to load workspaces:", err);
      })
      .finally(() => {
        if (isMounted) setLoadingInitial(false);
      });

    return () => {
      isMounted = false;
    };
  }, [authLoaded, userLoaded, isSignedIn, router, getToken, loadWorkspaceData]);

  // Trigger Reconciliation Engine
  const triggerReconciliation = async () => {
    if (!currentWs) return;
    setReconciling(true);
    try {
      const url = selectedStoreId !== "all" 
        ? `/workspaces/${currentWs.id}/reconcile?store_id=${selectedStoreId}`
        : `/workspaces/${currentWs.id}/reconcile`;
      await fetchWithAuth(url, { method: "POST" }, getToken);
      await loadWorkspaceData(currentWs.id, selectedStoreId);
    } catch (err) {
      console.error("Reconciliation error:", err);
    } finally {
      setReconciling(false);
    }
  };

  // Guided Upload Flow Handler
  const handleWizardUpload = async () => {
    if (!currentWs || !wizardFile) return;

    setUploading(true);
    setUploadError(null);
    setUploadProgress(20);

    const formData = new FormData();
    formData.append("file", wizardFile);
    if (wizardStoreId && wizardStoreId !== "all") {
      formData.append("store_id", wizardStoreId);
    }
    formData.append("report_type", wizardReportType);

    const progressTimer = setInterval(() => {
      setUploadProgress((prev) => (prev < 85 ? prev + 15 : prev));
    }, 200);

    try {
      const impRes = await fetchWithAuth(`/workspaces/${currentWs.id}/imports`, {
        method: "POST",
        body: formData,
      }, getToken);

      clearInterval(progressTimer);
      setUploadProgress(100);

      // Automatically trigger reconciliation on newly ingested report
      const reconUrl = wizardStoreId && wizardStoreId !== "all"
        ? `/workspaces/${currentWs.id}/reconcile?store_id=${wizardStoreId}`
        : `/workspaces/${currentWs.id}/reconcile`;
      const reconRes = await fetchWithAuth(reconUrl, { method: "POST" }, getToken);

      setUploadResult({
        import: impRes,
        recon: reconRes,
      });

      // Reload fresh workspace data
      await loadWorkspaceData(currentWs.id, selectedStoreId);
      setWizardStep(4);
    } catch (err: any) {
      clearInterval(progressTimer);
      setUploadError(err.message || "Failed to process upload file.");
    } finally {
      clearInterval(progressTimer);
      setUploading(false);
    }
  };

  // Bank Statement Upload
  const handleBankUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWs || !bankFile) return;
    setBankUploading(true);
    setBankMessage(null);

    const formData = new FormData();
    formData.append("file", bankFile);

    try {
      const res = await fetchWithAuth(`/workspaces/${currentWs.id}/bank-statements/upload`, {
        method: "POST",
        body: formData,
      }, getToken);
      setBankMessage(`Successfully imported ${res.transactions_imported || 0} bank transactions!`);
      setBankFile(null);
      await loadWorkspaceData(currentWs.id, selectedStoreId);
    } catch (err: any) {
      setBankMessage(`Error: ${err.message || "Failed to import bank statement"}`);
    } finally {
      setBankUploading(false);
    }
  };

  // TallyPrime XML Export Handler
  const handleExportTally = async () => {
    if (!currentWs) return;
    setExportingTally(true);
    setExportError(null);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/workspaces/${currentWs.id}/export-tally`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Export failed with status ${res.status}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SellerFlow_Tally_DayBook_${currentWs.name.replace(/\s+/g, "_")}.xml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error("Tally export error:", err);
      setExportError(err.message || "Failed to download Tally XML");
    } finally {
      setExportingTally(false);
    }
  };

  // Reconciliation CSV Export
  const handleExportCsv = () => {
    if (!reconciliation?.discrepancies || reconciliation.discrepancies.length === 0) {
      alert("No discrepancies to export.");
      return;
    }
    const headers = ["Order ID", "SKU", "Type", "Status", "Expected Fee (INR)", "Actual Fee (INR)", "Overcharge (INR)"];
    const rows = reconciliation.discrepancies.map((d: any) => [
      d.external_order_id || "",
      d.sku || "",
      d.discrepancy_type || "",
      d.status || "",
      d.expected_amount || "0.00",
      d.actual_amount || "0.00",
      d.discrepancy_amount || "0.00"
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e: any[]) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Reconciliation_Discrepancies_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Evidence Drawer Loader
  const openEvidenceDrawer = async (orderId: string) => {
    if (!currentWs) return;
    setDrawerOrderId(orderId);
    setLoadingEvidence(true);
    try {
      const data = await fetchWithAuth(`/workspaces/${currentWs.id}/evidence/${orderId}`, {}, getToken);
      setEvidenceData(data);
    } catch (e) {
      console.error("Evidence drawer error:", e);
    } finally {
      setLoadingEvidence(false);
    }
  };

  // Dispute Package Generator
  const openDisputePackageModal = async (disc: any) => {
    if (!currentWs) return;
    setSelectedDiscrepancy(disc);
    setShowDisputeModal(true);
    setGeneratingDispute(true);
    try {
      const data = await fetchWithAuth(
        `/workspaces/${currentWs.id}/discrepancies/${disc.id}/dispute-package`,
        { method: "POST" },
        getToken
      );
      setDisputePackage(data);
    } catch (e) {
      console.error("Dispute package error:", e);
    } finally {
      setGeneratingDispute(false);
    }
  };

  // Add New Store Handler
  const handleAddStore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWs || !newStoreName.trim()) return;
    setAddingStore(true);
    try {
      const form = new FormData();
      form.append("store_name", newStoreName.trim());
      form.append("marketplace", newStoreMarketplace);
      await fetchWithAuth(`/workspaces/${currentWs.id}/stores`, {
        method: "POST",
        body: form,
      }, getToken);
      setNewStoreName("");
      setShowAddStoreModal(false);
      await loadWorkspaceData(currentWs.id, selectedStoreId);
    } catch (err: any) {
      alert(`Failed to add store: ${err.message}`);
    } finally {
      setAddingStore(false);
    }
  };

  // Filtered Discrepancies
  const filteredDiscrepancies = useMemo(() => {
    if (!reconciliation?.discrepancies) return [];
    return reconciliation.discrepancies.filter((item: any) => {
      const matchesSearch =
        (item.external_order_id && item.external_order_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.sku && item.sku.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.discrepancy_type && item.discrepancy_type.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [reconciliation, searchQuery, statusFilter]);

  if (loadingInitial) {
    return (
      <div className="min-h-screen bg-[#0B132B] flex flex-col items-center justify-center p-6 text-slate-100 font-sans">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
        <p className="text-sm text-slate-400 font-medium">Opening your workspace...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Application Navbar */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-2 text-slate-900 hover:opacity-90 transition">
            <div className="bg-emerald-500 text-slate-950 p-1.5 rounded-lg font-black flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-slate-950" />
            </div>
            <span className="font-black text-base tracking-tight text-slate-950">SellerFlow <span className="text-emerald-600">AI</span></span>
          </Link>

          {/* Workspace Switcher / Name */}
          <div className="hidden sm:flex items-center gap-2 pl-4 border-l border-slate-200">
            <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              {currentWs?.name || "Workspace"}
            </span>
          </div>
        </div>

        {/* Global Controls & Primary CTA */}
        <div className="flex items-center space-x-3">
          {/* Store Filter Dropdown */}
          <div className="flex items-center space-x-1.5">
            <StoreIcon className="w-4 h-4 text-slate-400" />
            <select
              value={selectedStoreId}
              onChange={(e) => {
                setSelectedStoreId(e.target.value);
                if (currentWs) loadWorkspaceData(currentWs.id, e.target.value);
              }}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Connected Stores</option>
              {stores.map((st: any) => (
                <option key={st.id} value={st.id}>
                  {st.store_name} ({st.marketplace.toUpperCase()})
                </option>
              ))}
            </select>
          </div>

          {/* Upload Button */}
          <button
            onClick={() => {
              setShowUploadWizard(true);
              setWizardStep(1);
            }}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition flex items-center gap-1.5 cursor-pointer"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Upload Report
          </button>

          {/* User Profile */}
          <div className="pl-2 border-l border-slate-200">
            <UserButton />
          </div>
        </div>
      </header>

      {/* Main Navigation Tabs */}
      <div className="bg-white border-b border-slate-200 px-6 pt-3 flex items-center justify-between">
        <nav className="flex space-x-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === "overview"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            Overview
          </button>

          <button
            onClick={() => setActiveTab("imports")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === "imports"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            Imports
            {imports.length > 0 && (
              <span className="bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full text-[10px] font-semibold">
                {imports.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("reconciliation")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === "reconciliation"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Reconciliation
            {reconciliation?.discrepancies?.length > 0 && (
              <span className="bg-rose-100 text-rose-700 px-1.5 py-0.2 rounded-full text-[10px] font-bold">
                {reconciliation.discrepancies.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("settings")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === "settings"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <SettingsIcon className="w-4 h-4" />
            Settings
          </button>
        </nav>

        {/* Action Shortcuts: Bank Statement & Export Tally */}
        <div className="flex items-center space-x-2 pb-2">
          <button
            onClick={() => setShowBankModal(true)}
            className="text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-200 transition font-medium flex items-center gap-1.5 cursor-pointer"
          >
            <Landmark className="w-3.5 h-3.5 text-slate-500" />
            Bank Match
          </button>

          <button
            onClick={handleExportTally}
            disabled={exportingTally}
            className="text-xs text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-2.5 py-1.5 rounded-lg transition font-bold flex items-center gap-1.5 cursor-pointer"
          >
            {exportingTally ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <FileCode className="w-3.5 h-3.5" />}
            Export Tally XML
          </button>

          <button
            onClick={handleExportCsv}
            className="text-xs text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-lg transition font-medium flex items-center gap-1 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            CSV
          </button>
        </div>
      </div>

      {exportError && (
        <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>Tally Export Notice: {exportError}</span>
          </div>
          <button onClick={() => setExportError(null)} className="text-rose-500 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">

        {/* ==================== TAB 1: OVERVIEW ==================== */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-6">
            {/* 0-Imports Callout Banner */}
            {imports.length === 0 && (
              <div className="bg-gradient-to-r from-emerald-500/10 via-teal-500/5 to-transparent border border-emerald-500/30 rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-800 text-[11px] font-bold mb-2">
                    <Sparkles className="w-3 h-3 text-emerald-600" />
                    First Step
                  </div>
                  <h2 className="text-lg font-black text-slate-900 tracking-tight">
                    Welcome to your new workspace! Upload your first settlement sheet.
                  </h2>
                  <p className="text-xs text-slate-600 mt-1 max-w-xl">
                    SellerFlow uses raw order & disbursement data from Amazon, Flipkart, or Meesho to calculate exact fee deductions, return clawbacks, and missing reimbursements.
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowUploadWizard(true);
                    setWizardStep(1);
                  }}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs px-5 py-3 rounded-xl shadow-md transition flex items-center gap-2 shrink-0 cursor-pointer"
                >
                  <UploadCloud className="w-4 h-4" />
                  Upload First Report
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Financial Summary KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500">Total Actual Payout</span>
                <div className="mt-2 text-2xl font-black text-slate-900 flex items-center">
                  <IndianRupee className="w-5 h-5 text-emerald-600" />
                  {reconciliation?.summary?.total_disbursed_amount
                    ? Number(reconciliation.summary.total_disbursed_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })
                    : "0.00"}
                </div>
                <span className="text-[11px] text-emerald-600 font-medium mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Reconciled Net Bank Deposit
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500">Unexplained Difference</span>
                <div className="mt-2 text-2xl font-black text-rose-600 flex items-center">
                  <IndianRupee className="w-5 h-5 text-rose-600" />
                  {reconciliation?.summary?.total_discrepancy_amount
                    ? Number(reconciliation.summary.total_discrepancy_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })
                    : "0.00"}
                </div>
                <span className="text-[11px] text-rose-600 font-medium mt-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Audit Claims Ready
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500">Potential Return Leakage</span>
                <div className="mt-2 text-2xl font-black text-amber-600 flex items-center">
                  <IndianRupee className="w-5 h-5 text-amber-600" />
                  {returnLeakages?.total_leakage_amount
                    ? Number(returnLeakages.total_leakage_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })
                    : "0.00"}
                </div>
                <span className="text-[11px] text-amber-600 font-medium mt-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Returns older than 45 days
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500">Monthly Usage Tier</span>
                <div className="mt-2 text-2xl font-black text-slate-900">
                  {reconciliation?.summary?.total_orders_reconciled || 0}
                  <span className="text-sm font-normal text-slate-400"> / 10,000</span>
                </div>
                <span className="text-[11px] text-slate-500 font-medium mt-1 flex items-center gap-1">
                  Free Reconciliations
                </span>
              </div>
            </div>

            {/* Reconciliation Waterfall Chart */}
            {waterfallData?.waterfall && (
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Settlement Revenue Waterfall (Deterministic)</h3>
                    <p className="text-xs text-slate-500">Breakdown from Gross Product Sales to Net Bank Disbursement</p>
                  </div>
                  <button
                    onClick={triggerReconciliation}
                    disabled={reconciling}
                    className="text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 transition font-medium flex items-center gap-1.5"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? "animate-spin" : ""}`} />
                    Re-run Engine
                  </button>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={waterfallData.waterfall}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <XAxis dataKey="step" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip
                        formatter={(val: any) => [`₹${Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`, "Amount"]}
                        contentStyle={{ borderRadius: "8px", fontSize: "12px" }}
                      />
                      <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                        {waterfallData.waterfall.map((entry: any, index: number) => {
                          const amt = Number(entry.amount);
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.step === "Gross Sales" ? "#10b981" : amt < 0 ? "#f43f5e" : "#0284c7"}
                            />
                          );
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 2: IMPORTS ==================== */}
        {activeTab === "imports" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-slate-900">Ingested Settlement & Bank Reports</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Raw files uploaded and parsed with SHA-256 deduplication and Decimal precision.
                </p>
              </div>
              <button
                onClick={() => {
                  setShowUploadWizard(true);
                  setWizardStep(1);
                }}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm transition flex items-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Upload New Report
              </button>
            </div>

            {imports.length === 0 ? (
              <div className="py-16 text-center border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center">
                <FileSpreadsheet className="w-12 h-12 text-slate-300 mb-3" />
                <h4 className="text-sm font-bold text-slate-800">No reports ingested yet</h4>
                <p className="text-xs text-slate-500 max-w-md mt-1 mb-4">
                  Upload your marketplace settlement flat-files (Amazon Flat File V2, Flipkart or Meesho settlements) to populate your audit records.
                </p>
                <button
                  onClick={() => {
                    setShowUploadWizard(true);
                    setWizardStep(1);
                  }}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm transition flex items-center gap-1.5 cursor-pointer"
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  Upload First Report
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs text-slate-600">
                  <thead className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4">Filename</th>
                      <th className="py-3 px-4">Report Type</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Records</th>
                      <th className="py-3 px-4">Uploaded At</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {imports.map((imp: any) => (
                      <tr key={imp.id} className="hover:bg-slate-50/60 transition">
                        <td className="py-3.5 px-4 font-semibold text-slate-900 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-slate-400" />
                          {imp.filename}
                        </td>
                        <td className="py-3.5 px-4 uppercase text-[11px] font-bold text-slate-600">
                          {imp.report_type || "Settlement"}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            imp.status === "completed"
                              ? "bg-emerald-100 text-emerald-800"
                              : imp.status === "failed"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-amber-100 text-amber-800"
                          }`}>
                            {imp.status === "completed" && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                            {imp.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-medium text-slate-800">
                          {imp.record_count ? imp.record_count.toLocaleString() : "0"}
                        </td>
                        <td className="py-3.5 px-4 text-slate-500">
                          {imp.created_at ? new Date(imp.created_at).toLocaleString() : "—"}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => {
                              setActiveTab("reconciliation");
                            }}
                            className="text-xs text-emerald-600 hover:text-emerald-800 font-semibold"
                          >
                            View Audit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 3: RECONCILIATION ==================== */}
        {activeTab === "reconciliation" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Audit Discrepancies & Line-Item Claims</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Overcharges detected using dynamic rate cards and order evidence lineage.
                </p>
              </div>

              {/* Sub-view switcher */}
              <div className="flex space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
                <button
                  onClick={() => setReconSubTab("discrepancies")}
                  className={`text-xs px-3 py-1.5 rounded-md font-semibold transition cursor-pointer ${
                    reconSubTab === "discrepancies" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  Claims Table
                </button>
                <button
                  onClick={() => setReconSubTab("cycles")}
                  className={`text-xs px-3 py-1.5 rounded-md font-semibold transition cursor-pointer ${
                    reconSubTab === "cycles" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  Disbursement Cycles
                </button>
                <button
                  onClick={() => setReconSubTab("pivot")}
                  className={`text-xs px-3 py-1.5 rounded-md font-semibold transition cursor-pointer ${
                    reconSubTab === "pivot" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  Multi-Marketplace Pivot
                </button>
                <button
                  onClick={() => setReconSubTab("leakage")}
                  className={`text-xs px-3 py-1.5 rounded-md font-semibold transition cursor-pointer ${
                    reconSubTab === "leakage" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                  }`}
                >
                  RTO Leakage
                </button>
              </div>
            </div>

            {/* Sub-tab 1: Discrepancies Claims Table */}
            {reconSubTab === "discrepancies" && (
              <div className="flex flex-col gap-4">
                {/* Search & Status Filters */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div className="relative w-full sm:w-72">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="Search Order ID, SKU, or Type..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full text-xs pl-8 pr-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div className="flex items-center space-x-2 w-full sm:w-auto">
                    <Filter className="w-3.5 h-3.5 text-slate-400" />
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
                    >
                      <option value="all">All Discrepancy Statuses</option>
                      <option value="flagged">Flagged</option>
                      <option value="approved">Approved</option>
                      <option value="disputed">Disputed</option>
                    </select>
                  </div>
                </div>

                {filteredDiscrepancies.length === 0 ? (
                  <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <h4 className="text-sm font-bold text-slate-800">No discrepancies found</h4>
                    <p className="text-xs text-slate-500 mt-1">
                      All settlement line items match rate cards within tolerance or no reports have been parsed.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs text-slate-600">
                      <thead className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200">
                        <tr>
                          <th className="py-3 px-4">Order ID</th>
                          <th className="py-3 px-4">Discrepancy Type</th>
                          <th className="py-3 px-4">Expected Fee</th>
                          <th className="py-3 px-4">Actual Charged</th>
                          <th className="py-3 px-4">Overcharge</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredDiscrepancies.map((d: any) => (
                          <tr key={d.id} className="hover:bg-slate-50/70 transition">
                            <td className="py-3 px-4 font-mono font-bold text-slate-900">
                              {d.external_order_id}
                            </td>
                            <td className="py-3 px-4">
                              <span className="font-semibold text-slate-800">{d.discrepancy_type}</span>
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-600">
                              ₹{Number(d.expected_amount || 0).toFixed(2)}
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-800">
                              ₹{Number(d.actual_amount || 0).toFixed(2)}
                            </td>
                            <td className="py-3 px-4 font-mono font-bold text-rose-600">
                              ₹{Number(d.discrepancy_amount || 0).toFixed(2)}
                            </td>
                            <td className="py-3 px-4">
                              <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 uppercase">
                                {d.status}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right flex items-center justify-end space-x-2">
                              <button
                                onClick={() => openEvidenceDrawer(d.external_order_id)}
                                className="text-xs text-slate-600 hover:text-slate-900 bg-slate-100 px-2 py-1 rounded transition flex items-center gap-1"
                              >
                                <Eye className="w-3 h-3" />
                                Evidence
                              </button>
                              <button
                                onClick={() => openDisputePackageModal(d)}
                                className="text-xs text-emerald-700 hover:text-emerald-900 bg-emerald-50 px-2 py-1 rounded transition font-bold"
                              >
                                Dispute
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Sub-tab 2: Settlement Cycles */}
            {reconSubTab === "cycles" && settlementCycle && (
              <div className="flex flex-col gap-4">
                <h4 className="text-sm font-bold text-slate-900">Marketplace Disbursement Cycles & Reserves</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-xs text-slate-500 font-semibold">Total Settlements Count</span>
                    <p className="text-xl font-black text-slate-900 mt-1">{settlementCycle.settlement_count || 0}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-xs text-slate-500 font-semibold">Total Net Disbursed</span>
                    <p className="text-xl font-black text-emerald-600 mt-1">₹{Number(settlementCycle.total_net_disbursed || 0).toFixed(2)}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-xs text-slate-500 font-semibold">Reserve Balances Held</span>
                    <p className="text-xl font-black text-amber-600 mt-1">₹{Number(settlementCycle.total_reserve_held || 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Sub-tab 3: Multi-Marketplace Pivot */}
            {reconSubTab === "pivot" && multiMarketplacePivot && (
              <div className="flex flex-col gap-4">
                <h4 className="text-sm font-bold text-slate-900">Unified Multi-Marketplace Comparison</h4>
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-700 font-bold uppercase">
                      <tr>
                        <th className="py-2.5 px-4">Marketplace</th>
                        <th className="py-2.5 px-4">Gross Sales</th>
                        <th className="py-2.5 px-4">Total Deductions</th>
                        <th className="py-2.5 px-4">Net Payout</th>
                        <th className="py-2.5 px-4">Payout %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(multiMarketplacePivot).map(([mp, data]: [string, any]) => (
                        <tr key={mp}>
                          <td className="py-3 px-4 font-bold uppercase">{mp}</td>
                          <td className="py-3 px-4 font-mono">₹{Number(data.gross_sales || 0).toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-rose-600">₹{Number(data.total_deductions || 0).toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-emerald-600 font-bold">₹{Number(data.net_payout || 0).toFixed(2)}</td>
                          <td className="py-3 px-4 font-bold">{data.payout_percentage ? `${data.payout_percentage}%` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Sub-tab 4: RTO Leakage */}
            {reconSubTab === "leakage" && returnLeakages && (
              <div className="flex flex-col gap-4">
                <h4 className="text-sm font-bold text-slate-900">Return & RTO Leakage (&gt; 45 Days)</h4>
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 flex items-start gap-3">
                  <Clock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-bold text-amber-900 text-xs">Marketplace Return Window Audit</h5>
                    <p className="text-[11px] text-amber-800 mt-1">
                      Marketplaces are legally obligated to return physical stock or reimburse the seller within 45 days of a customer return initiation.
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-700 font-bold uppercase">
                      <tr>
                        <th className="py-2.5 px-4">Order ID</th>
                        <th className="py-2.5 px-4">SKU</th>
                        <th className="py-2.5 px-4">Return Date</th>
                        <th className="py-2.5 px-4">Days Elapsed</th>
                        <th className="py-2.5 px-4">Claimable Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {(returnLeakages.leakage_records || []).map((rec: any, idx: number) => (
                        <tr key={idx}>
                          <td className="py-3 px-4 font-mono font-bold">{rec.order_id}</td>
                          <td className="py-3 px-4 font-mono">{rec.sku}</td>
                          <td className="py-3 px-4">{rec.return_date || "—"}</td>
                          <td className="py-3 px-4 font-bold text-rose-600">{rec.days_elapsed} days</td>
                          <td className="py-3 px-4 font-mono font-bold text-emerald-600">₹{Number(rec.claim_amount || 0).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 4: SETTINGS ==================== */}
        {activeTab === "settings" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-6">
              <div>
                <h3 className="text-base font-bold text-slate-900">Connected Stores & Channels</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Marketplace accounts linked to this workspace for automated reconciliation.
                </p>
              </div>

              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl">
                {stores.map((st: any) => (
                  <div key={st.id} className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center font-black text-xs text-slate-700 uppercase">
                        {st.marketplace.slice(0, 2)}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">{st.store_name}</h4>
                        <span className="text-[11px] text-slate-500 uppercase">{st.marketplace}</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      Active
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setShowAddStoreModal(true)}
                className="self-start text-xs font-bold text-emerald-700 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-3.5 py-2 rounded-lg transition flex items-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Another Marketplace Store
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col gap-4">
              <h3 className="text-base font-bold text-slate-900">Workspace Details</h3>
              <div className="text-xs space-y-3">
                <div>
                  <span className="text-slate-400 font-semibold">Workspace Name</span>
                  <p className="font-bold text-slate-800">{currentWs?.name}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Workspace ID</span>
                  <p className="font-mono text-[11px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-200">
                    {currentWs?.id}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold">Reconciliation Engine</span>
                  <p className="text-emerald-700 font-bold">SellerFlow Deterministic v2.0</p>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* ==================== GUIDED 4-STEP UPLOAD WIZARD MODAL ==================== */}
      {showUploadWizard && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              onClick={() => {
                setShowUploadWizard(false);
                setWizardFile(null);
                setUploadError(null);
                setWizardStep(1);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Stepper Indicator */}
            <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-2 text-xs font-bold">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  wizardStep >= 1 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-400"
                }`}>1</span>
                <span className={wizardStep === 1 ? "text-emerald-700" : "text-slate-400"}>Store</span>

                <span className="text-slate-300">→</span>

                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  wizardStep >= 2 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-400"
                }`}>2</span>
                <span className={wizardStep === 2 ? "text-emerald-700" : "text-slate-400"}>Type</span>

                <span className="text-slate-300">→</span>

                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  wizardStep >= 3 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-400"
                }`}>3</span>
                <span className={wizardStep === 3 ? "text-emerald-700" : "text-slate-400"}>Upload</span>

                <span className="text-slate-300">→</span>

                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  wizardStep >= 4 ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-400"
                }`}>4</span>
                <span className={wizardStep === 4 ? "text-emerald-700" : "text-slate-400"}>Result</span>
              </div>
            </div>

            {uploadError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </div>
            )}

            {/* STEP 1: SELECT STORE */}
            {wizardStep === 1 && (
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-900">Step 1: Select Marketplace Store</h3>
                <p className="text-xs text-slate-500">
                  Select which connected store this settlement report belongs to.
                </p>

                <div className="space-y-2 mt-2">
                  {stores.map((st: any) => (
                    <label
                      key={st.id}
                      className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition ${
                        wizardStoreId === st.id
                          ? "border-emerald-600 bg-emerald-50/50"
                          : "border-slate-200 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          name="wizardStore"
                          value={st.id}
                          checked={wizardStoreId === st.id}
                          onChange={() => setWizardStoreId(st.id)}
                          className="accent-emerald-600"
                        />
                        <div>
                          <span className="font-bold text-xs text-slate-900">{st.store_name}</span>
                          <span className="block text-[10px] text-slate-400 uppercase font-semibold">{st.marketplace}</span>
                        </div>
                      </div>
                      <span className="text-xs text-slate-500 uppercase font-mono font-medium">Channel</span>
                    </label>
                  ))}
                </div>

                <div className="mt-4 flex justify-end">
                  <button
                    onClick={() => setWizardStep(2)}
                    disabled={!wizardStoreId}
                    className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs px-5 py-2.5 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
                  >
                    Next: Report Type
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: CHOOSE REPORT TYPE */}
            {wizardStep === 2 && (
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-900">Step 2: Choose Report Type</h3>
                <p className="text-xs text-slate-500">
                  Select the format of the settlement file downloaded from your seller portal.
                </p>

                <div className="space-y-2.5 mt-2">
                  <label
                    className={`flex items-start p-3.5 rounded-xl border cursor-pointer transition ${
                      wizardReportType === "settlement"
                        ? "border-emerald-600 bg-emerald-50/50"
                        : "border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="wizardType"
                      value="settlement"
                      checked={wizardReportType === "settlement"}
                      onChange={() => setWizardReportType("settlement")}
                      className="accent-emerald-600 mt-1"
                    />
                    <div className="ml-3">
                      <span className="font-bold text-xs text-slate-900">Marketplace Settlement Report (Standard)</span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Amazon Flat File V2 (TSV/CSV), Flipkart Settlement CSV, or Meesho Payment Sheet.
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-start p-3.5 rounded-xl border cursor-pointer transition ${
                      wizardReportType === "bank_statement"
                        ? "border-emerald-600 bg-emerald-50/50"
                        : "border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="wizardType"
                      value="bank_statement"
                      checked={wizardReportType === "bank_statement"}
                      onChange={() => setWizardReportType("bank_statement")}
                      className="accent-emerald-600 mt-1"
                    />
                    <div className="ml-3">
                      <span className="font-bold text-xs text-slate-900">Bank Statement (CSV)</span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        HDFC, ICICI, SBI or generic current account CSV statement with value date and credit deposits.
                      </p>
                    </div>
                  </label>
                </div>

                <div className="mt-4 flex justify-between items-center">
                  <button
                    onClick={() => setWizardStep(1)}
                    className="text-xs font-semibold text-slate-600 hover:text-slate-900"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => setWizardStep(3)}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
                  >
                    Next: Upload File
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: DRAG & DROP / FILE INPUT */}
            {wizardStep === 3 && (
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-900">Step 3: Drop or Browse File</h3>
                <p className="text-xs text-slate-500">
                  Select your raw .csv, .tsv, or .xlsx file (max 50MB, verified SHA-256).
                </p>

                <div className="mt-2 border-2 border-dashed border-slate-300 rounded-2xl p-6 text-center hover:border-emerald-500 transition cursor-pointer">
                  <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept=".csv,.tsv,.txt,.xlsx"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setWizardFile(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                    id="wizardFileInput"
                  />
                  <label htmlFor="wizardFileInput" className="cursor-pointer">
                    <span className="text-xs font-bold text-emerald-600 hover:text-emerald-700">
                      Click to choose file
                    </span>
                    <span className="text-xs text-slate-500"> or drag and drop</span>
                    <p className="text-[10px] text-slate-400 mt-1">Supports Amazon Flat File V2, CSV, TSV</p>
                  </label>
                </div>

                {wizardFile && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                      <span className="font-bold text-slate-900">{wizardFile.name}</span>
                      <span className="text-slate-500">({(wizardFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                    <button
                      onClick={() => setWizardFile(null)}
                      className="text-rose-500 hover:text-rose-700 font-bold"
                    >
                      Remove
                    </button>
                  </div>
                )}

                {uploading && (
                  <div className="space-y-1.5 mt-2">
                    <div className="flex justify-between text-[11px] font-semibold text-slate-600">
                      <span>Ingesting & Reconciling...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-emerald-600 h-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="mt-4 flex justify-between items-center">
                  <button
                    onClick={() => setWizardStep(2)}
                    disabled={uploading}
                    className="text-xs font-semibold text-slate-600 hover:text-slate-900"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleWizardUpload}
                    disabled={!wizardFile || uploading}
                    className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs px-6 py-2.5 rounded-xl shadow-md transition flex items-center gap-1.5 cursor-pointer"
                  >
                    {uploading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        Upload & Reconcile
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* STEP 4: RESULTS & REVIEW */}
            {wizardStep === 4 && uploadResult && (
              <div className="flex flex-col gap-4 text-center py-2">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 mx-auto flex items-center justify-center mb-1">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="text-base font-black text-slate-900">Settlement Reconciled Successfully!</h3>
                <p className="text-xs text-slate-600 max-w-sm mx-auto">
                  Your settlement data has been normalized with Decimal precision. Order lines, fee deductions, and rate cards have been evaluated.
                </p>

                <div className="grid grid-cols-2 gap-3 my-2 text-left bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-[11px] text-slate-500 font-semibold">Records Ingested</span>
                    <p className="text-base font-black text-slate-900">
                      {uploadResult.import?.record_count || uploadResult.recon?.total_orders || 0}
                    </p>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 font-semibold">Flagged Discrepancies</span>
                    <p className="text-base font-black text-rose-600">
                      {uploadResult.recon?.summary?.total_discrepancies || 0}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-2 mt-2">
                  <button
                    onClick={() => {
                      setShowUploadWizard(false);
                      setActiveTab("reconciliation");
                    }}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs py-2.5 rounded-xl transition flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    View Discrepancy Claims
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      setShowUploadWizard(false);
                      handleExportTally();
                    }}
                    className="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold text-xs py-2.5 rounded-xl transition flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <FileCode className="w-3.5 h-3.5" />
                    Export Tally DayBook
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================== BANK STATEMENT MODAL ==================== */}
      {showBankModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              onClick={() => {
                setShowBankModal(false);
                setBankMessage(null);
                setBankFile(null);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <Landmark className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Upload Bank Statement CSV</h3>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Reconciles actual bank credit deposits with marketplace disbursement IDs.
            </p>

            {bankMessage && (
              <div className="mb-4 p-3 rounded-xl text-xs bg-slate-100 border border-slate-200 text-slate-800">
                {bankMessage}
              </div>
            )}

            <form onSubmit={handleBankUpload} className="space-y-4">
              <div className="border border-dashed border-slate-300 rounded-xl p-4 text-center">
                <input
                  type="file"
                  accept=".csv"
                  required
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setBankFile(e.target.files[0]);
                    }
                  }}
                  className="text-xs"
                />
              </div>

              <button
                type="submit"
                disabled={!bankFile || bankUploading}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs py-2.5 rounded-xl transition cursor-pointer flex items-center justify-center gap-2"
              >
                {bankUploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />}
                Upload & Match Bank Credits
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ==================== ADD STORE MODAL ==================== */}
      {showAddStoreModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              onClick={() => setShowAddStoreModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-base font-bold text-slate-900 mb-4">Connect Marketplace Store</h3>

            <form onSubmit={handleAddStore} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Marketplace</label>
                <select
                  value={newStoreMarketplace}
                  onChange={(e: any) => setNewStoreMarketplace(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-xl bg-slate-50"
                >
                  <option value="amazon_in">Amazon India</option>
                  <option value="flipkart">Flipkart</option>
                  <option value="meesho">Meesho</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Store Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Amazon Electronics IN"
                  value={newStoreName}
                  onChange={(e) => setNewStoreName(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-200 rounded-xl"
                />
              </div>

              <button
                type="submit"
                disabled={addingStore}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs py-2.5 rounded-xl transition cursor-pointer"
              >
                {addingStore ? "Connecting Store..." : "Connect Store"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ==================== EVIDENCE DRAWER ==================== */}
      {drawerOrderId && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex justify-end">
          <div className="bg-white w-full max-w-xl h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Order Evidence Drawer</h3>
                  <span className="font-mono text-xs text-slate-500">{drawerOrderId}</span>
                </div>
                <button onClick={() => setDrawerOrderId(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {loadingEvidence ? (
                <div className="py-12 text-center text-xs text-slate-400">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-500" />
                  Fetching order lineage and transaction rows...
                </div>
              ) : evidenceData ? (
                <div className="space-y-4 text-xs">
                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                    <span className="text-[10px] font-bold uppercase text-slate-500">Order Status & Amounts</span>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div>
                        <span className="text-slate-400 text-[10px]">Total Order Value</span>
                        <p className="font-bold text-slate-900">₹{evidenceData.order?.order_amount || "0.00"}</p>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px]">Net Payout Received</span>
                        <p className="font-bold text-emerald-600">₹{evidenceData.order?.disbursed_amount || "0.00"}</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-800 mb-2">Ingested Settlement Transactions</h4>
                    <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl max-h-56 overflow-y-auto">
                      {(evidenceData.transactions || []).map((t: any) => (
                        <div key={t.id} className="p-3 flex justify-between items-center text-[11px]">
                          <div>
                            <span className="font-semibold text-slate-800">{t.transaction_type}</span>
                            <span className="block text-[10px] text-slate-400">{t.amount_description || t.amount_type}</span>
                          </div>
                          <span className={`font-mono font-bold ${Number(t.amount) < 0 ? "text-rose-600" : "text-emerald-600"}`}>
                            ₹{Number(t.amount).toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500">No evidence details available.</p>
              )}
            </div>

            <button
              onClick={() => setDrawerOrderId(null)}
              className="mt-6 w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs py-2.5 rounded-xl transition cursor-pointer"
            >
              Close Evidence Drawer
            </button>
          </div>
        </div>
      )}

      {/* ==================== SINGLE DISPUTE PACKAGE MODAL ==================== */}
      {showDisputeModal && selectedDiscrepancy && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              onClick={() => {
                setShowDisputeModal(false);
                setSelectedDiscrepancy(null);
                setDisputePackage(null);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-base font-bold text-slate-900 mb-2">Marketplace Dispute Package</h3>
            <p className="text-xs text-slate-500 mb-4">
              Pre-filled claim evidence template for Seller Support dispute tickets.
            </p>

            {generatingDispute ? (
              <div className="py-12 text-center text-xs text-slate-400">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-500" />
                Generating claim dossier...
              </div>
            ) : disputePackage ? (
              <div className="space-y-4 text-xs">
                <div>
                  <span className="font-bold text-slate-700">Ticket Subject:</span>
                  <p className="bg-slate-50 p-2 rounded-lg border border-slate-200 mt-1 font-mono text-[11px]">
                    {disputePackage.ticket_subject}
                  </p>
                </div>

                <div>
                  <span className="font-bold text-slate-700">Dispute Narrative & Evidence:</span>
                  <textarea
                    readOnly
                    rows={6}
                    value={disputePackage.ticket_body}
                    className="w-full bg-slate-50 p-2.5 rounded-lg border border-slate-200 mt-1 font-mono text-[11px] text-slate-700"
                  />
                </div>

                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`${disputePackage.ticket_subject}\n\n${disputePackage.ticket_body}`);
                      alert("Copied dispute text to clipboard!");
                    }}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    Copy Ticket Text
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

    </div>
  );
}

export default function WorkspaceApp() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#0B132B] flex flex-col items-center justify-center p-6 text-slate-100 font-sans">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
          <p className="text-sm text-slate-400 font-medium">Opening your workspace...</p>
        </div>
      }
    >
      <WorkspaceAppContent />
    </Suspense>
  );
}
