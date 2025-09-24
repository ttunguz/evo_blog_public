#!/usr/bin/env python3
"""Test evaluator with Claude AP English grading"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from evaluator import BlogEvaluator
from models import ClaudeClient

# Sample blog post in Tom's style
sample_post = """AI agents will transform software pricing models in ways that echo Salesforce's disruption of perpetual licenses twenty years ago.

Today's SaaS companies face a fundamental question. When an AI agent performs the work of three employees, what happens to per-seat pricing? The answer will reshape the $600 billion software industry.

Consider Klarna's recent results. They reduced customer support costs by 66% using AI agents. Microsoft reports their engineers write code 50% faster with GitHub Copilot. These aren't incremental improvements. They represent a step function change in productivity that breaks traditional pricing models.

Three pricing strategies are emerging from early adopters. 

First, companies like ServiceNow are testing premium pricing for AI features, charging 2-3x standard seat costs. Their logic is straightforward. If the AI delivers 3x productivity, customers still capture significant value even at higher prices. Early data shows 40% of enterprise buyers accept these premiums when ROI is demonstrated clearly.

Second, usage-based pricing aligns costs with value creation. Snowflake pioneered this model for data warehouses, growing from $100M to $2B in revenue in five years. AI companies like Anthropic and OpenAI charge per token processed. This model provides transparency but requires sophisticated tracking and creates budget uncertainty that CFOs dislike. Companies adopting this approach report 25% higher net revenue retention but 30% longer sales cycles.

Third, outcome-based pricing ties fees directly to business results. An AI SDR company might charge per qualified meeting booked rather than per user. This model shares risk between vendor and customer but requires clear metrics and attribution. Early experiments show 2x higher close rates but face resistance from procurement teams unfamiliar with the structure.

The data tells a compelling story. Public SaaS companies trade at 6x revenue on average. Companies with usage-based models trade at 9x. Those with demonstrated AI capabilities command 12x multiples. Markets are betting on which model will dominate.

History suggests the winner won't be the model itself but the company that packages it best. Salesforce didn't invent SaaS. They created a movement around "No Software" that resonated with buyers tired of complex installations and upgrades. Today's opportunity is similar. The company that captures the narrative around AI transformation will define the next era of software pricing.

Smart founders are already positioning for this shift. They're building pricing flexibility into their products from day one. They're educating sales teams on value-based selling. Most importantly, they're collecting data on AI impact to justify premium pricing.

The transition won't be smooth. Customers need time to adjust budgets. Sales compensation plans require restructuring. Financial models need rebuilding. But the companies that navigate this transition successfully will emerge as the next generation of software giants.

The question isn't whether AI will change software pricing. It's whether your company will lead or follow that change."""

# Initialize with Claude client
config = {"model": "claude-3-5-sonnet-latest"}
claude_client = ClaudeClient(config=config)
evaluator = BlogEvaluator(claude_client=claude_client)

# Evaluate
print("Evaluating blog post with AP English teacher standards...")
print("=" * 60)

evaluation = evaluator.evaluate(sample_post, "How AI Agents Will Reshape Software Pricing")

print(f"Overall Grade: {evaluation.overall_grade}")
print(f"Overall Score: {evaluation.overall_score:.1f}/100")
print(f"Ready to Ship: {'✅ Yes' if evaluation.ready_to_ship else '❌ No (needs B+ or better)'}")
print("-" * 60)
print("Detailed Scores:")
print(f"  Grammar: {evaluation.grammatical_correctness:.1f}/100")
print(f"  Argument: {evaluation.argument_strength:.1f}/100")
print(f"  Style Match: {evaluation.style_match:.1f}/100")
print(f"  No Clichés: {evaluation.cliche_absence:.1f}/100")
print("-" * 60)
print("Feedback:")
for category, feedback in evaluation.feedback.items():
    print(f"\n{category.upper()}:")
    print(f"  {feedback}")

# Generate improvement suggestions
suggestions = evaluator.generate_improvement_suggestions(evaluation)
if suggestions:
    print("-" * 60)
    print("Improvement Suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")