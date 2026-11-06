import React, { useEffect, useState } from 'react';
import { ClipboardCheck, Search, Filter, Award, TrendingUp, Calendar } from 'lucide-react';
import axios from 'axios';

interface Assessment {
  assessment_id: number;
  employee_name: string;
  employee_code: string;
  period_name: string;
  overall_score: number;
  category: string;
  department?: string;
  assessment_date?: string;
}

export default function HRAssessments() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [periodFilter, setPeriodFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');

  useEffect(() => {
    fetchAssessments();
  }, [searchQuery, periodFilter, categoryFilter]);

  const fetchAssessments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);

      const response = await axios.get(`/api/assessments?${params.toString()}`);
      let data = response.data.assessments || [];

      if (categoryFilter !== 'All') {
        data = data.filter((a: Assessment) => a.category === categoryFilter);
      }

      setAssessments(data);
    } catch (error) {
      console.error('Error fetching assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'High': return 'bg-green-100 text-green-800';
      case 'Moderate': return 'bg-yellow-100 text-yellow-800';
      case 'Needs Support': return 'bg-red-100 text-red-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Assessments</h1>
        <p className="text-slate-500 mt-1">Review and track employee assessments</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by employee name or code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        >
          <option value="All">All Categories</option>
          <option value="High">High Performers</option>
          <option value="Moderate">Moderate</option>
          <option value="Needs Support">Needs Support</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Employee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Code</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Period</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Category</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {assessments.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center">
                      <ClipboardCheck className="w-12 h-12 mx-auto text-slate-300 mb-2" />
                      <p className="text-slate-500">No assessments recorded</p>
                      <p className="text-sm text-slate-400 mt-1">Assessments will appear here once reviews are completed</p>
                    </td>
                  </tr>
                ) : (
                  assessments.map((ass) => (
                    <tr key={ass.assessment_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900">{ass.employee_name}</div>
                        {ass.department && <div className="text-xs text-slate-500">{ass.department}</div>}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">{ass.employee_code}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{ass.period_name}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-slate-900">
                        {ass.overall_score}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(ass.category)}`}>
                          {ass.category}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}