import { useAppStore } from '@/stores/appStore';
import { ArrowLeft, Moon, Sun, CheckCircle, XCircle } from 'lucide-react';
import styles from './Settings.module.css';

export default function Settings() {
  const { theme, toggleTheme, setCurrentView, leftNavCollapsed, collapseLeftNav } = useAppStore();

  // Feature flags from env
  const enableNLQuery = import.meta.env.VITE_ENABLE_NL_QUERY === 'true';
  const enableOCR = import.meta.env.VITE_ENABLE_OCR === 'true';
  const enableCrawling = import.meta.env.VITE_ENABLE_CRAWLING === 'true';

  return (
    <div className={styles.settings}>
      {/* Header */}
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => setCurrentView('dashboard')}>
          <ArrowLeft size={20} />
          <span>Back to Dashboard</span>
        </button>
        <h2 className={styles.title}>SETTINGS</h2>
      </div>

      {/* Settings Sections */}
      <div className={styles.sections}>
        {/* Appearance */}
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>APPEARANCE</h3>
          <div className={styles.settingItem}>
            <div className={styles.settingInfo}>
              <label className={styles.settingLabel}>Theme</label>
              <p className={styles.settingDesc}>
                현재 테마: {theme === 'light' ? 'Light' : 'Dark'}
              </p>
            </div>
            <button className={styles.themeBtn} onClick={toggleTheme}>
              {theme === 'light' ? (
                <>
                  <Moon size={18} />
                  Switch to Dark
                </>
              ) : (
                <>
                  <Sun size={18} />
                  Switch to Light
                </>
              )}
            </button>
          </div>
        </section>

        {/* Navigation */}
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>NAVIGATION</h3>
          <div className={styles.settingItem}>
            <div className={styles.settingInfo}>
              <label className={styles.settingLabel}>Left Sidebar</label>
              <p className={styles.settingDesc}>
                사이드바 상태: {leftNavCollapsed ? 'Collapsed' : 'Expanded'}
              </p>
            </div>
            <button className={styles.actionBtn} onClick={collapseLeftNav}>
              {leftNavCollapsed ? 'Expand' : 'Collapse'} Sidebar
            </button>
          </div>
        </section>

        {/* Feature Flags */}
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>FEATURE FLAGS</h3>
          <div className={styles.featureList}>
            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>Natural Language Query</span>
                <span className={styles.featureDesc}>OpenAI 기반 자연어 쿼리 파싱</span>
              </div>
              <div
                className={`${styles.featureStatus} ${enableNLQuery ? styles.enabled : styles.disabled}`}
              >
                {enableNLQuery ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableNLQuery ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>

            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>OCR Parsing</span>
                <span className={styles.featureDesc}>PDF OCR 파싱 기능</span>
              </div>
              <div
                className={`${styles.featureStatus} ${enableOCR ? styles.enabled : styles.disabled}`}
              >
                {enableOCR ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableOCR ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>

            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>Web Crawling</span>
                <span className={styles.featureDesc}>웹 크롤링 기능</span>
              </div>
              <div
                className={`${styles.featureStatus} ${enableCrawling ? styles.enabled : styles.disabled}`}
              >
                {enableCrawling ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableCrawling ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>
          </div>
          <p className={styles.featureNote}>Feature flags는 .env 파일에서 설정할 수 있습니다</p>
        </section>

        {/* System Info */}
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>SYSTEM INFO</h3>
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Application</span>
              <span className={styles.infoValue}>naPO (naru Public Observer)</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Version</span>
              <span className={styles.infoValue}>1.0.0</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Environment</span>
              <span className={styles.infoValue}>{import.meta.env.MODE}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>API URL</span>
              <span className={styles.infoValue}>{import.meta.env.VITE_API_URL || '/api/v1'}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
