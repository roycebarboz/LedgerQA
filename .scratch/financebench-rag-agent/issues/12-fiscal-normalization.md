# 12: Fiscal period normalization

**What to build:** Every Filing stores its raw `period_of_report_date` alongside a normalized `fiscal_year`/`fiscal_quarter` pair, so companies with non-calendar fiscal years (e.g. Microsoft's June year-end) compare correctly across periods.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] A non-calendar-fiscal-year company's Filing has both a raw period date and a normalized fiscal_year/fiscal_quarter
- [ ] Cross-period questions ("FY2018 vs FY2019 CapEx") use the normalized fields and return correct period alignment even for non-calendar filers
- [ ] Normalization logic is derivable purely from filing metadata, no manual per-company mapping table required
