# Attribution & changes

This experiment is built on **[microsoft/lost_in_conversation](https://github.com/microsoft/lost_in_conversation)** (MIT License, © Microsoft Corporation — see `LICENSE`), the code release for *"LLMs Get Lost in Multi-Turn Conversation"* ([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)).

Vendored from upstream commit **`c865793fe34a929d316119b0451d01bd9183bcfd`**.

## What is original to this experiment

- **`simulator_embedded.py`** — new. The core contribution: a copy of `simulator_sharded.py` where, at each assistant call, the conversation-so-far is collapsed into a single narrative user turn (`build_embedded_input`) instead of a native multi-turn message array. Also holds the ablation variants (`minimal` = no framing instruction; `useronly` = drop the model's own prior turns).
- **`analyze.py`** — new. Performance / Aptitude(P90) / Unreliability(P90−P10) decomposition per condition.
- **`regrade.py`** — new. Fair re-grade that removes the answer-extraction artifact (an LLM judge that only ever flips wrong→right, applied identically to all conditions). The headline numbers are post-re-grade.
- **`run_ablation.py`** — new. Resumable runner for the 6-arm ablation on a fixed instance set.
- **`run_simulations.py`** — patched: import `ConversationSimulatorEmbedded`, an `embedded` branch, `--N_embedded_runs`, and run-count bookkeeping.
- **`tasks/tasks.py`** — patched: task imports made lazy so a math-only run needs only lightweight deps.
- **`model_openai.py`** — patched: added `gpt-4.1` / `gpt-4.1-mini` / `gpt-4.1-nano` entries to the cost table.
- **`data/sharded_math.json`** — the 103 math instances extracted from upstream `data/sharded_instructions_600.json` (the full 600-instance / 6-task file and the spider DBs are not vendored — not needed for a math run).
- **`data/sharded_math_subset20.json`, `data/sharded_math_subset3.json`** — fixed subsets (first 20 / 3 math instances by task_id) used for the 20-instance ablation and smoke tests.
- **`results/`** — raw run logs (`logs_gpt41mini/` = the 6-arm gpt-4.1-mini run, 6,180 conversations) and parsed JSON (`ablation103_regraded.json` is the primary result; `ablation103_raw.json` is the pre-re-grade view).

Everything else under this folder is upstream code, unmodified except for the caches/`.git`/venv/irrelevant-task data that were stripped when vendoring.
