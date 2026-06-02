"use client";

import React, { useState, useEffect } from "react";
import { Cpu, Zap, Wifi, Activity, BarChart3, TrendingUp, RefreshCw } from "lucide-react";
import { 
  ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, 
  CartesianGrid, Tooltip as ChartTooltip, AreaChart, Area 
} from "recharts";

interface Device {
  name: string;
  type: string;
  status: "online" | "offline";
  consumption: string;
}

export default function IoTDashboard() {
  // Live IoT telemetry states
  const [voltage, setVoltage] = useState(230.1);
  const [current, setCurrent] = useState(4.52);
  const [cumulativeEnergy, setCumulativeEnergy] = useState(15.204);
  const [lastTickTime, setLastTickTime] = useState("");

  // Simulated telemetry loop representing active WebSocket/MQTT messages
  useEffect(() => {
    setLastTickTime(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      // Fluctuations in Voltage (228 - 232 V)
      const newV = parseFloat((230 + (Math.random() * 4 - 2)).toFixed(1));
      
      // Fluctuations in Current (4.1 - 4.9 A)
      const newC = parseFloat((4.5 + (Math.random() * 0.8 - 0.4)).toFixed(2));
      
      // Compute power from new values
      const newPowerW = newV * newC;
      
      // Increment cumulative energy consumption (Power in kW * tick hours, say 3 seconds = 3/3600 h)
      const deltaKwh = (newPowerW / 1000) * (3.0 / 3600.0);
      
      setVoltage(newV);
      setCurrent(newC);
      setCumulativeEnergy(prev => parseFloat((prev + deltaKwh).toFixed(5)));
      setLastTickTime(new Date().toLocaleTimeString());
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const power = parseFloat((voltage * current).toFixed(0)); // Watts
  const co2Factor = 0.42; // kg CO₂e / kWh
  const estimatedCo2 = parseFloat((cumulativeEnergy * co2Factor).toFixed(3)); // kg

  const devices: Device[] = [
    { name: "Smart Meter", type: "Main Grid", status: "online", consumption: "1035 W" },
    { name: "Energy Plug", type: "Smart Appliance", status: "online", consumption: "120 W" },
    { name: "AC Monitor", type: "HVAC Sensor", status: "online", consumption: "850 W" },
    { name: "Solar Panel", type: "Generation Node", status: "online", consumption: "-340 W" },
    { name: "EV Charger", type: "Vehicle Charger", status: "offline", consumption: "0 W" }
  ];

  // Chart data 1: Energy Usage breakdown by Device
  const deviceBreakdownData = [
    { name: "AC Monitor", usage: 8.5, color: "#10b981" },
    { name: "Energy Plug", usage: 2.1, color: "#38bdf8" },
    { name: "EV Charger", usage: 4.6, color: "#f43f5e" },
    { name: "Misc load", usage: 1.2, color: "#64748b" }
  ];

  // Chart data 2: Hourly trend of energy usage
  const trendData = [
    { hour: "12:00", load: 1.2, gen: 0.0 },
    { hour: "13:00", load: 1.4, gen: 1.5 },
    { hour: "14:00", load: 1.8, gen: 2.2 },
    { hour: "15:00", load: 1.5, gen: 1.8 },
    { hour: "16:00", load: 2.3, gen: 0.8 },
    { hour: "17:00", load: 3.2, gen: 0.1 },
    { hour: "18:00", load: 4.1, gen: 0.0 }
  ];

  const CustomChartTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card bg-[#0b120f]/95 px-3.5 py-2.5 rounded-xl border border-emerald-500/20 text-xs shadow-xl backdrop-blur-md font-sans">
          <p className="font-extrabold text-[9px] text-stone-500 uppercase tracking-widest mb-1 pb-1 border-b border-white/5">{label}</p>
          <div className="space-y-1 font-bold">
            {payload.map((p: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center gap-4">
                <span className="text-stone-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: p.color || p.fill }}></span>
                  {p.name}:
                </span>
                <span className="text-stone-200">{Number(p.value).toFixed(2)} kWh</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-5 select-none">
      {/* Title Header */}
      <div className="flex justify-between items-center pb-2">
        <div>
          <h2 className="text-lg font-black uppercase tracking-wider text-white">Smart IoT Devices</h2>
          <p className="text-[10px] text-stone-550 font-bold uppercase tracking-wider mt-0.5">Live energy telemetry and hardware orchestration</p>
        </div>
        <div className="flex items-center space-x-2 text-[9px] text-emerald-450 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-lg font-black uppercase tracking-wider animate-pulse">
          <RefreshCw className="w-3 h-3 animate-spin" />
          <span>Real-time feed active: {lastTickTime}</span>
        </div>
      </div>

      {/* Grid: Status checklist on left, Live values in center/right */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Connected Devices checklist (1/3) */}
        <div className="glass-card rounded-3xl p-5 flex flex-col justify-between min-h-[300px]">
          <div>
            <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-3.5">
              <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
                Connected Hardware
              </h3>
            </div>

            <div className="space-y-2">
              {devices.map((dev) => (
                <div key={dev.name} className="flex items-center justify-between p-2 rounded-2xl border border-white/5 bg-white/[0.01]">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${dev.status === "online" ? "bg-emerald-500 shadow-sm shadow-emerald-500" : "bg-stone-700"}`}></div>
                    <div>
                      <h4 className="text-[11px] font-black text-white">{dev.name}</h4>
                      <span className="text-[8px] text-stone-500 font-bold uppercase">{dev.type}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                      dev.status === "online" ? "text-emerald-400 bg-emerald-500/10" : "text-stone-500 bg-white/5"
                    }`}>
                      {dev.status}
                    </span>
                    {dev.status === "online" && (
                      <span className="block text-[8px] text-stone-550 font-black uppercase mt-1">{dev.consumption}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button className="mt-4 w-full py-2 bg-emerald-500 hover:bg-emerald-450 text-[#080d0a] rounded-xl text-[10px] font-black uppercase transition-all tracking-wider cursor-pointer shadow shadow-emerald-500/10">
            + Connect New Device
          </button>
        </div>

        {/* Live Energy Telemetry Cards (2/3) */}
        <div className="xl:col-span-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {/* Card 1: Voltage */}
          <div className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[135px]">
            <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-stone-550" />
              Line Voltage
            </span>
            <div className="my-2">
              <div className="text-3xl font-black text-white font-sans">{voltage.toFixed(1)} <span className="text-xs text-stone-550">V</span></div>
              <span className="text-[8px] text-stone-605 font-bold block mt-1 uppercase">Standard single-phase supply</span>
            </div>
            <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${((voltage - 210) / 40) * 100}%` }}></div>
            </div>
          </div>

          {/* Card 2: Current */}
          <div className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[135px]">
            <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-stone-550" />
              Load Current
            </span>
            <div className="my-2">
              <div className="text-3xl font-black text-emerald-455 font-sans">{current.toFixed(2)} <span className="text-xs text-stone-550">A</span></div>
              <span className="text-[8px] text-stone-605 font-bold block mt-1 uppercase">Instantaneous RMS Current</span>
            </div>
            <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${(current / 10.0) * 100}%` }}></div>
            </div>
          </div>

          {/* Card 3: Real-Time Power */}
          <div className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[135px]">
            <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-stone-550" />
              Active Power
            </span>
            <div className="my-2">
              <div className="text-3xl font-black text-white font-sans">{power} <span className="text-xs text-stone-550">W</span></div>
              <span className="text-[8px] text-stone-605 font-bold block mt-1 uppercase">Real-time load rate</span>
            </div>
            <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${(power / 2500.0) * 100}%` }}></div>
            </div>
          </div>

          {/* Card 4: Energy Consumption */}
          <div className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[135px] sm:col-span-2 md:col-span-1">
            <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-stone-550" />
              Energy Consumed
            </span>
            <div className="my-2">
              <div className="text-3xl font-black text-white font-sans">{cumulativeEnergy.toFixed(4)} <span className="text-xs text-stone-550">kWh</span></div>
              <span className="text-[8px] text-stone-605 font-bold block mt-1 uppercase">Cumulative since boot</span>
            </div>
            <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: "65%" }}></div>
            </div>
          </div>

          {/* Card 5: Estimated CO2 */}
          <div className="glass-card rounded-2xl p-4.5 flex flex-col justify-between h-[135px] sm:col-span-2 md:col-span-2">
            <span className="text-[9px] font-black uppercase tracking-wider text-stone-500 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-stone-550" />
              Estimated Carbon Output
            </span>
            <div className="my-2">
              <div className="text-3xl font-black text-amber-500 font-sans">{estimatedCo2.toFixed(3)} <span className="text-xs text-stone-550">kg CO₂e</span></div>
              <span className="text-[8px] text-stone-605 font-bold block mt-1 uppercase">Grid emission multiplier applied</span>
            </div>
            <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500" style={{ width: "45%" }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Chart 1: Category Bar Chart */}
        <div className="glass-card rounded-3xl p-5 flex flex-col justify-between h-[300px]">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-4">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <BarChart3 className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              Consumption by Appliance
            </h3>
          </div>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deviceBreakdownData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="name" stroke="#44403c" fontSize={10} tickLine={false} style={{ fontWeight: "bold" }} />
                <YAxis stroke="#44403c" fontSize={10} tickLine={false} style={{ fontWeight: "bold" }} />
                <ChartTooltip content={<CustomChartTooltip />} />
                <Bar dataKey="usage" radius={[6, 6, 0, 0]}>
                  {deviceBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Hourly Line Area Chart */}
        <div className="glass-card rounded-3xl p-5 flex flex-col justify-between h-[300px]">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-white/5 mb-4">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-450" />
            </div>
            <h3 className="font-extrabold text-xs text-stone-300 uppercase tracking-widest">
              Live Hourly Load Trends
            </h3>
          </div>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="loadGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="hour" stroke="#44403c" fontSize={10} tickLine={false} style={{ fontWeight: "bold" }} />
                <YAxis stroke="#44403c" fontSize={10} tickLine={false} style={{ fontWeight: "bold" }} />
                <ChartTooltip content={<CustomChartTooltip />} />
                <Area type="monotone" name="Power Load" dataKey="load" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#loadGrad)" />
                <Area type="monotone" name="Solar Gen" dataKey="gen" stroke="#eab308" strokeWidth={1.5} fill="none" strokeDasharray="4 4" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
