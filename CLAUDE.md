# Project summary: "What transfer rates do not tell you: conditioning practice in adversarial transfer evaluation"

Repo: github.com/imjbassi/transferability-of-adversarial-attacks (branch main). Author: Jaiveer Bassi. Target venue: TMLR (anonymous PDF in paper/tmlr/). Current detailed status: `docs/REMAINING_WORK.md`.

## Thesis
Papers on transfer-based adversarial attacks usually report a single "transfer rate". That number can mean different things depending on:
- whether images the target already misclassifies are counted;
- whether transfer is measured only on examples that fooled the source model;
- what denominator is used.

The paper separates these quantities:
- **PTR** = P(target fooled | source and target both correct on the clean image)
- **a_st** = P(source fooled | both clean-correct)
- **CTR** = P(target fooled | both clean-correct, source fooled)
- **b_st** = P(target fooled | both clean-correct, source not fooled)
- Identity: PTR = a_st·CTR + (1−a_st)·b_st.

It surveys how 80 highly cited papers report these, reruns released code to measure them, and gives bounds for when papers report only unconditional error. The bound is max(0, attacked error − clean error): a lower bound on newly induced errors, valid only for the same fixed model, the same image population and an unconditional outcome.

## Survey method
- **Corpus:** 80 papers ranked by citations (`survey/corpus.csv`), with a preregistered coding scheme (`survey/coding_scheme.md`) and a preregistration tag.
- **Six fields:**
  - f1: clean accuracy reported separately;
  - f2: clean-correct denominator;
  - f3: conditioning on source success;
  - f4: absolute counts reported;
  - f5: numeric L∞/L2 budget;
  - f6: released artifacts sufficient to recompute.
- **Retrospective amendment (23 Sep 2026, not preregistered):** codes are per result group, aggregated unanimously per paper, with "mixed_explicit" and "not applicable" strata. The rules prefer "unclear" over "no", keep positive conditioning evidence, and never describe a paper as wrong.
- **Evidence review:** a full review of all 80 papers covering full texts, supplements, locators, source hashes, artifact checks and bounds eligibility (`survey/evidence_audit/reviews/NN.json`). Frozen 25 Sep 2026 (tag `repaired-first-pass-2026-09-25`, `survey/evidence_audit/freeze_manifest.json`). Later corrections go only in `survey/evidence_audit/post_freeze_errata.md`.

## First-pass counts (NON-BLIND, single auditor, not yet validated)
- f1: 13 yes, 67 unclear.
- f2: 4 yes, 3 no, 73 unclear. The unclears are 57 unresolved, 1 mixed and 15 not applicable; 13 papers have at least one explicit yes group.
- f3: 5 yes, 7 no, 68 unclear. The unclears are 52 unresolved, 1 mixed and 15 not applicable; 9 papers have at least one explicit yes group.
- f4: 1 yes.
- f5: 37 yes, 13 no, 30 unclear.
- f6: 1 yes (rank 10).

These must not be reported as final until an independent blind recode exists.

## Bounds (`survey/*bounds*`)
Lower bounds are in percentage points and account for rounding of the published figures.
- **Rank 38 (Wu et al., CVPR 2020):** the historical 96 rates are 72 single-model rates plus 24 against an ensemble that includes the source; they must be reported separately. The single-model bounds run 0.95–77.35 (median 33.15). The Table 3 cells were added (81 single-model rates in total).
- **Rank 68 (DAmageNet):** 18 victims, 3.19–69.28 (median 60.3).
- **Rank 20 (ILA, CIFAR-10):** 108 rates, 2.4–69.6 (median 55.1). The C&W columns are excluded because all 48 cells lie on a 1/96 grid, which implies a smaller, unstated image set.
- **Three-paper distribution:** 207 single-model rates; paper medians 34.25, 55.1 and 60.345. This is not a corpus prevalence.
- Every extraction was done by one auditor; a second person's check is pending.

## Reruns of released code (`survey/recomputation/*_rerun/`)
Each rerun has a manifest (commit, weight hashes, data hashes), a README and a test. All are selected configurations, not full-paper replications. f6 stays "unclear".

| Rank | Paper | What was run | Result |
|---|---|---|---|
| 23 | SSA | Inc-v3 source, two seeds | Within 1.5 points of Table 1 |
| 20 | ILA | CIFAR-10, all 10,000 test images | I-FGSM within 0.32; MI-FGSM within 0.86 with a consistent downward offset |
| 13 | SGM | Table 3 PGD and SGM | Within 1.14 points; the paper's "VGG19" column matches VGG19-BN |
| 47 | PNA | Table 1 method row | Within 2.55 points, all higher |
| 44 | Targeted transfer | Table 1 ResNet-50 block | All 27 cells within 1.8 points |
| 57 | SIA | Figure 3(a), bar values read from the PDF's vector geometry | Within 0.5 points at μ = 1; the release default μ = 0 is 3–27 points lower |
| 67 | RAP | Table 1 ResNet-50 I/+RAP/+RAP-LS | Within 2.1 points at the paper's ε_n = 12/255; the release default 16/255 is 10–14 points lower |
| 10 | Su et al. | Earlier TF1 original-runtime run | f6 = yes (one selected configuration) |

Other findings from the reruns:
- **SIA:** its images are described as clean-correct, but under the released pipeline only 89.5–98.4% are.
- **RAP:** the README's RAP commands omit the flag that turns RAP on.
- **PNA:** its pinned timm version was never published, so the ViT-B/16 weights it used can't be identified.
- **Conditioning across 88 source→target pairs** (`survey/recomputation/conditioning_across_reruns.json`): the source is fooled on 97–100% of eligible images, so CTR ≈ PTR. Counting images the target already misclassifies shifts rates by up to 5.4 points.

**Feasibility** (`survey/recomputation/FEASIBILITY.md`):
- TF1 releases (ranks 4, 5, 16, 21, 46, 48, 60) can't use the available RTX 4070.
- Some papers need ImageNet validation images, which require an account and terms (39, 68, 78).
- Some never released their sample lists or checkpoints (58, 72, 73, 77).

## Status and what remains
1. **Blocked on another person:** an independent blind recode of the preregistered 16-paper sample (packet in `survey/blind_recode/`), then per-field Cohen's kappa. The original author waived the waiting period but not independence. The earlier copied recode is invalid. A session that has seen the first-pass codes cannot act as the blind recoder.
2. **Blocked on another person:** a second check of the bounds extractions.
3. **After reliability data exist:** update the manuscript's headline numbers, then rebuild and check the PDFs, then make a new release and a new Zenodo deposit (the existing DOIs don't cover this work), then the author's submission checks.
4. **Optional:** second seeds for the single-seed reruns, and CPU-only TF1 runs (about 17 h per configuration).

## Ground rules for any assistant
- Never edit the frozen files, the corpus, the scheme or the preregistration. Use a dated amendment plus a refreeze, or the errata file.
- Don't claim blinding, replication or publication readiness without evidence.
- Distinguish insufficient reporting from explicit methodological choices, and never call a paper wrong.
- Keep the user-owned, untracked `paper/tmlr/main_anonymous.pdf`; never commit or delete it.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Checks: `python -m pytest -q survey/test_audit_tools.py` and `python survey/freeze_first_pass.py --check`.
- Local-only resources: weights, data and adversarial images are in `D:\transfer_recompute`, plus a `D:\targeted_attack` junction (hashes are in the manifests). They are not available in cloud sessions.
