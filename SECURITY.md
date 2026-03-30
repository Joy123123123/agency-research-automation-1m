# Security Policy — Agency Research Automation

**Owner:** Md Jamil Islam  
**Repository:** agency-research-automation-1m

---

## Supported Versions

This is a business operations repository (automation scripts, templates, and tracking tools). There are no versioned software releases. Security patches are applied to the `main` branch directly.

| Branch | Supported |
|--------|-----------|
| `main` | ✅ Yes — always kept current |
| Other branches | ❌ No — feature/fix branches only |

---

## Security Guidelines for Users

### ⚠️ Never Commit Secrets

This repository contains automation scripts that require API keys and SMTP credentials. **Never commit these to Git.**

- Always store credentials in a `.env` file (already in `.gitignore`)
- Never hardcode API keys, passwords, or tokens in scripts
- Rotate any credentials that are accidentally committed immediately

### Safe Files to Commit
- Python scripts (`scripts/*.py`)
- Markdown documentation
- Template files
- CSV tracking files with **sample/template data only** (no real client data)

### Files That Must Never Be Committed
- `.env` and any `*.env` files
- `output/` directory (contains scraped personal data)
- `credentials.json`, `token.json`, `api_keys.txt`
- Any file containing real client names, emails, or business information

---

## Reporting a Vulnerability

If you discover a security issue in this repository (e.g., accidentally committed credentials, a script vulnerability, or exposed personal data):

1. **Do NOT open a public GitHub issue** — this may expose sensitive information
2. **Contact the owner directly:**  
   - Open a private GitHub Security Advisory in this repository (Settings → Security → Advisories)
   - Or contact Md Jamil Islam directly via GitHub profile

3. **Include in your report:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

4. **Response timeline:**
   - Acknowledgement within **48 hours**
   - Fix or mitigation within **7 days** for critical issues

---

## Data Privacy

This repository may contain automation tools that collect publicly available business data (company names, websites, publicly listed contact info). Users are responsible for:

- Complying with applicable data protection laws (GDPR, CAN-SPAM, CASL, etc.)
- Obtaining proper consent where required
- Not using automation scripts for spam or harassment
- Respecting `robots.txt` and website terms of service when scraping

---

*Security is everyone's responsibility. When in doubt, don't commit it.*
