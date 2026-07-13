# the-working-prototype
Repository to accompany my Substack newsletter "The Working Prototype".

I'm the first Founding AI Engineer in an AI startup, building recruitment agents at scale. My AI agents talk to thousands of job candidates. They often pass Turing tests in production and they make decisions that affect people's careers. The alignment and safety in AI is where I don't have a right to fail, so I'm actively learning it while shipping another feature to our systems.

I found that most AI safety content is either dense academic papers or surface-level takes. I believe there's a gap for people actually building systems who need to understand alignment but don't have time for a PhD. This Substack newsletter is my attempt to close that gap.

Monthly (or more frequently) I will post:
- course notes translated into builder language
- production lessons from shipping AI agents
- system experiments testing alignment concepts

This repository hosts code for these experiments.

## Experiments

### [What kind of poker player is an AI?](experiments/llm-risk-preference/)

Do language models have a stable risk attitude, or does it shift with the wording and the task? This experiment strips poker down to pure priced decisions: the win percentage, the pot, and the price are all given, so it measures risk-taking rather than card-reading. Across 6,600 decisions from seven models (OpenAI, Anthropic, Mistral), it finds three things: they chase losing draws, some turn over-cautious and fold winning all-ins, and none fall for the sunk-cost trap that gets most people.

### [In character: does history format affect role coherence?](experiments/conversation-history-coherence/)

Tests whether passing conversation history as text embedded in the user message, versus a native message array, changes how well an agent holds its role under adversarial pressure. The agent is Maya, a recruitment coordinator built on GPT-4.1 with no off-topic guardrails. Uses promptfoo with the Crescendo and GOAT attack strategies over multi-turn sessions, plus a replay method that freezes a turn and runs it fifty times per format to isolate the effect.

