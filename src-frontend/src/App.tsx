import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate, NavLink } from 'react-router-dom';
import {
  Home, Users, BarChart3, Award, Target, Settings, LogOut,
  Shield, Calendar, TrendingUp, ClipboardCheck, FileText,
  User, CheckCircle, AlertCircle, UserCheck, Gauge
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

import 'chart.js/auto';

export interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id?: number;
}

const navigationConfig = {
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
    { name: 'Settings', href: '/settings', icon: Settings },
  ],
};

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser) as User);
      } catch {
        localStorage.removeItem('user');
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

  const isAuthenticated = !!user;

  if (!initialized) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
    </div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <LoginPage onLogin={handleLogin} /> : <Navigate to="/dashboard" replace />} />

        {isAuthenticated && user && (
          <>
            <Route path="/admin/*" element={user.role === 'admin' ? <AdminLayout user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" replace />} />
            <Route path="/hr/*" element={user.role === 'hr' || user.role === 'admin' ? <HRLayout user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={user.role === 'employee' ? <EmployeeLayout user={user} onLogout={handleLogout} /> : <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/hr/dashboard'} replace />} />
            <Route path="/performance" element={user.role === 'employee' ? <EmployeeLayout user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" replace />} />
            <Route path="/attendance" element={user.role === 'employee' ? <EmployeeLayout user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" replace />} />
            <Route path="/tasks" element={user.role === 'employee' ? <EmployeeLayout user={user} onLogout={handleLogout} /> : <Navigate to="/dashboard" replace />} />
            <Route path="/settings" element={<SettingsLayout user={user} onLogout={handleLogout} />} />
          </>
        )}

        <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} />

        <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
      </Routes>
    </BrowserRouter>
  );
}

interface LayoutProps {
  user: User;
  onLogout: () => void;
  children: React.ReactNode;
  role: 'admin' | 'hr' | 'employee';
}

function AdminLayout({ user, onLogout, children }: { user: User; onLogout: () => void; children: React.ReactNode }) {
  return (
    <LayoutProvider user={user} onLogout={onLogout} role="admin">
      <SidebarNav user={user} role="admin" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </LayoutProvider>
  );
}

function HRLayout({ user, onLogout, children }: { user: User; onLogout: () => void; children: React.ReactNode }) {
  return (
    <LayoutProvider user={user} onLogout={onLogout} role="hr">
      <SidebarNav user={user} role="hr" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </LayoutProvider>
  );
}

function EmployeeLayout({ user, onLogout, children }: { user: User; onLogout: () => void; children: React.ReactNode }) {
  return (
    <LayoutProvider user={user} onLogout={onLogout} role="employee">
      <SidebarNav user={user} role="employee" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </LayoutProvider>
  );
}

function SettingsLayout({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Header user={user} onLogout={onLogout} />
      <SidebarNav user={user} role={user.role} />
      <main className="flex-1 overflow-y-hidden">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <SettingsPage user={user} />
        </div>
      </main>
    </div>
  );
}

function SidebarNav({ user, role }: { user: User; role: 'admin' | 'hr' | 'employee' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const items = navigationConfig[role];

  const handleLogout = () => {
    onLogout();
    navigate('/login', { replace: true });
  };

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
          <span className="hidden sm:block text-sm text-slate-600">
            {user.full_name}
          </span>
          <span className="text-xs bg-teal-100 text-teal-700 px-2.5 py-0.5 rounded-full font-medium">
            {user.role.toUpperCase()}
          </span>
          <button
            onClick={() => {
              localStorage.removeItem('access_token');
              localStorage.removeItem('user');
              onLogout();
              navigate('/login', { replace: true });
            }}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}

function LayoutProvider({ user, onLogout, role, children }: { user: User; onLogout: () => void; role: 'admin' | 'hr' | 'employee'; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Header user={user} onLogout={onLogout} />
      <SidebarNav user={user} role={role} />
      <main className="md:ml-64">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}