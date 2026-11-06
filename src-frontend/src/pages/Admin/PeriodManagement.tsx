import React, { useEffect, useState } from 'react';
import { Calendar, Plus, Edit, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react';
import axios from 'axios';

interface Period {
  period_id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
}

export default function PeriodManagement() {
  const [periods, setPeriods] = useState<Period[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingPeriod, setEditingPeriod] = useState<Period | null>(null);

  useEffect(() => {
    fetchPeriods();
  }, []);

  const fetchPeriods = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/periods');
      setPeriods(response.data.periods || []);
    } catch (error) {
      console.error('Error fetching periods:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (periodId: number, periodName: string) => {
    if (window.confirm(`Are you sure you want to delete "${periodName}"?`)) {
      try {
        await axios.delete(`/api/periods/${periodId}`);
        setPeriods(prev => prev.filter(p => p.period_id !== periodId));
      } catch (error) {
        console.error('Error deleting period:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800';
      case 'Completed': return 'bg-blue-100 text-blue-800';
      case 'Draft': return 'bg-slate-100 text-slate-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Review Cycles</h1>
          <p className="text-slate-500 mt-1">Configure and manage performance review periods</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-xl hover:bg-teal-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Period
        </button>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Start Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">End Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {periods.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center">
                      <Calendar className="w-12 h-12 mx-auto text-slate-300 mb-2" />
                      <p className="text-slate-500">No review periods defined</p>
                      <p className="text-sm text-slate-400 mt-1">Create your first review cycle to get started</p>
                    </td>
                  </tr>
                ) : (
                  periods.map((period) => (
                    <tr key={period.period_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900">{period.name}</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">{period.start_date}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{period.end_date}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(period.status)}`}>
                          {period.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-full">
                            <Edit className="w-4 h-4" />
                          </button>
                          {period.status !== 'Active' && (
                            <button
                              onClick={() => handleDelete(period.period_id, period.name)}
                              className="p-2 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-full"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
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