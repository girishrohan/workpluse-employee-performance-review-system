import { Users, Calendar, Award, ClipboardCheck } from 'lucide-react';
import { Card, StatsCard } from '../../components/Card';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface DashboardMetrics {
  total_employees: number;
  active_periods: number;
  completed_assessments: number;
  unread_notifications: number;
  workforce_mean_score: number;
  benchmark_delta: number;
}

interface PerformanceDistribution {
  High: number;
  Moderate: number;
  'Needs Support': number;
}

const fetchDashboardSummary = async (): Promise<{
  metrics: DashboardMetrics;
  performance_distribution: PerformanceDistribution;
  active_review_cycles: Array<{
    period_id: number;
    name: string;
    start_date: string;
    end_date: string;
    status: string;
  }>;
}> => {
  const response = await axios.get('/api/dashboard/summary');
  return response.data;
};

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 w-3/4 bg-gray-200 rounded mb-2" />
              <div className="h-8 w-1/2 bg-gray-200 rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <p className="text-red-600">Failed to load dashboard data</p>
      </Card>
    );
  }

  const metrics: DashboardMetrics = data?.metrics ?? {
    total_employees: 0,
    active_periods: 0,
    completed_assessments: 0,
    unread_notifications: 0,
    workforce_mean_score: 0,
    benchmark_delta: 0,
  };
  const distribution: PerformanceDistribution = data?.performance_distribution ?? { High: 0, Moderate: 0, 'Needs Support': 0 };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your performance management system</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Employees"
          value={metrics.total_employees}
          icon={<Users className="h-6 w-6" />}
          description="Active employees in the system"
        />
        <StatsCard
          title="Active Review Cycles"
          value={metrics.active_periods}
          icon={<Calendar className="h-6 w-6" />}
          description="Currently running review periods"
        />
        <StatsCard
          title="Completed Reviews"
          value={metrics.completed_assessments}
          icon={<Award className="h-6 w-6" />}
          description="Assessments completed this cycle"
        />
        <StatsCard
          title="Notifications"
          value={metrics.unread_notifications}
          icon={<ClipboardCheck className="h-6 w-6" />}
          description="Unread notifications"
        />
      </div>

      {/* Performance Distribution */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Performance Distribution</h2>
          <span className="text-sm text-gray-500">
            Average Score: {metrics.workforce_mean_score.toFixed(1)}%
          </span>
        </div>

        <div className="space-y-4">
          {(['High', 'Moderate', 'Needs Support'] as const).map((category) => {
            const count = distribution[category];
            const percentage = metrics.completed_assessments
              ? ((count / metrics.completed_assessments) * 100).toFixed(0)
              : '0';
            const colorClasses = {
              High: { text: 'text-green-600', bg: 'bg-green-500' },
              Moderate: { text: 'text-yellow-600', bg: 'bg-yellow-500' },
              'Needs Support': { text: 'text-red-600', bg: 'bg-red-500' },
            }[category];

            return (
              <div key={category}>
                <div className="flex justify-between text-sm mb-1">
                  <span className={`${colorClasses.text} font-medium`}>{category}</span>
                  <span className="text-gray-600">{count} ({percentage}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${colorClasses.bg}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Active Review Cycles */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Active Review Cycles</h2>
          <a href="/periods" className="text-sm text-teal-600 hover:underline">
            View All
          </a>
        </div>

        <div className="space-y-3">
          {data?.active_review_cycles?.length ? (
            data.active_review_cycles.map((cycle) => (
              <div
                key={cycle.period_id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{cycle.name}</h3>
                    <p className="text-sm text-gray-500">
                      {cycle.start_date} - {cycle.end_date}
                    </p>
                  </div>
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                    {cycle.status}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 py-4">No active review cycles</p>
          )}
        </div>
      </Card>
    </div>
  );
}