# Can Large Language Models Evaluate Grant Proposal Quality? Revisiting the Wennerås and Wold Peer Review Data

*A test of language-model scores against expert ratings of 142 Swedish medical fellowship applications finds a weak match, with clear limits on what the models can judge.*

You’ve probably sorted a pile of applications, messages, or documents by what seems strongest. A language model can do something similar, then get a subtle case wrong because it’s finding patterns in words, not weighing a proposal like a reviewer with a particular standard in mind.

That question sits at the centre of “Can Large Language Models Evaluate Grant Proposal Quality? Revisiting the Wennerås and Wold Peer Review Data,” by Ulf Sandström and colleagues, published in the Journal of Data and Information Science.

The researchers asked how closely several medium-sized, open-weight language models scored grant proposals compared with human peer reviewers. Their test used a historical dataset: 142 Swedish Medical Council post-doctoral fellowship applications from 1994. The models produced scores, and the researchers compared those scores with the average expert ratings.

A correlation is a measure of how much two rankings tend to line up. A perfect match would be one. The models’ scores correlated moderately with one another, with an average of 0.34. Their agreement with the expert scores was weaker, though still positive and mostly statistically significant, with an average correlation of 0.22.

The strongest model result reached 0.33. That came from Gemma 3 27b, using proposal titles and summaries but leaving out the main texts. That number was about half the correlation between the human reviewers, at 56 percent.

There’s a useful comparison here: think of each model as a sieve. It lets certain patterns through, based on the material it receives and the scoring task it’s given. A sieve can help sort a pile, but the result depends on the mesh, the contents, and what counts as a good catch. A model score is similarly shaped by its input and by the relationship between language patterns and the target rating.

The practical suggestion is cautious. These models might help with application triage, meaning an early sorting step, or with breaking ties. The paper does not show that they can replace expert review. It tested one old funding call, one dataset, and a set of evaluation criteria that weren’t all the same. We also can’t tell from these selected passages how the models would perform on newer applications or other funding systems.

The small sample size, old funding call and heterogeneous evaluation criteria all undermine the robustness of the analysis.

So picture that pile of applications again. A model may help arrange it, but the ranking still needs a clear purpose and a human check on what the score misses. I’m Noor Haddad. Know what the model is for.

**Caveat:** The small sample size, old funding call and heterogeneous evaluation criteria all undermine the robustness of the analysis.

## Claims

- The study compared language-model scores with expert scores for 142 historical Swedish Medical Council post-doctoral fellowship applications.
  > This article compares scores from a range of medium sized open-weight LLMs with peer review scores for a well-researched dataset, 142 Swedish Medical Council post-doctoral fellowship applications from 1994.
- The models’ scores correlated moderately with each other.
  > Whilst the LLM scores correlate moderately between each other (mean Spearman correlation: 0.34)
- Agreement between model scores and average expert scores was weaker but positive.
  > they correlated weakly but positively and mostly statistically significantly with the average expert scores (mean Spearman correlation: 0.22).
- The highest model-to-expert rank correlation was 0.33, using titles and summaries without the main texts.
  > The highest rank correlation between expert scores and LLMs was 0.33 for Gemma 3 27 b based on proposal titles and summaries without their main texts
- The strongest model correlation was about half the correlation between human reviewers.
  > which is about half (56 %) of the correlation between reviewers.
- The analysis has several stated limitations.
  > The small sample size, old funding call and heterogeneous evaluation criteria all undermine the robustness of the analysis.

## Source
Can Large Language Models Evaluate Grant Proposal Quality? Revisiting the Wennerås and Wold Peer Review Data — Ulf Sandström, Mike Thelwall — Journal of Data and Information Science — https://doi.org/10.1515/jdis-2026-0048

Evidence tier: `abstract` · license: `cc-by`