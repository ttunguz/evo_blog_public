---
title: "Why Text-to-SQL Remains AI's Unsolved Challenge"
layout: post
draft: false
date: 2025-08-13
categories: [AI, data]
---

The Promise and Reality of Text-to-SQL: Why Natural Language Data Querying Isn't Ready for Prime Time

While ChatGPT dazzles us by writing poetry and debugging code, it stumbles on a seemingly simpler task: turning English questions into SQL queries. Recent [SPIDER 2.0 benchmark tests](https://spider2-sql.github.io/) show even the most advanced language models achieve only [17.1% accuracy with o1-preview and 10.1% with GPT-4o](https://spider2-sql.github.io/) on real-world enterprise database queries - a sobering reality check for anyone dreaming of truly democratized data access.

This limitation has real consequences. While I couldn't verify the specific 60% statistic, industry reports confirm that business analysts still heavily depend on data engineers to write SQL queries. [Stripe addressed similar challenges by building their Data Pipeline product](https://stripe.com/data-pipeline), a specialized no-code interface layer that sits between their analysts and their warehouse, allowing business teams to "immediately query Stripe data with other business data" without engineering support.

The problem goes deeper than just translating words to SQL syntax. Modern data warehouses have evolved into complex ecosystems. When a marketing manager asks "What's our customer acquisition cost by channel?" the query might need to navigate partitioned tables, handle nested JSON structures, and account for specific business logic around attribution windows.

[Databricks encountered this firsthand](https://www.databricks.com/blog/introducing-aibi-intelligent-analytics-real-world-data) when building their AI/BI analytics tools. What started as a simple natural language interface evolved into a [compound AI system with multiple specialized agents](https://www.databricks.com/product/databricks-assistant) - each handling different aspects like SQL generation, explanation, and visualization. Their Intelligence Engine uses context from Unity Catalog metadata to understand tables, columns, and popular data assets across the company.

The technical challenges compound at scale. A Fortune 500 retailer's data warehouse might contain thousands of tables with complex relationships. Understanding that "revenue" means summing the "transaction_amount" column from the "sales_facts" table, but only after joining three dimension tables and applying specific business rules, requires deep domain knowledge that current AI struggles to replicate.

Looking at [the actual SPIDER 2.0 progress data](https://spider2-sql.github.io/), we see the best performers reaching around 60% accuracy on simpler benchmarks (Spider 2.0-Snow) but struggling at 15-20% on more complex ones (Spider 2.0-DBT). The improvement trajectory shows steady but slow progress - at current rates, we're still years away from the reliability enterprises require.

This doesn't mean natural language querying is worthless. Companies like [Preset](https://preset.io/) and Thoughtspot have found success with hybrid approaches, using their dataset-centric design to constrain the problem space. These tools accelerate data work without sacrificing accuracy or context by pre-defining relevant data structures and business logic.

The path forward likely involves meeting in the middle. As I explored in my ["Semantic Cultivators" post](https://tomtunguz.com/semantic-layer/), the core challenge isn't the language model's raw capabilities but rather the invisible web of business context, data lineage, and organizational knowledge that humans instinctively bring to data analysis. Teams will need to become cultivators of constantly evolving semantic layers that properly contextualize data for AI agents.

The question isn't whether AI will help us query data - it's already doing that through tools like [Databricks Assistant](https://www.databricks.com/product/databricks-assistant) and [Stripe Data Pipeline](https://stripe.com/data-pipeline). The real question is how we'll balance the promise of natural language interfaces with the pragmatic needs of business users who need accurate, reliable answers to drive decisions. For now, human intelligence remains an essential part of the equation.

---

*Note: Some industry statistics mentioned in earlier drafts (Snowflake 60% analyst dependency, Databricks 70% context requirement) could not be verified through public sources and have been removed or qualified. The core argument remains supported by verified benchmarks and documented case studies.*