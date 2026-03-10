# How AI Generation Works

AutoApply uses Claude Code to create a unique resume and cover letter for every job application. Here's what happens behind the scenes.

## The Process

```
Your experience files  ─┐
                        ├──▶  Claude Code  ──▶  Tailored Resume (PDF)
Job description        ─┘                  ──▶  Cover Letter (text)
```

1. **Read your experience** — AutoApply reads all `.txt` files from your experience folder
2. **Build a prompt** — Your experience + the job description + your profile info are combined into a detailed prompt
3. **Generate resume** — Claude Code creates a resume in Markdown, selecting only the most relevant experiences for this specific job
4. **Generate cover letter** — A second call to Claude Code produces a professional cover letter that references specific details from the job posting
5. **Render PDF** — The Markdown resume is converted to an ATS-safe PDF

## What "ATS-Safe" Means

ATS (Applicant Tracking Systems) are software that companies use to screen resumes. Many ATS systems can't read fancy formatting. AutoApply generates PDFs that are:

- **Helvetica font only** — universally supported
- **Single-column layout** — no side panels or columns
- **No colors, tables, or images** — just clean text
- **Proper headings** — Summary, Experience, Skills, Education

This means your resume will be correctly parsed by LinkedIn, Indeed, Greenhouse, Lever, Workday, and other common ATS platforms.

## What Claude Code Is Told

The resume prompt instructs Claude Code to:

- Select only experiences relevant to **this specific job**
- Quantify achievements with numbers where your files include them
- Use strong action verbs
- Keep content to one page
- **Never invent or exaggerate** anything not in your experience files

The cover letter prompt instructs Claude Code to:

- Write 3 professional paragraphs
- Reference specific details from the job description
- Match the tone to the company culture
- Not repeat the resume content
- Avoid filler phrases like "I am excited to apply"

## Where Generated Documents Are Saved

```
~/.autoapply/profile/
├── resumes/          # PDF and Markdown files
│   ├── abc123_acme-corp_2026-03-09.pdf
│   └── abc123_acme-corp_2026-03-09.md
└── cover_letters/    # Plain text files
    └── abc123_acme-corp_2026-03-09.txt
```

Each file is named with the job ID, company name, and date.

## Without Claude Code

If Claude Code isn't installed, AutoApply falls back to:

- **Resume**: Your uploaded fallback PDF (set in Settings > Profile > Fallback Resume)
- **Cover letter**: A static template (set in Settings > Bot > Cover Letter Template)

These aren't tailored to each job, but applications still go out. A yellow banner on the dashboard reminds you to install Claude Code for better results.

## Privacy

All generation happens **locally on your machine**. Your experience files and job descriptions are sent to Claude Code running on your computer — nothing is uploaded to any cloud service by AutoApply.
