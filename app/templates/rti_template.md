# APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005

To,
The Public Information Officer (PIO),
{{ department }},
{{ municipal_body }}
[OFFICE ADDRESS — PLACEHOLDER, please verify before submission.]

**Subject:** Request for information under Section 6(1) of the Right to Information Act, 2005 regarding {{ issue_type_display }}.

Respected Sir/Madam,

I, {{ applicant_name_placeholder }}, a citizen of India, hereby request the following information under the provisions of the Right to Information Act, 2005:

### 1. Particulars of the Civic Issue
- **City/Jurisdiction:** {{ city }}
- **Department Concerned:** {{ department }}
- **Municipal / Local Body:** {{ municipal_body }}
- **Description of Grievance/Issue:**
  {{ user_text }}

### 2. Information Requested
1. Please provide the name and designation of the officer responsible for this issue.
2. Please provide the current status of action taken.
3. Please provide the expected timeline for resolution.
4. If this matter belongs to another department or public authority, please transfer this application under Section 6(3) of the RTI Act, 2005.

### 3. Application Fee Details
- **Prescribed Fee:** ₹{{ fee.amount }} ({{ fee.currency }})
- **Fee Rules & Notes:** {{ fee.notes }}
{% if fee.citation %}
- **Fee Citation:** {{ fee.citation.source }} ({{ fee.citation.section }} — {{ fee.citation.title }})
{% endif %}

### 4. Statutory Timeline
- {{ response_notice }}

Yours faithfully,

{{ signature_placeholder }}
Name: [APPLICANT NAME — PLACEHOLDER]
Address: [APPLICANT ADDRESS — PLACEHOLDER]
Phone/Email: [CONTACT DETAILS — PLACEHOLDER]
Date: {{ draft_date }}

---
{% if legal_citations %}
### Legal References Grounding this Application:
{% for c in legal_citations %}
- **{{ c.section }} of {{ c.source }}:** {{ c.title }}
{% endfor %}
{% endif %}

*Disclaimer: This is a drafting assistant and does not provide legal advice. The identity and office address of the Public Information Officer must be verified before submission.*
