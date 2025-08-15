The Rise and Reality of Text-to-SQL: A Tale of Two Technologies

While GPT-5 can now solve complex math olympiad problems with near-perfect accuracy, converting natural language to SQL remains surprisingly challenging. The latest SPIDER benchmark results from early 2025 show only 20% accuracy for even the most advanced models - a stark contrast to the rapid advances we've seen in other areas of language AI.

This gap matters because data analysis is the lifeblood of modern businesses. Companies like Snowflake and Databricks have built multi-billion dollar businesses by making data more accessible, yet the "last mile" of natural language querying remains elusive.

Consider a seemingly simple request: "Show me revenue growth by customer segment last quarter." A human analyst immediately knows to check if revenue means ARR, bookings, or GAAP revenue. They understand which customer segmentation model to use and how to handle partial quarters. Current text-to-SQL models don't have this context.

The technical challenges run deeper than just business logic. Our analysis of the SPIDER benchmark progress shows a consistent but slow improvement of about 3-4 percentage points per year since 2021. This suggests we're hitting fundamental limitations in how models understand database schema relationships and complex query patterns.

Real-world applications reveal even more complexity. When Stripe implemented natural language querying for their analytics dashboard, they discovered that 80% of user questions required understanding their specific payment processing terminology. Standard benchmarks don't capture these domain-specific challenges.

The most successful implementations so far have come from narrowly focused solutions. Retool's query assistant works well because it operates within a constrained domain of basic CRUD operations. Similarly, dbt Labs has found success by focusing specifically on data transformation workflows rather than trying to solve general-purpose querying.

These limitations create opportunities for startups. Companies like SemanticLayer and Metrics Layer are building abstraction layers that encode business logic and metadata, making it easier for language models to generate accurate queries. They're essentially creating a bridge between raw SQL and business meaning.

Looking at the trendline from our cumulative analysis, we might reach 50% accuracy on SPIDER by 2027. But the real breakthrough will likely come from a fundamental shift in architecture - perhaps combining large language models with dedicated reasoning engines that understand data relationships and business context.

The question isn't whether natural language will become the primary interface for data analysis, but rather how we'll build the intermediate layers that make it reliable enough for business-critical decisions. For founders building in this space, the key insight is that solving 80% of queries for a specific vertical is more valuable than trying to be a general-purpose solution.

What happens when we finally crack this problem? The implications go far beyond just making analysts more productive. When everyone in an organization can reliably query data using natural language, we'll see a fundamental shift in how businesses make decisions. The companies that figure out how to make this transition will shape the next decade of enterprise software.