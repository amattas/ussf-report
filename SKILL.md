---
name: ussf-report
description: Help a soccer referee write a factual, neutral USSF-style supplemental report (send-offs, team official misconduct, injuries, abandonments, unusual incidents). Interviews the referee, drafts in report tone, turns photos of hand sketches into field diagrams, and outputs PDF, Word, and plain text for app submission.
---

# USSF supplemental referee report

Walks a referee through what happened, writes a neutral factual report, and delivers:

1. A PDF and .docx per report, on the template in `assets/supplemental-template.docx`
2. One combined plain-text version of every report from the match, for pasting into a league app or web form
3. Field diagrams redrawn from photos of the referee's paper sketches

All paths below are relative to this skill's folder (the folder containing this SKILL.md).

## Step 1: Interview

Don't draft from the first message. Walk the referee through the incident using `references/interview.md`:

- Match details once, then one incident at a time, 3 to 5 questions per message
- Start open, then fill gaps from the checklist for that incident type
- Turn judgments into observable facts ("what did she say, word for word?")
- Note who saw what; never fill a gap with a guess
- If they share a timing-app screenshot (RefSix or similar), read minutes and card codes from it and check for cards logged to the wrong team

Before drafting, play back a short bullet summary of the facts per incident and ask: "Anything wrong or missing? Anything here you didn't see or hear yourself?"

## Step 2: Draft in report tone

Follow `references/writing-standards.md`: first person, past tense, actions not labels, exact quotes, every observation attributed, no opinions, intent, hypotheticals, or self-defense. Run its tone check on the draft, then show the draft in chat and get the referee's corrections before building any files.

If the referee attaches a previous report, match its section labels and order.

## Step 3: Diagrams

One diagram per on-field incident where position matters (fouls, offside-related misconduct, injuries, someone entering the field). Verbal dissent from the technical area usually needs none.

1. Share `assets/sketch-guide.png` and tell the referee: copy the half-field on paper, write whose goal is at the top, mark the AR's touchline, dot and label everyone involved, add arrows for ball, contact, and paths, then take one photo per incident, straight on. `assets/example-diagram.png` shows what the finished diagram looks like.
2. Read each photo. Keep the goal where they drew it (`goal_at_top`). Map positions to the canvas: touchlines x=90 and x=650, goal line and halfway line at y=70 and y=610, penalty area 300 wide by 150 deep centred at x=370. Place markers relative to the penalty area and touchlines as drawn.
3. Markers: `lex` solid circle = offender (number); `opp` outline circle = opponent (team initials); `ref` diamond; `ar` box ("AR1"/"AR2", name as a `text` label beneath, outside the touchline near x=46 or x=700); `coach` box; `other` grey dot = players blocking the view; `ball`; `arrow`; `sight` dashed line of sight; `text`.
4. Draw only what they drew or what the report states. Label a goal only when the report establishes whose it is. Ask about anything ambiguous instead of guessing.
5. Render, look at every PNG, move labels off lines and markers, and show the referee before building the report.

## Step 4: Build

Write a spec JSON in a working folder, starting from `examples/spec.example.json` (it documents every field), then run:

```bash
python3 scripts/draw.py spec spec.json diag/
python3 scripts/build_report.py spec.json assets/supplemental-template.docx diag/ out/
```

`draw.py` needs Playwright with Chromium, or `pip install cairosvg` as a fallback. `build_report.py` needs LibreOffice (`soffice`) for the PDF; without it you still get the .docx and the text file.

Spec notes: use "Player:" or "Team Official:" as the first subject line, then "Misconduct:". Sections with no label continue the previous incident. Add a `timing` string when logged minutes could look odd, for example: "30-minute halves. The first half ran 32 minutes and the second half ran 31 minutes. Minutes in this report are as logged in RefSix, which uses a running clock and started the second half at 35'."

Check every page of every PDF: logo and header present, nothing cut off, each diagram under the right paragraph. Fix and rebuild until clean.

## Step 5: Deliver

- Share each PDF and .docx, and `out/<game>_app.txt`. Also paste the app text in a plain code block so it copies cleanly on a phone. If it's over about 4,000 characters, mention it may need to be split at the dashed line.
- Before submission, remind the referee once to make sure the minutes and cards match what they entered in the official match report.

## Step 6: Submission

Ask which league or competition the match was in, then look up its reporting instructions if you can. Common patterns:

- The league's match app or report form, plus an email to the league or competition office. Copy the assignor, but when the report concerns the club that assigned the referee, send it to the league directly as well.
- US Club Soccer-sanctioned competitions: incident reports are due within 48 hours (US Club Soccer Policy 9.06(c)). Check the current policy manual and the league's own rules for a different deadline or format.
- Referee assault or abuse goes through a separate, faster process with the state association or sanctioning body. Tell the referee to contact the assignor today.
- If an AR's observation supports a caution, the AR should file their own supplemental report. Any official named in the report should get a heads-up.
