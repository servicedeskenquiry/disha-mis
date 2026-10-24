# DISHA MIS: client review changes (Preliminary Review Note, 28.09.2026)

Status: ✅ done · 🟡 done with a placeholder or assumption, needs client input

## 1. Welcome / section selection page (new page at `/`)
| # | Request | Status | Where |
|---|---|---|---|
| 1.1 | Full organisation name instead of "DISHA", plus logo | 🟡 Name done. Logo is a **placeholder**: replace `static/img/disha-logo.svg` with the official file | `home.html`, `config.py` |
| 1.2 | Show the 5 sections + welcome note "Welcome to the DISHA MIS System" (no separate heading) | ✅ | `home.html` |
| 1.3 | Small image/icon under each section | ✅ Icons in circles | `home.html` |
| 1.4 | English / বাংলা choice at the top corner | ✅ | `home.html` |
| 1.5 | Only Fisheries active, others "Coming Soon" | ✅ | `config.SECTIONS` |

## 2. Login page
| # | Request | Status |
|---|---|---|
| 2.1 | Fisheries section leads to the Fisheries login | ✅ |
| 2.2 | Welcome message "Welcome to the DISHA Fisheries MIS System" at the top | ✅ |
| 2.3 | "Fisheries NGO Management System" → "Fisheries Data Management System" | ✅ (also in sidebar and exports) |
| 2.4 | Remove "Empowering fishermen communities across West Bengal" | ✅ |
| 2.5 | "Admin / Staff" → "Admin" | ✅ |
| 2.6 | English / বাংলা options | ✅ |

## 3. Primary dashboard
| # | Request | Status |
|---|---|---|
| 3.1 | "Active Offices" → "Active Districts" | ✅ Shows 15, plus how many reported this month |
| 3.1 | Use the 15 real district/unit names everywhere instead of demo names | ✅ `config.DISTRICTS`, used in all dropdowns, charts, filters, demo data |
| 3.2 | Status limited to Approved / Pending (no Rejected/Deleted/Queried) | ✅ Also enforced in the database |
| 3.2 | Comment box for admin observations on a report | ✅ On each report and inline in the Approval Queue, kept as a dated comment thread |
| 3.3 | "By Office" chart with real district names | ✅ Renamed "By District" |
| 3.4 | "Recent Submissions" → "Pending Reports" | ✅ |
| 3.5 | Numbers shown on the charts themselves | ✅ Every chart (also in PowerPoint export) |

## 4. Submit report: five report types
| # | Request | Status |
|---|---|---|
| 4 | Daily Activity, Monthly, Quarterly, Half-Yearly, Annual Report | ✅ |
| 4 | Monthly report correlated with district, Due/Done marking | ✅ "Monthly Report Tracker" grid (district × month, ✓ Done / ! Due) on the Monthly Reports tab |
| 4 | Consistent terminology | ✅ All labels come from `config.REPORT_TYPES` |

## 5. Daily Activity Report form
| # | Request | Status |
|---|---|---|
| 5.1 | "Office/Branch" → "Active District" | ✅ |
| 5.2 | 5 activity types + Others | 🟡 **Provisional list** (Community Meeting, Training, Campaign & Awareness, Deputation, Research & Investigation, Others) until the Fisheries Team shares its formats |
| 5.3 | "Period" → "Date" for daily reports | ✅ |
| 5.4 | Issue-Tag for collation and search | 🟡 Works. **Provisional tag list** until the Fisheries Team shares theirs |
| 5.5 | Participant sub-categories, tick the ones that apply and enter numbers | ✅ Total + Women, Men, Fisher, Fish Workers, Fish Farmers, Leaders, Organisers, Experts, Others. Total auto-fills from Women + Men |

## 6. Periodic reports
| # | Request | Status |
|---|---|---|
| 6.1 | Selecting an Activity Type opens its format/template | 🟡 Works for every report type. Template fields are **placeholders** until the real formats arrive. Periodic reports also have "Consolidated (all activities)" |
| 6.2 | 15 districts + Head Office for periodic reports | ✅ Head Office is hidden for Daily reports |
| 6.3 | Period field: month / quarter / half-year / year | ✅ Indian financial year (Q1 = Apr–Jun) |
| 6.4–6.5 | Issue-Tag on periodic reports | ✅ (same provisional list) |
| 6.6 | Attachments split into A. Meeting Resolution / Minutes and B. Supporting Documents / Media | ✅ |
| 6.6 | Up to 10 attachments | ✅ Checked in the browser and on the server, 25 MB per file, videos allowed |
| 6.6 | Avoid repetition, reference the archive | ✅ "Reference a file already in the archive": re-use a file from an earlier report without uploading it again |

## 7. All Reports
| # | Request | Status |
|---|---|---|
| 7 | Sub-sections: Dashboard, All, Daily, Monthly, Quarterly, Half-Yearly, Annual | ✅ Tabs |
| 7 | Report Submission Overview: reports per month of a year (or per day of a month) by type, as a chart | ✅ |
| 7 | District-wise progress: total, activity breakup, count per activity type, month-wise progress | ✅ Pick a district (or all) and a financial year. Also a district × activity table |
| 7 | Tag-wise filtering everywhere | ✅ Dashboard, All Reports, Reports Dashboard, Approval Queue, Export |
| 7 | Download as DOC/DOCX, Excel, PPT, PDF | ✅ Current filters or a single report |
| 7 | Guest Mode unchanged | ✅ |

## Remaining modules (built together with the above)
- **Approval Queue**: pending reports with comment + Approve (Super Admin only).
- **Analytics**: the All Reports › Dashboard tab.
- **Export**: dedicated page plus download buttons on lists and report pages.
- **User Management**: create users, set role and district, enable or disable them, reset passwords.

## Assumptions to confirm with the client
1. Quarters and half-years follow the financial year (April–March).
2. Only a Super Admin can approve. Back Office can submit, comment and export.
3. A monthly report counts as "Done" as soon as it is submitted, even while it is still Pending approval.
4. "Total Participants" is entered separately because the sub-categories overlap (a woman can also be a fish worker).

## Waiting on the client / Fisheries Team
- Official DISHA logo file
- The 5 activity types and their formats
- The issue-tag list
- Review of the Bengali wording (`static/js/i18n_bn.js`)
