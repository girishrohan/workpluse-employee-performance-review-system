import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Home, Users, BarChart3, Award, Target, Settings, LogOut, Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';

const queryClient = new QueryClient();

interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  employee_id?: number;
}

const api = axios.create({
  baseURL: '/api',
});

const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
  `flex items-center py-2 text-sm font-medium transition-all duration-200 ${
    isActive
      ? 'border-b-2 border-teal-500 text-teal-600'
      : 'text-gray-500 hover:text-navy-600 hover:border-b-2 hover:border-transparent'
  }`;

function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = React.useState('admin@workpulse.local');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', 'demo-token');
        onLogin(data.user);
        navigate('/', { replace: true });
      } else {
        setError(data.error || 'Login failed');
      }
    } catch {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-navy-700 px-8 py-6 text-center">
          <div className="w-16 h-16 mx-auto bg-teal-500 rounded-full flex items-center justify-center mb-3">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">WorkPulse</h1>
          <p className="text-teal-200 text-sm mt-1">Employee Performance Review System</p>
        </div>
        <div className="px-8 py-8">
          <h2 className="text-xl font-bold text-navy-900 mb-6 text-center">Welcome Back</h2>
          <p className="text-gray-500 text-center mb-6">Sign in to access your performance reviews</p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="email">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// Dashboard
function Dashboard({ user }: { user: User }) {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user.full_name}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-teal-50 text-teal-700 rounded-full text-sm font-medium">
            {user.role.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard title="Total Employees" value="0" icon={<Users className="w-6 h-6 text-teal-600" />} />
        <DashboardCard title="Active Periods" value="0" icon={<Target className="w-6 h-6 text-teal-600" />} />
        <DashboardCard title="Completed Reviews" value="0" icon={<Award className="w-6 h-6 text-teal-600" />} />
        <DashboardCard title="Pending Reviews" value="0" icon={<BarChart3 className="w-6 h-6 text-teal-600" />} />
      </div>

      <div className="card p-6">
        <h2 className="text-lg font-semibold text-navy-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickActionCard
            title="View Employees"
            description="Manage employee records"
            icon={<Users className="w-5 h-5" />}
            href="/admin/employees"
            show={user.role === 'admin'}
          />
          <QuickActionCard
            title="Review Cycles"
            description="Configure review periods"
            icon={<Target className="w-5 h-5" />}
            href="/admin/periods"
            show={user.role === 'admin'}
          />
          <QuickActionCard
            title="Assessments"
            description="View team assessments"
            icon={<Award className="w-5 h-5" />}
            href="/hr/assessments"
            show={user.role === 'hr' || user.role === 'admin'}
          />
          <QuickActionCard
            title="Analytics"
            description="Performance insights"
            icon={<BarChart3 className="w-5 h-5" />}
            href="/hr/analytics"
            show={user.role === 'hr' || user.role === 'admin'}
          />
        </div>
      </div>
    </div>
  );
}

function DashboardCard({ title, value, icon }: { title: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div className="card p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-navy-900 mt-1">{value}</p>
        </div>
        <div className="p-3 bg-teal-50 rounded-lg">
          {icon}
        </div>
      </div>
    </div>
  );
}

function QuickActionCard({ title, description, icon, href, show = true }: {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  show?: boolean;
}) {
  if (!show) return null;

  return (
    <NavLink
      to={href}
      className="card p-5 hover:bg-teal-50 hover:border-teal-200 transition-all duration-200 group"
    >
      <div className="flex items-start gap-4">
        <div className="p-2 bg-teal-100 rounded-lg group-hover:bg-teal-200 transition-colors">
          {icon}
        </div>
        <div>
          <h3 className="font-medium text-navy-900">{title}</h3>
          <p className="text-sm text-gray-500 mt-0.5">{description}</p>
        </div>
      </div>
    </NavLink>
  );
}

// Employee Management
function EmployeeManagement() {
  const [employees, setEmployees] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    api.get('/employees')
      .then(res => setEmployees(res.data.employees || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-8">Loading employees...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Employee Management</h1>
          <p className="text-gray-600 mt-1">View and manage all employees</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        {employees.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No employees found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Code</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Department</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {employees.map((emp: any) => (
                <tr key={emp.employee_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-navy-900">{emp.employee_code}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{emp.employee_name}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{emp.department}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      emp.status === 'Active' ? 'bg-green-100 text-green-800' :
                      emp.status === 'Inactive' ? 'bg-gray-100 text-gray-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {emp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// Review Periods
function PeriodManagement() {
  const [periods, setPeriods] = React.useState([]);

  React.useEffect(() => {
    api.get('/periods').then(res => setPeriods(res.data.periods || []));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Review Periods</h1>
          <p className="text-gray-600 mt-1">Configure and manage review cycles</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        {periods.length === 0 ? (
          <div className="p-8 text-center">
            <Target className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No review periods defined</p>
            <p className="text-sm text-gray-400 mt-1">Create your first review cycle to get started</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Start Date</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">End Date</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {periods.map((p: any) => (
                <tr key={p.period_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-navy-900">{p.name}</p>
                    {p.description && <p className="text-sm text-gray-500 mt-0.5">{p.description}</p>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{p.start_date}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{p.end_date}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      p.status === 'Active' ? 'bg-green-100 text-green-800' :
                      p.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {p.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// Assessments
function HRAssessments() {
  const [assessments, setAssessments] = React.useState([]);

  React.useEffect(() => {
    api.get('/assessments').then(res => setAssessments(res.data.assessments || []));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Assessments</h1>
          <p className="text-gray-600 mt-1">Review and track employee assessments</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        {assessments.length === 0 ? (
          <div className="p-8 text-center">
            <Award className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No assessments recorded</p>
            <p className="text-sm text-gray-400 mt-1">Assessments will appear here once reviews are completed</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Employee</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Period</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {assessments.map((a: any) => (
                <tr key={a.assessment_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-navy-900">{a.employee_name}</p>
                    {a.employee_code && <p className="text-xs text-gray-500">{a.employee_code}</p>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{a.period_name}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-navy-900">{a.overall_score}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      a.category === 'High' ? 'bg-green-100 text-green-800' :
                      a.category === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {a.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// Analytics
function HRAnalytics() {
  const [analytics, setAnalytics] = React.useState<any>(null);

  React.useEffect(() => {
    api.get('/analytics').then(res => setAnalytics(res.data.kpis));
  }, []);

  if (!analytics) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Performance insights and metrics</p>
        </div>
        <div className="card p-8 text-center">
          <div className="skeleton h-8 w-48 mx-auto rounded"></div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="skeleton h-24 rounded-lg"></div>
            <div className="skeleton h-24 rounded-lg"></div>
            <div className="skeleton h-24 rounded-lg"></div>
            <div className="skeleton h-24 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Performance insights and metrics</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Avg Attendance"
          value={`${analytics.avg_attendance?.toFixed(1) || '0'}%`}
          icon={<BarChart3 className="w-6 h-6 text-teal-600" />}
        />
        <DashboardCard
          title="Avg Task Completion"
          value={`${analytics.avg_task_completion?.toFixed(1) || '0'}%`}
          icon={<Target className="w-6 h-6 text-teal-600" />}
        />
        <DashboardCard
          title="Mean Score"
          value={analytics.workforce_mean_score?.toFixed(1) || '0'}
          icon={<Award className="w-6 h-6 text-teal-600" />}
        />
        <DashboardCard
          title="Total Employees"
          value={analytics.total_employees || 0}
          icon={<Users className="w-6 h-6 text-teal-600" />}
        />
      </div>
    </div>
  );
}

// Settings
function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure application preferences</p>
      </div>

      <div className="card p-6">
        <h2 className="text-lg font-semibold text-navy-900 mb-4">Application Settings</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium text-navy-900">Dark Mode</h3>
              <p className="text-sm text-gray-500">Enable dark theme for the application</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-300 transition-colors">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"></span>
            </button>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium text-navy-900">Email Notifications</h3>
              <p className="text-sm text-gray-500">Receive email updates for review cycles</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-teal-500 transition-colors">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform translate-x-6"></span>
            </button>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium text-navy-900">Auto-save Drafts</h3>
              <p className="text-sm text-gray-500">Automatically save assessment drafts</p>
            </div>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-teal-500 transition-colors">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform translate-x-6"></span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App - Layout component with header and nav
function AppLayout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = user.role === 'admin';
  const isHR = user.role === 'hr' || isAdmin;

  const showNav = location.pathname !== '/login';

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    onLogout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {showNav && (
        <>
          <header className="bg-navy-700 text-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xl font-bold">WorkPulse</span>
                    <div className="text-xs opacity-80">Performance Review System</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="hidden sm:block text-sm opacity-80">
                    {user.full_name}
                  </span>
                  <span className="text-xs bg-teal-500 px-2 py-1 rounded-full">
                    {user.role.toUpperCase()}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors"
                    title="Logout"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </header>

          <nav className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex space-x-8">
                <NavLink to="/" className={navLinkClasses}>
                  <Home className="w-4 h-4 mr-2" />
                  Dashboard
                </NavLink>
                {isAdmin && (
                  <>
                    <NavLink to="/admin/employees" className={navLinkClasses}>
                      <Users className="w-4 h-4 mr-2" />
                      Employees
                    </NavLink>
                    <NavLink to="/admin/periods" className={navLinkClasses}>
                      <Target className="w-4 h-4 mr-2" />
                      Review Cycles
                    </NavLink>
                  </>
                )}
                {isHR && (
                  <>
                    <NavLink to="/hr/assessments" className={navLinkClasses}>
                      <Award className="w-4 h-4 mr-2" />
                      Assessments
                    </NavLink>
                    <NavLink to="/hr/analytics" className={navLinkClasses}>
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Analytics
                    </NavLink>
                  </>
                )}
                <NavLink to="/settings" className={navLinkClasses}>
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </NavLink>
              </div>
            </div>
          </nav>
        </>
      )}

      <main className="max-w-7xl mx-auto py-8 px-4">
        <Outlet />
      </main>
    </div>
  );
}

// Root component with auth state
function Root() {
  const [user, setUser] = React.useState<User | null>(null);
  const [initialized, setInitialized] = React.useState(false);

  React.useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
    setInitialized(true);
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  const isAdmin = user?.role === 'admin';
  const isHR = user?.role === 'hr' || isAdmin;

  if (!initialized) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>;
  }

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Routes>
          <Route path="/login" element={
            <LoginPage onLogin={handleLogin} />
          } />
          <Route element={user ? <AppLayout user={user} onLogout={handleLogout} /> : <Navigate to="/login" replace />}>
            <Route index element={<Dashboard user={user!} />} />
            <Route path="admin/employees" element={
              isAdmin ? <EmployeeManagement /> : <Navigate to="/" replace />
            } />
            <Route path="admin/periods" element={
              isAdmin ? <PeriodManagement /> : <Navigate to="/" replace />
            } />
            <Route path="hr/assessments" element={
              isHR ? <HRAssessments /> : <Navigate to="/" replace />
            } />
            <Route path="hr/analytics" element={
              isHR ? <HRAnalytics /> : <Navigate to="/" replace />
            } />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </QueryClientProvider>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);