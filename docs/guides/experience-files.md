# Writing Experience Files

Experience files are plain `.txt` files that describe your work history, skills, and achievements. AutoApply reads these to generate tailored resumes and cover letters for each job application.

## Where They Live

- **On disk**: `~/.autoapply/profile/experiences/`
- **In the app**: Profile tab — you can add, edit, and delete files from the dashboard

## How to Write Good Experience Files

### One file per role works best

```
senior_engineer_acme.txt
frontend_lead_startupco.txt
skills_and_tools.txt
education_and_certs.txt
```

### Include specific achievements with numbers

**Good:**
> Led migration from monolith to microservices, reducing deploy time from 45 minutes to 8 minutes. Managed team of 5 engineers.

**Too vague:**
> Worked on backend systems and helped with deployments.

### Mention technologies and tools

> Proficient in Python, Flask, PostgreSQL, Docker, Kubernetes, Terraform, and AWS (EC2, S3, RDS, Lambda).

### Describe projects you contributed to

> Built the real-time notification system serving 2M daily active users. Designed the event-driven architecture using AWS SNS and SQS, reducing notification latency from 30s to under 2s.

### Include education and certifications

> BS Computer Science — MIT (2016)
> AWS Solutions Architect Associate (2023)

## What Happens With Your Files

When AutoApply finds a matching job:

1. It reads **all** your experience files
2. It sends them to Claude Code along with the job description
3. Claude Code picks the **most relevant** experiences for that specific job
4. It generates a tailored resume (PDF) and cover letter (text)
5. Both are saved in `~/.autoapply/profile/resumes/` and `~/.autoapply/profile/cover_letters/`

Claude Code is instructed to **never invent or exaggerate** anything not in your files. It only selects and rephrases what you wrote.

## Tips

- **More detail is better** — you can always add more files. Claude Code will pick what's relevant.
- **Don't worry about formatting** — just write naturally. The AI handles formatting.
- **Update regularly** — add new roles, projects, and skills as your career progresses.
- **One topic per file is fine too** — some people prefer `projects.txt`, `skills.txt`, `leadership.txt` instead of one-per-job. Both work.

## If Claude Code Isn't Installed

Without Claude Code, AutoApply uses your fallback resume (a PDF you upload) and a static cover letter template from Settings. You'll see a yellow warning banner on the dashboard.

To get AI-tailored documents, [install Claude Code](https://docs.anthropic.com/en/docs/claude-code) and authenticate it.
