To,
The First Appellate Authority,
{{ department }},
{{ municipal_body }}
[OFFICE ADDRESS — PLACEHOLDER, please verify before submission.]

**Subject:** First Appeal under Section 19(1) of the Right to Information Act, 2005

Respected Sir/Madam,

I, {{ applicant_name_placeholder }}, had filed an RTI application dated {{ submission_date }} with the Public Information Officer, {{ department }}, {{ municipal_body }}, seeking information regarding the following issue:

**Issue described:** {{ user_text }}

As of the date of this appeal, {{ days_overdue }} days have elapsed since the statutory response deadline of {{ response_due_date }} under Section 7(1) of the RTI Act, 2005, and no response has been received.

I therefore file this First Appeal under Section 19(1) of the RTI Act, 2005, and request that:

1. The Public Information Officer be directed to furnish the information requested without further delay.
2. Given the delay beyond the statutory 30-day period, the information be provided free of charge, as contemplated under Section 7(6) of the Act.
3. Appropriate action be considered against the Public Information Officer for non-compliance with statutory timelines, if deemed fit.

I have enclosed a copy of my original RTI application and proof of submission dated {{ submission_date }}.

Yours faithfully,

{{ signature_placeholder }}
Name: [APPLICANT NAME — PLACEHOLDER]
Address: [APPLICANT ADDRESS — PLACEHOLDER]
Phone/Email: [CONTACT DETAILS — PLACEHOLDER]
Date: {{ draft_date }}

---
{% if citations %}
**Legal references used in this appeal:**
{% for c in citations %}
- {{ c.source }}, {{ c.section }} — {{ c.title }}
{% endfor %}
{% endif %}

*Disclaimer: This is a drafting assistant and does not provide legal advice. The identity and office address of the First Appellate Authority must be verified before submission.*
