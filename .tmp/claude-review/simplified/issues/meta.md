TITLE: Resolver fixes: overview and merge order

Seven PRs fix `$ref`/`$id` resolution bugs. They replace the earlier chain of eight (#2, #8–#12, #14, #16). The naming fix of #3/#8 is left to horejsek/python-fastjsonschema#224.

| PR | Fixes | Base branch | Needs |
|---|---|---|---|
| #{P_DATA} data keywords | #{I_DATA} | `master` | – |
| #{P_UNCHANGED} schema unchanged | #{I_UNCHANGED} | `master` | – (release together with #{P_HANDLER}) |
| #{P_URN} urn: ids | #{I_URN} | #{P_DATA} | #{P_DATA}, horejsek/python-fastjsonschema#224 |
| #{P_ARRAYS} schema arrays | #{I_ARRAYS} | merge of #{P_DATA} + #{P_UNCHANGED} | #{P_DATA}, #{P_UNCHANGED} |
| #{P_REL} relative ids | #{I_REL} | #{P_UNCHANGED} | #{P_UNCHANGED} |
| #{P_HANDLER} loaded schemas | #{I_HANDLER} | #{P_REL} | #{P_REL} |
| #{P_SIB} definitions next to $ref | #{I_SIB} | merge of all others | all others |

- #{P_DATA} and #{P_UNCHANGED} can be merged now, in any order.
- A PR with two parents targets a merge branch (`simple/base-for-walk-schema-arrays`, `simple/integration-base`), so its diff shows only its own change. Retarget it to `master` once its parents are merged.
