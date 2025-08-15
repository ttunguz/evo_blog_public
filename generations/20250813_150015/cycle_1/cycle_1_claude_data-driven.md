The Promise and Reality of Text-to-SQL: A Sobering Look at Enterprise AI

While GPT-5 can now solve complex mathematical olympiad problems with near-perfect accuracy, converting natural language to SQL remains surprisingly challenging. The latest SPIDER benchmark results from early 2025 show just 20% accuracy on complex queries, highlighting a stark contrast in AI capabilities.

This gap matters because data accessibility is the lifeblood of modern enterprises. Companies like Snowflake and Databricks have made storing and processing data easier than ever, but the "last mile" problem of helping business users access this data remains largely unsolved.

Looking at the SPIDER benchmark trend line, we see steady but slow improvement. In 2021, accuracy hovered around 12%. By 2023, it reached 16%. The current 20% mark represents progress but falls far short of the breakthrough many expected.

Real-world implementations tell an even more nuanced story. When Stripe implemented a natural language interface for their analytics platform, they found that even simple queries like "show me revenue by month" became complex due to multiple revenue definitions and business logic layers. What seems straightforward to humans requires deep context that current models struggle to capture.

MongoDB's recent experiment with text-to-SQL interfaces revealed another challenge: while their model showed 85% accuracy on basic SELECT statements, performance dropped to below 15% when dealing with complex joins and nested queries – the kinds of analyses that drive actual business decisions.

The technical bottleneck isn't SQL's syntax, which is relatively constrained. The challenge lies in understanding business context and translating complex analytical intentions into correct query structures. As I wrote in my Semantic Cultivators post, the semantic gap between human intention and formal query language remains wider than many appreciate.

This creates an interesting opportunity for startups. Rather than trying to solve the general text-to-SQL problem, successful companies are focusing on specific vertical use cases. Retool, for instance, has found success by combining natural language interfaces with human-in-the-loop validation for common query patterns in their customer base.

The data suggests we're still years away from reliable, general-purpose text-to-SQL conversion. However, the steady improvement trend points to a future where domain-specific solutions will increasingly augment, rather than replace, data analysts and engineers.

For founders building in this space, the key insight is to embrace the current limitations. Focus on specific industries or use cases where you can deeply embed business logic and context. The winners won't be those who promise to eliminate SQL expertise, but those who make data more accessible while respecting its complexity.

Looking ahead, will we see specialized text-to-SQL models that deeply understand specific business domains outperform general-purpose solutions? The next few years of benchmark results should tell us whether the path to success lies in vertical specialization or continued pursuit of general intelligence.