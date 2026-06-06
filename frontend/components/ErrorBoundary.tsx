"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { ShieldAlert, RefreshCw } from "lucide-react";

import { logger } from "../utils/logger";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error("ErrorBoundary", `React rendering exception caught: ${error.message}`, { 
      error: error.toString(), 
      errorInfo 
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 sm:p-8 rounded-3xl border border-rose-500/25 bg-rose-500/5 dark:bg-rose-950/10 text-rose-700 dark:text-rose-400 max-w-4xl mx-auto my-8 flex flex-col items-center text-center space-y-4 shadow-xl shadow-rose-500/5 animate-in fade-in">
          <ShieldAlert className="w-12 h-12 text-rose-500 animate-bounce" />
          <div>
            <h3 className="font-extrabold text-lg text-earth-800 dark:text-forest-100">
              Sustainability Intel component interrupted
            </h3>
            <p className="text-sm text-stone-500 dark:text-stone-400 mt-2 max-w-md">
              A temporary issue occurred while rendering this dashboard panel. Click below to reload state.
            </p>
            {this.state.error && (
              <pre className="mt-4 p-3 bg-black/25 text-left rounded-xl text-xs font-mono text-stone-400 overflow-auto max-w-lg border border-white/5">
                {this.state.error.toString()}
              </pre>
            )}
          </div>
          <button
            onClick={this.handleReset}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition-all flex items-center space-x-2 active:scale-95 cursor-pointer shadow-lg shadow-rose-650/20"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload Dashboard</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
