"use client";

import React, { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, RefreshCw, X, Image as ImageIcon } from "lucide-react";
import { useAIStore } from "../stores/aiStore";

interface MultimodalUploadProps {
  onUploadSuccess: () => void;
  region: string;
}

export default function MultimodalUpload({ onUploadSuccess, region }: MultimodalUploadProps) {
  const { uploadReceipt, systemHealth } = useAIStore();
  const ocrOffline = systemHealth?.ocr === "offline";
  const ocrDegraded = systemHealth?.ocr === "degraded";

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type.startsWith("image/")) {
        setFile(droppedFile);
        setError(null);
        setResults(null);
      } else {
        setError("Only image files (PNG, JPG, WEBP) are supported for receipt/bill parsing.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type.startsWith("image/")) {
        setFile(selectedFile);
        setError(null);
        setResults(null);
      } else {
        setError("Only image files are supported.");
      }
    }
  };

  const handleBrowseClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleUploadSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const response = await uploadReceipt(file, region);
      if (response.success && response.logged_activities) {
        setResults(response.logged_activities);
        onUploadSuccess(); // trigger dashboard refresh
      } else {
        throw new Error("No activities were parsed from this image.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to process receipt image. Ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setResults(null);
    setError(null);
  };

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 transition-all duration-300">
      <div className="flex items-center space-x-2.5 mb-6 border-b border-white/10 dark:border-white/5 pb-3">
        <Upload className="w-5 h-5 text-emerald-500" />
        <h3 className="font-bold text-lg text-earth-800 dark:text-forest-100">
          Multimodal Bill &amp; Receipt OCR
        </h3>
      </div>

      <p className="text-xs text-stone-500 dark:text-stone-400 mb-4 leading-relaxed">
        Upload photos of restaurant receipts, grocery list invoices, or power bills (kWh metrics) to instantly digitize and log activities in region: <span className="font-black text-forest-650 dark:text-forest-400">{region}</span>.
      </p>

      {/* Upload Zone */}
      {!file && (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
            dragActive 
              ? "border-emerald-500 bg-emerald-500/5" 
              : "border-white/10 dark:border-white/5 bg-white/5 dark:bg-black/10 hover:bg-forest-600/5 dark:hover:bg-forest-950/10 hover:border-forest-500/30"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="flex flex-col items-center space-y-3">
            <div className="p-3 bg-forest-600/10 border border-forest-600/20 rounded-xl">
              <ImageIcon className="w-6 h-6 text-forest-500" />
            </div>
            <div>
              <p className="text-xs font-bold text-earth-800 dark:text-stone-300">
                Drag and drop your receipt image here, or <span className="text-forest-550 dark:text-forest-400 hover:underline">browse</span>
              </p>
              <p className="text-[10px] text-stone-500 mt-1">Supports JPEG, PNG, WEBP files up to 5MB</p>
            </div>
          </div>
        </div>
      )}

      {/* Selected File Details */}
      {file && !results && (
        <div className="p-4 rounded-2xl border border-white/10 bg-white/5 dark:bg-black/20 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-forest-400" />
              <div className="min-w-0">
                <p className="text-xs font-bold text-stone-300 truncate max-w-[200px]">{file.name}</p>
                <p className="text-[10px] text-stone-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <button
              onClick={clearFile}
              disabled={loading}
              className="p-1 hover:bg-white/10 rounded-lg transition-all"
            >
              <X className="w-4 h-4 text-stone-400 hover:text-white" />
            </button>
          </div>

          <button
            onClick={handleUploadSubmit}
            disabled={loading || ocrOffline}
            className="w-full py-2.5 bg-forest-600 hover:bg-forest-500 disabled:opacity-50 text-white font-extrabold text-xs uppercase tracking-wider rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg shadow-forest-600/15 cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running AI OCR Parser...</span>
              </>
            ) : (
              <span>Process and Log Emissions</span>
            )}
          </button>
        </div>
      )}

      {/* Error feedback */}
      {error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-550 dark:text-rose-450 text-xs font-semibold flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* OCR Offline feedback */}
      {ocrOffline && (
        <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-550 dark:text-rose-450 text-xs font-semibold flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>OCR service temporarily unavailable.</span>
        </div>
      )}

      {/* OCR Degraded feedback */}
      {ocrDegraded && (
        <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-550 dark:text-amber-450 text-xs font-semibold flex items-center space-x-2 animate-pulse">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Running in degraded mode.</span>
        </div>
      )}

      {/* Parsed results success list */}
      {results && (
        <div className="mt-4 p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="w-5 h-5" />
            <h4 className="font-extrabold text-xs uppercase tracking-wider">OCR Scanned Successfully</h4>
          </div>
          
          <div className="space-y-2">
            {results.map((act) => (
              <div
                key={act.id}
                className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-black/15 border border-white/5"
              >
                <div>
                  <p className="font-extrabold text-stone-300 capitalize">{act.item}</p>
                  <p className="text-[10px] text-stone-500">Scanned: "{act.input_text}"</p>
                </div>
                <span className="font-black text-forest-600 dark:text-forest-400">
                  +{act.calculated_value} kg CO2e
                </span>
              </div>
            ))}
          </div>

          <button
            onClick={clearFile}
            className="w-full mt-2 py-2 border border-white/10 hover:border-white/20 text-stone-300 hover:text-white font-bold text-[10px] uppercase rounded-xl transition-all cursor-pointer"
          >
            Scan Another Document
          </button>
        </div>
      )}
    </div>
  );
}
