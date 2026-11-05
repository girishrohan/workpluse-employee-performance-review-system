import React from 'react';
import { NavLink, useLocation, Outlet, useNavigate } from 'react-router-dom';
import {
  Home,
  Users,
  BarChart3,
  Award,
  Target,
  Settings,
  LogOut,
  Shield,
  Calendar,
  TrendingUp,
  ClipboardCheck,
  FileText
} from 'lucide-react';

interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  employee_id?: number;
}

interface AppProps {
  user: User;
  onLogout: () => void;
}

const NAVIGATION_ITEMS = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Employees', href: '/admin/employees', icon: Users, roles: ['admin'] },
  { name: 'Review Cycles', href: '/admin/periods', icon: Calendar, roles: ['admin'] },
  { name: 'Assessments', href: '/hr/assessments', icon: ClipboardCheck, roles: ['admin', 'hr'] },
  { name: 'Analytics', href: '/hr/analytics', icon: TrendingUp, roles: ['admin', 'hr'] },
  { name: 'Reports', href: '/reports', icon: FileText, roles: ['admin', 'hr'] },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const SidebarNav = ({ user }: { user: User }) => {
  const location = useLocation();

  return (
    <nav className="w-64 bg-white border-r border-gray-200 h-screen fixed left-0 top-16 z-40 overflow-y-auto">
      <div className="px-4 py-6 space-y-2">
        {NAVIGATION_ITEMS.filter(item => {
          if (item.roles) {
            return item.roles.includes(user.role);
          }
          return true;
        }).map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
          return (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center w-full px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-teal-50 text-teal-700 border-r-2 border-teal-500 pl-4'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-navy-700'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-teal-600' : 'text-gray-500'}`} />
                  <span>{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default function App({ user, onLogout }: AppProps) {
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
          <header className="bg-navy-700 text-white shadow-lg sticky top-0 z-30">
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

          <div className="flex pt-16">
            <SidebarNav user={user} />
            <main className="flex-1 overflow-y-auto">
              <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <Outlet />
              </div>
            </main>
          </div>
        </>
      )}
      {showNav === false && (
        <main className="min-h-screen bg-gray-50">
          <Outlet />
        </main>
      )}
    </div>
  );
}