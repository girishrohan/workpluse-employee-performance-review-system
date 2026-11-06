import React, { useEffect, useState } from 'react';
import { TrendingUp, BarChart3, PieChart, Users, Award, Calendar } from 'lucide-react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

interface AnalyticsData {
  kpis: {
    total_employees: number;
    avg_attendance: number;
    avg_task_completion: number;
    avg_training_hours: number;
    avg_experience: number;
    workforce_mean_score: number;
    high_performers: number;
    moderate_performers: number;
    needs_support: number;
  };
  department_benchmarks: any[];
}

export default function HRAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const kpiCards = [
    { title: 'Avg Attendance', value: `${analytics?.kpis?.avg_attendance?.toFixed(1) ?? 0}%`, icon: Calendar },
    { title: 'Avg Task Completion', value: `${analytics?.kpis?.avg_task_completion?.toFixed(1) ?? 0}%`, icon: Award },
    { title: 'Mean Score', value: analytics?.kpis?.workforce_mean_score?.toFixed(1) ?? '0.0', icon: BarChart3 },
    { title: 'Total Employees', value: analytics?.kpis?.total_employees ?? 0, icon: Users },
  ];

  const performanceDistribution = {
    labels: ['High Achievers', 'Moderate', 'Needs Support'],
    datasets: [{
      data: [
        analytics?.kpis?.high_performers ?? 0,
        analytics?.kpis?.moderate_performers ?? 0,
        analytics?.kpis?.needs_support ?? 0,
      ],
      backgroundColor: ['#22c55e', '#eab308', '#ef4444'],
    }],
  };

  const barData = {
    labels: analytics?.department_benchmarks?.map((d) => d.department || 'N/A') ?? [],
    datasets: [{
      label: 'Avg Score by Department',
      data: analytics?.department_benchmarks?.map((d) => d.avg_score || 0) ?? [],
      backgroundColor: '#168c83',
    }],
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
        <p className="text-slate-500 mt-1">Performance insights and metrics</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {kpiCards.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-slate-500 font-medium">{item.title}</p>
                      <p className="text-2xl font-bold text-slate-900 mt-1">{item.value}</p>
                    </div>
                    <div className="p-3 bg-teal-50 rounded-xl">
                      <Icon className="w-6 h-6 text-teal-600" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <PieChart className="w-5 h-5 text-teal-600" />
                Performance Distribution
              </h2>
              <div className="h-64">
                <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-teal-600" />
                Department Benchmarks
              </h2>
              <div className="space-y-3">
                {analytics?.department_benchmarks?.map((dept) => (
                  <div key={dept.department} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <span className="text-sm font-medium text-slate-700">{dept.department}</span>
                    <span className="text-sm font-bold text-slate-900">{dept.avg_score?.toFixed(1) ?? '0.0'}</span>
                  </div>
                )) ?? (
                  <p className="text-slate-500 text-center py-4">No department data available</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}