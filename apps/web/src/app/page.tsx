"use client";

import React, { useState, useEffect, useMemo } from "react";
import LandingHome from "./LandingHome";
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
  Home
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

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";

export default function AppEntry() {
  const [viewMode, setViewMode] = useState<"landing" | "workspace">("landing");

  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [currentWs, setCurrentWs] = useState<any>(null);
  const [stores, setStores] = useState<any[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string>("all");
  const [selectedMarketplace, setSelectedMarketplace] = useState<string>("amazon_in");
  const [imports, setImports] = useState<any[]>([]);
  const [reconciliation, setReconciliation] = useState<any>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [returnLeakages, setReturnLeakages] = useState<any>(null);
  const [waterfallData, setWaterfallData] = useState<any>(null);

  // New Insights State
  const [settlementCycle, setSettlementCycle] = useState<any>(null);
  const [multiMarketplacePivot, setMultiMarketplacePivot] = useState<any>(null);
  const [cohortReturns, setCohortReturns] = useState<any>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [reconciling, setReconciling] = useState(false);
  
  const [activeTab, setActiveTab] = useState<
    "overview" | "settlement_cycle" | "multi_pivot" | "cohort_returns" | "discrepancies" | "leakage" | "profitability"
  >("overview");

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");

  // Batch Dispute Selection
  const [selectedDiscrepancyIds, setSelectedDiscrepancyIds] = useState<string[]>([]);

  // Evidence Drawer State
  const [drawerOrderId, setDrawerOrderId] = useState<string | null>(null);
  const [evidenceData, setEvidenceData] = useState<any>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

  // Dispute Package Modal
  const [disputePackage, setDisputePackage] = useState<any>(null);
  const [copiedDispute, setCopiedDispute] = useState(false);

  // Cost edit modal
  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [cogsInput, setCogsInput] = useState("");
  const [pkgInput, setPkgInput] = useState("");
  const [shipInput, setShipInput] = useState("");

  // Feedback modal
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [reviewSubmitted, setReviewSubmitted] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/workspaces`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.length > 0) {
          setWorkspaces(data);
          setCurrentWs(data[0]);
          loadWorkspaceData(data[0].id, "all");
        }
      })
      .catch((err) => console.error("Error loading workspaces", err));
  }, []);

  const loadWorkspaceData = (wsId: string, storeFilter: string = "all") => {
    fetch(`${API_BASE}/workspaces/${wsId}/stores`)
      .then((res) => res.json())
      .then((st) => setStores(st));

    fetch(`${API_BASE}/workspaces/${wsId}/imports`)
      .then((res) => res.json())
      .then((imp) => setImports(imp));

    const reconUrl = storeFilter && storeFilter !== "all"
      ? `${API_BASE}/workspaces/${wsId}/reconciliation/latest?store_id=${storeFilter}`
      : `${API_BASE}/workspaces/${wsId}/reconciliation/latest`;

    fetch(reconUrl)
      .then((res) => res.json())
      .then((recon) => setReconciliation(recon));

    fetch(`${API_BASE}/workspaces/${wsId}/products`)
      .then((res) => res.json())
      .then((prods) => setProducts(prods));

    fetch(`${API_BASE}/workspaces/${wsId}/returns-leakage`)
      .then((res) => res.json())
      .then((leak) => setReturnLeakages(leak));

    fetch(`${API_BASE}/workspaces/${wsId}/waterfall`)
      .then((res) => res.json())
      .then((wf) => setWaterfallData(wf));

    fetch(`${API_BASE}/workspaces/${wsId}/settlement-cycle-recon`)
      .then((res) => res.json())
      .then((sc) => setSettlementCycle(sc));

    fetch(`${API_BASE}/workspaces/${wsId}/multi-marketplace-pivot`)
      .then((res) => res.json())
      .then((mp) => setMultiMarketplacePivot(mp));

    fetch(`${API_BASE}/workspaces/${wsId}/cohort-returns`)
      .then((res) => res.json())
      .then((cr) => setCohortReturns(cr));
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !currentWs) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("marketplace", selectedMarketplace);
    
    const matchedStore = stores.find(s => s.marketplace_code === selectedMarketplace);
    if (matchedStore) {
      formData.append("store_id", matchedStore.id);
    }
    formData.append("report_type", "settlement");

    setUploading(true);
    setUploadProgress(20);
    const interval = setInterval(() => {
      setUploadProgress((prev) => (prev < 90 ? prev + 25 : prev));
    }, 200);

    try {
      const res = await fetch(`${API_BASE}/workspaces/${currentWs.id}/imports`, {
        method: "POST",
        body: formData,
      });
      clearInterval(interval);
      setUploadProgress(100);

      if (res.ok) {
        await triggerReconciliation();
      } else {
        const err = await res.json();
        alert(`Upload error: ${err.detail || "Failed to process file"}`);
      }
    } catch (err) {
      alert("Network error connecting to API");
    } finally {
      clearInterval(interval);
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 500);
      loadWorkspaceData(currentWs.id, selectedStoreId);
    }
  };

  const triggerReconciliation = async () => {
    if (!currentWs) return;
    setReconciling(true);
    try {
      const url = selectedStoreId !== "all" 
        ? `${API_BASE}/workspaces/${currentWs.id}/reconcile?store_id=${selectedStoreId}`
        : `${API_BASE}/workspaces/${currentWs.id}/reconcile`;
      await fetch(url, { method: "POST" });
      loadWorkspaceData(currentWs.id, selectedStoreId);
    } catch (err) {
      console.error(err);
    } finally {
      setReconciling(false);
    }
  };

  const openEvidenceDrawer = async (orderId: string) => {
    if (!currentWs) return;
    setDrawerOrderId(orderId);
    setLoadingEvidence(true);
    try {
      const res = await fetch(`${API_BASE}/workspaces/${currentWs.id}/evidence/${orderId}`);
      const data = await res.json();
      setEvidenceData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const handleExportCSV = () => {
    if (!currentWs) return;
    window.open(`${API_BASE}/workspaces/${currentWs.id}/reconciliation/export`, "_blank");
  };

  const handleExportTallyXML = () => {
    if (!currentWs) return;
    window.open(`${API_BASE}/workspaces/${currentWs.id}/export/tally-xml`, "_blank");
  };

  const handleGenerateDispute = async (discrepancyId: string) => {
    if (!currentWs) return;
    try {
      const formData = new FormData();
      formData.append("seller_name", currentWs.name);
      const res = await fetch(`${API_BASE}/workspaces/${currentWs.id}/discrepancies/${discrepancyId}/dispute-package`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setDisputePackage(data);
      setCopiedDispute(false);
    } catch (err) {
      alert("Failed to generate dispute ticket");
    }
  };

  const handleBatchManifestExport = async () => {
    if (!currentWs || selectedDiscrepancyIds.length === 0) return;
    try {
      const res = await fetch(`${API_BASE}/workspaces/${currentWs.id}/discrepancies/batch-manifest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedDiscrepancyIds),
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Batch_Dispute_Manifest_${selectedDiscrepancyIds.length}_orders.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert("Failed to export batch manifest");
    }
  };

  const handleSaveCosts = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWs || !editingProduct) return;
    const formData = new FormData();
    formData.append("sku", editingProduct.sku);
    formData.append("title", editingProduct.title || editingProduct.sku);
    formData.append("cogs", cogsInput || "0");
    formData.append("packaging", pkgInput || "0");
    formData.append("shipping", shipInput || "0");

    await fetch(`${API_BASE}/workspaces/${currentWs.id}/products`, {
      method: "POST",
      body: formData,
    });
    setEditingProduct(null);
    loadWorkspaceData(currentWs.id, selectedStoreId);
  };

  const filteredDiscrepancies = useMemo(() => {
    const list = reconciliation?.discrepancies || [];
    return list.filter((disc: any) => {
      const matchesSearch = !searchQuery || 
        (disc.external_order_id && disc.external_order_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (disc.explanation && disc.explanation.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesSeverity = severityFilter === "all" || disc.severity === severityFilter;
      return matchesSearch && matchesSeverity;
    });
  }, [reconciliation?.discrepancies, searchQuery, severityFilter]);

  const summary = reconciliation?.summary || {
    matched_count: 0,
    partial_count: 0,
    unmatched_count: 0,
    discrepancy_count: 0,
    total_difference: "0.0",
    total_actual: "0.0",
    total_expected: "0.0",
  };

  if (viewMode === "landing") {
    return <LandingHome onGoToApp={() => setViewMode("workspace")} />;
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] text-[#172033] flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between sticky top-0 z-20 shadow-sm">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode("landing")}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 border border-slate-200 px-2.5 py-1.5 rounded-lg hover:bg-slate-50 transition"
            title="Return to Home Landing Page"
          >
            <Home className="w-3.5 h-3.5" />
            Home
          </button>

          <div className="bg-[#172B4D] text-white p-2 rounded-lg font-bold flex items-center gap-1.5 shadow-sm">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="tracking-tight text-lg">SellerFlow AI</span>
          </div>
          <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200">
            Free Early-Access Tier
          </span>
        </div>

        {/* Multi-Store Selector & Action Buttons */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-inner">
            <StoreIcon className="w-4 h-4 text-slate-500" />
            <select
              value={selectedStoreId}
              onChange={(e) => {
                setSelectedStoreId(e.target.value);
                if (currentWs) loadWorkspaceData(currentWs.id, e.target.value);
              }}
              className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer"
            >
              <option value="all">Unified Multi-Store View (All Stores)</option>
              {stores.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name} ({s.marketplace_code.toUpperCase()})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleExportTallyXML}
            disabled={!reconciliation?.run}
            className="flex items-center gap-1.5 text-xs bg-amber-50 hover:bg-amber-100 text-amber-800 font-semibold px-3 py-1.5 rounded-md border border-amber-300 transition disabled:opacity-50"
          >
            <FileCode className="w-3.5 h-3.5" />
            Export Tally XML
          </button>

          <button
            onClick={handleExportCSV}
            disabled={!reconciliation?.run}
            className="flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-3 py-1.5 rounded-md border border-slate-300 transition disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            CSV
          </button>

          <button
            onClick={() => setShowFeedbackModal(true)}
            className="flex items-center gap-1.5 text-xs bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium px-3 py-1.5 rounded-md border border-indigo-200 transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Leave Review
          </button>
        </div>
      </header>

      {/* Main Body */}
      <div className="max-w-7xl mx-auto px-6 py-8 w-full flex-1 flex flex-col gap-6">
        
        {/* Real-time Ingestion Progress Bar */}
        {uploading && (
          <div className="bg-indigo-600 text-white p-4 rounded-xl shadow flex flex-col gap-2 animate-pulse">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span>Ingesting & Reconciling File ({uploadProgress}%)</span>
              <span>Matching with deterministic ruleset v1.0...</span>
            </div>
            <div className="w-full bg-indigo-900/50 rounded-full h-2">
              <div
                className="bg-emerald-400 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Found Money Teaser Card */}
        <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white p-6 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-md border border-emerald-500/20">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center gap-1">
                <DollarSign className="w-3.5 h-3.5" /> Settlement-Cycle Reconciler
              </span>
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight">
              SellerFlow found ₹{Number(waterfallData?.found_money_total || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })} in potential claims
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-xl">
              Reconciles strictly by settlement disbursement cycle. Matches bank deposits against gross sales, referral fees, and rolling reserves.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedMarketplace}
              onChange={(e) => setSelectedMarketplace(e.target.value)}
              className="bg-slate-800 text-white text-xs px-3 py-2.5 rounded-lg border border-slate-700 font-medium focus:outline-none"
            >
              <option value="amazon_in">Amazon India</option>
              <option value="flipkart">Flipkart</option>
              <option value="meesho">Meesho</option>
            </select>

            <label className="cursor-pointer bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm px-4 py-2.5 rounded-lg flex items-center gap-2 shadow transition">
              <UploadCloud className="w-4 h-4" />
              {uploading ? "Parsing..." : "Upload Settlement Report"}
              <input
                type="file"
                accept=".csv,.tsv,.txt,.xlsx"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1.5 border-b border-slate-200 pb-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition ${
              activeTab === "overview"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Reconciliation Overview
          </button>

          <button
            onClick={() => setActiveTab("settlement_cycle")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "settlement_cycle"
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Settlement Period & Reserves
          </button>

          <button
            onClick={() => setActiveTab("multi_pivot")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "multi_pivot"
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <SplitSquareVertical className="w-3.5 h-3.5" />
            Multi-Marketplace Stacked Pivot
          </button>

          <button
            onClick={() => setActiveTab("cohort_returns")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "cohort_returns"
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Cohort Return Attribution
          </button>
          
          <button
            onClick={() => setActiveTab("discrepancies")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "discrepancies"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Discrepancies & Claims
            {summary.discrepancy_count > 0 && (
              <span className="bg-amber-100 text-amber-800 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                {summary.discrepancy_count}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("leakage")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "leakage"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-rose-500" />
            RTO Leakage (&gt;45d)
            {returnLeakages?.count > 0 && (
              <span className="bg-rose-100 text-rose-800 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                {returnLeakages.count}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("profitability")}
            className={`px-3 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              activeTab === "profitability"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5 text-slate-500" />
            Unit Economics
          </button>
        </div>

        {/* Feature 1: Settlement-Period & Reserve Tracking Recon Tab */}
        {activeTab === "settlement_cycle" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col gap-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-indigo-600" />
                  Settlement Cycle & Bank Deposit Reconciliation
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Reconciles by disbursement cycle (Settlement ID) with rolling reserve releases instead of artificial calendar months.
                </p>
              </div>
              <span className="text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> 100% Balanced to Bank NEFT
              </span>
            </div>

            {settlementCycle && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Disbursement Header
                    </span>
                    <h4 className="text-lg font-mono font-bold text-slate-900 mt-1">
                      {settlementCycle.settlement_id}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">
                      Cycle Period: <strong>{settlementCycle.cycle_period}</strong> ({settlementCycle.marketplace})
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-200 flex justify-between items-center">
                    <div>
                      <span className="text-xs text-slate-500">Actual Bank NEFT Deposit</span>
                      <p className="text-2xl font-extrabold text-emerald-600">
                        ₹{settlementCycle.bank_deposit_expected.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500">Variance to Net Payout</span>
                      <p className="text-sm font-bold text-slate-800">
                        ₹{settlementCycle.reconciliation_variance.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-5 divide-y divide-slate-100 text-xs">
                  <div className="py-2 flex justify-between">
                    <span className="text-slate-600 font-medium">(+) Gross Dispatched Sales</span>
                    <span className="font-bold text-slate-900">₹{settlementCycle.line_items.gross_sales.toFixed(2)}</span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-slate-600 font-medium">(-) Marketplace Referral & Commission</span>
                    <span className="font-semibold text-rose-600">₹{settlementCycle.line_items.referral_fees.toFixed(2)}</span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-slate-600 font-medium">(-) Fulfillment, Shipping & Weight Handling</span>
                    <span className="font-semibold text-rose-600">₹{settlementCycle.line_items.fulfillment_fees.toFixed(2)}</span>
                  </div>
                  <div className="py-2 flex justify-between">
                    <span className="text-slate-600 font-medium">(-) Customer Returns in this cycle</span>
                    <span className="font-semibold text-rose-600">₹{settlementCycle.line_items.refunds_debited.toFixed(2)}</span>
                  </div>
                  <div className="py-2 flex justify-between bg-amber-50/50 px-2 rounded">
                    <span className="text-amber-800 font-medium">(-) Current Account Reserve Held (Rolling)</span>
                    <span className="font-semibold text-amber-700">₹{settlementCycle.line_items.current_reserve_held.toFixed(2)}</span>
                  </div>
                  <div className="py-2 flex justify-between bg-emerald-50/50 px-2 rounded">
                    <span className="text-emerald-800 font-medium">(+) Previous Account Reserve Released</span>
                    <span className="font-semibold text-emerald-700">+₹{settlementCycle.line_items.previous_reserve_released.toFixed(2)}</span>
                  </div>
                  <div className="py-2.5 flex justify-between font-bold text-sm bg-slate-100/70 px-2 rounded mt-1">
                    <span className="text-slate-900">(=) Calculated Net Payout</span>
                    <span className="text-slate-900">₹{settlementCycle.calculated_net_payout.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Feature 2: Multi-Marketplace Stacked Pivot Table Tab */}
        {activeTab === "multi_pivot" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <SplitSquareVertical className="w-5 h-5 text-indigo-600" />
                  Universal Multi-Marketplace Stacked Pivot
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Standardizes different marketplace fee names into one universal format. Amazon, Flipkart, and Meesho stacked side-by-side.
                </p>
              </div>
            </div>

            {multiMarketplacePivot?.rows && (
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4">Universal Fee Category</th>
                      <th className="py-3 px-4 text-right">Amazon India</th>
                      <th className="py-3 px-4 text-right">Flipkart</th>
                      <th className="py-3 px-4 text-right">Meesho</th>
                      <th className="py-3 px-4 text-right bg-slate-100">Total Stacked</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {multiMarketplacePivot.rows.map((row: any, i: number) => (
                      <tr key={i} className={row.is_net ? "bg-slate-100/70 font-extrabold text-slate-900 text-sm" : "hover:bg-slate-50 text-slate-700"}>
                        <td className="py-3 px-4 font-medium">{row.universal_fee_category}</td>
                        <td className="py-3 px-4 text-right font-mono">₹{row.amazon_in.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right font-mono">₹{row.flipkart.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right font-mono">₹{row.meesho.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right font-mono font-bold bg-slate-50/50">
                          ₹{row.total_stacked.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Feature 3: Cohort Return Attribution Tab */}
        {activeTab === "cohort_returns" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-indigo-600" />
                  Cohort-Based Return Attribution (Original Order Date Linking)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Tracks returns and refunds back to the original dispatch date and SKU rather than corrupting current settlement period margins.
                </p>
              </div>
            </div>

            {cohortReturns?.cohort_summary && (
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4">SKU</th>
                      <th className="py-3 px-4 text-right">Units Dispatched</th>
                      <th className="py-3 px-4 text-right">Gross Order Revenue</th>
                      <th className="py-3 px-4 text-right">Returns Debited</th>
                      <th className="py-3 px-4 text-right">Refunded Loss</th>
                      <th className="py-3 px-4 text-right">Realized Return %</th>
                      <th className="py-3 px-4 text-right bg-emerald-50 text-emerald-900">Net Cohort Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {cohortReturns.cohort_summary.map((c: any, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-slate-900">{c.sku}</td>
                        <td className="py-3 px-4 text-right font-mono">{c.units_dispatched}</td>
                        <td className="py-3 px-4 text-right font-mono">₹{c.gross_dispatched_revenue.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right font-mono font-semibold text-rose-600">{c.returns_count}</td>
                        <td className="py-3 px-4 text-right font-mono text-rose-600">₹{c.refunded_loss.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right">
                          <span className={`px-2 py-0.5 rounded-full font-semibold ${
                            c.is_high_return_risk ? "bg-red-50 text-red-700 border border-red-200" : "bg-slate-100 text-slate-700"
                          }`}>
                            {c.realized_return_rate_pct}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold bg-emerald-50/50 text-emerald-800">
                          ₹{c.net_cohort_revenue.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Overview Tab Content with Financial Waterfall Chart */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-6">
            {waterfallData?.waterfall && (
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Settlement Waterfall (Money Flow Breakdown)</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      How Gross Order Revenue flows down to Net Bank Disbursement after marketplace deductions.
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                    Calculated from audited settlement rows
                  </span>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={waterfallData.waterfall} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={(val) => `₹${Math.abs(val)}`} />
                      <Tooltip
                        formatter={(val: any) => [`₹${Math.abs(Number(val)).toFixed(2)}`, "Amount"]}
                        contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e2e8f0" }}
                      />
                      <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                        {waterfallData.waterfall.map((entry: any, index: number) => {
                          let color = "#3b82f6";
                          if (entry.type === "deduction") color = "#f97316";
                          if (entry.type === "leakage") color = "#ef4444";
                          if (entry.type === "total") color = "#10b981";
                          return <Cell key={`cell-${index}`} fill={color} />;
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold uppercase text-slate-500">Total Actual Payout</span>
                <p className="text-2xl font-bold text-slate-900 mt-2 flex items-center">
                  <IndianRupee className="w-5 h-5 text-slate-600 inline mr-0.5" />
                  {Number(summary.total_actual).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
                <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 mt-2">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Deterministic reconciliation
                </span>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold uppercase text-slate-500">Unexplained Difference</span>
                <p className="text-2xl font-bold text-amber-600 mt-2 flex items-center">
                  <IndianRupee className="w-5 h-5 inline mr-0.5" />
                  {Number(summary.total_difference).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
                <span className="text-xs text-slate-500 font-medium mt-2 block">
                  {summary.partial_count + summary.unmatched_count} orders need dispute filing
                </span>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold uppercase text-slate-500">Potential Return Leakage</span>
                <p className="text-2xl font-bold text-rose-600 mt-2 flex items-center">
                  <IndianRupee className="w-5 h-5 inline mr-0.5" />
                  {Number(returnLeakages?.total_leakage_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
                <span className="text-xs text-slate-500 font-medium mt-2 block">
                  {returnLeakages?.count || 0} unreturned refunds &gt;45 days
                </span>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold uppercase text-slate-500">Free Tier Usage</span>
                <p className="text-2xl font-bold text-slate-900 mt-2">
                  {summary.total_orders || 0} <span className="text-sm font-normal text-slate-500">/ 10,000</span>
                </p>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, ((summary.total_orders || 0) / 10000) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-900 flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-slate-600" />
                  Ingested Multi-Marketplace Reports
                </h3>
                <button
                  onClick={triggerReconciliation}
                  disabled={reconciling || imports.length === 0}
                  className="text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-md flex items-center gap-1.5 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? "animate-spin" : ""}`} />
                  Re-run Matching Engine
                </button>
              </div>

              {imports.length === 0 ? (
                <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                  <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-700">No reports uploaded yet</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    Upload your Amazon, Flipkart, or Meesho settlement reports to begin reconciliation.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-600 text-xs font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">File Name</th>
                        <th className="py-2.5 px-3">Marketplace</th>
                        <th className="py-2.5 px-3">Rows</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Uploaded At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {imports.map((imp) => (
                        <tr key={imp.id} className="hover:bg-slate-50">
                          <td className="py-3 px-3 font-medium text-slate-800">{imp.file_name}</td>
                          <td className="py-3 px-3">
                            <span className="text-xs font-semibold uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                              {imp.report_type || "Marketplace"}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-slate-600">{imp.row_count}</td>
                          <td className="py-3 px-3">
                            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2 py-0.5 rounded-full font-medium">
                              {imp.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-slate-500 text-xs">
                            {new Date(imp.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Flagged Discrepancies */}
        {activeTab === "discrepancies" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col gap-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Settlement Discrepancies & Dispute Claims</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Overcharges, missing payouts, and rate-card variances. Click any row to inspect source evidence.
                </p>
              </div>

              {selectedDiscrepancyIds.length > 0 && (
                <button
                  onClick={handleBatchManifestExport}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shadow transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export Batch Dispute Manifest ({selectedDiscrepancyIds.length} orders)
                </button>
              )}
            </div>

            <div className="flex flex-col md:flex-row items-center gap-3 pt-2">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search by Order ID or issue keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full text-xs pl-9 pr-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="flex items-center gap-1.5 self-start md:self-auto overflow-x-auto w-full md:w-auto">
                <button
                  onClick={() => setSeverityFilter("all")}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    severityFilter === "all" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  All Items
                </button>
                <button
                  onClick={() => setSeverityFilter("high")}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    severityFilter === "high" ? "bg-red-600 text-white" : "bg-red-50 text-red-700 hover:bg-red-100"
                  }`}
                >
                  High Severity (&gt; ₹100)
                </button>
                <button
                  onClick={() => setSeverityFilter("medium")}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    severityFilter === "medium" ? "bg-amber-600 text-white" : "bg-amber-50 text-amber-700 hover:bg-amber-100"
                  }`}
                >
                  Medium Severity
                </button>
              </div>
            </div>

            {filteredDiscrepancies.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-700">No discrepancies match your search filter</p>
                <p className="text-xs text-slate-500 mt-1">All processed transactions match expected settlement criteria.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 text-xs font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-3 w-8">
                        <input
                          type="checkbox"
                          checked={selectedDiscrepancyIds.length === filteredDiscrepancies.length && filteredDiscrepancies.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedDiscrepancyIds(filteredDiscrepancies.map((d: any) => d.id));
                            } else {
                              setSelectedDiscrepancyIds([]);
                            }
                          }}
                          className="rounded text-indigo-600 cursor-pointer"
                        />
                      </th>
                      <th className="py-3 px-3">Order ID</th>
                      <th className="py-3 px-3">Category</th>
                      <th className="py-3 px-3">Issue Explanation</th>
                      <th className="py-3 px-3">Discrepancy</th>
                      <th className="py-3 px-3">Source Row</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredDiscrepancies.map((disc: any) => (
                      <tr key={disc.id} className="hover:bg-slate-50 group">
                        <td className="py-3 px-3">
                          <input
                            type="checkbox"
                            checked={selectedDiscrepancyIds.includes(disc.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedDiscrepancyIds([...selectedDiscrepancyIds, disc.id]);
                              } else {
                                setSelectedDiscrepancyIds(selectedDiscrepancyIds.filter(id => id !== disc.id));
                              }
                            }}
                            className="rounded text-indigo-600 cursor-pointer"
                          />
                        </td>
                        <td className="py-3 px-3 font-mono text-xs font-bold text-slate-900">
                          {disc.external_order_id || "N/A"}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                            disc.severity === "high" ? "bg-red-50 text-red-700 border border-red-200" : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}>
                            {disc.category.replace("_", " ")}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-600 max-w-md">{disc.explanation}</td>
                        <td className="py-3 px-3 font-semibold text-red-600 text-xs">
                          -₹{Math.abs(Number(disc.difference_amount)).toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-500">Row #{disc.source_row_number || "-"}</td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => openEvidenceDrawer(disc.external_order_id)}
                              className="text-slate-500 hover:text-slate-800 p-1.5 rounded hover:bg-slate-100 transition"
                              title="Inspect Raw Evidence"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleGenerateDispute(disc.id)}
                              className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold px-2.5 py-1.5 rounded-md flex items-center gap-1 transition"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              Dispute
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Return & RTO Leakage Tab */}
        {activeTab === "leakage" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-rose-500" />
                  RTO & Customer Return Leakage (&gt;45 Days Policy Window)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Orders refunded to buyers where physical merchandise was not returned to your warehouse within the 45-day window.
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500 font-medium">Total Recoverable Leakage:</span>
                <p className="text-lg font-bold text-rose-600">
                  ₹{Number(returnLeakages?.total_leakage_amount || 0).toFixed(2)}
                </p>
              </div>
            </div>

            {(!returnLeakages?.leakages || returnLeakages.leakages.length === 0) ? (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-700">No return leakage detected</p>
                <p className="text-xs text-slate-500 mt-1">All customer refunds have corresponding restocks or are within the 45-day window.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 text-xs font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-3">Order ID</th>
                      <th className="py-3 px-3">SKU</th>
                      <th className="py-3 px-3">Refund Debited</th>
                      <th className="py-3 px-3">Days Since Refund</th>
                      <th className="py-3 px-3">Recommended Policy Action</th>
                      <th className="py-3 px-3">Claim Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {returnLeakages.leakages.map((leak: any) => (
                      <tr key={leak.id} className="hover:bg-slate-50">
                        <td className="py-3 px-3 font-mono text-xs font-bold text-slate-900">{leak.order_id}</td>
                        <td className="py-3 px-3 text-xs text-slate-700 font-medium">{leak.sku}</td>
                        <td className="py-3 px-3 text-xs font-bold text-rose-600">₹{leak.refund_debited.toFixed(2)}</td>
                        <td className="py-3 px-3 text-xs text-slate-600">
                          <span className="bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full font-semibold">
                            {leak.days_elapsed} days ago
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-600 max-w-sm">{leak.recommended_action}</td>
                        <td className="py-3 px-3">
                          <span className="text-xs bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full font-medium">
                            Eligible for SAFE-T Claim
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Profitability Tab */}
        {activeTab === "profitability" && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900">Product Unit Economics & Profitability</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Calculate real profit by entering your COGS, packaging, and shipping costs.
                </p>
              </div>
            </div>

            {products.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                <Package className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-700">No SKUs discovered yet</p>
                <p className="text-xs text-slate-500 mt-1">Upload a settlement report to auto-populate your product catalogue.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 text-xs font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-3">SKU</th>
                      <th className="py-3 px-3">Title</th>
                      <th className="py-3 px-3">COGS</th>
                      <th className="py-3 px-3">Packaging</th>
                      <th className="py-3 px-3">Est. Shipping</th>
                      <th className="py-3 px-3">Total Unit Cost</th>
                      <th className="py-3 px-3">Status</th>
                      <th className="py-3 px-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.map((prod) => (
                      <tr key={prod.id} className="hover:bg-slate-50">
                        <td className="py-3 px-3 font-mono text-xs font-bold text-slate-900">{prod.sku}</td>
                        <td className="py-3 px-3 text-slate-700 text-xs">{prod.title}</td>
                        <td className="py-3 px-3 text-slate-800 text-xs">₹{prod.cogs_amount.toFixed(2)}</td>
                        <td className="py-3 px-3 text-slate-800 text-xs">₹{prod.packaging_cost.toFixed(2)}</td>
                        <td className="py-3 px-3 text-slate-800 text-xs">₹{prod.shipping_estimate.toFixed(2)}</td>
                        <td className="py-3 px-3 font-bold text-slate-900 text-xs">₹{prod.total_unit_cost.toFixed(2)}</td>
                        <td className="py-3 px-3">
                          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                            prod.cost_coverage === "Complete" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}>
                            {prod.cost_coverage}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <button
                            onClick={() => {
                              setEditingProduct(prod);
                              setCogsInput(prod.cogs_amount ? String(prod.cogs_amount) : "");
                              setPkgInput(prod.packaging_cost ? String(prod.packaging_cost) : "");
                              setShipInput(prod.shipping_estimate ? String(prod.shipping_estimate) : "");
                            }}
                            className="text-xs font-medium text-indigo-600 hover:text-indigo-800 underline"
                          >
                            Edit Cost
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
      </div>

      {/* Slide-Over Evidence Drawer */}
      {drawerOrderId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex justify-end z-50">
          <div className="bg-white w-full max-w-lg h-full p-6 shadow-2xl flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
            <div>
              <div className="flex justify-between items-center pb-4 border-b border-slate-200">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Evidence Drawer</h3>
                  <p className="font-mono text-xs text-indigo-600 mt-0.5">{drawerOrderId}</p>
                </div>
                <button
                  onClick={() => {
                    setDrawerOrderId(null);
                    setEvidenceData(null);
                  }}
                  className="p-1 rounded-md hover:bg-slate-100 text-slate-500"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {loadingEvidence ? (
                <div className="py-12 text-center text-xs text-slate-500">Loading audit records...</div>
              ) : evidenceData ? (
                <div className="mt-4 flex flex-col gap-4">
                  <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex justify-between items-center">
                    <div>
                      <span className="text-xs text-slate-500">Expected Net Payout</span>
                      <p className="text-sm font-bold text-slate-800">₹{evidenceData.expected_order_net.toFixed(2)}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                    <div className="text-right">
                      <span className="text-xs text-slate-500">Actual Remitted</span>
                      <p className="text-sm font-bold text-rose-600">₹{evidenceData.actual_settlement_total.toFixed(2)}</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-2">
                      Settlement Statement Lines
                    </h4>
                    <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                      {evidenceData.transactions.map((t: any, i: number) => (
                        <div key={i} className="p-3 bg-white flex justify-between items-center text-xs">
                          <div>
                            <span className="font-semibold text-slate-800">{t.type}</span>
                            <span className="text-slate-400 ml-2">Row #{t.row}</span>
                          </div>
                          <span className={t.amount < 0 ? "text-rose-600 font-semibold" : "text-slate-800 font-semibold"}>
                            ₹{t.amount.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {evidenceData.source_rows && evidenceData.source_rows.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-2">
                        Original Raw Ingested Payload
                      </h4>
                      <pre className="bg-slate-900 text-emerald-400 p-3 rounded-xl text-[11px] font-mono overflow-x-auto max-h-56">
                        {JSON.stringify(evidenceData.source_rows[0].raw_payload, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className="pt-4 border-t border-slate-200">
              <button
                onClick={() => setDrawerOrderId(null)}
                className="w-full text-xs font-semibold py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg transition"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dispute Ticket Modal */}
      {disputePackage && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-xl w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  1-Click Dispute Claim Package
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Ready to copy and paste into Seller Central / Helpdesk ticket.
                </p>
              </div>
              <span className="text-xs bg-red-50 text-red-700 border border-red-200 px-2.5 py-1 rounded-full font-bold">
                Claim Value: ₹{disputePackage.disputed_amount.toFixed(2)}
              </span>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-600">Ticket Subject</label>
                <div className="bg-slate-50 border border-slate-200 p-2.5 rounded-lg text-xs font-mono text-slate-800 mt-1 select-all">
                  {disputePackage.dispute_subject}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600">Ticket Body & Audit Evidence</label>
                <textarea
                  readOnly
                  rows={8}
                  value={disputePackage.dispute_body}
                  className="w-full text-xs p-3 font-mono bg-slate-50 border border-slate-200 rounded-lg mt-1 focus:outline-none"
                />
              </div>

              <div className="bg-indigo-50 border border-indigo-100 p-3 rounded-lg text-xs text-indigo-800">
                <strong>Next Step:</strong> {disputePackage.action_step}
              </div>

              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={() => setDisputePackage(null)}
                  className="text-xs text-slate-600 hover:bg-slate-100 px-3 py-2 rounded-lg font-medium"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(
                      `Subject: ${disputePackage.dispute_subject}\n\n${disputePackage.dispute_body}`
                    );
                    setCopiedDispute(true);
                    setTimeout(() => setCopiedDispute(false), 2000);
                  }}
                  className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium shadow flex items-center gap-1.5"
                >
                  <Copy className="w-3.5 h-3.5" />
                  {copiedDispute ? "Copied to Clipboard!" : "Copy Full Dispute Ticket"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Cost Modal */}
      {editingProduct && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-sm w-full p-6 shadow-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-base">Edit Unit Costs for {editingProduct.sku}</h3>
            <form onSubmit={handleSaveCosts} className="mt-4 flex flex-col gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700">Cost of Goods Sold (COGS in ₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={cogsInput}
                  onChange={(e) => setCogsInput(e.target.value)}
                  placeholder="e.g. 450.00"
                  className="w-full text-xs p-2.5 mt-1 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700">Packaging Cost (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={pkgInput}
                  onChange={(e) => setPkgInput(e.target.value)}
                  placeholder="e.g. 25.00"
                  className="w-full text-xs p-2.5 mt-1 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700">Estimated Shipping Cost (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={shipInput}
                  onChange={(e) => setShipInput(e.target.value)}
                  placeholder="e.g. 70.00"
                  className="w-full text-xs p-2.5 mt-1 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="flex justify-end gap-2 mt-3">
                <button
                  type="button"
                  onClick={() => setEditingProduct(null)}
                  className="text-xs text-slate-600 hover:bg-slate-100 px-3 py-2 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium shadow"
                >
                  Save Costs
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review / Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              Help Us Improve SellerFlow AI!
            </h3>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              You are using our free tier. As an early seller, your feedback helps us refine fee calculation models and add more marketplace adapters.
            </p>

            {reviewSubmitted ? (
              <div className="bg-emerald-50 text-emerald-800 p-4 rounded-lg my-4 text-center text-sm font-medium">
                Thank you! Your feedback has been recorded.
              </div>
            ) : (
              <div className="mt-4 flex flex-col gap-3">
                <textarea
                  rows={4}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="Did SellerFlow spot any fees or settlement issues accurately? Any marketplace reports you need next?"
                  className="w-full text-xs p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                <div className="flex justify-end gap-2 mt-2">
                  <button
                    onClick={() => setShowFeedbackModal(false)}
                    className="text-xs text-slate-600 hover:bg-slate-100 px-3 py-2 rounded-lg font-medium"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      setReviewSubmitted(true);
                      setTimeout(() => setShowFeedbackModal(false), 2000);
                    }}
                    className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium shadow"
                  >
                    Submit Feedback
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
