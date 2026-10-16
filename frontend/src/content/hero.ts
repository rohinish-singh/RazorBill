/**
 * ------------------------------------------------------------
* HERO CONTENT CONFIGURATION
* ------------------------------------------------------------
 * Centralized content configuration for the marketing hero section.
 * Keeping all copy, images, CTA links, and trust assets in one place
 * makes the component reusable and easier to maintain.
 *
 * Used by:
 * - Hero section component
 * - Trust/brand logos strip
 * - Social proof elements
 */

// /content/marketing/hero.ts

export const HERO_CONTENT = {
  /**
   * Social proof badge displayed above the hero heading.
   */
  badge: "Best Platform to get Leads and Close Deals",

  /**
   * User avatars shown alongside the social proof badge.
   */
  reviewBadgeImgs: [
    {
      src: "/avatar_imgs/img_1.png",
      alt: "reviewimg1",
    },
    {
      src: "/avatar_imgs/img_2.png",
      alt: "reviewimg2",
    },
    {
      src: "/avatar_imgs/img_3.jpg",
      alt: "reviewimg3",
    },
    {
      src: "/avatar_imgs/img_4.jpg",
      alt: "reviewimg4",
    },
    {
      src: "/avatar_imgs/img_5.jpg",
      alt: "reviewimg5",
    },
  ],

  /**
   * Main hero headline.
   */
  heading: "Turn More Leads Into",

  highlightedHeading: "Closed Deals",

  /**
   * Supporting hero description.
   */
  subheading:
    `
      LeadFlow uses AI to optimize your sales pipeline, manage deals,
              and automate repetitive sales tasks, so your team can spend less
              time managing leads and more time closing them.
    `,

  /**
   * Hero call-to-action buttons.
   */
  cta: {
    /**
     * Primary CTA 
     */
    primary: {
      label: "Get-Started",
      link: "/auth",
    },

    /**
     * Secondary CTA 
     */
    secondary: {
      label: "Login",
      link: "/auth",
    },
  },

  /**
   * Main hero illustration or product preview image.
   */
  heroImage: {
    src: "/dashboard.png",
    alt: "hero-image",
  },

  /**
   * Heading displayed above the trust logos section.
   */
  trustHeading: "Trusted by leading companies",

  /**
   * Collection of company/client logos used for credibility.
   */
  trustLogos: [
    { src: '/logos/google.png', alt: 'google' },
    { src: '/logos/figma.png', alt: 'figma' },
    { src: '/logos/adobe.png', alt: 'adobe' },
     { src: '/logos/netflix.png', alt: 'netflix' },
    { src: '/logos/stripe.png', alt: 'stripe' },
  ],
};