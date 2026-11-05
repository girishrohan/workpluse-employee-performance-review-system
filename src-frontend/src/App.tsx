import React from 'react';
import { NavLink, useLocation, Outlet } from 'react-router-dom';
import {
  Home,
  Users,
  BarChart3,
  Award,
  Target,
  Settings,
  LogOut,
  Shield,
} from 'lucide-react';

interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  employee_id?: number;
}

interface AppProps {
  user: { user: User; role: string };
  onLogout: () => void;
}

export default function App({ user, onLogout }: AppProps) {
  const { role } = user;
  const location = useLocation();

  const isAdmin = role === 'admin';
  const isHR = role === 'hr' || isAdmin;

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
                  <div>
                    <span className="text-xl font-bold">WorkPulse</span>
                    <div className="text-xs opacity-80">Performance Review System</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="hidden sm:block text-sm opacity-80">
                    {user.user.full_name}
                  </span>
                  <span className="text-xs bg-teal-500 px-2 py-1 rounded-full">
                    {role.toUpperCase()}
                  </span>
                  <button
                    onClick={onLogout}
                    className="p-2 hover:bg-white/10 rounded-full"
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
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `flex items-center py-2 text-sm font-medium ${
                      isActive
                        ? 'border-b-2 border-teal-500 text-teal-600'
                        : 'text-gray-500 hover:text-navy-600'
                    }`
                  }
                >
                  <Home className="w-4 h-4 mr-1" />
                  Dashboard
                </NavLink>
                {isAdmin && (
                  <>
                    <NavLink
                      to="/admin/employees"
                      className={({ isActive }) =>
                        `flex items-center py-2 text-sm font-medium ${
                          isActive
                            ? 'border-b-2 border-teal-500 text-teal-600'
                            : 'text-gray-500 hover:text-navy-600'
                        }`
                      }
                    >
                      <Users className="w-4 h-4 mr-1" />
                      Employees
                    </NavLink>
                    <NavLink
                      to="/admin/periods"
                      className={({ isActive }) =>
                        `flex items-center py-2 text-sm font-medium ${
                          isActive
                            ? 'border-b-2 border-teal-500 text-teal-600'
                            : 'text-gray-500 hover:text-navy-600'
                        }`
                      }
                    >
                      <Target className="w-4 h-4 mr-1" />
                      Review Cycles
                    </NavLink>
                  </>
                )}
                {isHR && (
                  <>
                    <NavLink
                      to="/hr/assessments"
                      className={({ isActive }) =>
                        `flex items-center py-2 text-sm font-medium ${
                          isActive
                            ? 'border-b-2 border-teal-500 text-teal-600'
                            : 'text-gray-500 hover:text-navy-600'
                        }`
                      }
                    >
                      <Award className="w-4 h-4 mr-1" />
                      Assessments
                    </NavLink>
                    <NavLink
                      to="/hr/analytics"
                      className={({ isActive }) =>
                        `flex items-center py-2 text-sm font-medium ${
                          isActive
                            ? 'border-b-2 border-teal-500 text-teal-600'
                            : 'text-gray-500 hover:text-navy-600'
                        }`
                      }
                    >
                      <BarChart3 className="w-4 h-4 mr-1" />
                      Analytics
                    </NavLink>
                  </>
                )}
                <NavLink
                  to="/settings"
                  className={({ isActive }) =>
                    `flex items-center py-2 text-sm font-medium ${
                      isActive
                        ? 'border-b-2 border-teal-500 text-teal-600'
                        : 'text-gray-500 hover:text-navy-600'
                    }`
                  }
                >
                  <Settings className="w-4 h-4 mr-1" />
                  Settings
                </NavLink>
              </div>
            </div>
          </header>
        </>
      )}
      <main className="max-w-7xl mx-auto py-8 px-4">
        <Outlet />
      </main>
    </div>
  );
}