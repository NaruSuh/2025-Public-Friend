import React from 'react';
import styles from './BrutalCard.module.css';

export interface BrutalCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'accent' | 'warning' | 'success';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function BrutalCard({
  children,
  title,
  subtitle,
  icon,
  variant = 'default',
  size = 'md',
  className = '',
  onClick,
  hoverable = false,
}: BrutalCardProps) {
  const cardClasses = [
    styles.card,
    styles[`variant-${variant}`],
    styles[`size-${size}`],
    hoverable && styles.hoverable,
    onClick && styles.clickable,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const Component = onClick ? 'button' : 'div';

  return (
    <Component className={cardClasses} onClick={onClick} type={onClick ? 'button' : undefined}>
      {(icon || title) && (
        <div className={styles.header}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <div className={styles.headerText}>
            {title && <h3 className={styles.title}>{title}</h3>}
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
        </div>
      )}
      <div className={styles.content}>{children}</div>
    </Component>
  );
}
