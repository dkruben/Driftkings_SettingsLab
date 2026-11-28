'use strict';
// Formatted-text preview: one logical line stays on one row with mixed colours, explicit breaks are kept, nested
// formatting is preserved, the sample macros the production formatter writes are resolved, and unknown macros are
// marked. The structure is asserted; actual Gameface line layout is not something the synthetic DOM can establish.
const assert = require('assert');
const {createEnvironment} = require('../../support/frontend/dom_fixture');
const env = createEnvironment(), {DK, document} = env;

function render(source, options) {
    const container = document.createElement('div');
    DK.richText.render(container, source, options);
    return container.children[0];         // the .dk-rich-line root
}
function rows(root) { return root.children.filter(child => child.className === 'dk-rich-row'); }
function text(node) { return node.textContent; }
function segments(row) { return row.children.filter(child => child.className.indexOf('dk-rich-seg') >= 0); }
function walk(node, visit) { visit(node); node.children.forEach(child => walk(child, visit)); }

// 1. The WN8/EFF/DIFF template: one logical line, mixed colours, no implicit break.
{
    const root = render("WN8: <font color='{c:wn8}'>{wn8}</font> EFF: <font color='{c:eff}'>{eff}</font> DIFF: <font color='{c:diff}'>{diff}</font>");
    assert.equal(rows(root).length, 1, 'one logical line, one row');
    assert.equal(text(root), 'WN8: 2150 EFF: 1650 DIFF: +120');
    const colours = segments(rows(root)[0]).map(seg => seg.style.color);
    assert.deepEqual(colours, ['#02C9B3', '#A6FFA6', '#F8F400'], 'each value keeps its semantic colour');
    walk(root, node => assert.ok(!node.style.height, 'no fixed height hides the content'));
}

// 2. Changing colour, bold or italic does not add a line.
{
    const root = render("<b>Bold</b> <i>Italic</i> <font color='#ff0000'>red</font> <font size='10'>small</font>");
    assert.equal(rows(root).length, 1);
    assert.equal(segments(rows(root)[0])[0].style.fontWeight, 'bold');
    assert.equal(segments(rows(root)[0])[1].style.fontStyle, 'italic');
}

// 3. Explicit breaks are kept, in each supported form: br, <br/>, and a newline character.
{
    assert.equal(rows(render('A<br>B')).length, 2);
    assert.equal(rows(render('A<br/>B')).length, 2);
    assert.equal(rows(render('A\nB')).length, 2, 'a newline in the template is a real break');
    assert.equal(rows(render('A<br><br>B')).length, 3, 'consecutive breaks keep their empty line');
}

// 4. Nested formatting stays nested inside its parent segment.
{
    const root = render("<font color='#ff0000'>A<font size='10'>B</font></font>");
    const outer = segments(rows(root)[0])[0];
    assert.equal(outer.style.color, '#FF0000');
    assert.equal(segments(outer).length, 1, 'the inner font is a child of the outer one');
    assert.equal(text(root), 'AB');
}

// 5. Alignment and paragraph margins apply to the rows they contain.
{
    const centred = render('Hi', {align: 'center'});
    assert.equal(rows(centred)[0].style.justifyContent, 'center');
    const block = render("<textformat leading='3'>One</textformat>");
    assert.equal(rows(block)[0].style.marginBottom, '3rem');
}

// 6. Sample macros the production formatter writes are resolved (no unknown marker), and unknown macros are marked.
{
    assert.equal(DK.richText.fill('{wnx}/{xwn8}/%(wnx)d'), '1480/1610/1480');
    assert.equal(DK.richText.fill('{c:wnx}'), '#02C9B3');
    assert.equal(DK.richText.fill('{nope}'), '‹nope›', 'an unsupported macro is marked, not silently dropped');
}

// 7. Template text is never parsed as markup: only the supported tags create elements.
{
    const root = render("<script>x</script>A<b>B</b>");
    walk(root, node => assert.notEqual(node.tagName, 'SCRIPT'));
    assert.equal(text(root), 'xAB', 'an unsupported tag is dropped, its text is kept as text');
    assert.ok(text(root).indexOf('<script>') < 0);
}

DK.app.dispose();
console.log('Formatted text preview: one logical line, explicit breaks, nested formatting, sample macros and safe DOM passed');
