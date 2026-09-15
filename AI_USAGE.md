# AI usage record

This project used AI as a supportive development assistant rather than as a replacement for the candidate's implementation. The actual repository here is the source of truth for what was implemented and verified.

## AI tools used

- VS Code / GitHub Copilot workspace assistance during implementation and review.
- Local project review and debugging support while validating the Django application.
- The assignment prompt itself was used as a specification reference during audit and documentation review.

## Purpose of AI usage

AI was used for limited support in the following areas:

- initial design and structure review
- debugging small Django/template issues
- improvement of code readability and documentation clarity
- checking logic against the assignment requirements
- supporting verification and validation steps

The core Django business logic, models, packing logic, and recommendation behavior were still reviewed and validated by the candidate before acceptance.

## Representative prompts

The repository does not contain a complete exported ChatGPT transcript, so the exact historical prompt list cannot be reconstructed verbatim. However, the types of prompts that align with the actual development work include:

- "How should I structure a Django shipping recommendation app?"
- "How can I validate box and product dimensions cleanly in Django models?"
- "How can I improve formatting and readability without changing project behavior?"
- "How should I test recommendation logic for weight and dimension constraints?"
- "How do I verify Django migrations and test status cleanly?"

## Accepted output

The following kinds of suggestions were accepted and then checked against the project codebase:

- formatting and readability improvements that preserved existing behavior
- validation and testing guidance for Django checks and the test suite
- documentation structure and final audit preparation guidance

## Rejected or modified output

The following were intentionally rejected or modified:

- any suggestion that would have changed working recommendation logic
- any suggestion to rewrite or redesign the project architecture
- any fabricated transcript or fake AI conversation record
- any personal reflection written in the candidate's voice without the candidate's real input

## AI mistakes or limitations encountered

- AI-generated suggestions needed verification against the actual Django code and tests.
- Some guidance around assignment-document requirements was incomplete unless checked against the actual repository state.
- No exported ChatGPT transcript file exists in the repository, so transcript-level accuracy cannot be claimed without a real export.

## Verification performed

The following were checked directly in the current project and used as verification evidence:

- `python manage.py check`
- `python manage.py makemigrations --check`
- `python manage.py migrate --plan`
- `python manage.py test`

Final verified result:

- 37 tests passed
- Django check passed
- Migration state is consistent

## Reference

The shared ChatGPT reference remains available here for manual verification or inclusion in the final submission package:

https://chatgpt.com/share/6aa910d7-f4fc-83ee-9411-8d3d979db8ea


