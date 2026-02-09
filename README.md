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

### 1. [Conversation History Coherence](experiments/conversation-history-coherence/)

**Status**: Ready to run
**Model**: GPT-4.1
**Focus**: Testing whether message formatting affects model coherence under adversarial pressure

Testing if passing conversation history as JSON-dumped strings vs. traditional multi-message arrays affects:
- Boundary maintenance over multi-turn conversations
- Role consistency and context awareness
- Resistance to sophisticated jailbreak attacks

Uses promptfoo's red-team with agentic attack strategies (`jailbreak:meta`, `jailbreak:composite`) to generate adaptive adversarial attacks. 180 tests comparing both approaches under identical adversarial conditions.

