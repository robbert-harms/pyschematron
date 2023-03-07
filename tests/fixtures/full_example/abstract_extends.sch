<rule xmlns="http://purl.oclc.org/dsdl/schematron">
    <assert test="parent::$pv_category">
        The item <name/> is in the wrong category ($pv_category) (external check).
    </assert>
</rule>
