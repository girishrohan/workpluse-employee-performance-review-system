import React, { useEffect, useState } from 'react';
import { Users, Calendar, Award, ClipboardCheck, TrendingUp, FileText, Shield, BarChart3, UserCheck, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { User } from '../../types';

interface DashboardStats {
  total_employees: number;
  active_periods: number;
  completed_assessments: number;
  avg_score: number;
  workforce_mean_score?: number;
}

interface Period {
  period_id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
}

interface Employee {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  status: string;
}

export default function AdminDashboard({ user }: { user: User }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, periodsRes, employeesRes, assessmentsRes] = await Promise.all([
          axios.get('/api/dashboard/summary'),
          axios.get('/api/periods'),
          axios.get('/api/employees?limit=10'),
          axios.get('/api/assessments?limit=10'),
        ]);

        setStats({
          total_employees: statsRes.data.metrics?.total_employees ?? 0,
          active_periods: statsRes.data.metrics?.active_periods ?? 0,
          completed_assessments: statsRes.data.metrics?.completed_assessments ?? 0,
          avg_score: statsRes.data.metrics?.workforce_mean_score ?? 0,
        });

        if (periodsRes.data.periods) {
          setPeriods(periodsRes.data.periods);
        }

        if (employeesRes.data.employees) {
          setEmployees(employeesRes.data.employees.slice(0, 10));
        }

        if (assessmentsRes.data.assessments) {
          setAssessments(assessmentsRes.data.assessments);
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const cardData = [
    {
      title: 'Total Employees',
      value: stats?.total_employees ?? 0,
      change: '+12% from last quarter',
      Icon: Users,
    },
    {
      title: 'Active Review Cycles',
      value: stats?.active_periods ?? 0,
      change: 'Currently reviewing',
      Icon: Calendar,
    },
    {
      title: 'Completed Assessments',
      value: stats?.completed_assessments ?? 0,
      change: 'This year',
      Icon: Award,
    },
    {
      title: 'Avg Score',
      value: stats?.avg_score?.toFixed(1) ?? '0.0',
      change: 'Workforce average',
      Icon: BarChart3,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="text-slate-500 mt-1">System overview and management controls</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {cardData.map((item) => {
          const Icon = item.Icon;
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
            <Shield className="w-5 h-5 text-teal-600" />
            Organization Overview
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-b-0">
              <span className="text-slate-600">Total Employees</span>
              <span className="font-medium text-slate-900">{stats?.total_employees ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-b-0">
              <span className="text-slate-600">Active Review Cycles</span>
              <span className="font-medium text-slate-900">{stats?.active_periods ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-b-0">
              <span className="text-slate-600">Completed Assessments</span>
              <span className="font-medium text-slate-900">{stats?.completed_assessments ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-slate-600">Avg Workforce Score</span>
              <span className="font-medium text-slate-900">{stats?.avg_score?.toFixed(1) ?? '0.0'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-teal-600" />
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <a href="/admin/employees" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
              <Users className="w-5 h-5 text-teal-600 mb-2" />
              <p className="text-sm font-medium text-slate-900">Manage Employees</p>
              <p className="text-xs text-slate-500 mt-1">Add, edit, or remove staff</p>
            </a>
            <a href="/admin/periods" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
              <Calendar className="w-5 h-5 text-teal-600 mb-2" />
              <p className="text-sm font-medium text-slate-900">Review Cycles</p>
              <p className="text-xs text-slate-500 mt-1">Configure periods</p>
            </a>
            <a href="/admin/assessments" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
              <ClipboardCheck className="w-5 h-5 text-teal-600 mb-2" />
              <p className="text-sm font-medium text-slate-900">Assessments</p>
              <p className="text-xs text-slate-500 mt-1">View all evaluations</p>
            </a>
            <a href="/admin/analytics" className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
              <TrendingUp className="w-5 h-5 text-teal-600 mb-2" />
              <p className="text-sm font-medium text-slate-900">Analytics</p>
              <p className="text-xs text-slate-500 mt-1">Performance insights</p>
            </a>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-900">Recent Review Cycles</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Start Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">End Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {periods.map((period) => (
                <tr key={period.period_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-3 text-sm font-medium text-slate-900">{period.name}</td>
                  <td className="px-6 py-3 text-sm text-slate-600">{period.start_date}</td>
                  <td className="px-6 py-3 text-sm text-slate-600">{period.end_date}</td>
                  <td className="px-6 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      period.status === 'Active' ? 'bg-green-100 text-green-800' :
                      period.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {period.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}