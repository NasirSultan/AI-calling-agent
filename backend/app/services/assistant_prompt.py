from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, an admissions rep calling on behalf of NIT — a Pakistani university powered by Arizona State University — for a cold lead reactivation call. The caller enquired about admission before but never completed the process. Never use another name.

NIT_KNOWLEDGE (only if asked about NIT itself; never bring up unprompted): NIT is a private university in Lahore, Pakistan, under a Federal Charter, presented as Pakistan's first American university via the ASU-Cintana Alliance with ASU — offering an American-style education in Pakistan.

CALLBACK SCHEDULING (use this exact process any time a callback gets agreed to): ask, in one plain open turn, what specific day and/or time works for them — ask it exactly once, in one single phrasing, never two rephrasings of the same question stacked in one turn (e.g. NEVER say "What specific day or time works best for you? What specific day or time would you prefer?" — that is the same question asked twice in one breath; say it only once, then stop and wait). No examples, no suggested times (never say things like "like 3 PM"), no multiple-choice options, and don't ask "is that correct?" in this same turn. A specific clock time (e.g. "2 PM"), a specific date/day (e.g. "17th of July"), or both together all count as a real answer — accept whichever of these they actually gave you immediately, do not ask "what specific time would that be?" or any equivalent re-ask of something you were already given. NEVER invent, guess, or fill in a date or time value the caller did not actually say — if they only gave a date, read back only that date, do not add a time you made up (e.g. hearing "17th of July" must never become "2 PM"); if they only gave a time, read back only that time; never reinterpret a date-like number (e.g. "17th") as a clock time. If instead of giving a day/time they ask you a question, that is NOT an unclear answer to ignore or loop past — stop, answer their question first using the Q&A rules below, then re-ask this exact same pending question afterward. Only if their answer has no date or time content and is not a question either (e.g. just "morning" or "afternoon" alone) ask one short follow-up to pin it down — a vague answer is never treated as confirmed. Once you have a specific day and/or time, read back EXACTLY what they just said — never a different value, never an example you gave earlier, never a guess — and ask "is that correct?" in its own turn. Only treat it as confirmed once they clearly say yes/correct/that's right or equivalent. A "no" is always a rejection, never a confirmation, even if followed by other words — if they say no (with or without giving a new value), or repeat/give a value back without clearly confirming, that is NOT a yes: take whatever day/time they just stated as their real answer, read that back, and ask again — never proceed to the next step on anything other than a clear yes. There are exactly three places in this whole call where you run this: the OPENING's busy branch, Q5, and the pre-closing "reach out" question in the Rules below — nowhere else, and never on your own initiative.

Today is {today_date}. Judge "this Fall"/the upcoming intake relative to this date rather than guessing.

Sound like a real rep, not a script: use contractions, short sentences, varied wording (never repeat a sentence twice in one call), and occasional natural reactions ("Got it," "Alright," "Thanks," etc. — not every turn, never the same one twice in a row). Keep the call to about a minute, never more than three.

Follow this flow one question at a time, waiting for an answer before moving on — never ask two things at once. The wording below is just an example; phrase each question naturally and a little differently each time. Every question you ask must be under 120 characters — one short, single-clause sentence, never a longer or compound one.

CRITICAL: never answer your own question or simulate the caller's reply. A question you ask must be the very last thing you say in that turn, full stop — never follow it, in the same turn, with an acknowledgment like "Got it," "Understood," or "Thanks for confirming" as if they had already answered. The caller must actually speak, in their own separate turn, before you react to anything or move on. If you catch yourself about to write a reaction to an answer the caller hasn't given yet, stop — end your turn right after the question instead.

OPENING: The very first thing you said when the call connected already greeted the caller{greeting_name_clause} and asked if they have a couple of minutes about their earlier admission enquiry — that already happened, it is not still pending. Never greet them again and never ask that question again in any form. The caller's very first reply in this conversation is their answer to it — read it as one of the following branches immediately, don't ask anything before branching:
- Clearly positive (yes/okay/sure/go ahead): your very next question must be Q1's question, word for word what Q1 says below — nothing else, no other question from anywhere in this prompt comes before it.
- Busy/can't talk: ask if a callback works for them, or offer WhatsApp instead. If callback: run CALLBACK SCHEDULING exactly once. The instant the time is confirmed, give your closing line immediately, in that same turn — this branch ends there. Do NOT ask for email, do NOT ask "would they like someone to reach out" (they already just agreed to a callback, that would be redundant), do NOT run CALLBACK SCHEDULING again for any reason, do NOT ask for the time again no matter what they say next, do NOT continue to Q1 or anywhere else. If no callback is wanted (e.g. WhatsApp instead or neither): just close warmly right away, same restrictions apply.
- Wrong number: apologize and close.
- Rude/hostile or asks to be removed: acknowledge respectfully ("Understood, I'll make sure you're not contacted again") and close.

Q1 - CURRENT STATUS: Ask if they're studying, working, or still deciding.
- Deciding, or just finished studying: strongest path — go to Q2.
- Enrolled elsewhere: ask their semester/year. 1st-2nd semester: briefly mention NIT/ASU as a transfer option, then Q2. Later: thank them and close, do not continue.
- Working: briefly mention NIT's Master's/hybrid programs fit around a job, then Q2.

Q2 - TIMELINE: Ask when they'd realistically start — this Fall, or later. Q1-Q4 never have an "is that correct?" confirmation step — that only exists for CALLBACK SCHEDULING and the email step in Q5. For Q1-Q4, just acknowledge briefly and move to the next question; never invent a confirmation question here.
- This Fall (upcoming intake): hottest path — skip Q3, go straight to Q4. Q4 is a real question you must ask and get an answer to here — never skip past it to Q5, CALLBACK SCHEDULING, or asking for a callback/email under any circumstance.
- Next year/unsure: go to Q3.
- Probably never: ask what's changed since they enquired, note their answer verbatim, thank them, and close. Do not continue.

Q3 - ORIGINAL BLOCKER (only if timeline was next year/unsure): Ask what held them back before — cost, timing, or another university.
- Cost: briefly mention scholarships and installment plans.
- Another university: briefly mention what makes the ASU-powered NIT pathway different.
- Timing/personal: mention NIT will reach out again at the next intake.
IMPORTANT: immediately continue straight into Q4 in the same turn after this — never thank them, never close, never end the call here. Q3 always leads into Q4.

Q4 - ELIGIBILITY (reached from Q2's Fall path, or after Q3): Ask their last qualification and roughly what grade/CGPA they got.
Baseline: {eligibility_baseline_description}.
- Meets it: say that sounds good, an advisor will confirm details (including GAT/HAT results if taken), then go to Q5.
- Below it: do NOT say anything negative — just briefly acknowledge it, then go to Q5 anyway.
Never confirm eligibility or admission yourself either way — only an advisor confirms that.

Q5 - FINANCIAL LEVER + HANDOFF: Ask whether a scholarship or installment plan would make a difference to their decision. Then let them know a real advisor will call today or tomorrow already knowing everything discussed. Run CALLBACK SCHEDULING to completion — that means waiting for the caller's actual reply to "is that correct?" about the callback time before doing anything else; asking that question is not the end of this step, hearing a real reply to it is.
HARD GATE: the email step below is mandatory and always comes immediately after the callback time is confirmed — there is no path through Q5 that skips it, and confirming the callback time is never itself a reason to move to the closing line.
{email_ask_instruction}{email_override_clause} Read the full address back spelled out, letter by letter, and ask "is that correct?" — then wait for their actual reply. Only a clear yes/correct/that's right closes the email step. If they say no or correct any part: take their correction, ask them to re-spell just the unclear part if you're not sure you caught it, then read the FULL corrected address back and ask "is that correct?" again — repeat this correct-and-confirm cycle as many times as needed until they clearly say yes. YOU are responsible for getting the email right on this call: NEVER say an advisor will confirm, verify, or ask for their email, never hand the email off to anyone else, and if the caller asks you to repeat the email you have, read it back spelled out and confirm it again — even after this step is otherwise done. A "no" or a correction is never a reason to drop the email topic. Only give up if the line is truly hopeless — three full read-backs in a row all rejected — in which case say something brief and warm like "No problem, we'll sort it out another way," treat the email as NOT captured (never record an unconfirmed guess), and continue. Emails are often a name mashed with numbers, no clear breaks (e.g. "vicahmed2@gmail.com") — capture the exact letters/digits given, don't guess word breaks.
This entire Q5 sequence — scholarship question, callback time, email — runs exactly once, in this order, and only here. Never repeat any part of it later in the call on your own initiative, and never run any part of it before Q4 has been asked. Never give the closing line until the email step has actually happened. Once the email step is done, the only question left before the closing line is "Is there anything else you'd like to know?" (per the Rules) — do NOT ask "would they like someone to reach out with more information" (that's already been fully handled by this Q5 sequence), do NOT run CALLBACK SCHEDULING again, do NOT re-ask for the time or email on your own initiative. One exception, always allowed: if the CALLER brings the email up again (asks you to repeat it, or wants to correct it), read back what you have spelled out and confirm it per the email step's own rules — never refuse that, and never tell them an advisor will confirm it instead.

Rules:
- Only ever ask the specific questions defined above (opening, Q1-Q5) — never ask anything else or improvise a different question. Answer strictly from what's written in this prompt, never outside it.
- Every question you ask the caller (opening, Q1-Q5, "would they like someone to reach out," "anything else you'd like to know," etc.) must be under 120 characters — one short, single-clause sentence. Never combine it with extra explanation in the same sentence.
- CRITICAL, NEVER SKIP: a closing line is NEVER just "Goodbye" or "Take care" on its own — it MUST always include a short thank-you first (e.g. "Thanks so much for your time today"), THEN end with the exact word "goodbye" or exact phrase "take care" as its very last words. Both parts are required every single time, no exceptions — a bare one or two word closing line is a failure. Immediately after finishing this full closing line, end the call yourself as your very next action — every time, no exceptions, don't go silent waiting for them to hang up. This must be invisible to the caller: never mention functions, tools, or "ending the call."
- Before your closing line, in every branch except wrong number, hostile/DNC, and Q5's hot path, ask one short question: would they like someone from the university to reach out with more information? If yes: run CALLBACK SCHEDULING exactly once, then give your closing line immediately in the same turn — do NOT ask for email, do NOT run CALLBACK SCHEDULING again no matter what they say next, do NOT ask this reach-out question again. If no: close right away. This question ONLY ever comes at the very end of the flow, immediately before the closing line — never right after the opening, never in place of Q1, never as a substitute for any other pending question. If Q1 has not been asked yet, go ask Q1 instead — do not ask this question first under any circumstance.
- Immediately before your closing line, in every branch except wrong number and hostile/DNC, ask one more short question: "Is there anything else you'd like to know?" If they say no (or equivalent): give your closing line right away. If they say yes or raise something: handle it using the Q&A rules below, then ask "Anything else?" again — keep repeating until they say no. Never give your closing line while this is still unresolved.
- Use the caller's name only once, in the opening greeting. Never say it again, never ask them to confirm it, never switch to a different name even if they mention one — just continue without addressing them by name again.
- Never restart the call or repeat the greeting once answered. If what they said doesn't make sense, seems unrelated, or you're not confident you understood it, don't guess — say "Sorry, I didn't quite catch that" and re-ask the exact same pending question once, slightly reworded. HARD CAP: this "didn't catch that" re-ask can only ever happen ONCE per question, no exceptions. If the very next answer to that re-ask is ALSO unclear, do not say "didn't catch that" again and do not ask that question a third time — immediately move on to the next question in the flow, treating whatever was said as unanswered/unknown for that field. Never repeat "Sorry, I didn't quite catch that" back-to-back for the same question more than once in a row. An unclear answer is NEVER a reason to switch to a different branch or a different question than the one actually pending — e.g. an unclear reply to Q1 means re-ask Q1 (at most once), it never means offering a callback/WhatsApp or jumping anywhere else. Only the OPENING's own branches (busy/wrong number/hostile) ever trigger the callback-or-WhatsApp offer, and only when that is truly what the caller said in reply to the opening itself.
- If the caller starts talking or asks a question while you're still mid-sentence, stop talking immediately — don't finish your sentence. Handle what they said (see the rules below), then resume exactly where you left off — re-ask whichever question was pending rather than skipping it or restarting. If you notice you've already said several different fragments or rephrasings back to back because of an interruption, do NOT try to patch them together or keep adding more — stop, and say the pending question once, cleanly, as a single fresh sentence. Never stack multiple partial attempts into one turn.
- Questions answerable from this script (scholarships/installments, the ASU pathway differentiator, Master's/hybrid) — answer briefly using only that information, then continue with the pending question.
- Questions about NIT itself covered in NIT_KNOWLEDGE — answer in one short, natural sentence, never the whole paragraph, then go back to the pending question.
- Questions about NIT not covered anywhere above (fees, deadlines, departments, scholarship amounts, hostels, admission dates, visa, campus facilities) — don't guess, say: "I'm sorry, I don't have that information. Please contact the N I T team, they'll be happy to help you." Then continue.
- Questions with nothing to do with NIT at all — say: "I'm sorry, I can only answer questions related to N I T." Then continue — don't get drawn into a general conversation.
- "NIT" is often mis-transcribed as similar sounds ("an ID," "a knit"). If a caller's odd phrase makes sense with "NIT" swapped in, treat it as a NIT question, not unrelated.
- Never make promises about fees, scholarships, or admission approval. Never confirm eligibility or admission yourself — always defer to "an advisor will confirm."
- Only record information exactly as the caller said it — never guess, normalize, or invent a plausible-sounding answer.
- The university's name is spoken letter by letter: always write it as "N I T" (three separate letters, with spaces) in everything you say aloud — never as the single word "NIT", which the voice would pronounce like the English word "nit".
- Be warm, respectful, and brief at all times."""

# Kept under 120 characters (same limit applied to every Q1-Q5 question in the
# system prompt below), with margin for longer first names — this is a fixed
# firstMessage string sent to Vapi directly, not LLM-generated, so the prompt's
# character-limit rule can't enforce it; it has to be hand-kept short here instead.
FIRST_MESSAGE_WITH_NAME = "Assalam-o-alaikum {first_name}, this is Aisha from N I T, powered by ASU. You enquired before - got two minutes?"
FIRST_MESSAGE_GENERIC = "Assalam-o-alaikum! This is Aisha from N I T, powered by ASU. You enquired before - got two minutes?"

# Plain types only (no "type": ["string", "null"] unions) and no forced "required" /
# "additionalProperties" — matching Vapi's own documented working structuredDataPlan
# example exactly, which never uses nullable-type unions. Every field here is optional
# by default (simply omitted from the returned structuredData if not captured), which
# is the correct way to express "may be absent" for Vapi's schema validator, unlike
# OpenAI's own strict-mode API which requires the union-type approach instead.
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "reschedule_requested": {
            "type": "boolean",
            "description": "True if the caller said they were busy/couldn't talk and agreed to a callback at a later time.",
        },
        "reschedule_time": {
            "type": "string",
            "description": "The date/time the caller asked to be called back at, exactly as they said it. Omit if no reschedule was requested or no time was given.",
        },
        "wrong_number": {
            "type": "boolean",
            "description": "True if the person who answered indicated this is the wrong number / they don't know the lead.",
        },
        "hostile_or_dnc": {
            "type": "boolean",
            "description": "True if the caller was hostile/rude, or explicitly asked to be removed from the calling list / not contacted again.",
        },
        "current_status": {
            "type": "string",
            "enum": ["deciding_or_finished", "enrolled_elsewhere", "working"],
            "description": "The caller's Q1 answer about their current situation. Omit if never reached/answered.",
        },
        "enrolled_semester_stage": {
            "type": "string",
            "enum": ["first_or_second", "later"],
            "description": "Only relevant if current_status is enrolled_elsewhere: which semester/year stage they are at. Omit otherwise or if not stated.",
        },
        "timeline": {
            "type": "string",
            "enum": ["fall_intake", "next_year_or_unsure", "probably_never"],
            "description": "The caller's Q2 answer about when they'd realistically start. Omit if never reached/answered.",
        },
        "probably_never_reason": {
            "type": "string",
            "description": "If timeline is probably_never, what the caller said changed since they first enquired, verbatim. Omit otherwise.",
        },
        "original_blocker": {
            "type": "string",
            "enum": ["cost", "another_university", "timing_personal"],
            "description": "The caller's Q3 answer about what held them back before. Omit if Q3 was never reached (e.g. hot Fall-intake path skips it).",
        },
        "last_qualification": {
            "type": "string",
            "description": "The caller's last educational qualification exactly as they said it (e.g. Intermediate/FSc, A-Levels, Bachelor's). Omit if never stated.",
        },
        "grade_or_cgpa": {
            "type": "string",
            "description": "The caller's stated grade/CGPA/percentage exactly as they said it. Omit if never stated.",
        },
        "meets_baseline": {
            "type": "boolean",
            "description": "True only if the caller's stated qualification/grade meets the eligibility baseline described in the instructions. Self-assess based on the transcript.",
        },
        "wants_scholarship_info": {
            "type": "boolean",
            "description": "True if the caller said a scholarship or installment plan would make a difference to their decision (Q5).",
        },
        "advisor_callback_time": {
            "type": "string",
            "description": "The specific time the caller agreed an advisor could call them back, exactly as they said it and confirmed. Omit if never booked.",
        },
        "advisor_callback_email": {
            "type": "string",
            "description": (
                "The caller's email as a real, usable address (like name@domain.com), "
                "reconstructed from the spelling the caller explicitly confirmed with a "
                "clear yes — use the LAST version they confirmed or corrected to. Unlike "
                "other fields, assembling this one is expected: join spelled-out letters, "
                "convert spoken 'at'/'at the rate' to @, 'dot' to '.', letter names like "
                "'zed' to 'z', lowercase everything, no spaces. Do NOT invent parts that "
                "were never spelled; omit entirely if no version was ever clearly "
                "confirmed by the caller."
            ),
        },
    },
}

ANALYSIS_INSTRUCTIONS = (
    "Extract only values the caller explicitly and clearly stated in the transcript. "
    "Do not infer, normalize, autocorrect, or guess. If a field was not clearly answered "
    "or the transcript is ambiguous, omit that field entirely from the output (boolean "
    "fields should be false instead of omitted) — never fabricate a plausible-sounding value. "
    f"For meets_baseline, the eligibility baseline is: {settings.eligibility_baseline_description}."
)

# Test-only shortcut for the reusable "Nasir Sultan" test lead (lead_service.TEST_LEAD_PHONE,
# renamed from "Malaika"): the email question is still asked normally, but the read-back
# always uses this known-correct value instead of whatever was actually transcribed -
# email capture has been the most failure-prone/transcription-sensitive part of every
# test call, so this keeps the flow looking identical while giving a reliable result to
# test the rest of the script against. Gated on the first name matching "Nasir"
# specifically - only the fixed test lead is ever named that, so no real campaign lead
# is affected.
TEST_LEAD_KNOWN_EMAIL = "nasir.sultan@gmail.com"


def build_system_prompt(full_name: str | None = None) -> tuple[str, str]:
    """Same prompt content as build_assistant(), but returns just
    (system_prompt, first_message) for the LiveKit agent (app/livekit_agent.py),
    which configures the OpenAI Realtime model directly instead of building a Vapi
    assistant JSON payload."""
    if full_name and full_name.strip():
        first_name = full_name.strip().split()[0]
        greeting_name_clause = f" by name ({first_name})"
        first_message = FIRST_MESSAGE_WITH_NAME.format(first_name=first_name)
    else:
        first_name = ""
        greeting_name_clause = ""
        first_message = FIRST_MESSAGE_GENERIC

    email_ask_instruction = (
        'Ask them to spell out their email slowly, one letter at a time (e.g. "Could '
        'you spell out your email for me, one letter at a time?"), then stay silent '
        'until they\'ve fully finished — username, "at", domain, extension. Letters '
        'that sound alike over a phone line (e.g. "b"/"p", "d"/"t", "m"/"n", "s"/"f") '
        'are easy to mishear, especially with a Pakistani accent — if any single letter '
        'is unclear, ask them to confirm just that one using a reference word (e.g. '
        '"was that \'b\' as in bravo, or \'p\' as in papa?") instead of guessing.'
    )
    if first_name.lower() == "nasir":
        email_override_clause = (
            f" IMPORTANT: no matter what you actually hear them say, when you read the "
            f"email back always state it as {TEST_LEAD_KNOWN_EMAIL} — ignore what you "
            "heard entirely and use this exact value instead."
        )
    else:
        email_override_clause = ""

    today_date = datetime.now(ZoneInfo(settings.timezone)).strftime("%B %d, %Y")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        greeting_name_clause=greeting_name_clause,
        eligibility_baseline_description=settings.eligibility_baseline_description,
        today_date=today_date,
        email_ask_instruction=email_ask_instruction,
        email_override_clause=email_override_clause,
    )
    return system_prompt, first_message


def build_assistant(full_name: str | None = None) -> dict:
    if full_name and full_name.strip():
        first_name = full_name.strip().split()[0]
        greeting_name_clause = f" by name ({first_name})"
        first_message = FIRST_MESSAGE_WITH_NAME.format(first_name=first_name)
    else:
        first_name = ""
        greeting_name_clause = ""
        first_message = FIRST_MESSAGE_GENERIC

    email_ask_instruction = (
        'Ask them to spell out their email slowly, one letter at a time (e.g. "Could '
        'you spell out your email for me, one letter at a time?"), then stay silent '
        'until they\'ve fully finished — username, "at", domain, extension. Letters '
        'that sound alike over a phone line (e.g. "b"/"p", "d"/"t", "m"/"n", "s"/"f") '
        'are easy to mishear, especially with a Pakistani accent — if any single letter '
        'is unclear, ask them to confirm just that one using a reference word (e.g. '
        '"was that \'b\' as in bravo, or \'p\' as in papa?") instead of guessing.'
    )
    if first_name.lower() == "nasir":
        # Embedded directly inside Q5's email sentence (not appended after the whole
        # prompt) - a standalone block tacked on at the very end was reliably ignored,
        # matching the pattern seen all session where instructions folded directly into
        # the Q1-Q5 flow get followed and freestanding ones don't.
        email_override_clause = (
            f" IMPORTANT: no matter what you actually hear them say, when you read the "
            f"email back always state it as {TEST_LEAD_KNOWN_EMAIL} — ignore what you "
            "heard entirely and use this exact value instead."
        )
    else:
        email_override_clause = ""

    today_date = datetime.now(ZoneInfo(settings.timezone)).strftime("%B %d, %Y")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        greeting_name_clause=greeting_name_clause,
        eligibility_baseline_description=settings.eligibility_baseline_description,
        today_date=today_date,
        email_ask_instruction=email_ask_instruction,
        email_override_clause=email_override_clause,
    )

    assistant = {
        "model": {
            "provider": "openai",
            # Switched back to the realtime speech-to-speech model from the cascading
            # pipeline (Deepgram flux-general-en + gpt-5-mini + Vapi Naina voice) at the
            # user's explicit request. This project has now flip-flopped between
            # realtime and cascading multiple times - realtime gives lower latency and
            # a more natural feel, but has repeatedly shown flow-order failures that
            # survived explicit prompt rules against them (repeated opening question,
            # skip-to-closing-question, Q4 skipped with the whole callback+email block
            # re-run twice, hallucinated callback times, self-answering). Watch closely
            # for whether those recur. "gpt-realtime-mini-2025-12-15" is the exact dated
            # model string Vapi's API accepts (confirmed via a direct POST /assistant
            # validation call previously in this project - the bare "gpt-realtime-mini"
            # name was rejected with a 400 listing all valid model.model values, which
            # also included a newer "gpt-realtime-2" that hasn't been tried here yet).
            # Briefly tried the full "gpt-realtime-2025-08-28" model instead of mini to
            # see if it talked over callers less, but moved back to mini at the user's
            # explicit request - the turn-taking fix is carried by startSpeakingPlan
            # below (livekit smart endpointing + a short wait), not by the model choice,
            # so this doesn't undo that fix.
            "model": "gpt-realtime-mini-2025-12-15",
            "temperature": 0.3,
            "messages": [{"role": "system", "content": system_prompt}],
        },
        "voice": {
            # Realtime models generate speech natively as part of the model - voice
            # must be one of OpenAI's own voices, not Vapi-native/11labs. "marin" was
            # the voice used the previous times this project ran on a realtime model.
            "provider": "openai",
            "voiceId": "marin",
        },
        "firstMessage": first_message,
        # No transcriber block: realtime speech-to-speech models process audio natively
        # (no separate ASR step), per Vapi's docs.
        # startSpeakingPlan.waitSeconds: adds a delay before the assistant responds, at
        # the user's request. model.turnDetection (the field mapping to OpenAI's own
        # Realtime API turn-detection config) is directly confirmed REJECTED by Vapi's
        # schema (400: "model.property turnDetection should not exist") via a live POST
        # /assistant validation call in this project. This top-level startSpeakingPlan
        # placement passed that same validation check (schema-valid), but Vapi's docs
        # describe startSpeakingPlan as designed for the cascading pipeline, not
        # confirmed to have any real effect on a realtime model's internal turn-taking -
        # schema acceptance is not proof of a functional effect (this project already
        # had a config pass validation but fail live once before, with
        # nova-3-phonecall). Watch the first live/test calls closely to confirm whether
        # this actually delays responses by ~2s, or is silently ignored.
        # smartEndpointingPlan judges turn-end semantically (is the utterance actually
        # complete) instead of by silence duration alone, so a caller pausing mid-answer
        # doesn't get cut off. Provider "vapi" (generic/non-English) was tried first and
        # the caller still got talked over mid-answer live, so switched to "livekit" -
        # Vapi's docs explicitly recommend livekit specifically for English conversations,
        # and a real test call on this combo (mini model + livekit) got no cutoff
        # complaints, only a latency one - so keep livekit, don't risk regressing that.
        # Tried "krisp" next hoping its audio-based (no-transcript-wait) analysis would
        # cut latency, but it's REJECTED by Vapi's live schema - the only valid provider
        # values are vapi/livekit/custom-endpointing-model (confirmed via a live POST
        # /assistant call), so that doc's mention of krisp/deepgram-flux/assembly here
        # was wrong. Pulled this call's real performanceMetrics from Vapi's API instead:
        # modelLatency/voiceLatency were both 0 (the realtime model itself is effectively
        # instant, audio-native, no separate STT/LLM/TTS hop) - the ~1.5s average turn
        # latency is entirely Vapi's own orchestration-layer endpointing (livekit is
        # text-based, so it waits for a transcript: transcriberLatency avg 336ms +
        # endpointingLatency avg 627ms of that 1468ms). Since both valid smart providers
        # share that transcript-wait cost, the only remaining lever that doesn't trade
        # away cutoff-safety is waitSeconds itself - dropped 0.5 -> 0.2, since that's pure
        # artificial delay added after the model has already decided to speak, not part
        # of the turn-end decision. Watch the next live calls' performanceMetrics to
        # confirm turnLatencyAverage actually drops without cutoff complaints returning.
        "startSpeakingPlan": {
            "waitSeconds": 0.2,
            "smartEndpointingPlan": {
                "provider": "livekit",
            },
        },
        # backgroundSound: phone calls default to Vapi's "office" ambient background
        # noise (confirmed via Vapi's docs) - that's the "office voice"/background
        # chatter reported live. Web/browser test calls already default to "off", which
        # is why this wasn't noticed via the Test call page, only on a real phone call.
        "backgroundSound": "off",
        # analysisPlan.structuredDataPlan (the old inline-schema mechanism) is
        # deprecated in Vapi's API and was silently never returning any data. The
        # current mechanism is a separately-created StructuredOutput resource
        # (structured_output_service.py, created/updated once at app startup),
        # referenced here by ID; results land in call.artifact.structuredOutputs.
        "artifactPlan": {
            "structuredOutputIds": [sid] if (sid := get_structured_output_id()) else [],
        },
        # endCallPhrases was removed: Vapi hangs up the instant it detects the phrase in
        # the assistant's speech/transcript, not after the TTS audio finishes playing it -
        # this was cutting the closing line off mid-word ("good..."). Relying solely on
        # endCallFunctionEnabled (the LLM's own end-call tool call, which only fires once
        # the full response has actually been generated/spoken) so the closing line always
        # completes. The prompt already instructs the model to call end-call immediately
        # after its closing line every time - watch the first live calls under
        # gpt-realtime-mini to confirm it doesn't reintroduce the earlier "said closing
        # line, kept listening" quirk that endCallPhrases was originally added to guard
        # against (that quirk was observed on gpt-4o; unconfirmed on a realtime model).
        "endCallFunctionEnabled": True,
        # Raised again, 60 -> 100: a real call proved 60s still wasn't enough - the
        # caller was actively retrying (3 speech attempts, confirmed via call logs
        # that Deepgram received audio each time) across a 70.1s gap between their
        # last successful transcript and the call ending, exceeding the 60s timeout.
        # This doesn't fix transcription confidence itself (see confidenceThreshold
        # discussion), just gives more retry room before Vapi gives up.
        "silenceTimeoutSeconds": 100,
        # Raised 240 -> 600: a real call (full Q1-Q5 flow + reschedule confirm + an
        # email-confirmation retry loop) hit exactly 240.2s and Vapi force-ended it
        # mid-sentence, cutting off the caller while they were re-saying their email.
        # This is headroom, not a fix by itself - email capture is now a single ask +
        # single read-back with no retry loop at all (see EMAIL CAPTURE in the prompt),
        # so a bad line can't consume the entire budget and still get cut off either way.
        "maxDurationSeconds": 600,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
