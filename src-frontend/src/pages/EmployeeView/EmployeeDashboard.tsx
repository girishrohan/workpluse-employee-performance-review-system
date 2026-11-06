import React, { useEffect, useState } from 'react';
import { Users, Calendar, Award, CheckCircle, BarChart3, UserCheck, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { User, Employee, Assessment } from '../../types';

interface EmployeeDashboardProps {
  user: User;
}

interface PerformanceData {
  overall_score: number;
  category: string;
  department: string;
  employee_name: string;
}

export default function EmployeeDashboard({ user }: EmployeeDashboardProps) {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [assessments, setAssessments] = useState<PerformanceData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [employeeRes, assessmentsRes] = await Promise.all([
          axios.get(`/api/employees?employee_id=${user.employee_id || 1}`),
          axios.get(`/api/assessments?employee_id=${user.employee_id || 1}`),
        ]);

        if (employeeRes.data.employees && employeeRes.data.employees.length > 0) {
          setEmployee(employeeRes.data.employees[0]);
        } else if (user.employee_id) {
          const emp = await axios.get(`/api/employees/${user.employee_id}`);
          setEmployee(emp.data);
        }

        if (assessmentsRes.data.assessments) {
          setAssessments(assessmentsRes.data.assessments);
        }
      } catch (error) {
        console.error('Error fetching employee dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const emp = employee;
  const avgScore = assessments.length > 0
    ? assessments.reduce((sum, a) => sum + (a.overall_score || 0), 0) / assessments.length
    : 0;

  const latestAssessment = assessments[0] || null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Dashboard</h1>
        <p className="text-slate-500 mt-1">Welcome, {user.full_name}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Attendance Rate</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {emp?.attendance_rate?.toFixed(1) ?? '---'}%
              </p>
            </div>
            <div className="p-3 bg-teal-50 rounded-xl">
              <Calendar className="w-6 h-6 text-teal-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Task Completion</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {emp?.task_completion_rate?.toFixed(1) ?? '---'}%
              </p>
            </div>
            <div className="p-3 bg-teal-50 rounded-xl">
              <CheckCircle className="w-6 h-6 text-teal-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Avg Performance</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {avgScore.toFixed(1)}
              </p>
            </div>
            <div className="p-3 bg-teal-50 rounded-xl">
              <BarChart3 className="w-6 h-6 text-teal-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <User className="w-5 h-5 text-teal-600" />
            Your Profile
          </h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-slate-500">Employee Information</h3>
              <dl className="mt-2 space-y-3">
                <div>
                  <dt className="text-xs text-slate-500">Employee ID</dt>
                  <dd className="text-sm font-medium text-slate-900">{emp?.employee_code ?? 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Department</dt>
                  <dd className="text-sm font-medium text-slate-900">{emp?.department ?? 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Status</dt>
                  <dd className="text-sm font-medium text-slate-900">{emp?.status ?? 'N/A'}</dd>
                </div>
              </dl>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-500">Latest Performance</h3>
              <dl className="mt-2 space-y-3">
                <div>
                  <dt className="text-xs text-slate-500">Overall Score</dt>
                  <dd className="text-sm font-medium text-slate-900">
                    {latestAssessment?.overall_score?.toFixed(1) ?? 'No assessments'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500">Category</dt>
                  <dd className="text-sm font-medium">
                    {latestAssessment ? (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        latestAssessment.category === 'High' ? 'bg-green-100 text-green-800' :
                        latestAssessment.category === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {latestAssessment.category}
                      </span>
                    ) : 'N/A'}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}