import React, { useState, useEffect } from 'react';
import {
  Home,
  Users,
  Settings,
  LogOut,
  Shield,
  TrendingUp,
  Menu,
  X,
} from 'lucide-react';
import axios from 'axios';
import { DashboardPage } from './pages/Dashboard';
import { EmployeesPage } from './pages/Employees';
import { AnalyticsPage } from './pages/Analytics';
import { Card } from './components/Card';
import { Button } from './components/Button';
import { Input } from './components/Input';

const API_BASE = '/api';

const apiPost = async (url: string, data: unknown) => {
  const response = await axios.post(`${API_BASE}${url}`, data);
  return response.data;
};

interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id?: number;
  must_change_password?: boolean;
}

const NAVIGATION_ITEMS = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Employees', href: '/employees', icon: Users },
  { name: 'Analytics', href: '/analytics', icon: TrendingUp },
  { name: 'Reports', href: '/reports', icon: FileTextIcon },
  { name: 'Settings', href: '/settings', icon: Settings },
];

function FileTextIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.59a2 2 0 011.41.59l3.95 3.95a2 2 0 01.59 1.41V19a2 2 0 01-2 2z" />
    </svg>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
    setInitialized(true);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const getCurrentPage = () => {
    const path = window.location.pathname;
    if (path === '/' || path === '/dashboard') return 'dashboard';
    if (path.startsWith('/employees')) return 'employees';
    if (path.startsWith('/analytics')) return 'analytics';
    if (path.startsWith('/reports')) return 'reports';
    if (path.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  const renderPage = () => {
    switch (getCurrentPage()) {
      case 'dashboard':
        return <DashboardPage />;
      case 'employees':
        return <EmployeesPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">{getCurrentPage().charAt(0).toUpperCase() + getCurrentPage().slice(1)}</h1>
            <Card>
              <p className="text-gray-500">Page content coming soon.</p>
            </Card>
          </div>
        );
    }
  };

  if (!initialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading WorkPulse...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center">
            <Shield className="w-6 w-6 text-white" />
          </div>
          <div>
            <p className="font-medium text-gray-900">{user.full_name}</p>
            <span className="text-xs text-gray-500">{user.role.toUpperCase()}</span>
          </div>
        </div>
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl lg:hidden">
            <div className="p-4 border-b border-gray-200">
              <button
                onClick={() => setSidebarOpen(false)}
                className="absolute top-4 right-4 p-1 rounded-full hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center">
                  <Shield className="w-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{user.full_name}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
            </div>
            <nav className="p-4 space-y-2">
              {NAVIGATION_ITEMS.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </a>
              ))}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="h-5 w-5" />
                Logout
              </button>
            </nav>
          </div>
        </>
      )}

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:fixed lg:inset-y-0 lg:left-0 lg:bg-white lg:border-r lg:border-gray-200">
        <nav className="flex-1 flex flex-col pt-5">
          <div className="flex-1 px-4 space-y-1">
            {NAVIGATION_ITEMS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </a>
            ))}
          </div>
          <div className="border-t border-gray-200 p-4">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="lg:pl-64">
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-gray-600 mt-1">Generate and view performance reports</p>
      </div>
      <Card>
        <div className="space-y-4">
          <Button variant="primary">Generate Performance Report</Button>
          <Button variant="outline" type="button">Export to CSV</Button>
        </div>
      </Card>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure system preferences</p>
      </div>
      <Card>
        <p className="text-gray-500">Settings functionality coming soon.</p>
      </Card>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = useState('admin@workpulse.local');
  const [password, setPassword] = useState('Admin@WorkPulse2024');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data = await apiPost('/auth/login', { email, password });

      if (data.success) {
        localStorage.setItem('access_token', 'demo-token');
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user);
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Network error. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-xl">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-teal-600 rounded-full flex items-center justify-center mx-auto mb-3">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">WorkPulse</h1>
            <p className="text-gray-600 mt-1">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" loading={isLoading}>
              Sign In
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center mb-3">Demo accounts:</p>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500">Admin:</span>
                <span className="text-gray-600 ml-2">admin@workpulse.local / Admin@WorkPulse2024</span>
              </div>
              <div>
                <span className="text-gray-500">HR:</span>
                <span className="text-gray-600 ml-2">hr@workpulse.local / Hr@WorkPulse2024</span>
              </div>
              <div>
                <span className="text-gray-500">Employee:</span>
                <span className="text-gray-600 ml-2">employee@workpulse.local / Emp@WorkPulse2024</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}