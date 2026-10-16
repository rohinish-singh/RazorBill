/**
 * ------------------------------------------------------------
 * PROCESS SECTION CONTENT CONFIGURATION
 * ------------------------------------------------------------
 * Centralized content source for the ProcessTabs component.
 *
 * Defines:
 * - Section badge
 * - Heading & subheading
 * - Step-by-step workflow data
 *
 * Purpose:
 * Keeps process content separate from UI components,
 * making it easier to maintain, update, and reuse.
 * ------------------------------------------------------------
 */

import { Workflow } from "lucide-react";

/* =========================
   PROCESS CONTENT DATA
========================= */

export const PROCESS_CONTENT = {
  /**
   * Section badge displayed above the heading
   */
  badge: {
    title: "Process",
    icon: Workflow,
  },

  /**
   * Main section heading
   */
  heading: "How It Works",

  /**
   * Supporting description shown below heading
   */
  subheading:
    `
      LeadFlow AI gives your sales team the
       AI-powered tools to find the right leads,
          manage every deal, and automate the work that slows them down.
          `,
cta: {
    label: "Get Started",
    href: "/auth"
},
  /**
   * Process steps displayed inside ProcessTabs
   */
  steps: [
 {
    id: 'step-1',
    number: '01',
    title: 'Bring in Your Leads',
    description:
      'Connect your existing tools or import your leads into LeadFlow AI and keep your entire pipeline in one place.',
    imageSrc: '/dashboard.png',
  },
  {
    id: 'step-2',
    number: '02',
    title: 'Let AI Prioritize',
    description:
      'LeadFlow AI scores and ranks your contacts based on engagement history, deal size, and conversion likelihood.',
    imageSrc: '/dashboard.png',
  },
  {
    id: 'step-3',
    number: '03',
    title: 'Close More Deals',
    description:
      'Automate follow-up sequences, send timely reminders, and focus your conversations where they matter most.',
    imageSrc: '/dashboard.png',
  },
  
    
  ],
};