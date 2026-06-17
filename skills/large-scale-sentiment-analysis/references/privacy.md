# Privacy And De-Identification

Use a de-identified working copy before AI labeling or export. Hash user, URL, ID, account, location, and link-like fields when they are needed for grouping; drop them when they are not needed. Do not hash the full comment text because sentiment analysis needs readable text. Instead mask sensitive fragments inside text:

- URL -> `[URL]`
- @handle/account mention -> `[@USER]`
- email -> `[EMAIL]`
- phone or long numeric ID -> `[PHONE_OR_ID]`

If field selection or sample selection sends row examples to an external AI, run privacy audit and mask examples first. If field selection is purely local, formal de-identification can happen after text/source/date fields are identified.

Recommended wording:

> The workflow used a de-identified working copy. Identifier-like fields were hashed or excluded, and sensitive text fragments were masked before downstream AI labeling and export.
