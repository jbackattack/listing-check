# Roadmap

This is the checklist for building a first working version and then taking it to one where nearly all routine checks and low-risk fixes run on their own. It is a plan, not built.

**v1 means:** Connected to real MLS data read-only for one MLS and one or two sites, with the 15-minute run and the nightly sweep, the persistent-mismatch rule, Slack alerts, an audit log, and people fixing problems by hand.

**What nearly autonomous means here.** The aim is that routine checking, explaining and low-risk fixing run without a person, and people spend their time on exceptions and judgment calls. It does not mean no people. Each stage should be earned with measured results before the next starts. The agentic stage (F) is optional and only worth doing if the problem needs open-ended investigation.

## V1. Build the first working version

- [ ] Get written permission from Legal and the MLS for the data you will read, store and show. *Done when: Written approval, and a rule for where the data may live.*
- [ ] Pick the first MLS, one or two sites and a small set of listings. Agree the success measures with the Director. *Done when: A written scope and success measures.*
- [ ] Get read-only credentials and keep them in a secrets store, not in code. *Done when: The credentials work and none are in the repo.*
- [ ] Keep the tests and the demo on made-up data. Real data never goes in the repo or the public logs. *Done when: Checked before each push.*
- [ ] Build the MLS source adapter (the RESO Web API where the MLS offers it). Map fields and statuses from that MLS's own documentation. *Done when: Real records come back in the shape the validator uses, and the mapping is checked against the documentation.*
- [ ] Build a site adapter for the first site: its API if it has one, otherwise the public page within its terms and rate limits. *Done when: It returns what the site shows, in the validator's shape.*
- [ ] Move that MLS's rules into a config file: field mapping, status words, required fields. *Done when: The first MLS runs from config, not code.*
- [ ] Run read-only on a few listings and check every finding by hand. Fix the rules and count false alarms. *Done when: Findings match what a person sees.*
- [ ] Run beside the manual process for a few weeks. *Done when: Side-by-side results written down.*
- [ ] Make an empty or failed feed report 'no data' with one alert. *Done when: Tested with a simulated outage.*
- [ ] Add memory between runs for the persistent-mismatch rule. *Done when: A difference seen on two runs becomes a finding, and a test proves it.*
- [ ] Schedule the 15-minute run (changed listings plus open rechecks, critical fields every run, no overlapping runs) and the nightly sweep on an internal scheduler. *Done when: Both run on their own and the logs show it.*
- [ ] Add Slack alerts: route by severity, one thread per listing, no repeats, a daily summary for medium and low. Keep the webhook in the secrets store. *Done when: A test critical finding shows up in Slack with the right details.*
- [ ] Add run logging and a health check: run time, listings checked, errors, last successful run. *Done when: Someone is alerted if a run does not happen.*
- [ ] Keep seller personal details out of logs and reports, set how long logs are kept, and take extra care with hidden-address listings. *Done when: Reviewed by Privacy and Security.*
- [ ] Name an owner for alerts and an escalation path for a critical alert nobody acknowledges. *Done when: The owner and the escalation time are written down.*
- [ ] Create a ticket for each high and critical finding and confirm the fix by running the check again. *Done when: Closed means the check passes again.*
- [ ] Document how it works, how to add an MLS, how to read a finding, and known issues. *Done when: A new teammate can run it.*
- [ ] Review with the Director and Legal and decide whether to turn it on for real. *Done when: A go or no-go decision on record.*

## A. Stabilize v1

- [ ] Measure a baseline before and after: manual time, problems caught and missed, time to detect, time to fix. *Done when: Numbers written down from a few weeks of manual checking.*
- [ ] Track the false alarm rate and the missed-problem rate every week. *Done when: A weekly number the team reviews.*
- [ ] Measure sync time per site and set the recheck window per site. *Done when: Each site has its own window, set from measured data.*
- [ ] Write a runbook for each alert type and name an owner. *Done when: Every alert type has a next step and an owner.*
- [ ] Prove the failure cases: feed down, API limits, bad data, overlapping runs. *Done when: Each case has a test and a behavior that is never 'all clear.'*
- [ ] Build a labeled set of real cases from reviewed alerts, with approval to use the data. *Done when: A set the team agrees is correct.*

## B. Widen coverage

- [ ] Add fields: photos, open houses, price history, showing instructions. *Done when: Each one has rules and tests.*
- [ ] Add more sites, then more MLSs, through config and not code. *Done when: A new MLS needs only a config file and tests.*
- [ ] Keep a change log of rule changes per MLS. *Done when: Every rule change has a date, a reason and an owner.*
- [ ] Generate a scenario library from requirements (AI step 1) and have a person review it. *Done when: A coverage map by brand, market, MLS rule set, listing status and seller instruction.*

## C. Add AI judgment

- [ ] Compare description text to MLS remarks, using a labeled test set. *Done when: An accuracy target the team agreed on is met on the test set.*
- [ ] Add plain-language explanations and grouping of findings. *Done when: Reviewers rate most of them as useful.*
- [ ] Score root-cause guesses against what engineering found. *Done when: A hit rate is tracked.*
- [ ] Draft rules and SOP updates from MLS documents, with approval. *Done when: A person approves every draft.*
- [ ] Version the prompts and re-run the tests on every change. Track cost and speed. *Done when: No change ships without passing the test set.*

## D. Suggest-then-approve fixes

- [ ] Build a fix catalog from the runbook: preconditions, action, verification, rollback. *Done when: One page per fix type.*
- [ ] Add a dry run and Approve / Reject buttons in Slack. *Done when: Every proposed fix shows its evidence and the exact change.*
- [ ] Track approval rate, rejection reasons and failed-fix rate. *Done when: Reviewed every week.*
- [ ] Run this way for several weeks before moving on. *Done when: Approval and failure rates the team agrees are good enough.*

## E. Autonomy for low-risk fixes

- [ ] Get Legal, Compliance, Privacy and Security sign-off and a sanctioned way to write. *Done when: Written approval.*
- [ ] Add the controls: allowed list, hourly limit, kill switch, re-check after each fix, roll back on failure, stop after two failures. *Done when: Each control is tested.*
- [ ] Start with one fix type on one site. *Done when: It runs on its own and every action is logged.*
- [ ] Review everything it did on its own, every week. *Done when: No unexplained changes.*
- [ ] Add fix types one at a time. *Done when: Each one earns its place with a track record.*

## F. Agentic investigation (only if needed)

- [ ] Give it read-only tools with a step limit and a log of every tool call. *Done when: A tool allowlist and logs are in place.*
- [ ] Test it on labeled cases and compare it with how a person triages. *Done when: It matches or beats human triage on the test set.*
- [ ] Add tools only after a track record. *Done when: Each new tool is reviewed.*

## G. Run it as a team process

- [ ] Train support, brand and operations teams: walkthroughs, quick-reference guides, office hours. *Done when: Teams know what an alert means and who acts on it.*
- [ ] Retire manual steps cleanly and name who reviews exceptions. *Done when: The old process is removed and owners are named.*
- [ ] Track adoption and feedback until the new way sticks. *Done when: Usage and feedback are reviewed.*
- [ ] Report the impact: hours returned, error rates, turnaround time. *Done when: Reported to the Director.*
- [ ] Review every quarter: false alarms, rule drift, new MLS rule changes. *Done when: The review is on the calendar.*
- [ ] Document every automation: what it does, inputs, limits, owner. *Done when: Anyone can audit it.*

## What stays with people, at every stage

- People review exceptions.
- The MLS record is never edited by the tool. If the MLS entry looks wrong, it alerts the listing agent or data owner.
- Price, status and address are never typed in as new values by the tool.
- Anything tied to seller privacy or Fair Housing stays with a person until Legal agrees.
- An empty or failed feed is an alert, never an all clear.
