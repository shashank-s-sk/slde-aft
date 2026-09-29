# Draft: Declaration of generative AI and AI-assisted technologies

Status: DRAFT for the user's review (2026-09-29). Not yet inserted into
main.tex. Goes immediately before the references once approved.

Check the template sentence against the current Elsevier Guide for Authors
before finalising. Elsevier revises this wording; the fixed parts below
follow its standard form ("During the preparation of this work the
author(s) used [TOOL] in order to [REASON]. After using this tool/service,
the author(s) reviewed and edited the content as needed and take(s) full
responsibility for the content of the publication.").

---

**Declaration of generative AI and AI-assisted technologies in the
manuscript preparation process**

During the preparation of this work the authors used Claude Code and
Claude (Anthropic) in order to:

- write and run the analysis and experiment scripts, including the API
  extraction runs, the bootstrap and significance analyses, and the audit
  of the released DySECT code and knowledge base;
- check the manuscript's numbers against the committed outputs and its
  references against bibliographic records (ACL Anthology, Crossref,
  JMLR, PMLR, NeurIPS proceedings, arXiv);
- draft and edit text of the manuscript and the supplementary material.

The authors decided the research questions, the experimental designs and
their pre-registrations, and every interpretation. Every reported number
comes from scripts and outputs committed to the public repository. After
using these tools, the authors reviewed and edited the content as needed
and take full responsibility for the content of the publication.

Separately, several large language models (Llama-3.1-8B, DeepSeek-V3.2,
Llama-3.3-70B, GPT-4o, GPT-4.1-mini, Claude Sonnet 5 and Gemini 2.5 Pro)
are objects of study or evaluation tools in this research. Their use is
described in the Methods and is not covered by this declaration.

---

## Notes for the user (not part of the declaration)

1. **Model versions.** This session ran Claude Opus 5.5 in Claude Code.
   Earlier sessions may have used other Claude models, which I cannot see.
   The draft therefore names the products (Claude Code, Claude) and no
   versions. If you want versions named, list the ones you know you used.
2. **Scope.** Elsevier's policy covers AI used in *preparing the
   manuscript*. The draft goes further and also declares the analysis
   scripting and verification, because this project used AI heavily
   there and an honest reader would want to know. If you prefer the
   narrow scope, drop the first two bullets. I recommend keeping them.
3. **"Claude (chat)" use.** Your note mentions a preliminary DySECT
   code trace done in the chat interface. It is covered by "the audit of
   the released DySECT code" (the final audit was redone and verified in
   Claude Code). Mention it separately if you want that distinction
   explicit.
4. **Accuracy check.** I have not claimed anything I could not verify.
   If Claude or another AI tool was used for things I cannot see (e.g.
   literature search, figure design, translation), add them.
5. **LLM-judge use.** GPT-4.1-mini was an evaluation tool (DySECT Step
   A), which is internal and not in the paper. If Step A is cited, keep it
   in the "objects of study or evaluation tools" list; otherwise remove it.
