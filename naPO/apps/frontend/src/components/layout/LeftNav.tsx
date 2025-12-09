import { useState } from 'react';
import {
  Database,
  Globe,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  History,
} from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import styles from './LeftNav.module.css';

const navItems = [
  {
    id: 'data-sources',
    label: 'DATA SOURCES',
    icon: Database,
    children: [
      { id: 'api', label: 'API 연동', path: '/sources/api' },
      { id: 'crawler', label: '크롤러', path: '/sources/crawler' },
    ],
  },
  {
    id: 'crawlers',
    label: 'CRAWLERS',
    icon: Globe,
    children: [
      { id: 'nec', label: '선거정보도서관', path: '/crawl/nec' },
      { id: 'bigkinds', label: '빅카인즈', path: '/crawl/bigkinds' },
      { id: 'manifesto', label: '매니페스토', path: '/crawl/manifesto' },
      { id: 'custom', label: '커스텀 URL', path: '/crawl/custom' },
    ],
  },
  {
    id: 'parsers',
    label: 'PDF PARSERS',
    icon: FileText,
    children: [
      { id: 'clova', label: 'Clova OCR', path: '/parse/clova' },
      { id: 'google', label: 'Google Vision', path: '/parse/google' },
      { id: 'pymupdf', label: 'PyMuPDF', path: '/parse/pymupdf' },
      { id: 'dolphin', label: 'Dolphin', path: '/parse/dolphin' },
    ],
  },
];

export default function LeftNav() {
  const { leftNavCollapsed, collapseLeftNav, setCurrentView } = useAppStore();
  const [expandedItems, setExpandedItems] = useState<string[]>(['data-sources']);

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
  };

  return (
    <nav className={styles.nav}>
      {/* Header */}
      <div className={styles.header}>
        {!leftNavCollapsed && <h1 className={styles.logo}>naPO</h1>}
        <button
          className={styles.collapseBtn}
          onClick={collapseLeftNav}
          aria-label={leftNavCollapsed ? 'Expand' : 'Collapse'}
        >
          {leftNavCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* Navigation Items */}
      <div className={styles.items}>
        {navItems.map((item) => (
          <div key={item.id} className={styles.group}>
            <button className={styles.groupHeader} onClick={() => toggleExpand(item.id)}>
              <item.icon size={18} />
              {!leftNavCollapsed && (
                <>
                  <span className={styles.groupLabel}>{item.label}</span>
                  <ChevronRight
                    size={14}
                    className={`${styles.chevron} ${expandedItems.includes(item.id) ? styles.expanded : ''}`}
                  />
                </>
              )}
            </button>

            {!leftNavCollapsed && expandedItems.includes(item.id) && item.children && (
              <div className={styles.children}>
                {item.children.map((child) => (
                  <button
                    key={child.id}
                    className={styles.childItem}
                    onClick={() => setCurrentView(child.path!)}
                  >
                    {child.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      <div className={styles.footerActions}>
        <button className={styles.actionBtn} onClick={() => setCurrentView('history')}>
          <History size={18} />
          {!leftNavCollapsed && <span>History</span>}
        </button>
        <button className={styles.actionBtn} onClick={() => setCurrentView('settings')}>
          <Settings size={18} />
          {!leftNavCollapsed && <span>Settings</span>}
        </button>
      </div>
    </nav>
  );
}
