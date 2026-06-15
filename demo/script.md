<!-- Demo narration. Each blank-line-separated block is one beat; beat N pairs with clip_00N.
     15 beats, richer detail, ≈ 6 minutes. Headings and comments are ignored by tts.py.
     Beat 14 (architecture) is a held still: demo/clips/clip_014.png. -->

# Beat 1 — The problem & the hypothesis
Nerdy closes individual tutoring sales with live phone agents. The hypothesis behind this project is consequential: that an AI agent could match, or beat, human sales benchmarks. If that holds, the payoff is operational — coverage around the clock every day of the year, perfectly consistent performance, and the ability to run controlled experiments on sales tactics at a scale no human team could reach. This is Ada, an autonomous voice sales agent built to test exactly that. Let me show you what she does.

# Beat 2 — Meet Ada
Ada has one job: hold a complete sales conversation, from the first hello all the way to a booked consultation. She keeps a consistent persona — a warm, concise learning advisor, never a script reader. Across a call she gathers the information a human agent would, answers hard questions, handles objections, and decides in real time how to move the sale forward. And she does it on two live channels.

# Beat 3 — Talk to her on the web
The first channel is the web, because the fastest way to judge a sales agent is to talk to it. You press start, allow your microphone, and just speak. Ada listens, replies in a natural voice, and if you interrupt her mid-sentence she stops and adapts. Under the hood that's the OpenAI Realtime API over a single low-latency socket, with server-side voice detection driving natural turn-taking and barge-in — none of the robotic walkie-talkie pauses.

# Beat 4 — A real phone call
The second channel is a real phone line, through Twilio. Same brain, same knowledge, same decisions — just delivered over the telephone network. A prospect can literally dial the number and have a full discovery-to-close conversation, which is what end-to-end realism actually means. The call bridges into the same Realtime session, so her behavior is identical whether you reach her on the web or on the phone.

# Beat 5 — Any lead, with history
Real leads don't arrive uniform. Some come in with full information, some partial, some with nothing at all — and Ada handles all three. She fills the gaps she needs and skips what she already knows. And because she remembers across calls, a returning lead never starts from scratch: she carries the prior conversation forward, so a second call opens with context instead of repetition.

# Beat 6 — The discovery playbook
She isn't improvising her way through discovery. A playbook tracks the required and the leading questions, ranks what to ask next by priority, and skips anything already known. So she asks for the grade, the subject, the goal, the timeline, the budget — one question at a time, acknowledging each answer — and she stops the moment she has what she needs, rather than marching through a fixed list.

# Beat 7 — Real-time decisioning
Every turn, Ada makes a genuine decision — ask the next question, answer from the knowledge base, pivot toward a close, or escalate — and she logs it. This is the decision timeline for a real call. Each entry shows the action she took, the alternative questions she considered, and a confidence score. You can read, turn by turn, exactly why she did what she did. The reasoning is surfaced, not buried in logs.

# Beat 8 — Knowing when to escalate
Not every moment should be fully automated. When Ada hits a low-confidence turn, or a high-stakes one — a real pricing concession, an upset caller, a policy she can't ground — she escalates and flags it for a human instead of bluffing. That boundary is deliberate: the system is autonomous where it's safe to be, and it hands off where judgment or authority is genuinely required.

# Beat 9 — Grounded answers, no hallucinations
When a prospect asks about pricing, policy, guarantees, or how Nerdy compares to a competitor, Ada looks it up in a knowledge base and answers only from what she finds — and every grounded answer carries its citation. If the answer isn't there, she doesn't invent one; she says she'll confirm, and escalates. These documents are her single source of truth, which is how you get an agent that's persuasive without making facts up.

# Beat 10 — Memory and privacy
Behind the conversation is memory. Every lead is stored with everything she's learned, so she can truly pick up where she left off — last time, you mentioned your daughter is in ninth-grade geometry. And privacy is built in, not bolted on: names, phone numbers, and emails are substituted out of transcripts at the moment they're written, so the stored history is protected by construction.

# Beat 11 — Fully observable, attributed by version
Nothing about a call is opaque. Every conversation — web, phone, or simulated — appears here with its outcome, its KPIs, and the exact version of the agent that handled it. Open one and you get the full transcript beside the decision timeline, the profile she gathered, and any escalations. Tagging every call with a version is what lets you attribute a change in performance to a specific change in the agent.

# Beat 12 — Honest synthetic prospects
To improve, Ada plays against synthetic prospects — and this is where weak systems quietly cheat. These are not obedient leads who always say yes. The budget skeptic pushes hard on price and compares us to a twenty-five-dollar local tutor. The fence-sitter stalls. The comparison shopper name-drops competitors. And one caller is simply out of fit, and should be politely turned away. Each has hidden goals and walk-away conditions, so a win has to be earned. That's honest self-play, not a victory lap.

# Beat 13 — It gets measurably better
And here is the loop that ties it together. We picked one dimension to prove the pattern — the price-objection rebuttal — and ran a controlled experiment. The baseline, a flat factual rebuttal, closed twenty-five percent of objection calls. The system generated variants, ran each against the same prospects, and a value-and-ROI framing closed seventy-five percent — a fifty-point gain on a real KPI, with objection resolution going from two-thirds to perfect. It was promoted, but because the swing was large, flagged for human review rather than shipped in silence. The agent got measurably better against prospects that fight back.

# Beat 14 — How it's built
A word on the architecture, because the architecture is the point. The voice core is OpenAI's Realtime API doing speech to speech over one socket — lowest latency, native barge-in, and it speaks the phone's audio format directly, so the Twilio bridge is almost a pass-through. A Python FastAPI relay is the trust boundary: it holds the keys, runs the tools, and logs every decision. SQLite serves as both the memory and the observability store. The dashboard is React. And crucially, the same agent logic runs in text mode for self-play, so improvements found cheaply in simulation transfer straight to live voice. It's one service, deployed on Railway, which runs the persistent voice sockets natively.

# Beat 15 — It's real
Everything you've seen is end-to-end functional and live — not a mockup, and not a render. It's a public repository, a deployed URL, a passing test suite, and documentation that includes an honest failure-mode report and a limitations memo, because a system you'd trust with customers is one that's candid about its edges. The bar we set was simple: a call that a real sales agent could be on the other end of. That is Ada.
