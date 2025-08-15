The hype around large language models (LLMs) is deafening.  GPT-5 aced the AIME math competition, scoring near 100%.  It feels like every problem involving text is solved.  But beneath the surface, critical business applications lag.  Text-to-SQL, the ability to translate natural language into database queries, is one such area.  While showing steady improvement, it’s far from the polished experience of ChatGPT.

This matters because data is the lifeblood of modern business.  Imagine asking your data warehouse, "What's our monthly recurring revenue from enterprise customers in EMEA?" and getting an accurate answer instantly.  That's the promise of text-to-SQL.  The reality, however, is more complex.

The SPIDER benchmark, a widely used measure of text-to-SQL performance, paints a sobering picture. As of early 2025, the state-of-the-art models achieve only around 20% accuracy.  Look at the graph in my related Semantic Cultivators post (linked below) – the progress is real, but the climb is steep.  We’re not talking about nuanced language understanding; we're talking about structured queries against well-defined schemas.

Why is this so hard?  SQL itself has a limited syntax.  The challenge lies in the complexity of modern cloud data warehouses.  Think about Snowflake, Databricks, or BigQuery.  They house intricate schemas, custom functions, and data pipelines that dwarf the complexity of traditional databases.

Furthermore, benchmarks like SPIDER don’t capture the nuances of real-world business data.  Take the concept of “revenue.”  A SaaS company might have multiple revenue definitions: recurring revenue, total revenue, and perhaps even revenue by product line.  These subtle differences, critical to business understanding, are lost on current text-to-SQL models.

Consider a sales leader at a fast-growing B2B SaaS company like Gong.  They want to understand deal flow from specific industries.  Asking, "How many deals did we close in FinTech last quarter?" should be straightforward.  But translating this simple question into a precise SQL query, navigating the complexities of their data warehouse, is currently beyond the capabilities of most text-to-SQL systems.

Similarly, imagine a product manager at Canva querying user engagement data.  "What's the average time spent designing presentations by users on the free tier?" seems simple enough.  Yet, converting this into a functional SQL query requires understanding the underlying data structure and user segmentation, something current models struggle with.

The implications for startups and VCs are clear. While the long-term potential of text-to-SQL is enormous, we’re not there yet.  Don't bet your business on seamless natural language access to your data warehouse just yet.  The tools are improving, but they require careful evaluation and realistic expectations.

The gap between the hype and reality of LLMs presents an opportunity.  Startups focused on solving the practical challenges of text-to-SQL, particularly in the context of complex business data, are well-positioned for success.  The question remains:  Will the next wave of innovation bridge this gap, or will the complexities of real-world data continue to be a stumbling block?  Check out my related post on Semantic Cultivators for a deeper dive: [link to your blog post].
