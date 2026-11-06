import { useState } from 'react';
import { Search, Plus, Edit, Trash2 } from 'lucide-react';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Input } from '../../components/Input';

interface Employee {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  experience_years: number;
  status: string;
  attendance_rate?: number;
  task_completion_rate?: number;
  training_hours?: number;
  previous_performance?: number;
}

const fetchEmployees = async (): Promise<Employee[]> => {
  const response = await axios.get('/api/employees');
  return response.data.employees;
};

const STATUS_OPTIONS = [
  { value: 'Active', label: 'Active', color: 'green' },
  { value: 'Inactive', label: 'Inactive', color: 'gray' },
  { value: 'On leave', label: 'On Leave', color: 'blue' },
];

export function EmployeesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [departmentFilter, setDepartmentFilter] = useState<string>('All');

  const { data: employees = [], isLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: fetchEmployees,
    staleTime: 5 * 60 * 1000,
  });

  const filteredEmployees = employees.filter(emp => {
    const matchesSearch = emp.employee_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          emp.employee_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          emp.department.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || emp.status === statusFilter;
    const matchesDept = departmentFilter === 'All' || emp.department === departmentFilter;
    return matchesSearch && matchesStatus && matchesDept;
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 w-1/2 bg-gray-200 rounded mb-2" />
              <div className="h-3 w-full bg-gray-200 rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Employees</h1>
          <p className="text-gray-600 mt-1">Manage employee records and performance</p>
        </div>
        <Button variant="primary" className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Employee
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search employees..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftAddon={<Search className="h-4 w-4 text-gray-400" />}
            />
          </div>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Status</option>
            {STATUS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
          >
            <option value="All">All Departments</option>
            {Array.from(new Set(employees.map(e => e.department))).map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>
      </Card>

      {/* Employees Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Experience
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No employees found
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((emp) => (
                  <tr key={emp.employee_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      {emp.employee_code}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-700">
                      {emp.employee_name}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-700">
                      {emp.department}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-700">
                      {emp.experience_years} yrs
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs font-semibold rounded-full ${
                        emp.status === 'Active' ? 'bg-green-100 text-green-800' :
                        emp.status === 'Active' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {emp.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-1 text-gray-400 hover:text-gray-600">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button className="p-1 text-gray-400 hover:text-red-600">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}