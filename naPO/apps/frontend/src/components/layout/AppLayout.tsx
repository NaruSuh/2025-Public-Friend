import React, { useEffect } from 'react';
import { useAppStore } from '@/stores/appStore';
import LeftNav from './LeftNav';
import RightNav from './RightNav';
import TopQueryBar from './TopQueryBar';
import Footer from './Footer';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { theme, leftNavOpen, leftNavCollapsed, rightNavOpen } = useAppStore();

  // Apply theme to document element for CSS variables to cascade properly
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div
      className={styles.layout}
      data-theme={theme}
      data-left-collapsed={leftNavCollapsed}
      data-right-open={rightNavOpen}
    >
      {leftNavOpen && (
        <aside className={styles.leftNav}>
          <LeftNav />
        </aside>
      )}

      <div className={styles.mainArea}>
        <header className={styles.queryBar}>
          <TopQueryBar />
        </header>

        <main className={styles.content}>{children}</main>

        <footer className={styles.footer}>
          <Footer />
        </footer>
      </div>

      {rightNavOpen && (
        <aside className={styles.rightNav}>
          <RightNav />
        </aside>
      )}
    </div>
  );
}
