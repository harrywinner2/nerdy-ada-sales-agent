<!-- Demo narration. Each blank-line-separated block is one beat; beat N pairs with clip_00N.
     ~10 beats, ~30s each ≈ 5 minutes. Headings and comments are ignored by tts.py. -->

# Beat 1 — The problem
Nerdy closes tutoring sales with live phone agents. The question on the table is whether an AI agent can match or beat that — with around-the-clock coverage, consistent performance, and the ability to experiment on sales tactics at scale. This is Ada, an autonomous voice sales agent that does exactly that. Let me show you.

# Beat 2 — Talk to her
The fastest way to judge a sales agent is to talk to it. From the browser you start a call and speak — Ada listens, responds with natural voice, and you can interrupt her mid-sentence. Under the hood that's the OpenAI Realtime API over a single low-latency socket, with server-side voice detection for natural turn-taking and barge-in.

# Beat 3 — A real phone call
For end-to-end realism, Ada also answers a real phone line through Twilio. Same brain, same knowledge, same decisions — just over the telephone network. A prospect can literally call the number and have a complete discovery-to-close conversation.

# Beat 4 — How she decides
Ada isn't reading a script. A discovery playbook tracks the required and leading questions, ranks what to ask next, and skips anything she already knows. Every turn she logs a decision — ask, answer, pivot to close, or escalate — with the alternatives she considered and a confidence score. You can read exactly why she did what she did.

# Beat 5 — Grounded, no hallucinations
When a prospect asks about pricing, policy, or how Nerdy compares to a competitor, Ada looks it up in a knowledge base and answers only from what she finds. If the answer isn't there, she says she'll confirm and escalates — she does not invent facts. Every grounded answer carries its citation.

# Beat 6 — Memory across calls
Ada remembers. Leads are stored with everything she's learned, so a second call opens with context — last time you mentioned your daughter is in ninth-grade geometry. Personal information in transcripts is substituted out at write time, so the stored history is private by construction.

# Beat 7 — Fully observable
Nothing is buried in logs. Every call — web, phone, or simulated — shows up with its outcome, its version tag, and its KPIs. Open one and you get the full transcript next to the decision timeline, the profile she gathered, and any escalations. This is how you attribute performance to a specific version of the agent.

# Beat 8 — Honest opponents
Here's where most agents quietly cheat. To improve, Ada plays against synthetic prospects — but these aren't obedient leads who always say yes. The budget skeptic pushes hard on price. The fence-sitter stalls. One caller is simply out of fit and should be politely turned away. A win has to be earned.

# Beat 9 — It gets measurably better
And it does get better. In a controlled experiment, Ada's flat price rebuttal closed twenty-five percent of objection calls. The loop generated variants, ran each against the same prospects, and a value-and-ROI framing closed seventy-five percent. That's a fifty-point gain on a real KPI — promoted, but flagged for human review because the swing was large.

# Beat 10 — The whole picture
So: real-time voice on web and phone, grounded answers, transparent decisions, cross-call memory, full observability, and a recursive loop that honestly moves a sales number. One Python service, a React dashboard, deployed and live. That's a sales agent you could actually put a customer on the other end of.
