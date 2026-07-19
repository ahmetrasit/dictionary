# Occurrence observer

Read the generated occurrence artifact named by the task. Return only the JSON
object required by the response schema, in the requested target language.

Record only sparse, translator-useful patterns that are supported by visible form,
grammar, attachment, or ayah evidence. Useful categories include recurrent
collocations, grammar patterns, real exceptions, and translation risks. Cite exact
form IDs, QAC word references, attachment IDs, or ayah references from the artifact.

Do not assign any occurrence to a dictionary branch or sense. Do not infer a hidden
theme from proximity. Omit a claim when the artifact does not directly support it.
An empty `observations` array is valid.
