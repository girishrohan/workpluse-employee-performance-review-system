import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Home, Users, BarChart3, Award, Target, Settings, LogOut, Shield } from 'lucide-react';
import axios from 'axios';

const queryClient = new QueryClient();

// Types
interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  employee_id?: number;
}

// API Client
const api = axios.create({
  baseURL: '/api',
});

// Login Page
function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = React.useState('admin@workpulse.local');
  const [password, setPassword] = React.useState('Admin@WorkPulse2024');
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);

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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6 text-navy-900">WorkPulse Login</h1>
        {error && <div className="text-red-600 mb-4">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="you@example.com"
            />
          </div>
          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary text-white"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="mt-6 text-xs text-gray-500">
          <p>Demo Credentials:</p>
          <p>Admin: admin / Admin@WorkPulse2024</p>
          <p>HR: hr / Hr@WorkPulse2024</p>
          <p>Employee: employee / Emp@WorkPulse2024</p>
        </div>
      </div>
    </div>
  );
}

// Dashboard
function Dashboard({ user }: { user: User }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome, {user.full_name}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard title="Total Employees" value="0" />
        <DashboardCard title="Active Periods" value="0" />
        <DashboardCard title="Completed Reviews" value="0" />
        <DashboardCard title="Pending Reviews" value="0" />
      </div>
    </div>
  );
}

function DashboardCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="card p-6">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-navy-900 mt-1">{value}</p>
    </div>
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
    <div>
      <h1 className="text-2xl font-bold mb-4 text-navy-900">Employee Management</h1>
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left">Code</th>
              <th className="px-4 py-2 text-left">Name</th>
              <th className="px-4 py-2 text-left">Department</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((emp: any) => (
              <tr key={emp.employee_id} className="border-b">
                <td className="px-4 py-2">{emp.employee_code}</td>
                <td className="px-4 py-2">{emp.employee_name}</td>
                <td className="px-4 py-2">{emp.department}</td>
                <td className="px-4 py-2">{emp.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
    <div>
      <h1 className="text-2xl font-bold mb-4 text-navy-900">Review Periods</h1>
      <div className="card">
        {periods.length === 0 ? (
          <p className="text-gray-500 py-8 text-center">No periods defined</p>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">Start Date</th>
                <th className="px-4 py-2 text-left">End Date</th>
                <th className="px-4 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {periods.map((p: any) => (
                <tr key={p.period_id} className="border-b">
                  <td className="px-4 py-2">{p.name}</td>
                  <td className="px-4 py-2">{p.start_date}</td>
                  <td className="px-4 py-2">{p.end_date}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
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
    <div>
      <h1 className="text-2xl font-bold mb-4 text-navy-900">Assessments</h1>
      <div className="card">
        {assessments.length === 0 ? (
          <p className="text-gray-500 py-8 text-center">No assessments recorded</p>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left">Employee</th>
                <th className="px-4 py-2 text-left">Period</th>
                <th className="px-4 py-2 text-left">Score</th>
                <th className="px-4 py-2 text-left">Category</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a: any) => (
                <tr key={a.assessment_id} className="border-b">
                  <td className="px-4 py-2">{a.employee_name}</td>
                  <td className="px-4 py-2">{a.period_name}</td>
                  <td className="px-4 py-2">{a.overall_score}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
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

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4 text-navy-900">Analytics</h1>
      {analytics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <DashboardCard title="Avg Attendance" value={analytics.avg_attendance?.toFixed(1) || '0'} />
          <DashboardCard title="Avg Task Completion" value={analytics.avg_task_completion?.toFixed(1) || '0'} />
          <DashboardCard title="Mean Score" value={analytics.workforce_mean_score?.toFixed(1) || '0'} />
          <DashboardCard title="Total Employees" value={analytics.total_employees || 0} />
        </div>
      ) : (
        <div className="text-center py-8">Loading analytics...</div>
      )}
    </div>
  );
}

// Settings
function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4 text-navy-900">Settings</h1>
      <div className="card">
        <p className="text-gray-600">Application settings coming soon...</p>
      </div>
    </div>
  );
}

// Main App
function App({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const isAdmin = user.role === 'admin';
  const isHR = user.role === 'hr';

  const showNav = location.pathname !== '/login';

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
                  <span className="text-xl font-bold">WorkPulse</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm opacity-80">{user.full_name}</span>
                  <span className="text-xs bg-teal-500 px-2 py-1 rounded-full">{user.role.toUpperCase()}</span>
                  <button onClick={onLogout} className="p-2 hover:bg-white/10 rounded-full">
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </header>

          <nav className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex space-x-8">
                <Link to="/" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                  <Home className="w-4 h-4 mr-1" /> Dashboard
                </Link>
                {isAdmin && (
                  <>
                    <Link to="/admin/employees" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                      <Users className="w-4 h-4 mr-1" /> Employees
                    </Link>
                    <Link to="/admin/periods" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                      <Target className="w-4 h-4 mr-1" /> Review Cycles
                    </Link>
                  </>
                )}
                {isHR && (
                  <>
                    <Link to="/hr/assessments" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                      <Award className="w-4 h-4 mr-1" /> Assessments
                    </Link>
                    <Link to="/hr/analytics" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                      <BarChart3 className="w-4 h-4 mr-1" /> Analytics
                    </Link>
                  </>
                )}
                <Link to="/settings" className="flex items-center py-2 text-sm font-medium text-gray-500 hover:text-navy-600">
                  <Settings className="w-4 h-4 mr-1" /> Settings
                </Link>
              </div>
            </div>
          </nav>
        </>
      )}

      <main className="max-w-7xl mx-auto py-8 px-4">
        <Routes>
          <Route path="/login" element={
            <LoginPage onLogin={(user) => {
              localStorage.setItem('access_token', 'demo-token');
              window.location.href = '/';
            }} />
          } />
          <Route path="/" element={<Dashboard user={user} />} />
          <Route path="/admin/employees" element={
            isAdmin ? <EmployeeManagement /> : <Navigate to="/" replace />
          } />
          <Route path="/admin/periods" element={
            isAdmin ? <PeriodManagement /> : <Navigate to="/" replace />
          } />
          <Route path="/hr/assessments" element={
            isHR ? <HRAssessments /> : <Navigate to="/" replace />
          } />
          <Route path="/hr/analytics" element={
            isHR ? <HRAnalytics /> : <Navigate to="/" replace />
          } />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

// Root component with auth state
function Root() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={() => {}} />} />
          <Route path="/*" element={<App user={{} as User} onLogout={() => {}} />} />
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