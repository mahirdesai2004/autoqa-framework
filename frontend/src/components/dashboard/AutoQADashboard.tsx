"use client";

import React, { useState, useEffect } from "react";

export default function AutoQADashboard() {
  const [statusData, setStatusData] = useState<{ status: string; providers_configured: string[] } | null>(null);
  const [requirement, setRequirement] = useState("User should be able to search for a product");
  const [url, setUrl] = useState("https://example.com");
  
  // Execution State
  const [phase, setPhase] = useState<"idle" | "generating" | "executing" | "complete" | "error">("idle");
  const [steps, setSteps] = useState<any[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetch(`${API_URL}/api/v1/status`)
      .then(res => res.json())
      .then(data => setStatusData(data))
      .catch(err => console.error("Failed to fetch status:", err));
  }, []);

  const runPipeline = async () => {
    setPhase("generating");
    setErrorMsg(null);
    setSteps([]);
    setResult(null);
    setReason(null);
    setScreenshot(null);

    try {
      // 1. Generate Steps
      const genRes = await fetch(`${API_URL}/api/v1/generate-steps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement, url }),
      });
      
      const genData = await genRes.json();
      if (!genRes.ok) throw new Error(genData.detail || "Failed to generate steps");
      
      setSteps(genData.steps);
      setPhase("executing");

      // 2. Run Test
      const testRes = await fetch(`${API_URL}/api/v1/run-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ steps: genData.steps, url }),
      });
      
      const testData = await testRes.json();
      if (!testRes.ok) throw new Error(testData.detail || "Test execution failed");

      setResult(testData.result);
      setReason(testData.reason);
      
      // The backend returns an absolute path on the host system (e.g. /Users/mahir/...).
      // We can't render that directly in Next.js. We need a route in FastAPI to serve it, 
      // or we just render the file path text. For now, we'll store the path.
      setScreenshot(testData.screenshot);
      setPhase("complete");

    } catch (err: any) {
      setErrorMsg(err.message);
      setPhase("error");
    }
  };

  return (
    <div className="mx-auto max-w-5xl py-12 px-4 sm:px-6 lg:px-8">
      {/* Hero Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl">
          AutoQA <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Engine</span>
        </h1>
        <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
          Resilient Agentic DOM Parsing & E2E Validation
        </p>
        
        {/* Badges */}
        <div className="mt-6 flex justify-center gap-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-800">
            <span className="w-2 h-2 mr-2 bg-emerald-500 rounded-full"></span>
            System {statusData ? "Online" : "Connecting..."}
          </span>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            <span className="w-2 h-2 mr-2 bg-blue-500 rounded-full"></span>
            Routing: {statusData?.providers_configured?.join(" → ") || "Detecting..."}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Configuration Form */}
        <div className="lg:col-span-1 bg-white shadow-sm ring-1 ring-gray-900/5 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Task Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Software Requirement</label>
              <textarea 
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                rows={4}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Target URL</label>
              <input 
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
              />
            </div>
            
            <button 
              onClick={runPipeline}
              disabled={phase === "generating" || phase === "executing"}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {phase === "generating" ? "Analyzing DOM..." : phase === "executing" ? "Running Test..." : "Run Automation"}
            </button>
          </div>
        </div>

        {/* Right Column: Execution & Telemetry */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Status Timeline */}
          {(phase !== "idle") && (
            <div className="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-xl p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Pipeline</h3>
              <div className="flex items-center space-x-4 mb-2">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${phase === 'generating' ? 'bg-indigo-100 text-indigo-600 animate-pulse' : 'bg-green-100 text-green-600'}`}>1</div>
                <div className="text-sm font-medium text-gray-900">LLM Orchestration & DOM Analysis</div>
              </div>
              <div className="flex items-center space-x-4 mb-2">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${phase === 'executing' ? 'bg-indigo-100 text-indigo-600 animate-pulse' : phase === 'complete' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>2</div>
                <div className="text-sm font-medium text-gray-900">Browser Automation Execution</div>
              </div>
            </div>
          )}

          {/* Error State */}
          {phase === "error" && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Pipeline Halted</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{errorMsg}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Telemetry */}
          {phase === "complete" && (
            <div className={`bg-white shadow-sm ring-1 rounded-xl p-6 ${result === 'PASS' ? 'ring-green-500/50 border-t-4 border-t-green-500' : 'ring-red-500/50 border-t-4 border-t-red-500'}`}>
              <h3 className="text-xl font-bold mb-2">
                {result === "PASS" ? "✅ Validation Passed" : "❌ Validation Failed"}
              </h3>
              <div className="prose prose-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-200 mt-4">
                <p className="whitespace-pre-wrap">{reason}</p>
              </div>

              {screenshot && (
                <div className="mt-4 text-sm text-gray-500">
                  📸 Screenshot saved to host disk: <code className="bg-gray-100 px-2 py-1 rounded">{screenshot}</code>
                </div>
              )}
            </div>
          )}

          {/* Logs Accordion */}
          {steps.length > 0 && (
             <details className="group bg-white shadow-sm ring-1 ring-gray-900/5 rounded-xl">
               <summary className="flex cursor-pointer items-center justify-between p-6 font-medium text-gray-900">
                 View Raw JSON Execution Plan
                 <span className="ml-1.5 flex-shrink-0 transition duration-300 group-open:-rotate-180">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                     <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                   </svg>
                 </span>
               </summary>
               <div className="px-6 pb-6 text-gray-500">
                 <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-xs">
                   {JSON.stringify(steps, null, 2)}
                 </pre>
               </div>
             </details>
          )}

        </div>
      </div>
    </div>
  );
}
