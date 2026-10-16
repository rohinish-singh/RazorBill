/**
 * ============================================================
 * COMPONENT NAME: PRICING_CONTENT
 * ============================================================
 * PURPOSE:
 * Interactive customer review showcase component featuring animated 
 * image zoom/fade transitions, author info slide-ups, and staggered 
 * line-by-line quote reveals using Framer Motion.
 * 
 * PROPS:
 * Self-contained review carousel dataset.
 * ============================================================
 */
import { CreditCard } from "lucide-react";


export const PRICING_CONTENT = {

    badge: {
        title: "Pricing",
        icon: CreditCard,
    },
    heading: "Transparent Pricing for All Our Services",
    subheading: "Choose the tier that matches your fleet size and needs for best performance and cost efficiency.",
    plans: [
          {
    id: 'starter',
    name: 'Starter Plan',
    description: 'For individuals and small teams getting started with a structured sales pipeline.',
    monthlyPrice: 19,
    annualPrice: 45,
    ctaText: 'Get Started',
    ctaHref: '/signup?plan=starter',
    features: [
      'Lead management',
      'Deal pipeline',
      'Contact management',
      'Basic automation',
      'Sales dashboard'
    ],
  },
  {
    id: 'business',
    name: 'Business Plan',
    description: 'For growing sales teams that want AI-powered insights and automation.',
    monthlyPrice: 49,
    annualPrice: 117,
    ctaText: 'Get Started',
    ctaHref: '/signup?plan=business',
    highlighted: true,
    highlightLabel: 'Most popular',
    features: [
      'Everything in Starter',
      'Advanced analytics dashboard',
      'Custom alert workflows',
      'AI deal insights',
      'Team Collaboration',
      'Priority support access',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise Plan',
    description: 'Best for national networks looking for reliable market monitoring tools.',
    monthlyPrice: 'Custom',
    annualPrice: 'Custom',
    ctaText: 'Contact Sales',
    ctaHref: '/contact-sales',
    features: [
    'Everything in Business',
      'Unlimited asset monitoring',
      'Unlimited automation',
      'Multi-region deployment',
      'Dedicated account manager',
      'Custom integrations available',
      'SLA guarantees included',
    ],
  },
    ]
}