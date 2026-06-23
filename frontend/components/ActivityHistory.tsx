"use client";

import React, { useState, useEffect } from "react";
import {
  Clock,
  Utensils,
  Car,
  Tv,
  ShoppingBag,
  Trash2,
  Droplet,
  Activity as ActivityIcon,
  Leaf,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  Download,
  BarChart2,
  Calendar,
  ChevronLeft,
  ChevronRight,
  TrendingDown,
  Award
} from "lucide-react";
import { api, HistoryRecord, HistoryStats } from "../services/api";
import { motion, AnimatePresence } from "framer-motion";

interface ActivityHistoryProps {
  activities?: any[]; // Keep props for backwards compatibility but we will fetch from history endpoints
  loading?: boolean;
}

const CATEGORY_ICONS: Record<string, any> = {
  food: Utensils,
  transport: Car,
  appliances: Tv,
  electricity: Tv,
  energy: Tv,
  shopping: ShoppingBag,
  waste: Trash2,
  water: Droplet,
  lifestyle: ActivityIcon,
};

const CATEGORY_COLORS: Record<string, string> = {
  food: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
  transport: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  electricity: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  energy: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  appliances: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
  shopping: "text-purple-500 bg-purple-500/10 border-purple-500/20",
  waste: "text-rose-500 bg-rose-500/10 border-rose-500/20",
  water: "text-cyan-500 bg-cyan-500/10 border-cyan-500/20",
  lifestyle: "text-slate-500 bg-slate-500/10 border-slate-500/20",
};

export default function ActivityHistory({}: ActivityHistoryProps) {
  // Main Data States
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filters, Search, Sort states
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [carbonLevel, setCarbonLevel] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortBy, setSortBy] = useState("latest");

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  // UI Expansion list
  const [expandedRecords, setExpandedRecords] = useState<Record<string, boolean>>({});

  const fetchHistoryData = async () => {
    setIsLoading(true);
    try {
      // Call standard endpoints
      const fetchedRecords = await api.getHistoryList({
        query: searchQuery || undefined,
        category: selectedCategory === "all" ? undefined : selectedCategory,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        carbon_level: carbonLevel === "all" ? undefined : carbonLevel,
        sort_by: sortBy,
      });
      // Triple-guard: ensure result is always an array before setting state
      const safeRecords = Array.isArray(fetchedRecords)
        ? fetchedRecords
        : Array.isArray((fetchedRecords as any)?.data)
        ? (fetchedRecords as any).data
        : Array.isArray((fetchedRecords as any)?.records)
        ? (fetchedRecords as any).records
        : [];
      setRecords(safeRecords);

      const fetchedStats = await api.getHistoryStats();
      setStats(fetchedStats);
    } catch (err) {
      console.error("Failed to load history data layer", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoryData();
  }, [searchQuery, selectedCategory, carbonLevel, startDate, endDate, sortBy]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this record from history?")) return;
    try {
      await api.deleteHistoryRecord(id);
      fetchHistoryData();
    } catch (err) {
      alert("Failed to delete record: " + err);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedRecords((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleExport = async (format: "json" | "csv") => {
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/api/v1/history/export?format=${format}`;
      window.open(url, "_blank");
    } catch (err) {
      alert("Failed to export history: " + err);
    }
  };

  // Pagination calculation — guard records to always be an array
  const safeRecords = Array.isArray(records) ? records : [];
  const totalItems = safeRecords.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedRecords = safeRecords.slice(startIndex, startIndex + itemsPerPage);

  const getIcon = (category: string) => {
    const cat = category.toLowerCase();
    const IconComponent = CATEGORY_ICONS[cat] || Leaf;
    const colorClass = CATEGORY_COLORS[cat] || "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    
    return (
      <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${colorClass}`}>
        <IconComponent className="w-4.5 h-4.5" />
      </div>
    );
  };

  const formatDateTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric"
      }) + " • " + d.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit"
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* ───────────────────────────────────────────────────────────────────────
          STATISTICS DASHBOARD GRID (Module 10)
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Stat 1: Total Activities */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-emerald-500/10 transition-all duration-300">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-stone-400" />
            Total Logs
          </span>
          <div className="mt-2 text-xl font-black text-white">
            {stats?.total_activities ?? 0} <span className="text-[10px] text-stone-400 font-bold uppercase">items</span>
          </div>
        </div>

        {/* Stat 2: Total Carbon */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-sky-500/10 transition-all duration-300">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-sky-450" />
            Total CO₂
          </span>
          <div className="mt-2 text-xl font-black text-white">
            {(stats?.total_carbon ?? 0).toFixed(1)} <span className="text-[10px] text-sky-400 font-bold uppercase">kg</span>
          </div>
        </div>

        {/* Stat 3: Average Carbon */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-amber-500/10 transition-all duration-300">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-amber-500" />
            Average CO₂
          </span>
          <div className="mt-2 text-xl font-black text-white">
            {(stats?.average_carbon ?? 0).toFixed(1)} <span className="text-[10px] text-amber-500 font-bold uppercase">kg</span>
          </div>
        </div>

        {/* Stat 4: Most Frequent Activity */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-purple-500/10 transition-all duration-300 xl:col-span-1">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <ActivityIcon className="w-3.5 h-3.5 text-purple-400" />
            Frequent
          </span>
          <div className="mt-2 text-xs font-bold text-white truncate" title={stats?.most_frequent_activity}>
            {stats?.most_frequent_activity || "N/A"}
          </div>
        </div>

        {/* Stat 5: Highest Carbon Activity */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-rose-500/10 transition-all duration-300 xl:col-span-1">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-rose-550" />
            Peak Source
          </span>
          <div className="mt-2 text-xs font-bold text-rose-400 truncate" title={stats?.highest_carbon_activity}>
            {stats?.highest_carbon_activity || "N/A"}
          </div>
        </div>

        {/* Stat 6: Lowest Carbon Activity */}
        <div className="glass-card rounded-2xl p-4 border border-white/5 bg-white/[0.01] hover:border-emerald-500/10 transition-all duration-300 xl:col-span-1">
          <span className="text-[9px] font-black uppercase tracking-widest text-stone-500 flex items-center gap-1.5">
            <Leaf className="w-3.5 h-3.5 text-emerald-450" />
            Eco Source
          </span>
          <div className="mt-2 text-xs font-bold text-emerald-400 truncate" title={stats?.lowest_carbon_activity}>
            {stats?.lowest_carbon_activity || "N/A"}
          </div>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────────────────
          FILTERS, SORTING, SEARCH & EXPORT (Modules 5, 6, 8, 9)
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="glass-card rounded-3xl p-5 border border-white/5 bg-white/[0.01] space-y-4">
        {/* Controls Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
          {/* Search bar (Module 6) */}
          <div className="lg:col-span-4 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-550" />
            <input
              type="text"
              placeholder="Search activity name, category or date..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full bg-stone-900 border border-white/5 rounded-2xl pl-10 pr-4 py-2.5 text-stone-200 text-xs font-semibold placeholder-stone-550 focus:outline-none focus:border-forest-500"
            />
          </div>

          {/* Category Select Filter (Module 5) */}
          <div className="lg:col-span-2">
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
              className="w-full bg-stone-900 border border-white/5 rounded-2xl px-3 py-2.5 text-stone-300 text-xs font-bold focus:outline-none focus:border-forest-500 cursor-pointer"
            >
              <option value="all">All Categories</option>
              <option value="transport">Transport</option>
              <option value="food">Food</option>
              <option value="energy">Energy</option>
              <option value="waste">Waste</option>
            </select>
          </div>

          {/* Carbon Level Filter (Module 5) */}
          <div className="lg:col-span-2">
            <select
              value={carbonLevel}
              onChange={(e) => { setCarbonLevel(e.target.value); setCurrentPage(1); }}
              className="w-full bg-stone-900 border border-white/5 rounded-2xl px-3 py-2.5 text-stone-300 text-xs font-bold focus:outline-none focus:border-forest-500 cursor-pointer"
            >
              <option value="all">All Carbon Levels</option>
              <option value="low">Low Carbon (≤ 1.0kg)</option>
              <option value="high">High Carbon (&gt; 5.0kg)</option>
            </select>
          </div>

          {/* Sort selection (Module 8) */}
          <div className="lg:col-span-2">
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setCurrentPage(1); }}
              className="w-full bg-stone-900 border border-white/5 rounded-2xl px-3 py-2.5 text-stone-300 text-xs font-bold focus:outline-none focus:border-forest-500 cursor-pointer"
            >
              <option value="latest">Latest Logs</option>
              <option value="oldest">Oldest Logs</option>
              <option value="highest_carbon">Highest Carbon</option>
              <option value="lowest_carbon">Lowest Carbon</option>
              <option value="category">By Category</option>
              <option value="alphabetical">Alphabetical</option>
            </select>
          </div>

          {/* Exports (Module 9) */}
          <div className="lg:col-span-2 flex gap-2">
            <button
              onClick={() => handleExport("csv")}
              className="flex-1 py-2.5 bg-white/5 hover:bg-forest-600/10 border border-white/5 hover:border-forest-500/20 text-stone-300 hover:text-white rounded-2xl text-[10px] font-black uppercase transition-all flex items-center justify-center gap-1.5 cursor-pointer active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              CSV
            </button>
            <button
              onClick={() => handleExport("json")}
              className="flex-1 py-2.5 bg-white/5 hover:bg-forest-600/10 border border-white/5 hover:border-forest-500/20 text-stone-300 hover:text-white rounded-2xl text-[10px] font-black uppercase transition-all flex items-center justify-center gap-1.5 cursor-pointer active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              JSON
            </button>
          </div>
        </div>

        {/* Date Filters row */}
        <div className="flex flex-wrap items-center gap-4 border-t border-white/5 pt-3.5">
          <span className="text-[10px] font-black text-stone-500 uppercase tracking-widest flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-stone-405" />
            Date Range Filter:
          </span>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
              className="bg-stone-900 border border-white/5 rounded-xl px-2 py-1 text-stone-300 text-[10px] font-bold focus:outline-none focus:border-forest-500 cursor-pointer"
            />
            <span className="text-stone-550 text-xs font-semibold">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
              className="bg-stone-900 border border-white/5 rounded-xl px-2 py-1 text-stone-300 text-[10px] font-bold focus:outline-none focus:border-forest-500 cursor-pointer"
            />
          </div>
          {(startDate || endDate || selectedCategory !== "all" || carbonLevel !== "all" || searchQuery) && (
            <button
              onClick={() => {
                setStartDate("");
                setEndDate("");
                setSelectedCategory("all");
                setCarbonLevel("all");
                setSearchQuery("");
                setCurrentPage(1);
              }}
              className="text-[9px] font-black uppercase tracking-wider text-rose-450 hover:text-rose-400 bg-rose-500/10 hover:bg-rose-500/15 border border-rose-500/10 rounded-lg px-2 py-1.5 transition-all cursor-pointer"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────────────────
          ACTIVITY HISTORY LEDGER / TIMELINE DISPLAY
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="glass-card rounded-3xl p-6 sm:p-8 border border-white/5 bg-white/[0.01]">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-[90px] rounded-2xl bg-white/5 border border-white/5"></div>
            ))}
          </div>
        ) : safeRecords.length > 0 ? (
          <div className="space-y-4">
            {paginatedRecords.map((record) => {
              const isExpanded = !!expandedRecords[record.id];
              return (
                <div
                  key={record.id}
                  className="rounded-2xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.03] transition-all duration-300 overflow-hidden cursor-pointer"
                  onClick={() => toggleExpand(record.id)}
                >
                  {/* Card Header Row */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4.5 gap-4">
                    {/* Left block: Categories tags + date */}
                    <div className="flex items-start gap-3.5 min-w-0">
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {(record.categories ?? []).map((cat) => getIcon(cat))}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-extrabold text-stone-400 uppercase tracking-wider">
                          Logged: {formatDateTime(record.timestamp)}
                        </p>
                        <p className="text-sm font-semibold text-white mt-1 truncate">
                          {(record.activities ?? []).map((a) => a?.name ?? "unknown").join(", ")}
                        </p>
                      </div>
                    </div>

                    {/* Right block: total emissions, delete, expand */}
                    <div className="flex items-center justify-between sm:justify-end gap-5">
                      <div className="text-right">
                        <div className="text-base font-black text-white">
                          {(record.total_carbon ?? 0.0).toFixed(2)}{" "}
                          <span className="text-[10px] font-normal text-stone-550">kg CO2e</span>
                        </div>
                        <span className="text-[8px] font-black uppercase tracking-widest text-stone-500 bg-white/5 border border-white/5 px-2 py-0.5 rounded-md mt-1 inline-block">
                          {record.source ?? "manual"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Delete Button */}
                        <button
                          onClick={(e) => handleDelete(record.id, e)}
                          className="p-2 bg-rose-500/5 hover:bg-rose-500/10 border border-rose-500/10 hover:border-rose-500/30 text-rose-450 hover:text-rose-400 rounded-xl transition-all cursor-pointer active:scale-95"
                          title="Delete Record"
                        >
                          <Trash2 className="w-4.5 h-4.5" />
                        </button>
                        
                        {/* Expand Icon */}
                        <div className="p-2 text-stone-400 hover:text-white rounded-xl">
                          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Expanded entities view showing factors & formulas */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: "auto" }}
                        exit={{ height: 0 }}
                        className="overflow-hidden bg-black/20 border-t border-white/5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="p-4.5 space-y-3">
                          {(record.activities ?? []).map((item, idx) => {
                            return (
                              <div
                                key={idx}
                                className="flex flex-col sm:flex-row sm:items-center justify-between p-3 border border-white/5 bg-white/[0.01] rounded-xl text-xs font-semibold gap-3"
                              >
                                <div className="flex items-center gap-3">
                                  {getIcon(item?.category ?? "lifestyle")}
                                  <div>
                                    <div className="text-stone-200 font-bold">{item?.name ?? "unknown"}</div>
                                    <div className="text-[10px] text-stone-500 uppercase font-black tracking-wider mt-0.5">
                                      Category: {item?.category ?? "lifestyle"} • Quantity: {item?.quantity ?? 0} {item?.unit ?? "units"}
                                    </div>
                                  </div>
                                </div>

                                <div className="sm:text-right flex flex-row sm:flex-col justify-between sm:justify-center items-center sm:items-end gap-2">
                                  <div className="text-[10px] font-bold text-stone-400">
                                    Formula: <code className="bg-stone-900 border border-white/5 px-1.5 py-0.5 rounded text-amber-500">{item?.formula || `${item?.quantity ?? 0} * ${item?.factor ?? 0}`}</code>
                                  </div>
                                  <div className="text-white font-extrabold text-xs">
                                    {Number(item?.carbon ?? item?.subtotal ?? 0.0).toFixed(2)} kg
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-6">
                <span className="text-[10px] font-bold text-stone-500">
                  Showing {startIndex + 1} - {Math.min(startIndex + itemsPerPage, totalItems)} of {totalItems} records
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="p-1.5 rounded-xl border border-white/5 bg-white/5 text-stone-400 hover:text-white disabled:opacity-30 disabled:hover:text-stone-400 transition-all cursor-pointer"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-xs font-extrabold text-stone-300 px-2">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1.5 rounded-xl border border-white/5 bg-white/5 text-stone-400 hover:text-white disabled:opacity-30 disabled:hover:text-stone-400 transition-all cursor-pointer"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-xs text-stone-500 flex flex-col items-center justify-center">
            <Leaf className="w-10 h-10 text-emerald-500/20 mb-3 animate-pulse" />
            <p className="font-semibold text-stone-400">No activity log history entries match your current search / filters.</p>
            <p className="text-stone-550 mt-1">Start logging carbon activities using the Logger Studio!</p>
          </div>
        )}
      </div>
    </div>
  );
}
