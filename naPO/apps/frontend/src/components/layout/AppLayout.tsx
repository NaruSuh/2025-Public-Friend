import React, { useEffect } from 'react';
import { MessageCircle, Database, Sun, Moon } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { theme, toggleTheme, currentView, setCurrentView } = useAppStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className={styles.layout} data-theme={theme}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.logo} onClick={() => setCurrentView('chat')}>
            <span className={styles.logoIcon}>🗳️</span>
            <span className={styles.logoText}>naPO</span>
          </h1>
        </div>

        <nav className={styles.nav}>
          <button
            className={`${styles.navBtn} ${currentView === 'chat' ? styles.navBtnActive : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            <MessageCircle size={16} />
            <span>챗봇</span>
          </button>
          <button
            className={`${styles.navBtn} ${currentView === 'data' ? styles.navBtnActive : ''}`}
            onClick={() => setCurrentView('data')}
          >
            <Database size={16} />
            <span>데이터조회</span>
          </button>
        </nav>

        <div className={styles.headerRight}>
          <button className={styles.themeBtn} onClick={toggleTheme} title="테마 전환">
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
      </header>

      <main className={styles.main}>
        {children}
      </main>
    </div>
  );
}
