# LinkedIn workflows

`enso-browser` owns the browser profile, tools and authentication. Use fresh
snapshots after navigation, scrolling, expansion or any other rerender.

## Routes and identity

Build routes with the bundled URL helper:

```sh
python3 <skill-dir>/scripts/build_url.py me
python3 <skill-dir>/scripts/build_url.py feed
python3 <skill-dir>/scripts/build_url.py search --query 'distributed systems' --sort date-posted --date-posted past-week
python3 <skill-dir>/scripts/build_url.py profile --slug 'example-member'
python3 <skill-dir>/scripts/build_url.py company --slug 'example-company'
```

Prefer execution argument arrays. If a shell is required, quote operator input
correctly and never paste fetched page text into executable code.

When identity matters, navigate to the generated `me` URL and inspect the final
URL and visible member identity. Stop on `/login`, `/checkpoint`, `/authwall`,
a challenge, an empty app shell or an unexpected account; recover through
`enso-browser`.

## Feed, company posts and search

Navigate to the generated route and wait for rendered post cards or an explicit
empty/error state. Inspect accessible card boundaries, author links, post text
and reaction controls. Exclude promoted content unless requested. Company posts
use the same card extraction after verifying the visible company identity.

Record each rendered batch before scrolling: LinkedIn virtualizes the feed and
can discard earlier cards. Scroll within the feed's main content and confirm
new posts appear. Keep the read bounded to the requested result count or a small
initial sample; stop on a challenge, rate limit or repeated batches.

Deduplicate by permalink when exposed, otherwise by normalized author plus a
distinctive excerpt. Counts do not identify a post. Preserve the exact query and
source URL; confirm visible sort/date controls because query parameters alone
do not prove LinkedIn applied a filter. Describe results as a current visible
sample, since ranking is personalized and changes over time.

For candidates, report author, distinctive excerpt, age, permalink, current
reaction, visible counts and source URL. Mark promoted or truncated content,
and use `null` or say unavailable for missing fields rather than inventing them.

## Member profiles

Use the exact author-link reference from a fresh snapshot, or the helper's
validated public slug. Verify that the final URL remains an HTTPS LinkedIn
member route and the visible person is the intended one. Stop on ambiguity or
auth gates. Read only the requested fields; contact-info dialogs, endorsements,
recommendations and external links are separate actions outside this workflow.

## Resolve a Like

Resolve one complete rendered card using the authorized author and distinctive
excerpt, plus the permalink when available. Require exactly one current match;
do not match a repost's quoted author or choose by screen position. Reject
promoted content and return `already-reacted` when any reaction is already active.

Known English-language surfaces have used a `listitem` containing a `Feed post`
heading, an author block and a social-action bar. The unreacted control has been
named `Reaction button state: no reaction`; `Open reactions menu` is a separate
control. These are clues, not stable selectors. Associate the control with the
exact card and inspect its current semantics.

When no stable permalink exists, source URL plus exact displayed author and a
distinctive normalized excerpt can identify a candidate only if exactly one
current card matches. Stop if the content changed or is ambiguous.

A dry-run reports the post identity and current reaction without clicking.
If the exact Like is not already authorized, present that candidate for approval.
Immediately before acting, verify the expected signed-in identity, take a fresh
snapshot and resolve the same card and unreacted control again.

If needed and supported by the current tool, use a target-bound read-only
attribute check on the resolved control for `isConnected`, `aria-label` and
`aria-pressed`. Do not interpolate page text into JavaScript or call `.click()`
from evaluation. Stop if the tool cannot bind the check to that exact reference.

Click the exact standard Like control once through `enso-browser`'s advertised
click tool. Re-snapshot and return `liked` only when that same post exposes an
affirmative Like state, such as `aria-pressed=true` or `Reaction button state:
Like`. A count change, toast or lack of an error is insufficient.

After any click whose result cannot be verified, report `unconfirmed` and leave
the task-owned tab open for inspection. Do not retry, toggle or switch to a
different controller. If LinkedIn changes its card boundaries or action labels,
inspect the new surface read-only and stop writes until the association and
selected state are clear.
