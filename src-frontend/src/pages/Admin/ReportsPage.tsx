import React, { useEffect, useState } from 'react';
import { FileText, Download, Calendar, Users, Award, BarChart3 } from 'lucide-react';
import axios from 'axios';

interface ReportsData {
  report_title: string;
  generation_time: string;
  total_reviews: number;
  average_workforce_score: number;
  active_periods: number;
  registered_headcount: number;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/reports/summary');
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (type: 'employees' | 'assessments') => {
    try {
      const response = await axios.get(`/api/reports/export-csv?type=${type}`);
      const url = window.URL.createObjectURL(new Blob([response.data, { type: 'text/csv' }]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `workpulse_${type}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Reports</h1>
          <p className="text-slate-500 mt-1">Generate and view performance reports</p>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : reports && (
        <>
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-teal-600" />
              Report Summary
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">Report Title</p>
                <p className="font-medium text-slate-900">{reports.report_title}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">Total Reviews</p>
                <p className="font-medium text-slate-900">{reports.total_reviews}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">Avg Score</p>
                <p className="font-medium text-slate-900">{reports.average_workforce_score?.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Download className="w-5 h-5 text-teal-600" />
              Export Data
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => handleExport('employees')}
                className="flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <Users className="w-5 h-5 text-teal-600" />
                <div className="text-left">
                  <p className="font-medium text-slate-900">Export Employees</p>
                  <p className="text-sm text-slate-500">CSV download of all employee records</p>
                </div>
              </button>
              <button
                onClick={() => handleExport('assessments')}
                className="flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <Award className="w-5 h-5 text-teal-600" />
                <div className="text-left">
                  <p className="font-medium text-slate-900">Export Assessments</p>
                  <p className="text-sm text-slate-500">CSV download of all performance assessments</p>
                </div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}