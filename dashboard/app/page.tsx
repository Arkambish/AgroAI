"use client";

import { Calendar, TrendingUp, MapPin, CloudSun, ArrowRight } from "lucide-react";
import StatCard from "@/components/StatCard";
import DistrictMap from "@/components/DistrictMap";
import Link from "next/link";
import { motion } from "framer-motion";

export default function Home() {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  };

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-emerald-600 px-8 py-12 text-white shadow-xl">
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
            Welcome to AgroAI
          </h1>
          <p className="mt-4 text-lg text-emerald-50 text-opacity-90">
            Intelligent spatial decision support for big onion farmers. Predict your yield, understand the reasons, and get expert recommendations.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link 
              href="/predict" 
              className="flex items-center space-x-2 rounded-xl bg-white px-6 py-3 font-bold text-emerald-600 transition-transform hover:scale-105"
            >
              <span>Start Prediction</span>
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500 opacity-20 blur-3xl"></div>
        <div className="absolute -bottom-20 right-20 h-64 w-64 rounded-full bg-lime-400 opacity-20 blur-3xl"></div>
      </section>

      {/* Stats Grid */}
      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        <motion.div variants={item}>
          <StatCard 
            label="Current Season" 
            value="Yala 2024" 
            icon={Calendar} 
            trend="Harvest in 3 months" 
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard 
            label="Avg. Predicted Yield" 
            value="14.2 MT/Ha" 
            icon={TrendingUp} 
            trend="+5.2% from last year" 
            trendType="up"
            color="bg-lime-500"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard 
            label="Best District" 
            value="Matale" 
            icon={MapPin} 
            trend="Highest potential" 
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard 
            label="Weather Summary" 
            value="Favorable" 
            icon={CloudSun} 
            trend="Moderate rainfall" 
            trendType="neutral"
            color="bg-lime-500"
          />
        </motion.div>
      </motion.div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Map Section */}
        <div className="lg:col-span-2">
          <DistrictMap />
        </div>

        {/* Quick Insights */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Quick Insights</h2>
          <div className="space-y-4">
            {[
              { 
                title: "Northern Region Potential", 
                text: "Jaffna shows promising signs due to improved soil moisture this season.",
                type: "success"
              },
              { 
                title: "Temperature Alert", 
                text: "Dry zones might experience heat stress in late May. Consider mulching.",
                type: "warning"
              },
              { 
                title: "Rainfall Patterns", 
                text: "Moderate rainfall is expected to support bulb development across most zones.",
                type: "info"
              }
            ].map((insight, index) => (
              <div 
                key={index} 
                className="rounded-2xl border bg-white p-5 shadow-sm transition-all hover:shadow-md dark:bg-slate-900"
              >
                <div className="mb-2 flex items-center space-x-2">
                  <div className={`h-2 w-2 rounded-full ${
                    insight.type === 'success' ? 'bg-emerald-500' : 
                    insight.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                  }`}></div>
                  <h4 className="font-bold text-slate-900 dark:text-white">{insight.title}</h4>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {insight.text}
                </p>
              </div>
            ))}
          </div>
          
          <Link 
            href="/recommend" 
            className="flex w-full items-center justify-center space-x-2 rounded-xl bg-slate-100 py-3 font-bold text-slate-600 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
          >
            <span>View All Recommendations</span>
            <ArrowRight size={18} />
          </Link>
        </div>
      </div>
    </div>
  );
}
