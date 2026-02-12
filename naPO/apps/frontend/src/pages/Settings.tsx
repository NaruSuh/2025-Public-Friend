import { useAppStore } from '@/stores/appStore';
import { ArrowLeft, Moon, Sun, CheckCircle, XCircle } from 'lucide-react';
import styles from './Settings.module.css';

export default function Settings() {
  const { theme, toggleTheme, setCurrentView } = useAppStore();

  const enableNLQuery = import.meta.env.VITE_ENABLE_NL_QUERY === 'true';
  const enableOCR = import.meta.env.VITE_ENABLE_OCR === 'true';
  const enableCrawling = import.meta.env.VITE_ENABLE_CRAWLING === 'true';

  return (
    <div className={styles.settings}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => setCurrentView('chat')}>
          <ArrowLeft size={20} />
          <span>돌아가기</span>
        </button>
        <h2 className={styles.title}>설정</h2>
      </div>

      <div className={styles.sections}>
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>테마</h3>
          <div className={styles.settingItem}>
            <div className={styles.settingInfo}>
              <label className={styles.settingLabel}>현재 테마</label>
              <p className={styles.settingDesc}>
                {theme === 'light' ? 'Light' : 'Dark'}
              </p>
            </div>
            <button className={styles.themeBtn} onClick={toggleTheme}>
              {theme === 'light' ? (
                <><Moon size={18} /> Dark 전환</>
              ) : (
                <><Sun size={18} /> Light 전환</>
              )}
            </button>
          </div>
        </section>

        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>기능 상태</h3>
          <div className={styles.featureList}>
            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>자연어 쿼리</span>
                <span className={styles.featureDesc}>Gemini 기반 자연어 쿼리 파싱</span>
              </div>
              <div className={`${styles.featureStatus} ${enableNLQuery ? styles.enabled : styles.disabled}`}>
                {enableNLQuery ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableNLQuery ? 'ON' : 'OFF'}
              </div>
            </div>

            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>OCR</span>
                <span className={styles.featureDesc}>PDF OCR 파싱</span>
              </div>
              <div className={`${styles.featureStatus} ${enableOCR ? styles.enabled : styles.disabled}`}>
                {enableOCR ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableOCR ? 'ON' : 'OFF'}
              </div>
            </div>

            <div className={styles.featureItem}>
              <div className={styles.featureInfo}>
                <span className={styles.featureName}>웹 크롤링</span>
                <span className={styles.featureDesc}>웹 크롤링 데이터 수집</span>
              </div>
              <div className={`${styles.featureStatus} ${enableCrawling ? styles.enabled : styles.disabled}`}>
                {enableCrawling ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {enableCrawling ? 'ON' : 'OFF'}
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>시스템 정보</h3>
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>애플리케이션</span>
              <span className={styles.infoValue}>naPO (naru Public Observer)</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>버전</span>
              <span className={styles.infoValue}>1.0.0</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>환경</span>
              <span className={styles.infoValue}>{import.meta.env.MODE}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>API</span>
              <span className={styles.infoValue}>{import.meta.env.VITE_API_URL || '/api/v1'}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
