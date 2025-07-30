"""
Contains css styles.

NOTE: this module is private. All functions and objects are available in the main
`cfgtools` namespace - use that instead.

"""

__all__ = []

TREE_CSS_STYLE = """<style type="text/css">
.cfgtools-tree li.m {
    display: block;
    position: relative;
    padding-left: 2.5rem;
}
.cfgtools-tree li.t, li.i {
    display: block;
    position: relative;
    padding-left: 0;
}
.cfgtools-tree li.i>span {
    border: solid .1em #666;
    border-radius: .2em;
    display: inline-block;
    margin-top: .5em;
    padding: .2em .5em;
    position: relative;
}
.cfgtools-tree li>details>summary>span.open, li>details[open]>summary>span.closed {
    display: none;
}
.cfgtools-tree li>details[open]>summary>span.open {
    display: inline;
}
.cfgtools-tree li>details>summary {
    display: block;
    cursor: pointer;
}
.cfgtools-tree ul {
    display: table;
    padding-left: 0;
    margin-left: 0;
}
</style>"""
