import { useState } from 'react';
import { Award, Users, Check } from 'lucide-react';
import { Card } from '../../components/Card';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface AnalyticsKPI {
  avg_attendance?: number;
  avg_task_completion?: number;
  mean_score?: number;
  total_employees?: number;
  workforce_mean_score?: number;
}

interface DeptBenchmark {
  department: string;
  avg_score: number;
  employee_count: number;
}

const fetchAnalytics = async (): Promise<{
  kpis: AnalyticsKPI;
  department_benchmarks: DeptBenchmark[];
}> => {
  const response = await axios.get('/api/analytics');
  return response.data;
};

export function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: fetchAnalytics,
    staleTime: 5 * 60 * 1000,
  });

  const [chartType, setChartType] = useState<'attendance' | 'department' | 'score'>('attendance');

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 w-1/2 bg-gray-200 rounded mb-2" />
              <div className="h-8 w-1/4 bg-gray-200 rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const benchmarks = data?.department_benchmarks || [];

  const kpiCards = [
    {
      title: 'Avg Attendance',
      value: `${kpis.avg_attendance?.toFixed(1) || '0'}%`,
      icon: <Users className="h-6 w-6 text-teal-600" />,
    },
    {
      title: 'Avg Task Completion',
      value: `${kpis.avg_task_completion?.toFixed(1) || '0'}%`,
      icon: <Check className="h-6 w-6 text-teal-600" />,
    },
    {
      title: 'Mean Score',
      value: (kpis.mean_score || 0).toFixed(1),
      icon: <Award className="h-6 w-6 text-teal-600" />,
    },
    {
      title: 'Total Employees',
      value: kpis.total_employees || 0,
      icon: <Users className="h-6 w-6 text-teal-600" />,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-1">Workforce insights and performance metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((kpi, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {kpi.icon}
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{kpi.title}</p>
                <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Department Performance</h2>
            <div className="flex gap-2">
              {['attendance', 'score', 'department'].map((t) => (
                <button
                  key={t}
                  onClick={() => setChartType(t as typeof chartType)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                    chartType === t
                      ? 'bg-teal-100 text-teal-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {t === 'attendance' ? 'Attendance' : t === 'score' ? 'Scores' : 'By Dept'}
                </button>
              ))}
            </div>
          </div>

          {benchmarks.length > 0 ? (
            <div className="space-y-4">
              {benchmarks.map((bench) => (
                <div key={bench.department} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">{bench.department}</span>
                    <span className="font-medium">{bench.avg_score?.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-teal-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(bench.avg_score || 0, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">{bench.employee_count} employees</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 py-8 text-center">No department data available</p>
          )}
        </Card>

        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Performance Summary</h2>
          </div>

          <div className="space-y-6">
            <div>
              <p className="text-sm text-gray-500 mb-2">Overall Workforce Score</p>
              <div className="text-3xl font-bold text-gray-900">
                {kpis.workforce_mean_score?.toFixed(1) || '0'}%
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-teal-500 h-2 rounded-full"
                  style={{ width: `${Math.min(kpis.workforce_mean_score || 0, 100)}%` }}
                />
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-500 mb-2">Attendance Rate</p>
              <div className="text-2xl font-semibold text-gray-900">
                {kpis.avg_attendance?.toFixed(1) || '0'}%
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-500 mb-2">Task Completion</p>
              <div className="text-2xl font-semibold text-gray-900">
                {kpis.avg_task_completion?.toFixed(1) || '0'}%
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}