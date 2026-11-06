export interface User {
  user_id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'hr' | 'employee';
  employee_id?: number;
}

export interface Employee {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  department: string;
  status: string;
  attendance_rate?: number;
  task_completion_rate?: number;
  previous_performance?: number;
}

export interface Assessment {
  assessment_id: number;
  employee_name: string;
  employee_code: string;
  period_name: string;
  overall_score: number;
  category: string;
  department?: string;
  assessment_date?: string;
}

export interface Period {
  period_id: number;
  period_name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  description?: string;
}