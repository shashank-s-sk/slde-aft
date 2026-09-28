# Stage C wording notes (hold — do NOT apply until the Stage C writing pass)

Decisions recorded 2026-09-29 from DEC-035 / EVID-050. Apply only in the
Stage C manuscript pass, together with the rest of `new feddback.md`.

## 1. Replace "defect" with the by-design framing (user-approved 2026-09-29)

Approved wording: DySECT counts repeated observations, including re-reads
of one source, as independent support **by design**; this paper tests that
independence assumption. Basis: DySECT Sect. 2.2, "Frequencies are
incorporated by treating f_i as repeated independent support for the same
confidence value (equivalently, by exponentiating the corresponding term)".

Locations in paper/main.tex (line numbers as of commit a22f672):
- l.1456-1457 "they target different defects" -> e.g. "they target
  different parts of the rule".
- l.1469 "The same defect appears outside the product domain" -> "The same
  repeat counting appears ...".
- Anywhere R3 is described as fixing an error: use "in our implementation"
  (professor) and "tests the independence assumption".
- supplementary.tex / cover letter: no "defect" found at time of writing;
  re-grep at Stage C.

## 2. Disambiguate m(t): ours != DySECT's (user-approved 2026-09-29)

DySECT's m(t) = "number of mutually exclusive instances detected for t";
in its code (`findAllMutuallyExclusiveInstances`) this is a TYPE-LEVEL
count: concepts declared mutually exclusive with the subject/object type
of which the entity is also an instance. Ours = number of rival object
values already accepted for a designated single-valued (subject,
predicate) slot. Same formula C = C_agg/(m+1), different m. In DySECT's
released KB the division fired 0 times out of 61,676 stored confidences.

Add one explicit sentence at each place that implies they are the same:
- l.76-78 (intro): "a conservative Noisy-OR with a mutual-exclusivity
  penalty for single-valued predicates" is attributed to DySECT, but
  DySECT's penalty is type-level, not per single-valued predicate.
- l.224-228 (related work, "What this paper takes from DySECT"): "the
  mutual-exclusivity penalty C = C_agg/(m(t)+1), which is the rule
  evaluated throughout this paper" -> add: DySECT's m(t) counts type-level
  mutual-exclusion conflicts; this paper keeps the functional form but
  counts rival values of a designated single-valued slot, so the penalty
  and the rival ceiling are properties of our instantiation.
- l.396-397 (Eq. conflict definition): add "(this reinterprets DySECT's
  m(t), Sect. 2.2)".
- Abstract (l.54): "The rule studied is the conservative Noisy-OR with a
  mutual-exclusivity penalty that the DySECT system published ..." -> say
  "adapted from DySECT", or state the reinterpretation in the body only.
- Rival-ceiling proposition: professor asked to reduce it to one
  proposition noted as a designed property; the note should say it holds
  for our m(t). For DySECT's code it also holds algebraically at its only
  live threshold (0.5), except a seed/trusted triple (C_agg=1) with k=1,
  which scores exactly 0.5 and passes its ">= 0.5" test.

## 3. Optional sentence on DySECT's released run (EVID-050)

In DySECT's released KB, 4,030 of the 4,604 generalization edges eligible
for its DocRED prompt (87.5%) pass its 0.5 threshold only through repeated
observations of the same source/document. Use only if the DySECT rerun
(DEC-035b) is not done; otherwise report the rerun result.
