The Promise and Reality of Text-to-SQL: Why Your Data Warehouse Still Needs Human Translators

Every week, another headline trumpets AI's latest breakthrough. GPT-5 can now solve complex math problems with near-perfect accuracy, and Claude-4 writes code that passes rigorous security audits. But there's a curious gap in this march of progress: converting natural language to SQL remains surprisingly difficult.

Recent benchmarks tell a sobering story. The SPIDER dataset, which measures how well AI models can convert English questions into SQL queries, shows only 20% accuracy as of early 2025. That means four out of five attempts to translate business questions into database queries still fail.

Snowflake's recent experiment highlights this challenge. Their data science team tested state-of-the-art language models against 1,000 real customer queries. The results? Only 12% of generated SQL queries returned the correct results without human intervention. Even "simple" questions like "Show me revenue by product category for Q4" proved challenging when dealing with complex data models.

The problem isn't SQL's syntax, which is relatively straightforward. The challenge lies in understanding business context. When a marketing executive asks about "revenue," do they mean gross bookings, net revenue, or recognized revenue? Each company defines these terms differently, and their definitions often evolve.

MongoDB's analytics team recently shared that they maintain over 30 different revenue calculations across their systems. This complexity multiplies when considering different business units, geographical regions, and accounting standards.

The progress we're seeing is real but incremental. Looking at the Spider2 cumulative progress data, accuracy has improved by roughly 2-3 percentage points per quarter over the past year. At this rate, we're still years away from reliable, context-aware text-to-SQL conversion.

This has immediate implications for startups and enterprises. Companies investing in natural language interfaces for their data warehouses should focus on hybrid approaches. Databricks' query assistant, for example, uses AI to suggest SQL snippets but keeps humans in the loop for validation and refinement.

As I discussed in my recent Semantic Cultivators post, the key is building systems that augment rather than replace SQL expertise. The most successful implementations combine AI's pattern recognition capabilities with human understanding of business context.

The gap between general language understanding and specialized SQL generation reveals something important about AI progress. While large language models excel at tasks with clear right answers, they struggle with problems that require deep domain knowledge and contextual understanding.

For founders building data tools, this suggests focusing on workflows that embrace this reality. Instead of promising fully automated SQL generation, build tools that make SQL experts more productive and help bridge the gap between business users and data teams.

Looking ahead, will we see a breakthrough that suddenly closes this gap? Or will text-to-SQL follow the steady but slow progress we've observed so far? The answer will shape how we interact with our data for years to come.