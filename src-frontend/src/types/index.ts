export interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id?: number;
  must_change_password?: boolean;
}

export interface Employee {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  experience_years: number;
  designation?: string;
  joining_date?: string;
  status?: string;
  attendance_rate?: number;
  task_completion_rate?: number;
  training_hours?: number;
  previous_performance?: number;
}

export interface Assessment {
  assessment_id: number;
  employee_id: number;
  employee_name: string;
  period_id: number;
  period_name: string;
  reviewer: string;
  assessment_date: string;
  scores: Record<string, number>;
  overall_score: number;
  comments: string;
  recommendations: string;
  category: 'High' | 'Moderate' | 'Needs Support';
}

export interface PerformancePeriod {
  period_id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: 'Draft' | 'Active' | 'Completed';
}

export interface PerformanceArea {
  area_id: number;
  name: string;
  description: string;
  weight: number;
  active: boolean;
}

export interface KPI {
  avg_attendance?: number;
  avg_task_completion?: number;
  mean_score?: number;
  total_employees?: number;
  workforce_mean_score?: number;
  benchmark_delta?: number;
}

export interface Notification {
  notification_id: number;
  title: string;
  message: string;
  created_at: string;
  read_at?: string;
}

export interface DashboardMetrics {
  total_employees: number;
  active_periods: number;
  completed_assessments: number;
  unread_notifications: number;
  workforce_mean_score: number;
  benchmark_delta: number;
}

export interface APIResponse<T> {
  success?: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PredictionResult {
  model_name: string;
  input_features: Record<string, unknown>;
  predicted_category: 'High' | 'Moderate' | 'Needs Support';
  probabilities: Record<string, number>;
  factor_drivers: string;
  feature_contributions: Array<{
    Feature: string;
    Value: string;
    Benchmark: string;
    Impact_Score: number;
    Direction: 'Positive' | 'Negative';
  }>;
  disclaimer: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user: User;
  must_change_password: boolean;
}