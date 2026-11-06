import React, { useState } from 'react';
import { Eye, EyeOff, Lock, Mail, Shield } from 'lucide-react';
import axios from 'axios';

interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  employee_id?: number;
}

interface LoginPageProps {
  onLogin: (user: User) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('admin@workpulse.local');
  const [password, setPassword] = useState('Admin@WorkPulse2024');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'admin' | 'hr' | 'employee'>('all');

  const roleCredentials = {
    admin: { email: 'admin@workpulse.local', password: 'Admin@WorkPulse2024', role: 'admin' as const },
    hr: { email: 'hr@workpulse.local', password: 'Hr@WorkPulse2024', role: 'hr' as const },
    employee: { email: 'employee@workpulse.local', password: 'Emp@WorkPulse2024', role: 'employee' as const },
  };

  const fillCredentials = (role: 'admin' | 'hr' | 'employee') => {
    setEmail(roleCredentials[role].email);
    setPassword(roleCredentials[role].password);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password,
      });

      localStorage.setItem('access_token', 'demo-token');
      localStorage.setItem('user', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-60 h-60 bg-teal-100 rounded-full filter blur-3xl opacity-30"></div>
      <div className="absolute bottom-0 left-0 w-40 h-40 bg-teal-50 rounded-full filter blur-2xl opacity-20"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
          <div className="bg-gradient-to-r from-slate-900 to-slate-800 px-8 py-10 text-center">
            <div className="w-16 h-16 mx-auto bg-teal-500 rounded-full flex items-center justify-center mb-4 shadow-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">WorkPulse</h1>
            <p className="text-teal-200 text-sm mt-2 opacity-90">Enterprise Performance Review System</p>
          </div>

          <div className="px-8 pb-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2 text-center">Welcome Back</h2>
            <p className="text-slate-500 text-center mb-6">Enter your credentials to access your workspace</p>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="email">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 placeholder-slate-400 text-base"
                    placeholder="you@company.com"
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-12 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 placeholder-slate-400 text-base"
                    placeholder="Enter your password"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-3.5 text-slate-400 hover:text-slate-600 focus:outline-none focus:bg-teal-50 rounded-full p-1"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-slate-300 rounded"
                    defaultChecked
                  />
                  <span className="ml-2 text-sm text-slate-600">Remember me</span>
                </label>
                <a href="#" className="text-sm text-teal-600 hover:text-teal-700 font-medium">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 shadow-md"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-slate-200">
              <p className="text-xs text-slate-400 text-center mb-3">Quick login with demo credentials:</p>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => fillCredentials('admin')}
                  className="text-xs py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium transition-colors"
                >
                  Admin
                </button>
                <button
                  onClick={() => fillCredentials('hr')}
                  className="text-xs py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium transition-colors"
                >
                  HR
                </button>
                <button
                  onClick={() => fillCredentials('employee')}
                  className="text-xs py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium transition-colors"
                >
                  Employee
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}