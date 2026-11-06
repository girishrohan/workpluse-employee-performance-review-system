import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate, Outlet, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import {
  Home, Users, BarChart3, Award, Target, Settings, LogOut,
  Shield, Calendar, TrendingUp, ClipboardCheck, FileText,
  User, CheckCircle, AlertCircle, UserCheck, Gauge,
  Mail, Lock, Eye, EyeOff, Search, Bell
} from 'lucide-react';
import axios from 'axios';

import LoginPage from './components/auth/LoginPage';
import AdminDashboard from './pages/Admin/AdminDashboard';
import EmployeeDashboard from './pages/EmployeeView/EmployeeDashboard';
import HRDashboard from './pages/HR/HRDashboard';
import EmployeeManagement from './pages/Admin/EmployeeManagement';
import PeriodManagement from './pages/Admin/PeriodManagement';
import HREmployeeDirectory from './pages/HR/EmployeeDirectory';
import HRAssessments from './pages/HR/HRAssessments';
import HRAnalytics from './pages/HR/HRAnalytics';
import ReportsPage from './pages/Admin/ReportsPage';
import SettingsPage from './pages/Admin/SettingsPage';

const queryClient = new QueryClient();

export interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id?: number;
}

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

const navigationConfig: Record<string, { name: string; href: string; icon: React.ElementType; roles?: string[] }[]> = {
  admin: [
    { name: 'Dashboard', href: '/admin/dashboard', icon: Home },
    { name: 'Employees', href: '/admin/employees', icon: Users },
    { name: 'Review Cycles', href: '/admin/periods', icon: Calendar },
    { name: 'Assessments', href: '/admin/assessments', icon: ClipboardCheck },
    { name: 'Analytics', href: '/admin/analytics', icon: TrendingUp },
    { name: 'Reports', href: '/admin/reports', icon: FileText },
    { name: 'Settings', href: '/admin/settings', icon: Settings },
  ],
  hr: [
    { name: 'Dashboard', href: '/hr/dashboard', icon: Home },
    { name: 'Employee Directory', href: '/hr/employees', icon: Users },
    { name: 'Assessments', href: '/hr/assessments', icon: ClipboardCheck },
    { name: 'Analytics', href: '/hr/analytics', icon: TrendingUp },
    { name: 'Reports', href: '/hr/reports', icon: FileText },
    { name: 'Settings', href: '/hr/settings', icon: Settings },
  ],
  employee: [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'My Performance', href: '/performance', icon: Award },
    { name: 'Attendance', href: '/attendance', icon: Calendar },
    { name: 'Tasks', href: '/tasks', icon: CheckCircle },
    { name: 'Goals', href: '/goals', icon: Target },
    { name: 'Settings', href: '/settings', icon: Settings },
  ],
};

function SidebarNav({ user }: { user: User }) {
  const location = useLocation();
  const items = navigationConfig[user.role] || [];

  return (
    <aside className="hidden md:block w-64 bg-white border-r border-slate-200 h-screen sticky top-16 z-40 overflow-y-auto">
      <nav className="px-4 py-6 space-y-2">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href || location.pathname.startsWith(item.href);
          return (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center w-full px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-teal-50 text-teal-700 border-r-2 border-teal-500 pl-4 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-teal-600'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-teal-600' : 'text-slate-500'}`} />
                  <span>{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

function Header({ user, onLogout }: { user: User; onLogout: () => void }) {
  const navigate = useNavigate();

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-30 h-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-teal-600 rounded-xl flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold text-slate-900">WorkPulse</span>
            <div className="text-xs text-slate-400">Performance Review System</div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-full">
            <Bell className="w-5 h-5" />
          </button>
          <button className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-full">
            <Mail className="w-5 h-5" />
          </button>
          <span className="hidden sm:block text-sm text-slate-600">
            {user.full_name}
          </span>
          <span className="text-xs bg-teal-100 text-teal-700 px-2.5 py-0.5 rounded-full font-medium">
            {user.role.toUpperCase()}
          </span>
          <button
            onClick={onLogout}
            className="p-2 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-full transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}

function ProtectedLayout({ user, onLogout, children }: { user: User; onLogout: () => void; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Header user={user} onLogout={onLogout} />
      <SidebarNav user={user} />
      <main className="md:ml-64">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}

function SettingsLayout({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Header user={user} onLogout={onLogout} />
      <SidebarNav user={user} />
      <main className="md:ml-64">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <SettingsPage user={user} />
        </div>
      </main>
    </div>
  );
}

function AppRoutes({ user, onLogout }: { user: User; onLogout: () => void }) {
  const isAdmin = user.role === 'admin';
  const isHR = user.role === 'hr' || isAdmin;

  return (
    <div className="space-y-6">
      {isAdmin && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard title="Total Employees" value="0" />
          <StatCard title="Active Review Cycles" value="0" />
          <StatCard title="Completed Reviews" value="0" />
          <StatCard title="Avg Score" value="0.0" />
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 font-medium">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
        </div>
        <div className="p-3 bg-teal-50 rounded-xl">
          <Gauge className="w-6 h-6 text-teal-600" />
        </div>
      </div>
    </div>
  );
}

function Root() {
  const [user, setUser] = useState<User | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser) as User);
        } catch {
          localStorage.removeItem('user');
        }
      }
    }
    setInitialized(true);
  }, []);

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  if (!initialized) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={!user ? <LoginPage onLogin={handleLogin} /> : <Navigate to="/dashboard" replace />} />

          {user && (
            <>
              <Route path="/admin/dashboard" element={<ProtectedLayout user={user} onLogout={handleLogout}><AdminDashboard user={user} /></ProtectedLayout>} />
              <Route path="/admin/employees" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeManagement /></ProtectedLayout>} />
              <Route path="/admin/periods" element={<ProtectedLayout user={user} onLogout={handleLogout}><PeriodManagement /></ProtectedLayout>} />
              <Route path="/admin/assessments" element={<ProtectedLayout user={user} onLogout={handleLogout}><HRAssessments /></ProtectedLayout>} />
              <Route path="/admin/analytics" element={<ProtectedLayout user={user} onLogout={handleLogout}><HRAnalytics /></ProtectedLayout>} />
              <Route path="/admin/reports" element={<ProtectedLayout user={user} onLogout={handleLogout}><ReportsPage /></ProtectedLayout>} />
              <Route path="/admin/settings" element={<SettingsLayout user={user} onLogout={handleLogout} />} />

              <Route path="/hr/dashboard" element={<ProtectedLayout user={user} onLogout={handleLogout}><HRDashboard user={user} /></ProtectedLayout>} />
              <Route path="/hr/employees" element={<ProtectedLayout user={user} onLogout={handleLogout}><HREmployeeDirectory /></ProtectedLayout>} />
              <Route path="/hr/assessments" element={<ProtectedLayout user={user} onLogout={handleLogout}><HRAssessments /></ProtectedLayout>} />
              <Route path="/hr/analytics" element={<ProtectedLayout user={user} onLogout={handleLogout}><HRAnalytics /></ProtectedLayout>} />
              <Route path="/hr/reports" element={<ProtectedLayout user={user} onLogout={handleLogout}><ReportsPage /></ProtectedLayout>} />
              <Route path="/hr/settings" element={<SettingsLayout user={user} onLogout={handleLogout} />} />

              <Route path="/dashboard" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeDashboard user={user} /></ProtectedLayout>} />
              <Route path="/performance" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeDashboard user={user} /></ProtectedLayout>} />
              <Route path="/attendance" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeDashboard user={user} /></ProtectedLayout>} />
              <Route path="/tasks" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeDashboard user={user} /></ProtectedLayout>} />
              <Route path="/goals" element={<ProtectedLayout user={user} onLogout={handleLogout}><EmployeeDashboard user={user} /></ProtectedLayout>} />
            </>
          )}

          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);