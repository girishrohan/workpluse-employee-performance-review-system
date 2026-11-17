import Link from "next/link";
import { ArrowRight, Users, CalendarDays, ClipboardCheck, Activity, TrendingUp, Sparkles, Shield, BarChart3 } from "lucide-react";

export default function HomePage() {
  return (
    <main className="marketing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-background" aria-hidden="true">
          <div className="hero-gradient" />
          <div className="hero-grid" />
        </div>

        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles className="badge-sparkle" size={14} />
            <span>New: AI-powered performance insights</span>
          </div>

          <h1 className="hero-title">
            Performance is a <br />
            <span className="highlight">conversation</span>, not a score.
          </h1>

          <p className="hero-description">
            Bring reviews, progress, and people into focus — all in one thoughtful workspace.
            WorkPulse helps teams build a steady rhythm of feedback, recognition, and growth.
          </p>

          <div className="hero-actions">
            <Link href="/auth/sign-up" className="button button-primary button-lg">
              <ArrowRight size={18} />
              <span>Start your workspace</span>
            </Link>
            <Link href="/auth/login" className="button button-outline button-lg">
              <span>Sign in</span>
            </Link>
          </div>

          <p className="hero-trust">
            Private by default. No sample data. Your team, your workspace.
          </p>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="dashboard-preview">
            <div className="preview-header">
              <div className="preview-dots">
                <span /><span /><span />
              </div>
              <div className="preview-title">WorkPulse Dashboard</div>
            </div>
            <div className="preview-content">
              <div className="preview-metric">
                <span className="metric-label">Active Team</span>
                <span className="metric-value">12</span>
              </div>
              <div className="preview-metric">
                <span className="metric-label">Avg Score</span>
                <span className="metric-value score-high">87</span>
              </div>
              <div className="preview-metric">
                <span className="metric-label">Open Cycles</span>
                <span className="metric-value">2</span>
              </div>
              <div className="preview-chart">
                <div className="chart-bar" style={{height: '45%'}} />
                <div className="chart-bar" style={{height: '72%'}} />
                <div className="chart-bar" style={{height: '38%'}} />
                <div className="chart-bar" style={{height: '85%'}} />
                <div className="chart-bar" style={{height: '61%'}} />
                <div className="chart-bar" style={{height: '92%'}} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="features-header">
          <p className="features-eyebrow">WHY WORKPULSE</p>
          <h2>Built for how people actually grow</h2>
        </div>

        <div className="features-grid">
          <article className="feature-card">
            <div className="feature-icon teal">
              <Users size={24} />
            </div>
            <h3>People-first directory</h3>
            <p>Keep your team roster current with roles, departments, and start dates. Search and filter instantly.</p>
          </article>

          <article className="feature-card">
            <div className="feature-icon navy">
              <CalendarDays size={24} />
            </div>
            <h3>Steady review rhythm</h3>
            <p>Create review cycles with clear windows. Draft, activate, and complete — on your timeline.</p>
          </article>

          <article className="feature-card">
            <div className="feature-icon amber">
              <ClipboardCheck size={24} />
            </div>
            <h3>Meaningful assessments</h3>
            <p>Capture thoughtful feedback with scores, written feedback, and reviewer context — all in one place.</p>
          </article>

          <article className="feature-card">
            <div className="feature-icon purple">
              <TrendingUp size={24} />
            </div>
            <h3>Performance insights</h3>
            <p>Track team health at a glance. Average scores, pending reviews, and cycle progress — no spreadsheets needed.</p>
          </article>

          <article className="feature-card">
            <div className="feature-icon green">
              <Activity size={24} />
            </div>
            <h3>AI-powered insights</h3>
            <p>Get intelligent summaries and growth recommendations from your review data automatically.</p>
          </article>

          <article className="feature-card">
            <div className="feature-icon blue">
              <Shield size={24} />
            </div>
            <h3>Private by default</h3>
            <p>Your workspace is yours alone. No sample data, no shared tenancy, no external access.</p>
          </article>
        </div>
      </section>

      {/* How it works */}
      <section className="how-it-works">
        <div className="how-header">
          <p className="how-eyebrow">HOW IT WORKS</p>
          <h2>From setup to insights in minutes</h2>
        </div>

        <div className="steps">
          <div className="step">
            <div className="step-number">01</div>
            <div className="step-content">
              <h3>Create your workspace</h3>
              <p>Sign up with your work email. No credit card, no trial timer — just start.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">02</div>
            <div className="step-content">
              <h3>Add your people</h3>
              <p>Import or manually add employees with roles, departments, and start dates.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">03</div>
            <div className="step-content">
              <h3>Set a review cycle</h3>
              <p>Define review windows — quarterly, bi-annual, or custom. Activate when ready.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">04</div>
            <div className="step-content">
              <h3>Capture feedback</h3>
              <p>Write thoughtful assessments with scores and written feedback. Save and share.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">05</div>
            <div className="step-content">
              <h3>Track progress</h3>
              <p>See team health at a glance. AI summaries highlight growth areas and wins.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="cta-content">
          <h2>Ready to bring clarity to performance?</h2>
          <p>Create your private workspace in under a minute. No sample data — just your people.</p>
          <Link href="/auth/sign-up" className="button button-primary button-lg cta-button">
            <ArrowRight size={18} />
            <span>Start free — no credit card</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="marketing-footer">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="footer-logo">
              <span className="logo-mark">W</span>
              <span>WorkPulse</span>
            </div>
            <p>Performance with purpose. Thoughtful reviews for stronger teams.</p>
          </div>

          <nav className="footer-nav">
            <div className="footer-column">
              <h4>Product</h4>
              <ul>
                <li><Link href="/auth/sign-up">Get started</Link></li>
                <li><Link href="/auth/login">Sign in</Link></li>
                <li><Link href="#features">Features</Link></li>
                <li><Link href="#how-it-works">How it works</Link></li>
              </ul>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <ul>
                <li><Link href="#">About</Link></li>
                <li><Link href="#">Blog</Link></li>
                <li><Link href="#">Careers</Link></li>
                <li><Link href="#">Contact</Link></li>
              </ul>
            </div>
            <div className="footer-column">
              <h4>Resources</h4>
              <ul>
                <li><Link href="#">Help center</Link></li>
                <li><Link href="#">Privacy</Link></li>
                <li><Link href="#">Terms</Link></li>
                <li><Link href="#">Security</Link></li>
              </ul>
            </div>
          </nav>
        </div>

        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} WorkPulse. All rights reserved.</p>
          <p className="footer-links">
            <Link href="#">Privacy Policy</Link>
            <span>·</span>
            <Link href="#">Terms of Service</Link>
            <span>·</span>
            <Link href="#">Cookie Policy</Link>
          </p>
        </div>
      </footer>
    </main>
  );
}