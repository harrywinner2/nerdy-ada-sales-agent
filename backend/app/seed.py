"""Seed the knowledge base with grounded sales content + ensure the experiment baseline.

NOTE: this content is SYNTHETIC demo data modeled on how a tutoring advisor would answer — it
is the *grounding source* so Ada cites facts instead of inventing them. Swap in Nerdy's real
policy/pricing docs for production. Run with:  python -m app.seed
"""
from __future__ import annotations

import asyncio

from . import db, experiments, kb

KB_DOCS = [
    ("pricing_plans", "Tutoring Plans & Pricing", "pricing",
     "Nerdy/Varsity Tutors offers 1-on-1 online tutoring in monthly memberships. Typical plans: "
     "Starter is 4 hours/month, Standard is 8 hours/month, and Intensive is 12+ hours/month. "
     "Memberships are billed monthly and hours roll within the month. Exact monthly price is "
     "quoted per student after a needs assessment; a common Standard plan lands around $400/month. "
     "There is no long-term contract; members can change or pause their plan."),
    ("free_consult", "Free Consultation Offer", "pricing",
     "Every prospective family can book a free 25-minute consultation with a learning advisor to "
     "build a custom plan and get matched with a tutor. There is no charge and no obligation for "
     "the consultation."),
    ("trial_session", "First Session / Satisfaction", "policy",
     "New members can start with a first session and, if they are not satisfied with their tutor "
     "match, request a different tutor at no extra cost. Nerdy focuses on getting the match right "
     "rather than locking families in."),
    ("refund_policy", "Cancellation & Refunds", "policy",
     "Memberships can be canceled anytime before the next billing date with no cancellation fee. "
     "Unused hours within a billing cycle do not roll over indefinitely; advisors can help "
     "right-size the plan so families don't pay for hours they won't use."),
    ("tutor_quality", "Tutor Vetting", "product",
     "Tutors are subject-vetted and selected for the student's specific goals (e.g. a geometry "
     "tutor for a geometry test). Sessions happen on the Live Learning Platform with a shared "
     "whiteboard, and session notes are shared with families."),
    ("subjects", "Subjects Covered", "product",
     "Coverage spans K-12 and college subjects: math (including algebra, geometry, calculus), "
     "sciences, reading and writing, and standardized test prep such as SAT and ACT. Niche "
     "professional licensing exams are generally outside the core tutoring offering."),
    ("scheduling", "Scheduling & Flexibility", "policy",
     "Sessions are scheduled around the family's availability, including evenings and weekends. "
     "Members can book recurring weekly slots or schedule ad hoc before a test. Sessions can be "
     "rescheduled with reasonable notice."),
    ("guarantee", "Outcomes & Guarantees", "policy",
     "Nerdy does not guarantee a specific test score or grade — no reputable tutor can promise an "
     "exact outcome. What is offered is a tailored plan, vetted tutors, progress tracking, and the "
     "flexibility to adjust. If a family wants a guaranteed score, that expectation cannot be met."),
    ("objection_price", "Objection: It's expensive", "objection",
     "When price is a concern, ground the conversation in value: 1-on-1 instruction is targeted, so "
     "fewer hours are needed than a generic class; the plan is customized; there is no contract; and "
     "a free consultation lets families try before committing. A right-sized smaller plan is a valid "
     "option. Avoid arbitrary discounts."),
    ("objection_diy", "Objection: We can use free apps / self-study", "objection",
     "Free apps and self-study work for some students, but they lack accountability and a tutor who "
     "adapts to the individual student. Nerdy's value is personalized, scheduled, expert help with "
     "progress tracking — useful when a student is stuck or a deadline is near."),
    ("competitive_chains", "Competitive: Big-box tutoring centers", "competitive",
     "Versus storefront tutoring centers, Nerdy is online (no commute), offers 1-on-1 rather than "
     "small-group sessions, and matches a subject-specific tutor rather than whoever is on shift. "
     "Scheduling is more flexible, including evenings and weekends."),
    ("competitive_marketplaces", "Competitive: Tutor marketplaces", "competitive",
     "Versus open tutor marketplaces where families vet strangers themselves, Nerdy vets and matches "
     "tutors to the student's goals, provides a consistent platform with shared whiteboard and notes, "
     "and supports re-matching if the fit isn't right."),
]


async def seed_kb(force: bool = False) -> int:
    if kb.doc_count() > 0 and not force:
        return kb.doc_count()
    for doc_id, title, cat, content in KB_DOCS:
        await kb.index_doc(doc_id, title, cat, content)
    return kb.doc_count()


async def main() -> None:
    db.init_db()
    experiments.ensure_baseline()
    n = await seed_kb(force=True)
    print(f"seeded {n} KB docs; baseline variant ensured.")


if __name__ == "__main__":
    asyncio.run(main())
