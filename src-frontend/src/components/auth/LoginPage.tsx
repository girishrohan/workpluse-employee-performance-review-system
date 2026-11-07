import React, { useState } from 'react';
import { Eye, EyeOff, Lock, Mail } from 'lucide-react';
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
  const [selectedRole, setSelectedRole] = useState<'all' | 'admin' | 'hr' | 'employee'>('all');

  const roleCredentials = {
    admin: { email: 'admin@workpulse.local', password: 'Admin@WorkPulse2024' },
    hr: { email: 'hr@workpulse.local', password: 'Hr@WorkPulse2024' },
    employee: { email: 'employee@workpulse.local', password: 'Emp@WorkPulse2024' },
  };

  const updateCredentialsForRole = (role: 'admin' | 'hr' | 'employee') => {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white flex">
      {/* Left Branding Panel */}
      <div className="hidden lg:flex lg:w-9/16 bg-[#102A43] min-h-screen items-center justify-center p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-10 rounded-full filter blur-3xl opacity-30"></div>
        <div className="absolute bottom-0 left-0 w-12 h-12 bg-teal-50 rounded-full filter blur-2xl opacity-20"></div>

        <div className="relative z-10 max-w-md">
          {/* Brand */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-white/10 border border-white/20 rounded-xl flex items-center justify-center">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2.5"
                   strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <div>
              <div className="text-2xl font-bold text-white">WorkPulse</div>
              <div className="text-xs font-bold text-teal-400 tracking-wider" style={{ letterSpacing: '0.1em' }}>PEOPLE ANALYTICS</div>
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-3xl font-bold text-white mb-6 leading-tight">
            Understand Performance.<br/>
            <span className="text-teal-400">Empower Growth.</span>
          </h1>

          {/* Subline */}
          <p className="text-slate-300 text-base mb-8 leading-relaxed">
            Bring employee reviews, performance analytics, and actionable insights together in one clear workspace.
          </p>

          {/* Feature List */}
          <ul className="space-y-4 mb-10">
            <li className="flex items-start gap-3">
              <div className="w-8 h-8 bg-teal-200/25 border border-teal-400/30 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="3"
                     strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="text-slate-300 text-sm leading-relaxed">
                Weighted KPI framework with real-time score calculation
              </span>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-8 h-8 bg-teal-200/25 border border-teal-400/30 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="3"
                     strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="text-slate-300 text-sm leading-relaxed">
                Department analytics with Plotly visualizations
              </span>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-8 h-8 bg-teal-200/25 border border-teal-400/30 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="3"
                     strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="text-slate-300 text-sm leading-relaxed">
                Decision Tree & Random Forest ML predictions
              </span>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-8 h-8 bg-teal-200/25 border border-teal-400/30 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="3"
                     strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="text-slate-300 text-sm leading-relaxed">
                Role-based access for Admin, HR, and Employee
              </span>
            </li>
          </ul>

          {/* Footer Tagline */}
          <div className="text-xs text-slate-500 letter-space-[0.03em]">
            Local SQLite · bcrypt-secured · Zero vendor lock-in
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="flex-1 min-h-screen flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md">
          {/* Secure Login Header */}
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-teal-600 tracking-wider uppercase">SECURE LOGIN</span>
            <a href="#" className="text-xs text-slate-500 hover:text-slate-700 font-medium" onClick={(e) => { e.preventDefault(); window.location.href = '/?page=Home'; }}>
              ← Back to Home
            </a>
          </div>

          {/* Form Title */}
          <h1 className="text-2xl font-bold text-[#102A43] mb-3">Sign in to WorkPulse</h1>
          <p className="text-slate-500 text-base mb-6">
            Enter your credentials to access your workspace.
          </p>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Role Tabs */}
            <div className="mb-2">
              <div className="flex gap-2 bg-slate-100 rounded-lg p-1">
                {(['all', 'admin', 'hr', 'employee'] as const).map((role) => {
                  const labels = {
                    all: 'All Roles',
                    admin: 'Admin Portal',
                    hr: 'HR Manager',
                    employee: 'Employee',
                  };
                  const isActive = selectedRole === role;
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => {
                        setSelectedRole(role);
                        if (role !== 'all') {
                          updateCredentialsForRole(role);
                        }
                      }}
                      className={`flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-[#102A43] text-white'
                          : 'text-slate-600 hover:text-slate-800'
                      }`}
                    >
                      {labels[role]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Email Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="email">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 placeholder-slate-400 text-base"
                  placeholder="you@workpulse.local"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password Input */}
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

            {/* Remember Me + Forgot Password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-slate-300 rounded"
                  defaultChecked
                />
                <span className="ml-2 text-sm text-slate-600">Remember me on this browser</span>
              </label>
              <a href="#" className="text-sm text-teal-600 hover:text-teal-700 font-medium" onClick={(e) => { e.preventDefault(); alert('Password reset'); }}>
                Forgot password?
              </a>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-[#102A43] hover:bg-[#1E3A5F] text-white font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In to Workspace'}
            </button>
          </form>

          {/* Demo Credentials Box */}
          <div className="mt-6">
            <div className="bg-slate-50 border border-teal-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                     stroke="#0F766E" strokeWidth="2.5"
                     strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                <span className="text-xs font-bold text-[#0F766E] uppercase tracking-wider">DEMO CREDENTIALS — CLICK BELOW OR USE PRE-FILLED VALUES</span>
              </div>
              <div className="divide-y divide-teal-200">
                <div className="flex justify-between items-center py-1">
                  <span className="text-xs font-semibold text-[#0D9488]">Admin</span>
                  <span className="text-xs text-[#134E4A]"><code>admin@workpulse.local · Admin@WorkPulse2024</code></span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-xs font-semibold text-[#0D9488]">HR Manager</span>
                  <span className="text-xs text-[#134E4A]"><code>hr@workpulse.local · Hr@WorkPulse2024</code></span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-xs font-semibold text-[#0D9488]">Employee</span>
                  <span className="text-xs text-[#134E4A]"><code>employee@workpulse.local · Emp@WorkPulse2024</code></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}