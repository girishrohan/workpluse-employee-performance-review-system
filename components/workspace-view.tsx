"use client";

import Link from "next/link";
import { useMemo, useState, type FormEvent } from "react";
import useSWR from "swr";
import { Activity, ArrowRight, ArrowUpRight, CalendarDays, Check, CirclePlus, ClipboardCheck, Clock3, Pencil, Plus, Search, Trash2, Users, X } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useWorkspaceUserId } from "@/components/workspace-user";

type Employee = {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department: string;
  job_title: string;
  status: "Active" | "On leave" | "Inactive";
  hire_date: string;
  created_at: string;
};
type Cycle = { id: string; name: string; starts_on: string; ends_on: string; status: "Draft" | "Active" | "Completed"; created_at: string };
type Assessment = { id: string; employee_id: string; cycle_id: string; reviewer: string; overall_score: number; feedback: string; created_at: string };
type WorkspaceData = { employees: Employee[]; cycles: Cycle[]; assessments: Assessment[] };
const EMPTY_EMPLOYEES: Employee[] = [];
const EMPTY_CYCLES: Cycle[] = [];
const EMPTY_ASSESSMENTS: Assessment[] = [];
export type WorkspaceSection = "dashboard" | "employees" | "cycles" | "assessments";

const pageContent: Record<WorkspaceSection, { eyebrow: string; title: string; description: string }> = {
  dashboard: { eyebrow: "YOUR WORKSPACE", title: "A clearer view of performance.", description: "Keep your people, review cycles, and conversations moving forward." },
  employees: { eyebrow: "PEOPLE DIRECTORY", title: "People make the progress.", description: "Manage your team roster and keep employee details up to date." },
  cycles: { eyebrow: "REVIEW CADENCE", title: "Make every review count.", description: "Plan review windows and bring a consistent rhythm to growth." },
  assessments: { eyebrow: "REVIEW RECORDS", title: "Turn feedback into forward motion.", description: "Capture thoughtful assessments and keep a clear record of progress." },
};

async function loadWorkspaceData(): Promise<WorkspaceData> {
  const supabase = createClient();
  const [employeesResult, cyclesResult, assessmentsResult] = await Promise.all([
    supabase.from("workpulse_employees").select("*").order("created_at", { ascending: false }),
    supabase.from("workpulse_review_cycles").select("*").order("starts_on", { ascending: false }),
    supabase.from("workpulse_assessments").select("*").order("created_at", { ascending: false }),
  ]);
  const firstError = employeesResult.error ?? cyclesResult.error ?? assessmentsResult.error;
  if (firstError) throw firstError;
  return { employees: employeesResult.data ?? [], cycles: cyclesResult.data ?? [], assessments: assessmentsResult.data ?? [] };
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(new Date(`${value.slice(0, 10)}T12:00:00Z`));
}
function scoreTone(score: number) { return score >= 80 ? "score-high" : score >= 60 ? "score-mid" : "score-low"; }
function initials(name: string) { return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(); }

export function WorkspaceView({ section }: { section: WorkspaceSection }) {
  const userId = useWorkspaceUserId();
  const { data, error, isLoading, mutate } = useSWR<WorkspaceData>(userId ? ["workpulse-workspace", userId] : null, loadWorkspaceData, { revalidateOnFocus: false });
  const [query, setQuery] = useState("");
  const [employeeEditor, setEmployeeEditor] = useState<Employee | null | false>(false);
  const [cycleEditor, setCycleEditor] = useState(false);
  const [assessmentEditor, setAssessmentEditor] = useState(false);
  const [notice, setNotice] = useState("");
  const content = pageContent[section];

  async function saveEmployee(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values = {
      employee_code: String(form.get("employee_code")).trim(),
      full_name: String(form.get("full_name")).trim(),
      email: String(form.get("email")).trim(),
      department: String(form.get("department")).trim(),
      job_title: String(form.get("job_title")).trim(),
      status: String(form.get("status") ?? "Active"),
      hire_date: String(form.get("hire_date")),
    };
    const supabase = createClient();
    const result = employeeEditor
      ? await supabase.from("workpulse_employees").update(values).eq("id", employeeEditor.id)
      : await supabase.from("workpulse_employees").insert({ ...values, user_id: (await supabase.auth.getUser()).data.user?.id });
    if (result.error) { setNotice(result.error.code === "23505" ? "That employee ID is already in use." : "We couldn’t save this employee. Check the details and try again."); return; }
    await mutate();
    setEmployeeEditor(false);
    setNotice(employeeEditor ? "Employee details updated." : "Employee added to your workspace.");
  }

  async function removeEmployee(employee: Employee) {
    if (!window.confirm(`Remove ${employee.full_name} and their linked review records?`)) return;
    const { error: deleteError } = await createClient().from("workpulse_employees").delete().eq("id", employee.id);
    if (deleteError) { setNotice("We couldn’t remove this employee. Please try again."); return; }
    await mutate();
    setNotice("Employee removed.");
  }

  async function saveCycle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    const { error: saveError } = await supabase.from("workpulse_review_cycles").insert({
      user_id: user?.id,
      name: String(form.get("name")).trim(),
      starts_on: String(form.get("starts_on")),
      ends_on: String(form.get("ends_on")),
      status: String(form.get("status")),
    });
    if (saveError) { setNotice("We couldn’t save this cycle. Check the dates and try again."); return; }
    await mutate();
    setCycleEditor(false);
    setNotice("Review cycle created.");
  }

  async function updateCycleStatus(cycle: Cycle, status: Cycle["status"]) {
    const { error: updateError } = await createClient().from("workpulse_review_cycles").update({ status }).eq("id", cycle.id);
    if (updateError) { setNotice("We couldn’t update this cycle."); return; }
    await mutate();
    setNotice(`Cycle marked ${status.toLowerCase()}.`);
  }

  async function removeCycle(cycle: Cycle) {
    if (!window.confirm(`Delete “${cycle.name}” and its assessments?`)) return;
    const { error: deleteError } = await createClient().from("workpulse_review_cycles").delete().eq("id", cycle.id);
    if (deleteError) { setNotice("We couldn’t delete this cycle."); return; }
    await mutate();
    setNotice("Review cycle deleted.");
  }

  async function saveAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    const { error: saveError } = await supabase.from("workpulse_assessments").insert({
      user_id: user?.id,
      employee_id: String(form.get("employee_id")),
      cycle_id: String(form.get("cycle_id")),
      reviewer: String(form.get("reviewer")).trim(),
      overall_score: Number(form.get("overall_score")),
      feedback: String(form.get("feedback")).trim(),
    });
    if (saveError) { setNotice("We couldn’t save this assessment. Check the details and try again."); return; }
    await mutate();
    setAssessmentEditor(false);
    setNotice("Assessment saved.");
  }

  const employees = data?.employees ?? EMPTY_EMPLOYEES;
  const cycles = data?.cycles ?? EMPTY_CYCLES;
  const assessments = data?.assessments ?? EMPTY_ASSESSMENTS;
  const filteredEmployees = useMemo(() => employees.filter((employee) => `${employee.full_name} ${employee.employee_code} ${employee.department} ${employee.job_title}`.toLowerCase().includes(query.toLowerCase())), [employees, query]);
  const employeeMap = useMemo(() => new Map(employees.map((employee) => [employee.id, employee])), [employees]);
  const cycleMap = useMemo(() => new Map(cycles.map((cycle) => [cycle.id, cycle])), [cycles]);
  const averageScore = assessments.length ? Math.round(assessments.reduce((sum, item) => sum + Number(item.overall_score), 0) / assessments.length) : null;

  return (
    <>
      <section className="page-heading">
        <div><p className="eyebrow">{content.eyebrow}</p><h1>{content.title}</h1><p>{content.description}</p></div>
        {section !== "dashboard" && <button className="button button-primary" onClick={() => section === "employees" ? setEmployeeEditor(null) : section === "cycles" ? setCycleEditor(true) : setAssessmentEditor(true)}><Plus size={17} />{section === "employees" ? "Add employee" : section === "cycles" ? "New review cycle" : "New assessment"}</button>}
      </section>

      {notice && <div className="inline-notice" role="status"><Check size={16} />{notice}<button type="button" aria-label="Dismiss message" onClick={() => setNotice("")}><X size={15} /></button></div>}
      {error && <div className="data-error" role="alert"><strong>Your workspace couldn’t load.</strong><span>Check your Supabase connection and try again.</span><button className="button button-outline button-sm" type="button" onClick={() => mutate()}>Retry</button></div>}
      {isLoading && !data ? <div className="loading-panel" role="status">Loading your workspace…</div> : (
        <>
          {section === "dashboard" && <Dashboard employees={employees} cycles={cycles} assessments={assessments} averageScore={averageScore} employeeMap={employeeMap} cycleMap={cycleMap} />}
          {section === "employees" && <>
            {employeeEditor !== false && <EmployeeEditor employee={employeeEditor || undefined} onCancel={() => setEmployeeEditor(false)} onSubmit={saveEmployee} />}
            <section className="panel">
              <div className="panel-toolbar"><div><h2>Team directory</h2><p>{employees.length} {employees.length === 1 ? "person" : "people"} in your workspace</p></div><label className="search-field"><Search size={16} /><span className="sr-only">Search employees</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people" /></label></div>
              {filteredEmployees.length ? <div className="table-wrap"><table><thead><tr><th>EMPLOYEE</th><th>DEPARTMENT</th><th>ROLE</th><th>STATUS</th><th>START DATE</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{filteredEmployees.map((employee) => <tr key={employee.id}><td><div className="person-cell"><span className="person-avatar">{initials(employee.full_name)}</span><span><strong>{employee.full_name}</strong><small>{employee.employee_code} · {employee.email}</small></span></div></td><td>{employee.department}</td><td>{employee.job_title}</td><td><span className={`status-pill ${employee.status === "Active" ? "status-active" : employee.status === "On leave" ? "status-pending" : "status-muted"}`}><i />{employee.status}</span></td><td>{formatDate(employee.hire_date)}</td><td><div className="row-actions"><button className="icon-button" type="button" aria-label={`Edit ${employee.full_name}`} onClick={() => setEmployeeEditor(employee)}><Pencil size={15} /></button><button className="icon-button icon-danger" type="button" aria-label={`Remove ${employee.full_name}`} onClick={() => removeEmployee(employee)}><Trash2 size={15} /></button></div></td></tr>)}</tbody></table></div> : <EmptyState title={query ? "No people match that search" : "Your directory starts here"} copy={query ? "Try another name, employee ID, or department." : "Add your first employee to bring your team into focus."} action={!query ? <button type="button" className="button button-primary button-sm" onClick={() => setEmployeeEditor(null)}><Plus size={15} />Add employee</button> : undefined} />}
            </section>
          </>}
          {section === "cycles" && <>
            {cycleEditor && <CycleEditor onCancel={() => setCycleEditor(false)} onSubmit={saveCycle} />}
            <section className="panel"><div className="panel-toolbar"><div><h2>Review cadence</h2><p>{cycles.length} {cycles.length === 1 ? "cycle" : "cycles"} created</p></div><span className="panel-icon"><CalendarDays size={19} /></span></div>
              {cycles.length ? <div className="cycle-list">{cycles.map((cycle) => <article key={cycle.id} className="cycle-row"><div className="cycle-icon"><CalendarDays size={18} /></div><div className="cycle-info"><h3>{cycle.name}</h3><p>{formatDate(cycle.starts_on)} — {formatDate(cycle.ends_on)}</p><small>{assessments.filter((assessment) => assessment.cycle_id === cycle.id).length} assessments</small></div><select aria-label={`Change ${cycle.name} status`} className={`cycle-status-select cycle-${cycle.status.toLowerCase()}`} value={cycle.status} onChange={(event) => updateCycleStatus(cycle, event.target.value as Cycle["status"])}><option>Draft</option><option>Active</option><option>Completed</option></select><button className="icon-button icon-danger" type="button" aria-label={`Delete ${cycle.name}`} onClick={() => removeCycle(cycle)}><Trash2 size={16} /></button></article>)}</div> : <EmptyState title="Set a steady review rhythm" copy="Create a review cycle to give feedback a clear timeline." action={<button type="button" className="button button-primary button-sm" onClick={() => setCycleEditor(true)}><Plus size={15} />Create a cycle</button>} />}
            </section>
          </>}
          {section === "assessments" && <>
            {assessmentEditor && <AssessmentEditor employees={employees} cycles={cycles.filter((cycle) => cycle.status !== "Completed")} onCancel={() => setAssessmentEditor(false)} onSubmit={saveAssessment} />}
            <section className="panel"><div className="panel-toolbar"><div><h2>Assessment history</h2><p>{assessments.length} {assessments.length === 1 ? "review" : "reviews"} recorded</p></div><span className="panel-icon"><ClipboardCheck size={19} /></span></div>
              {assessments.length ? <div className="table-wrap"><table><thead><tr><th>EMPLOYEE</th><th>REVIEW CYCLE</th><th>SCORE</th><th>REVIEWER</th><th>FEEDBACK</th><th>DATE</th></tr></thead><tbody>{assessments.map((assessment) => { const employee = employeeMap.get(assessment.employee_id); const cycle = cycleMap.get(assessment.cycle_id); return <tr key={assessment.id}><td><div className="person-cell"><span className="person-avatar">{initials(employee?.full_name ?? "Unknown")}</span><span><strong>{employee?.full_name ?? "Employee removed"}</strong><small>{employee?.employee_code ?? "Review record"}</small></span></div></td><td>{cycle?.name ?? "Cycle removed"}</td><td><span className={`score-value ${scoreTone(Number(assessment.overall_score))}`}>{Number(assessment.overall_score).toFixed(1)}</span></td><td>{assessment.reviewer}</td><td><span className="feedback-summary" title={assessment.feedback}>{assessment.feedback || "No written feedback"}</span></td><td>{formatDate(assessment.created_at)}</td></tr>; })}</tbody></table></div> : <EmptyState title="Make space for meaningful feedback" copy="Your assessment history will be ready when you complete your first review." action={employees.length && cycles.length ? <button type="button" className="button button-primary button-sm" onClick={() => setAssessmentEditor(true)}><Plus size={15} />Start an assessment</button> : <Link className="button button-outline button-sm" href={employees.length ? "/cycles" : "/employees"}>{employees.length ? "Set up a review cycle" : "Add your first employee"}<ArrowRight size={15} /></Link>} />}
            </section>
          </>}
        </>
      )}
    </>
  );
}

function Dashboard({ employees, cycles, assessments, averageScore, employeeMap, cycleMap }: { employees: Employee[]; cycles: Cycle[]; assessments: Assessment[]; averageScore: number | null; employeeMap: Map<string, Employee>; cycleMap: Map<string, Cycle> }) {
  const activeEmployees = employees.filter((employee) => employee.status === "Active").length;
  const activeCycles = cycles.filter((cycle) => cycle.status === "Active").length;
  const pendingCount = cycles.filter((cycle) => cycle.status === "Active").reduce((sum, cycle) => sum + employees.filter((employee) => employee.status === "Active" && !assessments.some((assessment) => assessment.employee_id === employee.id && assessment.cycle_id === cycle.id)).length, 0);
  return (
    <>
      <section className="welcome-banner"><div className="welcome-copy"><span className="welcome-kicker"><Activity size={14} /> YOUR PEOPLE, IN FOCUS</span><h2>Good work starts with a good conversation.</h2><p>Build a steady rhythm of feedback, recognition, and growth for your team.</p><Link href="/assessments" className="banner-link">Go to assessments <ArrowRight size={15} /></Link></div><div className="welcome-art" aria-hidden="true"><span className="welcome-ring ring-one" /><span className="welcome-ring ring-two" /><span className="welcome-ring ring-three" /><div className="welcome-mark">W</div><span className="welcome-spark spark-one" /><span className="welcome-spark spark-two" /></div></section>
      <section className="metric-grid" aria-label="Workspace metrics">
        <MetricCard label="Active team members" value={String(activeEmployees)} foot={`${employees.length} total in your directory`} icon={<Users size={18} />} accent="teal" />
        <MetricCard label="Average performance" value={averageScore === null ? "—" : `${averageScore}`} foot={averageScore === null ? "Add an assessment to see a score" : `${assessments.length} reviews inform this score`} icon={<Activity size={18} />} accent="navy" score={averageScore} />
        <MetricCard label="Open review cycles" value={String(activeCycles)} foot={cycles.length ? `${cycles.length} cycles set up` : "Create your first review cycle"} icon={<CalendarDays size={18} />} accent="amber" />
        <MetricCard label="Reviews to complete" value={String(pendingCount)} foot={pendingCount ? "Based on active team members" : "You’re all caught up"} icon={<ClipboardCheck size={18} />} accent="plum" />
      </section>
      <div className="dashboard-grid">
        <section className="panel dashboard-panel"><div className="panel-toolbar"><div><h2>Review cycles</h2><p>Your team&apos;s review cadence</p></div><Link className="text-link" href="/cycles">All cycles <ArrowRight size={15} /></Link></div>
          {cycles.length ? <div className="cycle-list cycle-list-compact">{cycles.slice(0, 4).map((cycle) => <div className="cycle-row" key={cycle.id}><div className="cycle-icon"><CalendarDays size={17} /></div><div className="cycle-info"><h3>{cycle.name}</h3><p>{formatDate(cycle.starts_on)} — {formatDate(cycle.ends_on)}</p></div><span className={`status-pill ${cycle.status === "Active" ? "status-active" : cycle.status === "Draft" ? "status-pending" : "status-muted"}`}><i />{cycle.status}</span></div>)}</div> : <EmptyState title="Start with a review cycle" copy="Choose a review window to help feedback happen regularly." action={<Link href="/cycles" className="text-link">Create a cycle <ArrowRight size={15} /></Link>} />}
        </section>
        <section className="panel dashboard-panel"><div className="panel-toolbar"><div><h2>Latest feedback</h2><p>Recent employee assessments</p></div><Link className="text-link" href="/assessments">View history <ArrowRight size={15} /></Link></div>
          {assessments.length ? <div className="feedback-list">{assessments.slice(0, 4).map((assessment) => { const employee = employeeMap.get(assessment.employee_id); return <div className="feedback-item" key={assessment.id}><span className="person-avatar">{initials(employee?.full_name ?? "Unknown")}</span><div className="feedback-copy"><strong>{employee?.full_name ?? "Employee removed"}</strong><span>{cycleMap.get(assessment.cycle_id)?.name ?? "Review cycle"} · {formatDate(assessment.created_at)}</span></div><span className={`score-chip ${scoreTone(Number(assessment.overall_score))}`}>{Number(assessment.overall_score).toFixed(0)}</span></div>; })}</div> : <EmptyState title="A little recognition goes a long way" copy="Your latest assessments will show up here." action={employees.length && cycles.length ? <Link href="/assessments" className="text-link">Write a review <ArrowRight size={15} /></Link> : <Link href={employees.length ? "/cycles" : "/employees"} className="text-link">{employees.length ? "Create a review cycle" : "Add an employee"} <ArrowRight size={15} /></Link>} />}
        </section>
      </div>
      <section className="quick-actions"><div><p className="eyebrow">KEEP THE MOMENTUM</p><h2>What would you like to work on?</h2></div><Link className="quick-action" href="/employees"><span className="quick-action-icon"><Users size={18} /></span><span><strong>Grow your directory</strong><small>Add or update people details</small></span><ArrowUpRight size={16} /></Link><Link className="quick-action" href="/assessments"><span className="quick-action-icon quick-action-purple"><CirclePlus size={18} /></span><span><strong>Record feedback</strong><small>Capture a thoughtful review</small></span><ArrowUpRight size={16} /></Link></section>
    </>
  );
}

function MetricCard({ label, value, foot, icon, accent, score }: { label: string; value: string; foot: string; icon: React.ReactNode; accent: string; score?: number | null }) {
  return <article className={`metric-card metric-${accent}`}><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><div className="metric-value-row"><strong>{value}</strong>{score !== undefined && score !== null && <span className={`metric-trend ${scoreTone(score)}`}>{score >= 80 ? "Strong" : score >= 60 ? "Steady" : "Focus"}</span>}</div><p>{foot}</p></article>;
}

function EmptyState({ title, copy, action }: { title: string; copy: string; action?: React.ReactNode }) {
  return <div className="empty-state"><span className="empty-state-icon"><Clock3 size={19} /></span><h3>{title}</h3><p>{copy}</p>{action && <div className="empty-state-action">{action}</div>}</div>;
}

function EmployeeEditor({ employee, onCancel, onSubmit }: { employee?: Employee; onCancel: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="panel editor-panel"><div className="panel-toolbar"><div><p className="eyebrow">TEAM DIRECTORY</p><h2>{employee ? "Update employee" : "Add an employee"}</h2><p>Keep the details clear and current.</p></div><button className="icon-button" type="button" aria-label="Close form" onClick={onCancel}><X size={18} /></button></div><form className="data-form" onSubmit={onSubmit}><label className="field"><span>Full name</span><input name="full_name" defaultValue={employee?.full_name} required maxLength={120} placeholder="Jordan Lee" /></label><label className="field"><span>Employee ID</span><input name="employee_code" defaultValue={employee?.employee_code} required maxLength={32} placeholder="WP-1042" /></label><label className="field"><span>Work email</span><input type="email" name="email" defaultValue={employee?.email} required maxLength={254} placeholder="jordan@company.com" /></label><label className="field"><span>Department</span><input name="department" defaultValue={employee?.department} required maxLength={100} placeholder="People & Culture" /></label><label className="field"><span>Job title</span><input name="job_title" defaultValue={employee?.job_title} required maxLength={100} placeholder="People Partner" /></label><label className="field"><span>Start date</span><input name="hire_date" type="date" defaultValue={employee?.hire_date ?? new Date().toISOString().slice(0, 10)} required /></label>{employee && <label className="field"><span>Employment status</span><select name="status" defaultValue={employee.status}><option>Active</option><option>On leave</option><option>Inactive</option></select></label>}<div className="form-actions"><button className="button button-outline" type="button" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit">{employee ? "Save changes" : "Add employee"}<ArrowRight size={16} /></button></div></form></section>;
}

function CycleEditor({ onCancel, onSubmit }: { onCancel: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="panel editor-panel"><div className="panel-toolbar"><div><p className="eyebrow">REVIEW CADENCE</p><h2>Create a review cycle</h2><p>Set the dates and status for this round of feedback.</p></div><button className="icon-button" type="button" aria-label="Close form" onClick={onCancel}><X size={18} /></button></div><form className="data-form" onSubmit={onSubmit}><label className="field field-wide"><span>Cycle name</span><input name="name" maxLength={120} required placeholder="FY2026 · Mid-year review" /></label><label className="field"><span>Starts on</span><input name="starts_on" type="date" required /></label><label className="field"><span>Ends on</span><input name="ends_on" type="date" required /></label><label className="field"><span>Initial status</span><select name="status" defaultValue="Draft"><option>Draft</option><option>Active</option></select></label><div className="form-actions"><button className="button button-outline" type="button" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit">Create cycle<ArrowRight size={16} /></button></div></form></section>;
}

function AssessmentEditor({ employees, cycles, onCancel, onSubmit }: { employees: Employee[]; cycles: Cycle[]; onCancel: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="panel editor-panel"><div className="panel-toolbar"><div><p className="eyebrow">REVIEW RECORD</p><h2>Write an assessment</h2><p>Keep feedback specific, constructive, and human.</p></div><button className="icon-button" type="button" aria-label="Close form" onClick={onCancel}><X size={18} /></button></div>{employees.length && cycles.length ? <form className="data-form" onSubmit={onSubmit}><label className="field field-wide"><span>Employee</span><select name="employee_id" required defaultValue=""><option value="" disabled>Select an employee</option>{employees.filter((employee) => employee.status === "Active").map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name} · {employee.employee_code}</option>)}</select></label><label className="field field-wide"><span>Review cycle</span><select name="cycle_id" required defaultValue=""><option value="" disabled>Select a review cycle</option>{cycles.map((cycle) => <option key={cycle.id} value={cycle.id}>{cycle.name}</option>)}</select></label><label className="field"><span>Reviewer</span><input name="reviewer" maxLength={120} required placeholder="Your name" /></label><label className="field"><span>Overall score (0–100)</span><input name="overall_score" type="number" min="0" max="100" step="0.1" required placeholder="78" /></label><label className="field field-wide"><span>Feedback</span><textarea name="feedback" rows={4} maxLength={3000} placeholder="What went well? Where can they grow?" /></label><div className="form-actions"><button className="button button-outline" type="button" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit">Save assessment<ArrowRight size={16} /></button></div></form> : <EmptyState title="A little setup first" copy={employees.length ? "Create an active review cycle before writing an assessment." : "Add an employee before you can create an assessment."} action={<Link className="button button-outline button-sm" href={employees.length ? "/cycles" : "/employees"}>{employees.length ? "Go to review cycles" : "Go to employees"}<ArrowRight size={15} /></Link>} />}</section>;
}
