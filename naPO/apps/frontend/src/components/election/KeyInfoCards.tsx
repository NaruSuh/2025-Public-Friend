import {
  Vote,
  Calendar,
  AlertTriangle,
  Smartphone,
  Phone,
  type LucideIcon,
} from 'lucide-react';
import { BrutalCard } from '@/components/common/BrutalCard';
import { keyInfo, type KeyInfo } from '@/data/keyInfo';
import styles from './KeyInfoCards.module.css';

const ICON_MAP: Record<string, LucideIcon> = {
  vote: Vote,
  calendar: Calendar,
  warning: AlertTriangle,
  phone: Smartphone,
  report: Phone,
};

function KeyInfoCard({ info }: { info: KeyInfo }) {
  const Icon = ICON_MAP[info.icon] || AlertTriangle;

  return (
    <BrutalCard
      title={info.title}
      icon={<Icon size={20} />}
      size="md"
      hoverable
      className={styles.card}
    >
      <ul className={styles.itemList}>
        {info.items.map((item, index) => (
          <li key={index} className={styles.item}>
            {item}
          </li>
        ))}
      </ul>
      {info.lawRef && (
        <div className={styles.lawRef}>
          <code>{info.lawRef}</code>
        </div>
      )}
    </BrutalCard>
  );
}

export function KeyInfoCards() {
  return (
    <section className={styles.section}>
      <header className={styles.header}>
        <h2 className={styles.title}>주요 정보</h2>
        <p className={styles.subtitle}>선거 참여를 위한 핵심 안내</p>
      </header>
      <div className={styles.grid}>
        {keyInfo.map((info) => (
          <KeyInfoCard key={info.id} info={info} />
        ))}
      </div>
    </section>
  );
}
