import React from 'react';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import styles from './Footer.module.css';

export default function Footer() {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <footer className={styles.footer}>
      <div className={styles.left}>
        <span className={styles.version}>naPO v1.0.0</span>
        <span className={styles.separator}>|</span>
        <span className={styles.status}>
          {isOnline ? (
            <>
              <Wifi size={12} className={styles.online} />
              Connected
            </>
          ) : (
            <>
              <WifiOff size={12} className={styles.offline} />
              Offline
            </>
          )}
        </span>
      </div>

      <div className={styles.right}>
        <span className={styles.env}>{import.meta.env.MODE.toUpperCase()}</span>
        <Activity size={12} />
      </div>
    </footer>
  );
}
