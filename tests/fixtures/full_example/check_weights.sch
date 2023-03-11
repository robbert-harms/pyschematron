<rule xmlns="http://purl.oclc.org/dsdl/schematron">
  <assert test="xs:integer(@weight) le $max-weight" properties="pr_maxWeight pr_weight" diagnostics="di_too-heavy-en di_too-heavy-nl">
    Weight not correct (<value-of select="@weight"/> vs <value-of select="$max-weight"/> at <name/>).
  </assert>
</rule>
