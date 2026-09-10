# X workflows

`enso-browser` owns the browser profile, tools and authentication. Use fresh
snapshots after navigation, scrolling, expansion or any other rerender.

## Routes and identity

```sh
python3 <skill-dir>/scripts/build_url.py home
python3 <skill-dir>/scripts/build_url.py search --query 'opensource OR "node.js" -filter:replies' --tab latest
python3 <skill-dir>/scripts/build_url.py search --query 'from:example min_faves:5' --tab top
python3 <skill-dir>/scripts/build_url.py profile --handle '@example'
python3 <skill-dir>/scripts/build_url.py status --handle '@example' --status-id '123'
python3 <skill-dir>/scripts/build_url.py validate-status-url --url 'https://x.com/example/status/123'
```

The validator accepts a clean `https://x.com/<handle>/status/<positive-uint64>`
permalink. It rejects other hosts, ports, credentials, tracking queries,
fragments, extra or encoded path segments, reserved routes and malformed IDs.
When a copied link includes tracking data, inspect its destination, build a
clean URL from the known handle and ID, then validate it before use.

The search builder preserves operators and quoted phrases while rejecting
control characters and excessive input. Prefer argument arrays; if a shell is
required, quote operator input correctly and never paste page text into code.

Navigate to home for the authentication gate. Verify the final route and visible
account-menu handle when identity matters. Stop on login, onboarding, challenge,
an empty app shell or the wrong account, and recover through `enso-browser`.

## Read posts

Wait for rendered articles or an explicit empty/error state. The primary author
and linked time commonly identify the article's own canonical post; a nested
quote has its own author, text and permalink. Keep those separate. Do not use a
quoted post's ID to identify its enclosing article.

Capture each rendered batch before scrolling because X virtualizes timelines.
For each post preserve its own ID and canonical URL, author and handle, visible
timestamp and text, nested quote data, current Like state, visible metrics,
truncation/promoted flags and source URL. Missing values stay unavailable, not
zero. Preserve compact counts such as `1.2K` as display strings unless an exact
number is exposed.

- Home: confirm the selected For you or Following view when requested.
- Search: confirm the visible Top or Latest tab and query. Apply requested
  exclusions after extraction; search operators may not be honored exactly.
- Profile: verify the final handle and selected Posts, Replies or Media view;
  stop on protected, suspended or unavailable profiles.
- Exact post or thread: resolve the outer article's primary status ID, record
  it first, then collect visible conversation context by each article's own ID.
  Do not assume every reply belongs to the original author's thread.

Exclude promoted content unless requested. Report a current visible sample,
not an exhaustive index. Keep results bounded to the requested count or a small
initial sample. Scroll within the main timeline, wait for new post IDs, capture
and deduplicate each batch; stop on repeated batches, challenges or rate limits.

## Resolve a Like

Validate the exact permalink, navigate to it and require the same final status
route. Resolve exactly one outer article by its own primary ID and matching
handle. Do not match nested quotes, text excerpts alone, neighboring articles
or timeline position.

Known English-language surfaces use a Like control ending in `Like`, sometimes
preceded by counts, and an inverse `Unlike` action for a liked post. Inspect
current semantics and selected/pressed state; these labels are clues, not stable
selectors. Return `already-liked` without clicking if the exact post is selected.
Stop when its current state is missing, conflicting or ambiguous.

A dry-run reports the canonical post URL/ID, author, excerpt and current state
without clicking. If that exact Like is not already authorized, present it for
approval. Immediately before acting, verify the expected signed-in handle,
take a new snapshot and resolve the same outer article and unselected control.

If needed and supported by the tool, use a target-bound read-only attribute
check on that exact control for `isConnected`, `aria-label`, `aria-pressed` and
`data-testid`. Do not interpolate page text into JavaScript or call `.click()`
from evaluation. Stop if the tool cannot bind the check to the exact reference.

Click the fresh standard Like reference once through `enso-browser`'s advertised
click tool. Re-snapshot and return `liked` only when that same post exposes
`Unlike` or an affirmative selected/pressed Like state. Counts, a toast, a
missing error or a different article's state do not prove success.

After any click whose result cannot be verified, return `unconfirmed` and leave
the task-owned tab open for inspection. Do not retry, toggle or switch browser
controllers. If X changes its article boundaries, permalink ownership or action
labels, inspect read-only and stop writes until the association and state are
clear.
