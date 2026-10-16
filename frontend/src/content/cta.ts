/**
 * ------------------------------------------------------------
 * CTA CONTENT 
 * ------------------------------------------------------------
 * Contains:
 * - Section metadata (badge, heading, subheading)
 * - FAQ accordion items
 * ------------------------------------------------------------
 */


export const CTA_CONTENT = {
   heading: "Stop Chasing Leads. Start Closing Deals.",
   subheding: `
   Let AI handle the busywork while your team 
   focuses on the conversations that drive revenue.
   `,
   cta: {
     /**
       * Primary CTA
       */
    primary: {
        label: "Get-Started",
        href: "/auth",
      },
  
      /**
       * Secondary CTA
       */
      secondary: {
        label: "Book a Demo",
        href: "/",
      },
  },
    ctaImage:{
       src: "/dashboard.png",
      alt: "hero-image",
    } 
}