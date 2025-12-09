import * as Sentry from '@sentry/node';
import { nodeProfilingIntegration } from '@sentry/profiling-node';

export function initSentry() {
  // Only initialize Sentry if DSN is provided
  const dsn = process.env.SENTRY_DSN;

  if (!dsn) {
    console.warn('⚠️  SENTRY_DSN not configured - Sentry monitoring disabled');
    return;
  }

  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV || 'development',

    // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Set profilesSampleRate to 1.0 to profile every transaction.
    // Since profilesSampleRate is relative to tracesSampleRate,
    // the final profiling rate can be computed as tracesSampleRate * profilesSampleRate
    // For example, a tracesSampleRate of 0.5 and profilesSampleRate of 0.5 would
    // result in 25% of transactions being profiled (0.5*0.5=0.25)
    profilesSampleRate: 1.0,

    integrations: [
      // Add profiling integration
      nodeProfilingIntegration(),
    ],

    // Capture console.error as breadcrumbs
    beforeBreadcrumb(breadcrumb) {
      if (breadcrumb.category === 'console' && breadcrumb.level === 'error') {
        return breadcrumb;
      }
      return breadcrumb;
    },

    // Filter sensitive data
    beforeSend(event) {
      // Remove sensitive headers
      if (event.request?.headers) {
        delete event.request.headers['authorization'];
        delete event.request.headers['cookie'];
      }
      return event;
    },
  });

  console.log('✅ Sentry monitoring initialized');
}

// Export Sentry for use in other files
export { Sentry };
