/**
 * ------------------------------------------------------------
 * REVIEWS SECTION CONTENT CONFIGURATION
 * ------------------------------------------------------------
 * Centralized content source for the ProcessTabs component.
 *
 * Defines:
 * - Section badge
 * - Heading & subheading
 * - Step-by-step workflow data
 *
 * Purpose:
 * Keeps REVIEWS content separate from UI components,
 * making it easier to maintain, update, and reuse.
 * ------------------------------------------------------------
 */

import { Star } from "lucide-react";

/* =========================
   REVIEWS CONTENT DATA
========================= */

export const REVIEWS_CONTENT = {
  /**
   * Section badge displayed above the heading
   */
  badge: {
    title: "Reviews",
    icon: Star,
  },

  /**
   * Main section heading
   */
  heading: "Our customer's reviews",



  /**
   * Reviews displayed inside review section
   */
  items: [
     {
    id: 1,
    name: "Ava Morgan",
    role: "Co-founder",
    company: "Veyra®",
    quote:
      "LeadyFlow gave our sales team a much clearer view of our pipeline. We spend less time updating deals and more time actually selling.",
    image: "/reviews_imgs/img_1.jpg",
  },
  {
    id: 2,
    name: "Sarah Johnson",
    role: "VP of Sales",
    company: "Northstar Solutions",
    quote:
      "The AI lead scoring has completely changed how we prioritize our prospects. Our reps know exactly where to focus every morning.",
    image: "/reviews_imgs/img_2.jpg",
  },
  {
    id: 3,
    name: "David Miller",
    role: "Head of Growth",
    company: "Orbit",
    quote:
      "Simple enough to get started quickly, but powerful enough to handle our entire sales workflow.",
    image: "/reviews_imgs/img_3.jpg",
  },
  {
    id: 4,
    name: "Marcus Reed",
    role: "Founder & CEO",
    company: "LuminaTech",
    quote:
      "LeadFlow AI has transformed our sales process. The automated follow-ups and reminders have saved us countless hours.",
    image: "/reviews_imgs/img_4.jpg",
  },
     
  ],
};