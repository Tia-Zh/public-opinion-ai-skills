# Privacy And De-Identification

Use this reference when the dataset contains user-generated comments, social-media exports, URLs, user IDs, nicknames, locations, or other personal/sensitive fields.

## Default Principle

Never overwrite the original file. Create a working copy and preserve row-level traceability with `row_id`, source sheet, and source row where possible.

## What To Hash

Hash fields that are useful for grouping or deduplication but should not be shown directly:

- nickname/user/account/author;
- profile URL, post URL, comment URL;
- platform user ID, post ID, comment ID;
- location/address/IP-like fields;
- phone/email fields if they must be retained structurally.

Hashing means the same original value maps to the same fixed token, so repeated users or links remain detectable without exposing the raw value.

## What To Mask In Text

For the main text/comment column, do not hash the entire text because downstream cleaning, keyword filtering, sentiment analysis, and review need readable content. Instead mask sensitive fragments:

- URL -> `[URL]`
- @handle/account mention -> `[@USER]`
- email -> `[EMAIL]`
- phone or long numeric ID -> `[PHONE_OR_ID]`

## What To Drop

Drop fields that are not needed for analysis and create unnecessary risk:

- avatars;
- raw profile pages;
- exact coordinates;
- private contact details;
- raw browser/cookie/session artifacts.

## AI Safety

Before sending samples to an external AI, either:

1. use a de-identified working copy; or
2. run `privacy_audit.py` and explicitly confirm that sampled columns do not contain risky raw identifiers.

If field selection is done locally from column names and summaries, it can happen before formal de-identification. If field selection sends row examples to an external AI, run privacy audit and mask examples first.

## Report Wording

Recommended wording:

> The analysis used a de-identified working copy. User/link/location-like fields were hashed or excluded, and URL, account mentions, email, and phone/long-ID patterns in text were masked before downstream labeling and export.
