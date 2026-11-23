# Presenting SupportLens on GitHub and your résumé

## Repository preparation

The folder includes a README, screenshot, MIT license, pinned dependency files, automated checks, tests, and a baseline evaluation report. The code is published at https://github.com/Abisheck553/supportlens.

1. Create an empty repository named `supportlens` in your GitHub account. Choose its visibility yourself. Do not initialize a second README in GitHub.
2. In this project folder, inspect `git status` and `.gitignore`. Do not stage `.env`, databases, uploaded customer files, models, `.venv`, or `node_modules`.
3. Create a commit and connect the repository using the exact URL GitHub gives you:

```sh
git init -b main
git add .
git commit -m "Build SupportLens local support copilot"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

`YOUR_GITHUB_REPOSITORY_URL` is a placeholder, not a runnable destination. Configure your own Git author name/email if Git requests them. Never embed access tokens in commands, screenshots, or the remote URL.

Suggested description: **Evidence-first support copilot with document retrieval, optional local LLM generation, ticket classification, and reproducible evaluation.**

Suggested topics: `python`, `fastapi`, `react`, `typescript`, `information-retrieval`, `machine-learning`, `rag`, `ollama`, `evaluation`.

After you push, inspect the Actions checks. They have been configured but cannot be verified on GitHub until the repository exists. Pin the project to your profile when you have reviewed and personalized it.

## Two-minute demo

1. Explain the support problem and show the eight synthetic source documents.
2. Ask a return-policy question and inspect the cited passage.
3. Upload a new policy and ask a question it answers.
4. Show an unanswered question and discuss where the current gate fails.
5. Run the evaluation and compare the two retrieval methods, including the tie.
6. Show one personal improvement and its measured effect.

If you demonstrate default mode, call it source-excerpt mode. Demonstrate generated RAG replies only after you have connected and tested a language model.

## Résumé wording after you understand and validate the project

**SupportLens — Customer Support Copilot | Python, FastAPI, React, SQLAlchemy, scikit-learn, Ollama, Sentence Transformers**

- Built a local support application with document ingestion, hybrid retrieval, inspectable citations, persistent conversations, and reviewer feedback.
- Implemented a five-category ticket classifier and a reproducible benchmark covering 32 retrieval questions and 20 held-out synthetic ticket examples.
- Added local LLM answer generation (Ollama, Qwen3 4B) with citation validation and a strict retry, passing 14/14 synthetic generation checks.
- Added sentence-embedding hybrid retrieval, raising recall@3 from 22/24 to 23/24 on the bundled benchmark, with 24 automated tests and CI. Do not claim a trained foundation model, real users, cost savings, production scale, or improved accuracy without evidence. Do not present the synthetic classifier score as real-world performance.

## Be ready to answer

- Which parts did you build or modify, and how did you use coding assistance?
- Why does BM25 + TF-IDF not count as dense semantic retrieval?
- Why did the baseline methods tie, and what experiment would you run next?
- Which unanswered questions are falsely accepted?
- What exactly does the citation validator check, and what does it not check?
- Why is the classifier's 100% score not sufficient evidence?
- How would you isolate one customer's documents from another's?

GitHub's [résumé project guidance](https://docs.github.com/en/account-and-profile/tutorials/using-your-github-profile-to-enhance-your-resume) recommends clear features, setup instructions, demonstrations, and testing information.
