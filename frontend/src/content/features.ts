/**
 * ------------------------------------------------------------
 * FEATURES CONTENT CONFIGURATION
 * ------------------------------------------------------------
 * Centralized data source for the Features section UI.
 *
 * This file defines:
 * - Section badge (title + icon)
 * - Heading & subheading copy
 * - Feature items (used in FeatureTabs01 component)
 *
 * Purpose:
 * Keeps UI content separate from presentation logic,
 * making it easier to scale, edit, and localize.
 * ------------------------------------------------------------
 */

import {
  TrendingUp,
  Sparkles,
  GitBranch,
  RefreshCw,
} from 'lucide-react';

/* =========================
   FEATURES CONTENT DATA
========================= */

export const FEATURESCONTENT = {
  /**
   * Section badge displayed above heading
   */
  badge: {
    title: "Solution",
    icon: Sparkles,
  },

  /**
   * Main section heading
   */
  heading: "Close More. Manage Less.",

  /**
   * Supporting description text under heading
   */
  subheading:
    `
     LeadFlow AI gives your sales team the AI-powered tools to find the
          right leads, manage every deal, and automate the work that slows them down.
    `,

  /**
   * Feature tabs/items displayed in FeatureTabs01
   */
  items: [
   {
    icon: TrendingUp,
    title: 'AI-Powered Lead Scoring',
    description:
      'Automatically identify your most promising leads and prioritize the opportunities most likely to convert.',
  },
  {
    icon: GitBranch,
    title: 'Smart Sales Pipeline',
    description:
      'See every deal at a glance, track progress, and know exactly what needs your attention next.',
  },
  {
    icon: RefreshCw,
    title: 'Automated Follow-Ups',
    description:
      'Handle repetitive follow-ups, reminders, and outreach sequences while you focus on conversations that matter.',
  },

   
  ],
};