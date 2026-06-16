# Field Inference

Infer column roles from both names and values. Never rely only on a fixed list of aliases.

## Generic roles

- Text/content: long strings, paragraphs, comments, descriptions, notes, summaries, titles.
- Time/date: parseable dates, timestamps, month/day strings, year-month strings.
- ID/key: mostly unique short values, numeric identifiers, URLs, ticket numbers, order numbers.
- Category: repeated low-cardinality text values, statuses, departments, platforms, regions, labels.
- Numeric: parseable numbers, counts, amounts, percentages, scores.
- URL/link: values starting with `http://` or `https://`, or column names containing link/url.
- Person/account: user, author, owner, handler, customer, employee, account-like values.
- Location: region, province, city, address, coordinate-like values.

## Alias examples

These aliases are hints, not rules:

- Content: `内容`, `正文`, `文本`, `评论`, `留言`, `描述`, `说明`, `标题`, `content`, `text`, `body`, `description`, `comment`.
- Time: `时间`, `日期`, `发布时间`, `创建时间`, `更新时间`, `采集时间`, `created_at`, `publish_time`, `date`, `time`.
- User: `用户`, `昵称`, `作者`, `账号`, `发布者`, `user`, `author`, `screen_name`, `nickname`.
- Link: `链接`, `网址`, `URL`, `原文链接`, `link`, `url`.
- Source: `来源`, `平台`, `渠道`, `工作表`, `source`, `platform`, `channel`.
- Status/category: `状态`, `类型`, `分类`, `标签`, `类别`, `status`, `type`, `category`, `label`.

## Recommendation style

When presenting inferred mappings, use a review-friendly format:

```text
已自动识别：
- 评论内容 -> 主要文本列
- 发布时间 -> 时间列
- 平台 -> 分组列
```

If confidence is low, say so and show alternatives.
