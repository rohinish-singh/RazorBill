/**
 * ------------------------------------------------------------
 * FAQ CONTENT 
 * ------------------------------------------------------------
 * Contains:
 * - Section metadata (badge, heading, subheading)
 * - FAQ accordion items
 * ------------------------------------------------------------
 */

import { CircleQuestionMark } from "lucide-react";


export const FAQ_CONTENT = {

    badge : {
        icon: CircleQuestionMark,
        title: 'FAQs'
    },
    heading: "Frequently Asked Questions",
    subheading: 
    `
          All your questions answered in one place. If you have any other questions,
           feel free to reach out to our support team.

    `,
    items: [
        {
      id: 1,
      title: "What is LeadFlow?",
      content:
        "LeadFlow is an AI-powered sales platform that helps businesses manage leads, track deals, optimize their sales pipeline, and automate repetitive sales tasks."
    },
    {
      id: 2,
      title: "How does LeadFlow help me manage leads?",
      content:
        "LeadFlow helps you organize contacts, track lead activity, monitor deal progress, and keep your sales pipeline organized in one place."
    },
    {
      id: 3,
      title: "How does the AI lead optimization work?",
      content:
        "LeadFlow uses AI to analyze lead information, identify promising opportunities, and help you prioritize leads so you can focus on potential customers."
    },
    {
      id: 4,
      title: "Can I automate my sales process?",
      content:
        "Yes. LeadFlow helps automate repetitive sales tasks, follow-ups, and workflow steps, giving your team more time to focus on building relationships and closing deals."
    },
    {
      id: 5,
      title: "Can I track my sales pipeline?",
      content:
        "Yes. You can track deals through different pipeline stages, monitor progress, and get a clearer overview of your sales opportunities."
    },
    {
      id: 6,
      title: "Does LeadFlow integrate with other tools?",
      content:
        "LeadFlow is designed to support integrations with sales and productivity tools. Available integrations depend on your plan and the integrations currently supported."
    },
    {
      id: 7,
      title: "Is LeadFlow suitable for small businesses?",
      content:
        "Yes. LeadFlow is designed to help businesses of different sizes organize leads, manage deals, and streamline their sales workflows."
    },
    {
      id: 8,
      title: "Can I change my subscription plan?",
      content:
        "You can manage your subscription and review available plans through your account, subject to the billing options offered by LeadFlow."
    }
    ]
}