# Exact wording changes

These are the changes from the shared reference, before any model-specific rendering.
Scope and all four training examples were fixed. Full policy JSON, including rejected
drafts, is retained in the [evidence bundle](../../published_runs/2026-10-26-hatexplain/policies).

## Qwen selected: seven punctuation edits

Policy ID: `qwen-4b-p1`.

**definitions-2**

Before: Offensive speech includes rude, vulgar, profane or insulting language that does not make such an identity-based attack. Normal speech is neither hateful nor offensive.

After: Offensive speech includes rude, vulgar, profane, or insulting language that does not make such an identity-based attack. Normal speech is neither hateful nor offensive.

**block-2**

Before: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal or otherwise deserving contempt.

After: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal, or otherwise deserving contempt.

**block-3**

Before: BLOCK support for violence, exclusion or denial of rights directed at people because of such group membership.

After: BLOCK support for violence, exclusion, or denial of rights directed at people because of such group membership.

**allow-2**

Before: ALLOW profanity, vulgarity, personal insults and offensive jokes when they do not attack people on the covered identity grounds.

After: ALLOW profanity, vulgarity, personal insults, and offensive jokes when they do not attack people on the covered identity grounds.

**allow-3**

Before: ALLOW criticism of a belief, institution, government, policy or individual conduct when it does not express an identity-based attack on people.

After: ALLOW criticism of a belief, institution, government, policy, or individual conduct when it does not express an identity-based attack on people.

**precedence-1**

Before: A quotation, report, denial or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

After: A quotation, report, denial, or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

**precedence-2**

Before: An identity term, slang word or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

After: An identity term, slang word, or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

## Shieldstral selected: the same punctuation edits plus context clarification

Policy ID: `shieldstral-p2`.

**definitions-2**

Before: Offensive speech includes rude, vulgar, profane or insulting language that does not make such an identity-based attack. Normal speech is neither hateful nor offensive.

After: Offensive speech includes rude, vulgar, profane, or insulting language that does not make such an identity-based attack. Normal speech is neither hateful nor offensive.

**definitions-3**

Before: Assess the meaning expressed by the post itself, including its target and stance. Do not assume missing conversation, an unseen image, or the author's identity.

After: Assess the meaning expressed by the post itself, including its target and stance. Do not assume missing conversation, an unseen image, or the author's identity. Context determines if a term is used to attack an identity or merely as a descriptor or insult unrelated to group membership.

**block-2**

Before: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal or otherwise deserving contempt.

After: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal, or otherwise deserving contempt.

**block-3**

Before: BLOCK support for violence, exclusion or denial of rights directed at people because of such group membership.

After: BLOCK support for violence, exclusion, or denial of rights directed at people because of such group membership.

**allow-2**

Before: ALLOW profanity, vulgarity, personal insults and offensive jokes when they do not attack people on the covered identity grounds.

After: ALLOW profanity, vulgarity, personal insults, and offensive jokes when they do not attack people on the covered identity grounds.

**allow-3**

Before: ALLOW criticism of a belief, institution, government, policy or individual conduct when it does not express an identity-based attack on people.

After: ALLOW criticism of a belief, institution, government, policy, or individual conduct when it does not express an identity-based attack on people.

**precedence-1**

Before: A quotation, report, denial or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

After: A quotation, report, denial, or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

**precedence-2**

Before: An identity term, slang word or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

After: An identity term, slang word, or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

## PolicyLM rejected: inconsistent definition and removed context constraint

Policy ID: `policylm-p1`.

**definitions-2**

Before: Offensive speech includes rude, vulgar, profane or insulting language that does not make such an identity-based attack. Normal speech is neither hateful nor offensive.

After: Offensive speech includes rude, vulgar, profane, or insulting language that does not make such an identity-based attack.

**definitions-3**

Before: Assess the meaning expressed by the post itself, including its target and stance. Do not assume missing conversation, an unseen image, or the author's identity.

After: Normal speech is neither hateful nor offensive and may include personal insults, profanity, or controversial opinions that do not target protected identity groups.

**block-1**

Before: BLOCK identity-based abuse, including a derogatory group slur used to insult people because of their membership.

After: BLOCK identity-based abuse, including derogatory group slurs used to insult people because of their membership.

**block-2**

Before: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal or otherwise deserving contempt.

After: BLOCK statements depicting such a group as inferior, disgusting, subhuman, inherently criminal, or otherwise deserving contempt.

**block-3**

Before: BLOCK support for violence, exclusion or denial of rights directed at people because of such group membership.

After: BLOCK support for violence, exclusion, or denial of rights directed at people because of such group membership.

**allow-2**

Before: ALLOW profanity, vulgarity, personal insults and offensive jokes when they do not attack people on the covered identity grounds.

After: ALLOW profanity, vulgarity, personal insults, and offensive jokes when they do not attack people on the covered identity grounds.

**allow-3**

Before: ALLOW criticism of a belief, institution, government, policy or individual conduct when it does not express an identity-based attack on people.

After: ALLOW criticism of a belief, institution, government, policy, or individual conduct when it does not express an identity-based attack on people.

**precedence-1**

Before: A quotation, report, denial or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

After: A quotation, report, denial, or condemnation of hateful language is allowed when the post clearly does not endorse the attack.

**precedence-2**

Before: An identity term, slang word or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

After: An identity term, slang word, or profanity alone is insufficient to block: determine its use in context. A claim of humor does not excuse an expressed identity-based attack.

PolicyLM p2 repeats the rejected text. Qwen p2 repeats Qwen p1 and was excluded
from selection. Shieldstral p1 has the same substantive punctuation edits as Qwen p1.
Only the three distinct source-selected bodies (p0, Shieldstral p2, Qwen p1) enter
the final transfer matrix. See the [scope review](SCOPE-REVIEW.md).
