import { ChatPanel } from '@/components/chat/ChatPanel';
import { KeyInfoCards } from '@/components/election/KeyInfoCards';
import styles from './FaqChat.module.css';

export default function FaqChat() {
  return (
    <div className={styles.page}>
      <div className={styles.layout}>
        <div className={styles.chatSection}>
          <ChatPanel />
        </div>
        <div className={styles.infoSection}>
          <KeyInfoCards />
        </div>
      </div>
    </div>
  );
}
