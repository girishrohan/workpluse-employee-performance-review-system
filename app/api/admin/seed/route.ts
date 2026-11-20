import { createClient } from '@/lib/supabase/server';
import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/auth/session';

// Admin seed endpoint - restores sample data for dashboard
// Only accessible by admin users (checked via custom session)
export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();
    
    // Verify user is authenticated via custom session
    const session = await getSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Verify user has admin role from session
    if (session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden - Admin access required' }, { status: 403 });
    }

    // Execute seed operations
    const results = await seedDatabase(supabase);

    return NextResponse.json({
      success: true,
      message: 'Sample data restored successfully',
      results
    });

  } catch (error) {
    console.error('Seed error:', error);
    return NextResponse.json(
      { error: 'Failed to seed database', details: String(error) },
      { status: 500 }
    );
  }
}

async function seedDatabase(supabase: Awaited<ReturnType<typeof createClient>>) {
  const results: Record<string, any> = {};

  // 1. Ensure performance areas
  const { error: areasError } = await supabase.from('performance_areas').upsert([
    { name: 'Attendance', description: 'Reliability and attendance over the review period.', weight: 20 },
    { name: 'Task completion', description: 'Delivery of agreed work and responsibilities.', weight: 25 },
    { name: 'Productivity', description: 'Quality and consistency of work output.', weight: 25 },
    { name: 'Teamwork', description: 'Collaboration and communication with colleagues.', weight: 15 },
    { name: 'Learning and development', description: 'Engagement with training and skill development.', weight: 15 },
  ], { onConflict: 'name' });
  results.performance_areas = areasError ? 'error' : 'ok';

  // 2. Ensure app settings
  const { error: settingsError } = await supabase.from('app_settings').upsert([
    { setting_key: 'default_review_period_days', setting_value: '90' },
    { setting_key: 'notification_days_before_deadline', setting_value: '7' },
    { setting_key: 'kpi_threshold_high', setting_value: '80' },
    { setting_key: 'kpi_threshold_moderate', setting_value: '60' },
    { setting_key: 'max_training_hours_per_period', setting_value: '40' },
  ], { onConflict: 'setting_key' });
  results.app_settings = settingsError ? 'error' : 'ok';

  // 3. Insert demo employees if not exists
  const demoEmployees = [
    { employee_code: 'EMP001', employee_name: 'John Smith', department: 'Engineering', designation: 'Senior Developer', joining_date: '2020-01-15', experience_years: 4.5, attendance_rate: 95, task_completion_rate: 92, training_hours: 35, previous_performance: 3.8, performance_category: 'High' },
    { employee_code: 'EMP002', employee_name: 'Sarah Johnson', department: 'Marketing', designation: 'Marketing Specialist', joining_date: '2021-03-10', experience_years: 2.8, attendance_rate: 88, task_completion_rate: 85, training_hours: 28, previous_performance: 3.2, performance_category: 'Moderate' },
    { employee_code: 'EMP003', employee_name: 'Michael Chen', department: 'Sales', designation: 'Sales Executive', joining_date: '2019-06-01', experience_years: 5.2, attendance_rate: 92, task_completion_rate: 89, training_hours: 42, previous_performance: 3.5, performance_category: 'High' },
    { employee_code: 'EMP004', employee_name: 'Emily Davis', department: 'HR', designation: 'HR Coordinator', joining_date: '2022-01-20', experience_years: 1.5, attendance_rate: 82, task_completion_rate: 78, training_hours: 15, previous_performance: 2.8, performance_category: 'Moderate' },
    { employee_code: 'EMP005', employee_name: 'David Wilson', department: 'Engineering', designation: 'QA Engineer', joining_date: '2020-08-12', experience_years: 3.8, attendance_rate: 78, task_completion_rate: 85, training_hours: 30, previous_performance: 3.1, performance_category: 'Moderate' },
    { employee_code: 'EMP006', employee_name: 'Lisa Anderson', department: 'Product', designation: 'Product Manager', joining_date: '2018-11-05', experience_years: 6.0, attendance_rate: 90, task_completion_rate: 88, training_hours: 50, previous_performance: 3.7, performance_category: 'High' },
    { employee_code: 'EMP007', employee_name: 'Robert Martinez', department: 'Finance', designation: 'Accountant', joining_date: '2021-09-15', experience_years: 3.0, attendance_rate: 85, task_completion_rate: 82, training_hours: 22, previous_performance: 3.0, performance_category: 'Moderate' },
    { employee_code: 'EMP008', employee_name: 'Jennifer Lee', department: 'Customer Success', designation: 'Support Specialist', joining_date: '2022-04-01', experience_years: 1.8, attendance_rate: 80, task_completion_rate: 85, training_hours: 18, previous_performance: 2.5, performance_category: 'Moderate' },
    { employee_code: 'EMP009', employee_name: 'Chris Thompson', department: 'Engineering', designation: 'DevOps Engineer', joining_date: '2019-04-20', experience_years: 5.0, attendance_rate: 94, task_completion_rate: 90, training_hours: 40, previous_performance: 3.9, performance_category: 'High' },
    { employee_code: 'EMP010', employee_name: 'Amanda White', department: 'Operations', designation: 'Operations Analyst', joining_date: '2020-12-01', experience_years: 3.2, attendance_rate: 87, task_completion_rate: 88, training_hours: 25, previous_performance: 3.3, performance_category: 'Moderate' },
  ];

  // Insert into demo_employees
  const { error: demoError } = await supabase.from('demo_employees').upsert(demoEmployees, { onConflict: 'employee_code' });
  results.demo_employees = demoError ? 'error' : 'ok';

  // 4. Migrate to main employees table
  const employeesForMain = demoEmployees.map(e => ({
    employee_code: e.employee_code,
    employee_name: e.employee_name,
    department: e.department,
    designation: e.designation,
    joining_date: e.joining_date,
    experience_years: e.experience_years,
    status: 'Active',
    data_origin: 'demo'
  }));

  const { error: employeesError } = await supabase.from('employees').upsert(employeesForMain, { onConflict: 'employee_code' });
  results.employees = employeesError ? 'error' : 'ok';

  // 5. Create performance periods
  const periods = [
    { name: 'Q4 2024 Review', start_date: '2024-10-01', end_date: '2024-12-31', status: 'Active' },
    { name: 'Q3 2024 Review', start_date: '2024-07-01', end_date: '2024-09-30', status: 'Completed' },
    { name: 'Q2 2024 Review', start_date: '2024-04-01', end_date: '2024-06-30', status: 'Completed' },
    { name: 'Q1 2024 Review', start_date: '2024-01-01', end_date: '2024-03-31', status: 'Completed' },
  ];

  const { error: periodsError } = await supabase.from('performance_periods').upsert(periods, { onConflict: 'name' });
  results.performance_periods = periodsError ? 'error' : 'ok';

  // 6. Get employee IDs and period IDs for assessments
  const { data: employees } = await supabase.from('employees').select('employee_id, employee_code').in('employee_code', demoEmployees.map(e => e.employee_code));
  const { data: periodData } = await supabase.from('performance_periods').select('period_id, status').eq('status', 'Active');

  if (employees && periodData && periodData.length > 0) {
    const activePeriod = periodData[0];
    const assessments = employees.map(e => {
      const emp = demoEmployees.find(d => d.employee_code === e.employee_code);
      const scores = { "Attendance": 85, "Task completion": 90, "Productivity": 78, "Teamwork": 80, "Learning and development": 75 };
      let overallScore = 75;
      let category = 'Moderate';
      
      if (emp) {
        switch (emp.employee_code) {
          case 'EMP001': overallScore = 88; category = 'High'; break;
          case 'EMP002': overallScore = 75; category = 'Moderate'; break;
          case 'EMP003': overallScore = 92; category = 'High'; break;
          case 'EMP004': overallScore = 70; category = 'Moderate'; break;
          case 'EMP005': overallScore = 72; category = 'Moderate'; break;
          case 'EMP006': overallScore = 85; category = 'High'; break;
          case 'EMP007': overallScore = 78; category = 'Moderate'; break;
          case 'EMP008': overallScore = 73; category = 'Moderate'; break;
          case 'EMP009': overallScore = 84; category = 'High'; break;
          case 'EMP010': overallScore = 77; category = 'Moderate'; break;
        }
      }

      return {
        employee_id: e.employee_id,
        period_id: activePeriod.period_id,
        assessment_date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        reviewer: 'Admin',
        scores_json: scores,
        overall_score: overallScore,
        category,
        status: 'Completed'
      };
    });

    const { error: assessmentsError } = await supabase.from('assessments').upsert(assessments, { onConflict: 'employee_id,period_id' });
    results.assessments = assessmentsError ? 'error' : 'ok';
  }

  // 7. Create performance records
  if (employees) {
    const perfRecords = employees.map(e => {
      const id = e.employee_id;
      return {
        employee_id: id,
        attendance_rate: 85 + (id % 10),
        task_completion_rate: 80 + (id % 7 + 1),
        training_hours: 20 + (id % 5 + 1),
        previous_performance: 3.0 + (id % 3) * 0.3,
        performance_category: id % 3 === 0 ? 'High' : id % 3 === 1 ? 'Moderate' : 'Needs Support',
        review_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      };
    });

    const { error: perfError } = await supabase.from('performance_records').upsert(perfRecords, { onConflict: 'employee_id' });
    results.performance_records = perfError ? 'error' : 'ok';
  }

  // 8. Create notifications
  const { data: employeeIds } = await supabase.from('employees').select('employee_id').eq('data_origin', 'demo');
  if (employeeIds && employeeIds.length > 0) {
    const notifications = employeeIds.map(e => ({
      title: 'Welcome back, Admin!',
      message: `You have ${employeeIds.length} employees in your workspace and 1 active review cycle.`,
      employee_id: e.employee_id
    }));

    // Check for existing notifications to avoid duplicates
    for (const notif of notifications) {
      const { data: existing } = await supabase
        .from('notifications')
        .select('notification_id')
        .eq('title', notif.title)
        .eq('employee_id', notif.employee_id)
        .limit(1);
      
      if (!existing || existing.length === 0) {
        await supabase.from('notifications').insert(notif);
      }
    }
    results.notifications = 'ok';
  }

  return results;
}