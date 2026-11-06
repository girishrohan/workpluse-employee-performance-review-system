import React, { useEffect, useState } from 'react';
import { Users, Calendar, Award, ClipboardCheck, TrendingUp, BarChart3, FileText, UserCheck, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { User, Employee, Assessment } from '../../types';

interface DashboardStats {
  total_employees: number;
  avg_attendance: number;
  avg_task_completion: number;
  workforce_mean_score: number;
}

export default function HRDashboard({ user }: { user: User }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, employeesRes, assessmentsRes] = await Promise.all([
          axios.get('/api/analytics'),
          axios.get('/api/employees?limit=10'),
          axios.get('/api/assessments?limit=10'),
        ]);

        setStats({
          total_employees: analyticsRes.data.kpis?.total_employees ?? 0,
          avg_attendance: analyticsRes.data.kpis?.avg_attendance ?? 0,
          avg_task_completion: analyticsRes.data.kpis?.avg_task_completion ?? 0,
          workforce_mean_score: analyticsRes.data.kpis?.workforce_mean_score ?? 0,
        });

        if (employeesRes.data.employees) {
          setEmployees(employeesRes.data.employees);
        }

        if (assessmentsRes.data.assessments) {
          setAssessments(assessmentsRes.data.assessments);
        }
      } catch (error) {
        console.error('Error fetching HR dashboard data:', error);
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
      change: 'Active staff',
      Icon: Users,
    },
    {
      title: 'Avg Attendance',
      value: `${stats?.avg_attendance?.toFixed(1) ?? 0}%`,
      change: 'Current rate',
      Icon: Calendar,
    },
    {
      title: 'Task Completion',
      value: `${stats?.avg_task_completion?.toFixed(1) ?? 0}%`,
      change: 'On-time delivery',
      Icon: UserCheck,
    },
    {
      title: 'Avg Score',
      value: stats?.workforce_mean_score?.toFixed(1) ?? '0.0',
      change: 'Performance index',
      Icon: Award,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">HR Dashboard</h1>
        <p className="text-slate-500 mt-1">Employee management and workforce analytics</p>
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
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-teal-600" />
              Employee Directory
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Code</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {employees.map((emp) => (
                  <tr key={emp.employee_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3 text-sm font-medium text-slate-900">{emp.employee_code}</td>
                    <td className="px-6 py-3 text-sm text-slate-700">{emp.employee_name}</td>
                    <td className="px-6 py-3 text-sm text-slate-600">{emp.department}</td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        emp.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'
                      }`}>
                        {emp.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-teal-600" />
              Recent Assessments
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Employee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Period</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Category</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assessments.map((ass) => (
                  <tr key={ass.assessment_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3 text-sm">
                      <div className="font-medium text-slate-900">{ass.employee_name}</div>
                      <div className="text-xs text-slate-500">{ass.employee_code}</div>
                    </td>
                    <td className="px-6 py-3 text-sm text-slate-600">{ass.period_name}</td>
                    <td className="px-6 py-3 text-sm font-semibold text-slate-900">{ass.overall_score}</td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        ass.category === 'High' ? 'bg-green-100 text-green-800' :
                        ass.category === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {ass.category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}