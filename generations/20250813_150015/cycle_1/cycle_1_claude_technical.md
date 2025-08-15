The Promise and Reality of Text-to-SQL: Why Natural Language Database Queries Remain Hard

While GPT-5 can ace complex math olympiad problems and write poetry indistinguishable from human work, a seemingly simpler task remains surprisingly difficult: converting natural language questions into SQL queries.

The latest SPIDER benchmark results from early 2025 tell a sobering story. Even state-of-the-art models achieve only 20% accuracy on complex database queries, a far cry from the near-perfect performance we see in other language tasks. This gap has profound implications for enterprise software.

Consider Snowflake customer Acme Corp, which maintains 147 different revenue definitions across their data warehouse. When a sales leader asks "What was our enterprise revenue growth last quarter?", the correct SQL query depends on understanding which of those 147 definitions applies. Current language models struggle with this crucial business context.

The progress, while steady, has been incremental. Looking at cumulative improvements since 2020, we see accuracy gains of roughly 3-4 percentage points per year. At this rate, we're still 5-7 years away from the 80% accuracy threshold that most enterprises consider minimally viable for production use.

This explains why companies like Databricks and dbt Labs continue to invest heavily in traditional data transformation workflows rather than betting entirely on natural language interfaces. The complexity of modern data warehouses - with their nested views, complex joins, and custom business logic - creates a semantic challenge that goes far beyond SQL's relatively simple syntax.

As I explored in my recent Semantic Cultivators post, the core challenge isn't the language model's raw capabilities. Rather, it's the invisible web of business context, data lineage, and organizational knowledge that humans instinctively bring to data analysis.

Some startups are finding creative ways forward. Preset.io has seen success by constraining the problem space to pre-built dashboards, where business context is explicitly encoded. Mode Analytics takes a hybrid approach, using language models to augment rather than replace traditional SQL workflows.

The path to truly reliable text-to-SQL likely runs through better ways to capture and encode business context. Just as dbt revolutionized data transformation by making business logic explicit and version-controlled, the next breakthrough may come from tools that help organizations formalize their semantic layer.

For founders building in this space, the message is clear: don't bet on language models magically solving the business context problem. Instead, look for ways to systematically capture and encode the organizational knowledge that makes data meaningful. The companies that crack this challenge will unlock the true potential of natural language interfaces to data.

The question isn't whether text-to-SQL will eventually work - it will. The question is who will build the tools that bridge the gap between raw language capabilities and the complex reality of enterprise data. Who's taking on that challenge?