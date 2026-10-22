// Builds timing-atlas.pptx. Run from a directory where pptxgenjs, react,
// react-dom, react-icons and sharp are installed:
//   NODE_PATH=<that dir>/node_modules node docs/slides/build.js <out.pptx> <apply_theme.js>
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const OUT = process.argv[2] || "timing-atlas.pptx";
const { applyTheme } = require(process.argv[3]);

const HEX = {
  ink: "1B2B34", white: "FFFFFF", teal: "1F6F78", pale: "EEF4F3",
  amber: "E3A33B", rust: "C8553D", slate: "6B7F86", sage: "9DBAB4", deep: "4A5859",
  rule: "C9D6D3",
};
const THEME = {
  name: "Timing Atlas",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: HEX.ink, lt1: HEX.white, dk2: HEX.teal, lt2: HEX.pale,
    accent1: HEX.teal, accent2: HEX.amber, accent3: HEX.rust,
    accent4: HEX.slate, accent5: HEX.sage, accent6: HEX.deep,
    hlink: HEX.teal, folHlink: HEX.slate,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "When does anatomy exist?";
pres.author = "David Osumi-Sutherland";
const C = pres.SchemeColor;
const S = pres.shapes;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.7, w: 11.7, h: 1.5,
        fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.3, w: 11.0, h: 1.0,
        fontSize: 22, color: C.accent5, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85,
        fontSize: 30, bold: true, color: C.text1, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.25, y: 6.95, w: 0.6, h: 0.35, fontSize: 12, color: C.accent4, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.5, w: 12.1, h: 0.9,
        fontSize: 32, bold: true, color: C.background1, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.25, y: 6.95, w: 0.6, h: 0.35, fontSize: 12, color: C.accent5, align: "right" },
});

// ------------------------------------------------------------------ helpers
let n = 0;
const id = (p) => `${p}-${++n}`;

function text(s, str, o) {
  s.addText(str, Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: C.text1,
    valign: "top", objectName: id("text") }, o));
}
function box(s, o) {
  s.addShape(o.rounded === false ? S.RECTANGLE : S.ROUNDED_RECTANGLE, Object.assign({
    rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2, width: 0 },
    objectName: id("box") }, o));
}
// An existence bar with its label inside.
function bar(s, x, y, w, label, o = {}) {
  s.addText(label, {
    shape: S.ROUNDED_RECTANGLE, rectRadius: 0.07, x, y, w, h: o.h || 0.36,
    fill: { color: o.fill || C.accent1, transparency: o.transparency || 0 },
    line: o.dashed ? { color: o.fill || C.accent1, width: 1.25, dashType: "dash" } : { color: o.fill || C.accent1, width: 0 },
    color: o.color || C.background1, fontSize: o.fontSize || 13, bold: !!o.bold,
    align: "left", valign: "middle", margin: [0, 8, 0, 8], isTextBox: true, objectName: id("bar"),
  });
}
function arrow(s, x1, y1, x2, y2, o = {}) {
  s.addShape(S.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color: o.color || C.accent6, width: o.width || 1.75, endArrowType: o.noHead ? undefined : "triangle",
      beginArrowType: o.both ? "triangle" : undefined, dashType: o.dash || "solid" },
    objectName: id("arrow"),
  });
}
// A row of contiguous stages. Returns at(i, f): x of stage i plus fraction f.
function ruler(s, x, y, w, labels, o = {}) {
  const h = o.h || 0.42, cw = w / labels.length;
  labels.forEach((lab, i) => {
    s.addText(lab, {
      shape: S.RECTANGLE, x: x + i * cw, y, w: cw, h,
      fill: { color: i % 2 ? C.background1 : C.background2 }, line: { color: C.accent5, width: 0.75 },
      fontSize: o.fontSize || 12, color: C.accent6, align: "center", valign: "middle", margin: 0,
      isTextBox: true, objectName: id("stage"),
    });
  });
  return (i, f = 0) => x + (i + f) * cw;
}
function chip(s, str, x, y, w, color) {
  s.addText(str, { shape: S.ROUNDED_RECTANGLE, rectRadius: 0.12, x, y, w, h: 0.38,
    fill: { color }, line: { color, width: 0 }, color: C.background1, fontSize: 13, bold: true,
    align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: id("chip") });
}
async function iconPng(Icon, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
// Icon in a filled circle -- the deck's small recurring device.
async function badge(s, Icon, x, y, d, circleColor, iconHex) {
  s.addShape(S.OVAL, { x, y, w: d, h: d, fill: { color: circleColor }, line: { color: circleColor, width: 0 }, objectName: id("badge") });
  s.addImage({ data: await iconPng(Icon, iconHex), x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52, objectName: id("icon") });
}
function slide(master, section, title) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}

(async () => {
  // ================================================================ 1 Title
  pres.addSection({ title: "Introduction" });
  {
    const s = slide("TITLE_DARK", "Introduction", "When does anatomy exist?");
    s.addText("Reasoning about developmental timing with an atlas of idealised individuals", { placeholder: "body" });
    text(s, "taxon-stage-axioms  ·  proof of concept  ·  October 2026", { x: 0.8, y: 4.45, w: 9, h: 0.4, fontSize: 16, color: C.accent4 });
    // motif: the five pharyngeal arches, staggered onsets, shared end
    const x0 = 6.2, cw = 0.85; // CS10..CS17 -> 8 stages
    const rows = [["arch 1", 0], ["arch 2", 0], ["arch 3", 1], ["arch 4", 2], ["arch 6", 2]];
    rows.forEach(([lab, st], i) => bar(s, x0 + (st + 0.5) * cw, 5.05 + i * 0.4, (7 - st) * cw, lab,
      { h: 0.3, fill: i % 2 ? C.accent2 : C.accent1, fontSize: 12, color: i % 2 ? C.text1 : C.background1 }));
    s.addNotes("This talk is about reasoning over when anatomical structures exist, relative to developmental stages and to each other. The bars at the bottom are the motif of the deck: each is the lifetime of a structure, here the five pharyngeal arches, which start at staggered Carnegie stages and all end together.");
  }

  // ================================================================ 2 Problem
  {
    const s = slide("CONTENT", "Introduction", "Two kinds of knowledge that never meet");
    text(s, "Uberon: what develops from what", { x: 0.6, y: 1.45, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const nodes = [["intermediate mesoderm", 0.6], ["metanephric mesenchyme", 3.45], ["metanephros", 6.3]];
    nodes.forEach(([lab, x]) => s.addText(lab, { shape: S.ROUNDED_RECTANGLE, rectRadius: 0.1, x, y: 2.0, w: 2.3, h: 0.62,
      fill: { color: C.background2 }, line: { color: C.accent1, width: 1.25 }, fontSize: 14, color: C.text1,
      align: "center", valign: "middle", isTextBox: true, objectName: id("node") }));
    arrow(s, 3.45, 2.31, 2.9, 2.31, { color: C.accent1 });
    arrow(s, 6.3, 2.31, 5.75, 2.31, { color: C.accent1 });
    text(s, "develops from", { x: 2.6, y: 2.72, w: 1.3, h: 0.3, fontSize: 12, color: C.accent6, align: "center" });
    text(s, "develops from", { x: 5.45, y: 2.72, w: 1.3, h: 0.3, fontSize: 12, color: C.accent6, align: "center" });

    text(s, "?", { x: 3.9, y: 3.15, w: 0.9, h: 0.8, fontSize: 40, bold: true, color: C.accent3, align: "center" });
    text(s, "nothing relates the two", { x: 4.8, y: 3.38, w: 3.5, h: 0.4, fontSize: 14, italic: true, color: C.accent3 });

    text(s, "Curated table: when each exists, in Carnegie stages", { x: 0.6, y: 4.05, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 0.6, 4.55, 8.0, ["CS9", "CS10", "CS11", "CS12", "CS13", "CS14", "CS15", "CS16"]);
    bar(s, at(0, 0.4), 5.1, at(7, 0.5) - at(0, 0.4), "intermediate mesoderm  CS9 – CS16");
    bar(s, at(4, 0.4), 5.55, at(8) - at(4, 0.4), "metanephric mesenchyme  from CS13", { fill: C.accent2, color: C.text1 });
    bar(s, at(5, 0.4), 6.0, at(8) - at(5, 0.4), "metanephros  from CS14", { fill: C.accent6 });

    box(s, { x: 9.1, y: 1.45, w: 3.65, h: 5.25, fill: { color: C.background2 } });
    text(s, "Questions we cannot answer today", { x: 9.35, y: 1.65, w: 3.2, h: 0.75, fontSize: 18, bold: true });
    const qs = ["Can a structure start before the thing it develops from?",
      "A structure has no curated stages. What follows from its precursors?",
      "Do two structures ever exist at the same time?"];
    qs.forEach((q, i) => {
      s.addShape(S.OVAL, { x: 9.35, y: 2.6 + i * 1.3, w: 0.42, h: 0.42, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: id("dot") });
      text(s, String(i + 1), { x: 9.35, y: 2.6 + i * 1.3, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle" });
      text(s, q, { x: 9.95, y: 2.55 + i * 1.3, w: 2.6, h: 1.1, fontSize: 15 });
    });
    s.addNotes("Uberon records developmental relations between structures. This repo curates when each structure exists, against Carnegie stages, with evidence. Both are present, but no axiom connects them, so the questions on the right have no answer in the ontology today. The rest of the talk is about making them meet.");
  }

  // ================================================================ 3 Classes to atlas
  {
    const s = slide("CONTENT", "Introduction", "From ontology classes to an atlas of one idealised embryo");
    box(s, { x: 0.6, y: 1.45, w: 5.3, h: 5.25 });
    text(s, "An ontology class", { x: 0.9, y: 1.65, w: 4.8, h: 0.45, fontSize: 20, bold: true, color: C.accent1 });
    for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
      const x = 1.0 + c * 1.18, y = 2.35 + r * 0.95;
      s.addShape(S.OVAL, { x, y, w: 0.95, h: 0.7, fill: { color: C.background1 }, line: { color: C.accent4, width: 1 }, objectName: id("embryo") });
      s.addShape(S.OVAL, { x: x + 0.38, y: y + 0.25, w: 0.2, h: 0.2, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: id("arch") });
    }
    text(s, "pharyngeal arch 3 stands for every arch 3, in every embryo, at every time. Axioms quantify over all of them.",
      { x: 0.9, y: 5.3, w: 4.8, h: 1.2, fontSize: 15 });

    arrow(s, 6.05, 3.6, 7.25, 3.6, { color: C.accent1, width: 2.5 });
    text(s, "generated from the OWL by macro expansion", { x: 5.95, y: 3.75, w: 1.45, h: 1.0, fontSize: 12, color: C.accent6, align: "center" });

    box(s, { x: 7.45, y: 1.45, w: 5.3, h: 5.25 });
    text(s, "An atlas individual", { x: 7.75, y: 1.65, w: 4.8, h: 0.45, fontSize: 20, bold: true, color: C.accent1 });
    s.addShape(S.OVAL, { x: 8.2, y: 2.3, w: 3.8, h: 2.75, fill: { color: C.background1 }, line: { color: C.accent4, width: 1.5 }, objectName: id("embryo") });
    const parts = [["arch 1", 8.85, 2.75], ["arch 2", 8.85, 3.25], ["arch 3", 8.85, 3.75], ["heart", 10.35, 2.95], ["liver", 10.35, 3.6], ["metanephros", 9.6, 4.35]];
    parts.forEach(([lab, x, y]) => {
      const hl = lab === "arch 3";
      s.addShape(S.OVAL, { x, y, w: 0.26, h: 0.26, fill: { color: hl ? C.accent2 : C.accent1 }, line: { color: hl ? C.accent2 : C.accent1, width: 0 }, objectName: id("part") });
      text(s, lab, { x: x + 0.34, y: y - 0.04, w: 1.4, h: 0.34, fontSize: 13, bold: hl });
    });
    text(s, "the arch 3 of one canonical human embryo: a single node where every fact about it meets.",
      { x: 7.75, y: 5.3, w: 4.8, h: 1.2, fontSize: 15 });
    s.addNotes("An anatomy ontology describes classes. An anatomical atlas describes one specimen. Make the specimen idealised, a canonical human embryo, and every structure it has a determinate number of becomes an individual. Nothing here is hand-curated: the atlas is generated from the class-level OWL by macro expansion, so the OWL stays the source of truth.");
  }

  // ================================================================ 4 Existence windows
  {
    const s = slide("CONTENT", "Introduction", "Every structure is an existence window");
    // one structure, two points
    text(s, "One structure: two time points", { x: 0.6, y: 1.45, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    bar(s, 2.0, 2.1, 4.6, "otic placode", { h: 0.42, fontSize: 14 });
    s.addShape(S.LINE, { x: 2.0, y: 1.95, w: 0.001, h: 0.75, line: { color: C.accent3, width: 2 }, objectName: id("tick") });
    s.addShape(S.LINE, { x: 6.6, y: 1.95, w: 0.001, h: 0.75, line: { color: C.accent3, width: 2 }, objectName: id("tick") });
    text(s, "s(X)  starts to exist", { x: 0.6, y: 2.75, w: 2.6, h: 0.35, fontSize: 14, color: C.accent3 });
    text(s, "e(X)  ceases", { x: 6.0, y: 2.75, w: 2.6, h: 0.35, fontSize: 14, color: C.accent3 });

    text(s, "A series: the window spans all members", { x: 0.6, y: 3.35, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 0.6, 3.85, 8.0, ["CS10", "CS11", "CS12", "CS13", "CS14", "CS15", "CS16", "CS17"]);
    const arches = [["arch 1", 0], ["arch 2", 0], ["arch 3", 1], ["arch 4", 2], ["arch 6", 2]];
    arches.forEach(([lab, st], i) => bar(s, at(st, 0.4), 4.4 + i * 0.38, at(7, 0.6) - at(st, 0.4), lab, { h: 0.3, fontSize: 12 }));
    bar(s, at(0, 0.4), 6.35, at(7, 0.6) - at(0, 0.4), "pharyngeal arch (generic): first start to last end", { h: 0.34, fill: C.accent2, color: C.text1, fontSize: 13, bold: true });

    box(s, { x: 9.1, y: 1.45, w: 3.65, h: 5.25 });
    const pts = [
      ["One per embryo", "liver, arch 3: the window is that structure's lifetime."],
      ["A series or population", "pharyngeal arch, somite, haemangioblast: the window runs from the first member's start to the last member's end."],
      ["Every term can join", "Windows keep every relation sound. Knowing a term is one per embryo only adds precision."],
    ];
    pts.forEach(([h, b], i) => {
      text(s, h, { x: 9.35, y: 1.7 + i * 1.65, w: 3.2, h: 0.4, fontSize: 16, bold: true });
      text(s, b, { x: 9.35, y: 2.1 + i * 1.65, w: 3.2, h: 1.15, fontSize: 14 });
    });
    s.addNotes("Every structure gets a start point and an end point. For something there is one of per embryo, that is its lifetime. For a series like the pharyngeal arches, or a population of cells, the generic term's window runs from the first member's start to the last member's end. Every relation we use stays sound on windows except transformations, which are exact only when the precursor is one per embryo. So nothing has to be excluded; countability only buys precision. Bars here are the curated arch bounds.");
  }

  // ================================================================ 5 Stages as individuals
  {
    const s = slide("CONTENT", "Introduction", "Stages are individuals too");
    text(s, "A series: consecutive stages share a boundary", { x: 0.6, y: 1.45, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const cw = 1.3, x0 = 0.6;
    ["CS9", "CS10", "CS11", "CS12", "CS13", "CS14"].forEach((lab, i) => bar(s, x0 + i * cw + 0.02, 2.0, cw - 0.04, lab,
      { h: 0.48, fill: i % 2 ? C.accent4 : C.accent6, fontSize: 14, bold: true }));
    const bx = x0 + 3 * cw;
    arrow(s, bx, 3.05, bx, 2.55, { color: C.accent3, width: 2 });
    text(s, "end(CS11) = start(CS12)", { x: bx - 1.6, y: 3.1, w: 3.2, h: 0.35, fontSize: 15, bold: true, color: C.accent3, align: "center" });
    text(s, "HsapDv: CS12 immediately_preceded_by CS11", { x: bx - 2.2, y: 3.45, w: 4.4, h: 0.35, fontSize: 13, color: C.accent6, align: "center" });

    text(s, "Nesting: part_of between stages", { x: 0.6, y: 4.05, w: 8, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    bar(s, 0.6, 4.6, 4.9, "embryonic stage", { h: 0.42, fill: C.accent6, fontSize: 14, bold: true });
    bar(s, 5.56, 4.6, 3.04, "fetal stage", { h: 0.42, fill: C.accent6, fontSize: 14, bold: true });
    [["CS1", 0.6], ["…", 1.84], ["CS22", 3.08], ["CS23", 4.32]].forEach(([lab, x]) => bar(s, x, 5.1, 1.18, lab,
      { h: 0.38, fill: C.accent4, fontSize: 12 }));
    ["week 9", "week 10", "…"].forEach((lab, i) => bar(s, 5.56 + i * 1.02, 5.1, 0.98, lab, { h: 0.38, fill: C.accent4, fontSize: 12 }));
    text(s, "No HsapDv edge says CS23 is followed by week 9. The order is still derived: CS23 ends within the embryonic stage, which immediately precedes the fetal stage, which contains week 9.",
      { x: 0.6, y: 5.75, w: 8.0, h: 0.95, fontSize: 14, color: C.accent6 });

    box(s, { x: 9.1, y: 1.45, w: 3.65, h: 5.25 });
    text(s, "No stage numbers", { x: 9.35, y: 1.7, w: 3.2, h: 0.4, fontSize: 16, bold: true });
    text(s, "Each stage is an interval with a start and an end. HsapDv's own relations order them, so sub-stages and nested stages need no special handling.",
      { x: 9.35, y: 2.1, w: 3.2, h: 1.9, fontSize: 14 });
    await badge(s, fa.FaExclamationTriangle, 9.35, 4.1, 0.55, C.accent3, HEX.white);
    text(s, "The check found an HsapDv error", { x: 10.0, y: 4.15, w: 2.6, h: 0.5, fontSize: 15, bold: true, color: C.accent3 });
    text(s, "Carnegie stage 05a is asserted both part of stage 05 and immediately after it. A part cannot begin when its whole ends.",
      { x: 9.35, y: 4.8, w: 3.2, h: 1.7, fontSize: 14 });
    s.addNotes("Stages get the same treatment as structures: each is an interval with two boundary points, never a single point. immediately_preceded_by makes two stages share a boundary; part_of nests one inside another. HsapDv has no edge from CS23 to week 9, but the order is derived through the embryonic and fetal stages. Running the stage ontology alone through the reasoner found one inconsistency in HsapDv itself.");
  }

  // ================================================================ 5a Limits
  {
    const s = slide("CONTENT", "Introduction", "Limits: an idealised atlas only works for countable structures");
    const rows = [
      ["One per embryo", "liver, notochord, pharyngeal arch 3", "exact", C.accent1, "single"],
      ["A series, each member named", "pharyngeal arches 1, 2, 3, 4, 6", "exact per member", C.accent1, "series"],
      ["Uncountable or variable", "haemangioblasts, chorionic villi, nephrons", "window only", C.accent2, "population"],
    ];
    rows.forEach(([h, ex, verdict, col, kind], i) => {
      const y = 1.5 + i * 1.75;
      box(s, { x: 0.6, y, w: 8.1, h: 1.55 });
      text(s, h, { x: 0.85, y: y + 0.2, w: 3.3, h: 0.4, fontSize: 17, bold: true });
      text(s, ex, { x: 0.85, y: y + 0.65, w: 3.3, h: 0.75, fontSize: 14, color: C.accent6 });
      const dx = 4.35, dw = 2.5;
      if (kind === "single") bar(s, dx + 0.3, y + 0.58, dw - 0.6, "arch 3", { h: 0.36, fontSize: 12 });
      if (kind === "series") [0, 0, 1, 2, 2].forEach((st, j) => bar(s, dx + st * 0.3, y + 0.2 + j * 0.24, dw - st * 0.3, "", { h: 0.18 }));
      if (kind === "population") {
        [[0.0, 0.7], [0.35, 0.9], [0.2, 1.2], [0.9, 0.8], [1.2, 1.0], [0.7, 1.5]].forEach(([o, w], j) =>
          s.addShape(S.ROUNDED_RECTANGLE, { x: dx + o, y: y + 0.18 + j * 0.11, w, h: 0.08, rectRadius: 0.03,
            fill: { color: C.accent4, transparency: 40 }, line: { color: C.accent4, width: 0 }, objectName: id("member") }));
        bar(s, dx, y + 0.95, dw, "one window", { h: 0.34, fill: C.accent2, color: C.text1, fontSize: 12 });
      }
      chip(s, verdict, 7.0, y + 0.58, 1.5, col);
    });

    box(s, { x: 9.1, y: 1.5, w: 3.65, h: 5.05, fill: { color: C.background2 } });
    text(s, "What else the model assumes away", { x: 9.35, y: 1.7, w: 3.2, h: 0.75, fontSize: 17, bold: true });
    text(s, [
      { text: "Variation between embryos: absorbed into the width of the stage bounds", options: { bullet: true, breakLine: true } },
      { text: "One sex and one anatomical variant per atlas", options: { bullet: true, breakLine: true } },
      { text: "One taxon per atlas", options: { bullet: true, breakLine: true } },
      { text: "Counts that grow over time (somites added one by one) need a term and bounds per member", options: { bullet: true } }],
      { x: 9.35, y: 2.55, w: 3.2, h: 3.9, fontSize: 14, paraSpaceAfter: 8 });
    text(s, "Uncountable terms still take part, but only as a window from first appearance to last disappearance. Timing per member is lost.",
      { x: 0.6, y: 6.75, w: 11.6, h: 0.45, fontSize: 14, italic: true, color: C.accent6 });
    s.addNotes("The atlas idea works cleanly only for things a normal embryo has a determinate number of: one liver, one arch 3, or a series whose members each have a term. For uncountable populations, or structures whose number varies, such as haemangioblasts, villi or nephrons, an individual doesn't stand for a real thing. They can still take part as a window from first appearance to last disappearance, which keeps reasoning sound but loses anything per member. The model also assumes away variation between embryos, sex and anatomical variants, and taxon: one idealised atlas each.");
  }

  // ================================================================ 5a2 Countability assessment
  {
    const s = slide("CONTENT", "Introduction", "How much developmental anatomy is countable?");
    const cats = ["one per embryo", "fixed number (mostly pairs)", "named series member", "whole series", "populations, repeated units", "abstract types"];
    const ehd = [35.8, 29.4, 26.1, 4.6, 3.6, 0.3];
    const ubn = [34.1, 11.4, 18.3, 9.3, 6.0, 21.0];
    const data = cats.map((c, i) => ({ name: c, labels: ["Uberon: our network (778)", "EHDAA2: all classes (2,456)"], values: [ubn[i], ehd[i]] }));
    s.addChart(pres.charts.BAR, data, {
      x: 0.6, y: 1.5, w: 8.1, h: 3.6, barDir: "bar", barGrouping: "percentStacked", barGapWidthPct: 45,
      chartColors: ["1F6F78", "3E8C93", "7FB5B9", "B9D7D8", "E3A33B", "A9B8BC"],
      catAxisLabelFontSize: 13, catAxisLabelColor: HEX.ink, catAxisLabelFontFace: "+mn-lt", catAxisLineShow: false,
      valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HEX.ink,
      showValue: false, showTitle: false, objectName: id("chart"),
    });
    text(s, [{ text: "Teal: countable.  ", options: { bold: true, color: C.accent1 } },
      { text: "Amber and grey: not countable.", options: { bold: true, color: C.accent6 } }],
      { x: 0.6, y: 5.2, w: 8.1, h: 0.35, fontSize: 13, align: "center" });
    const stats = [["96%", "of EHDAA2 classes are countable"],
      ["92%", "of EHDAA2's 2,125 develops_from edges have both ends countable"],
      ["50%", "are left/right pairs: usually fine as one window, since the sides develop together"]];
    stats.forEach(([num, lab], i) => {
      const y = 1.5 + i * 1.3;
      text(s, num, { x: 9.1, y, w: 1.55, h: 0.75, fontSize: 36, bold: true, color: i === 2 ? C.accent6 : C.accent1, fontFace: "Cambria" });
      text(s, lab, { x: 10.7, y: y + 0.05, w: 2.05, h: 1.15, fontSize: 14 });
    });
    box(s, { x: 0.6, y: 5.65, w: 12.15, h: 1.1, fill: { color: C.background2 } });
    text(s, [{ text: "Uberon scores lower mostly because of abstract classes ", options: { bold: true } },
      { text: "(organ, primordium), which enter the network only as superclass windows; without them it is 92% countable. Each term was classified from latent knowledge, by eight parallel model instances that agreed 100% on countable vs not over 50 shared terms. A Wikipedia check comes next." }],
      { x: 0.85, y: 5.75, w: 11.7, h: 0.95, fontSize: 14, valign: "middle" });
    s.addNotes("A first measurement of the limit on the previous slide. Every EHDAA2 class, and every Uberon structure in our timing network, was classified by how many separate structures it denotes in one embryo. 96% of EHDAA2 is countable, and 92% of its develops_from edges have both ends countable, which is what timing inference runs on. Half the countable terms are left and right pairs; for timing a pair is usually fine as one window. EHDAA2 is atlas-shaped by design, since it names series members and even splits cell populations by location. Uberon looks less countable, but that is almost all abstract classes; without them it is 92%. This is latent knowledge: eight parallel model instances agreed completely on countable versus not over fifty shared terms, which measures consistency rather than correctness. A Wikipedia check is next. Details in docs/countability-assessment.md.");
  }

  // ================================================================ 5b Templated metamodel
  {
    const s = slide("CONTENT", "Introduction", "The atlas is generated from Uberon by templates");
    text(s, "Uberon pattern", { x: 0.6, y: 1.45, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: C.accent1 });
    text(s, "Generated in the atlas", { x: 7.15, y: 1.45, w: 5.6, h: 0.4, fontSize: 16, bold: true, color: C.accent1 });
    const rows = [
      ["Class", "pharyngeal arch 3, in the human subset", "an individual with a start and an end", "arch3-human:  s, e"],
      ["Relation", "pharyngeal arch artery 3  ⊑  part_of some  pharyngeal arch 3", "a relation between two individuals", "part_of(artery3-human, arch3-human)"],
      ["Stage bound", "(pharyngeal arch 3 ⊓ in_taxon some Homo sapiens)  ⊑  existence_starts_during some CS11", "an ordering against stage points", "starts_during(arch3-human, CS11)"],
      ["Subclass", "hindbrain marginal layer  ⊑  neural tube marginal layer", "window inside window; axioms inherited", "within(hindbrain-ML, NT-ML)"],
    ];
    rows.forEach(([tag, pat, gloss, out], i) => {
      const y = 1.95 + i * 1.12;
      box(s, { x: 0.6, y, w: 5.3, h: 0.95 });
      text(s, tag, { x: 0.8, y: y + 0.08, w: 4.9, h: 0.3, fontSize: 12, bold: true, color: C.accent4 });
      text(s, pat, { x: 0.8, y: y + 0.36, w: 4.95, h: 0.55, fontSize: 13, fontFace: "Cambria" });
      arrow(s, 6.0, y + 0.47, 7.05, y + 0.47, { color: C.accent1, width: 2 });
      box(s, { x: 7.15, y, w: 5.6, h: 0.95, fill: { color: C.accent1 } });
      text(s, gloss, { x: 7.35, y: y + 0.08, w: 5.2, h: 0.3, fontSize: 12, bold: true, color: C.accent5 });
      text(s, out, { x: 7.35, y: y + 0.4, w: 5.2, h: 0.45, fontSize: 14, color: C.background1, fontFace: "Cambria" });
    });
    const notes = [["Deterministic", "identifiers are a function of term and taxon: …/individual/UBERON_0003114-9606"],
      ["Regenerated", "every build from the OWL; nothing about individuals is curated by hand"],
      ["Opt-in precision", "an annotation tags terms that are one per embryo"]];
    notes.forEach(([h, b], i) => {
      const x = 0.6 + i * 4.12;
      text(s, [{ text: h + ": ", options: { bold: true, color: C.accent1 } }, { text: b }], { x, y: 6.5, w: 3.95, h: 0.75, fontSize: 13 });
    });
    s.addNotes("The individuals are a templated metamodel of Uberon. A small set of templates turns each class-level pattern into atlas content: a class becomes an individual with a start and an end; an existential relation between classes becomes a relation between individuals; a taxon-scoped stage bound becomes an ordering against stage points; a subclass axiom nests one window inside another and passes its axioms down. Identifiers are deterministic, so nothing has to be allocated, and everything is regenerated from the OWL each build. Today the templates are SPARQL queries emitting Datalog facts; the same templates could emit OWL individuals.");
  }

  // ================================================================ 6 Why individuals
  pres.addSection({ title: "Why individuals" });
  {
    const s = slide("CONTENT", "Why individuals", "Why move timing reasoning to individuals");
    box(s, { x: 0.6, y: 1.45, w: 4.6, h: 5.25 });
    text(s, "Class layer: OWL", { x: 0.9, y: 1.65, w: 4.0, h: 0.45, fontSize: 20, bold: true, color: C.accent6 });
    const owl = [[fa.FaCheck, C.accent1, HEX.white, "Subsumption and inheritance, fast (ELK)"],
      [fa.FaTimes, C.accent3, HEX.white, "Composing two timing relations gives a set of possibilities; OWL can hold only one"],
      [fa.FaTimes, C.accent3, HEX.white, "No way to intersect two lines of evidence about the same thing"],
      [fa.FaTimes, C.accent3, HEX.white, "One conflict makes the whole ontology inconsistent"]];
    for (let i = 0; i < owl.length; i++) {
      const [I, cc, ih, t] = owl[i];
      await badge(s, I, 0.9, 2.3 + i * 1.08, 0.48, cc, ih);
      text(s, t, { x: 1.55, y: 2.27 + i * 1.08, w: 3.45, h: 0.95, fontSize: 14 });
    }

    arrow(s, 5.35, 4.05, 6.35, 4.05, { color: C.accent1, width: 2.5 });
    text(s, "generate", { x: 5.25, y: 4.2, w: 1.2, h: 0.35, fontSize: 13, color: C.accent6, align: "center" });

    box(s, { x: 6.5, y: 1.45, w: 6.25, h: 5.25, fill: { color: C.accent1 } });
    text(s, "Atlas layer: Datalog", { x: 6.8, y: 1.65, w: 5.6, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
    const dl = [[fa.FaCrosshairs, "Facts meet", "Bounds from a structure, its parts and its precursors all land on one node, and combine."],
      [fa.FaExchangeAlt, "Relations walk both ways", "\"What develops from X?\" is as easy as \"what does X develop from?\""],
      [fa.FaMapPin, "Conflicts are local", "A conflict is a derived fact with its explanation, not a failure of the whole run."],
      [fa.FaCogs, "New reasoning technology", "Exact and polynomial on endpoints; Soufflé scales; rule engines, ASP and provenance become usable."]];
    for (let i = 0; i < dl.length; i++) {
      const [I, h, b] = dl[i];
      await badge(s, I, 6.8, 2.3 + i * 1.08, 0.48, C.background1, HEX.teal);
      text(s, h, { x: 7.45, y: 2.25 + i * 1.08, w: 5.1, h: 0.35, fontSize: 16, bold: true, color: C.background1 });
      text(s, b, { x: 7.45, y: 2.6 + i * 1.08, w: 5.1, h: 0.65, fontSize: 14, color: C.background1 });
    }
    s.addNotes("The class layer stays in OWL: it is proven, and it is what feeds Uberon. But OWL is bad at exactly the operations timing needs. Allen-style composition gives disjunctions, OWL has no property intersection, and a single conflict makes the whole ontology inconsistent. On individuals, in Datalog, facts about one structure meet at one node, relations can be walked in both directions, and a conflict is just another derived fact, with its explanation. Because everything reduces to order constraints between endpoints, reasoning is exact and polynomial, and the door opens to rule engines, answer-set programming and provenance tooling.");
  }

  // ================================================================ 7 Allen
  pres.addSection({ title: "Relations in time" });
  {
    const s = slide("CONTENT", "Relations in time", "Allen's interval relations: a vocabulary for timing");
    const rels = [["p", "precedes", [0, 3], [5, 10]], ["m", "meets", [0, 4], [4, 10]], ["o", "overlaps", [0, 6], [4, 10]],
      ["F", "finished by", [0, 10], [5, 10]], ["D", "contains", [0, 10], [3, 7]], ["s", "starts", [0, 4], [0, 10]], ["e", "equals", [1, 9], [1, 9]]];
    const pw = 1.62, gap = 0.12, x0 = 0.6, y0 = 1.55;
    rels.forEach(([L, name, X, Y], i) => {
      const px = x0 + i * (pw + gap);
      box(s, { x: px, y: y0, w: pw, h: 2.9 });
      text(s, L, { x: px, y: y0 + 0.12, w: pw, h: 0.6, fontSize: 30, bold: true, color: C.accent1, align: "center", fontFace: "Cambria" });
      text(s, name, { x: px, y: y0 + 0.75, w: pw, h: 0.35, fontSize: 14, align: "center" });
      const ix = px + 0.16, iw = pw - 0.32, u = iw / 10;
      bar(s, ix + X[0] * u, y0 + 1.4, (X[1] - X[0]) * u, "X", { h: 0.34, fontSize: 12, bold: true });
      bar(s, ix + Y[0] * u, y0 + 1.95, (Y[1] - Y[0]) * u, "Y", { h: 0.34, fill: C.accent2, color: C.text1, fontSize: 12, bold: true });
    });
    text(s, "Swap X and Y and each becomes its converse, written in capitals: P, M, O, f, d, S. With equals, 13 relations in all; every pair of intervals stands in exactly one.",
      { x: 0.6, y: 4.75, w: 12.1, h: 0.75, fontSize: 16 });
    box(s, { x: 0.6, y: 5.65, w: 12.1, h: 1.05, fill: { color: C.background2 } });
    text(s, [{ text: "A string of letters means one of them. ", options: { bold: true } },
      { text: "dfOMP is \"X during, finishes, overlapped by, met by or preceded by Y\", which is simply: X starts after Y starts. That is the reading we give develops_from." }],
      { x: 0.85, y: 5.8, w: 11.6, h: 0.8, fontSize: 16, valign: "middle" });
    s.addNotes("James Allen's thirteen interval relations are the standard vocabulary for qualitative time. Seven are shown; the other six are their converses, written in capitals. Uncertainty is a set of relations, written as a string of letters. For example dfOMP covers every case where X starts after Y starts, which is exactly what we mean by develops_from.");
  }

  // ================================================================ 8 Mapping
  {
    const s = slide("CONTENT", "Relations in time", "Every relation becomes ≤ and < between endpoints");
    const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 } } });
    const row = (a, b, c) => [{ text: a }, { text: b, options: { fontFace: "Cambria" } }, { text: c, options: { bold: true, color: C.accent1, align: "center" } }];
    const rows = [
      [hdr("Relation"), hdr("As endpoints"), hdr("Allen, X to Y")],
      row("X starts during stage S", "start(S) ≤ s(X) < end(S)", "–"),
      row("X ends during stage S", "start(S) ≤ e(X) < end(S)", "–"),
      row("X develops_from Y", "s(Y) < s(X)", "dfOMP"),
      row("X directly_develops_from Y", "s(Y) < s(X) ≤ e(Y)", "dfOM"),
      row("X transformation_of Y", "e(Y) ≤ s(X)", "MP"),
      row("X immediate_transformation_of Y", "e(Y) = s(X)", "M"),
      row("X part_of Y (containment reading)", "s(Y) ≤ s(X), e(X) ≤ e(Y)", "sdfe"),
    ];
    s.addTable(rows, { x: 0.6, y: 1.5, w: 8.6, colW: [3.5, 3.6, 1.5], rowH: 0.6, fontSize: 15, color: C.text1,
      border: { type: "solid", pt: 0.75, color: HEX.rule }, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1], objectName: id("table") });

    box(s, { x: 9.6, y: 1.5, w: 3.15, h: 4.8, fill: { color: C.background2 } });
    text(s, "Why endpoints?", { x: 9.85, y: 1.7, w: 2.7, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    text(s, "Composing Allen relations produces sets of possibilities.", { x: 9.85, y: 2.2, w: 2.7, h: 0.9, fontSize: 14 });
    text(s, "Written as ≤ and < between endpoints, the same knowledge is decided exactly by transitive closure.", { x: 9.85, y: 3.1, w: 2.7, h: 1.2, fontSize: 14 });
    text(s, "Polynomial, with a derivation for every conclusion.", { x: 9.85, y: 4.35, w: 2.7, h: 0.8, fontSize: 14, bold: true });
    text(s, "Same-stage claims stay unordered: two structures that start in CS11 have no order unless something else gives one.",
      { x: 0.6, y: 6.45, w: 12.1, h: 0.45, fontSize: 14, italic: true, color: C.accent6 });
    s.addNotes("Every relation in play, stage bounds and developmental relations alike, is a conjunction of less-than and less-than-or-equal between endpoints. That is the convex point algebra, which transitive closure decides completely. So we reason over endpoints and read Allen relations off the result, rather than composing Allen relations directly. Granularity comes for free: two starts in the same stage stay unordered. The part_of row is one interpretation; slide 11 returns to it.");
  }

  // ================================================================ 8a Existing OBO relations
  {
    const s = slide("CONTENT", "Relations in time", "OBO timing relations already have Allen readings");
    text(s, "Between stages or processes", { x: 0.6, y: 1.45, w: 7.9, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const occ = [["X preceded_by Y", "BFO:0000062", "end(Y) ≤ start(X)", "MP", 0.3], ["X immediately_preceded_by Y", "RO:0002087", "end(Y) = start(X)", "M", 0]];
    occ.forEach(([rel, rid, def, allen, gap], i) => {
      const y = 1.95 + i * 0.95;
      box(s, { x: 0.6, y, w: 7.9, h: 0.8 });
      text(s, rel, { x: 0.8, y: y + 0.1, w: 3.2, h: 0.35, fontSize: 15, bold: true });
      text(s, rid + "   " + def, { x: 0.8, y: y + 0.45, w: 3.4, h: 0.3, fontSize: 12, color: C.accent6, fontFace: "Cambria" });
      bar(s, 4.4, y + 0.22, 1.4, "Y", { h: 0.34, fill: C.accent2, color: C.text1, fontSize: 12 });
      bar(s, 5.8 + gap, y + 0.22, 1.4, "X", { h: 0.34, fontSize: 12 });
      text(s, allen, { x: 7.55, y: y + 0.18, w: 0.8, h: 0.42, fontSize: 18, bold: true, color: C.accent1, align: "center", fontFace: "Cambria" });
    });

    text(s, "Structure to stage: when existence starts and ends", { x: 0.6, y: 3.95, w: 7.9, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 4.5, 4.45, 4.0, ["CS10", "CS11", "CS12", "CS13", "CS14"], { h: 0.38 });
    const cs = [["existence starts during CS11", "RO:0002488", 1, 1.5], ["existence ends during CS13", "RO:0002492", 3, 3.5],
      ["existence starts during or after CS11", "RO:0002496", 1, 5], ["existence ends during or before CS13", "RO:0002497", 0, 3.5]];
    cs.forEach(([lab, rid, a, b], i) => {
      const y = 4.95 + i * 0.44;
      s.addShape(S.LINE, { x: at(a), y: y + 0.17, w: at(Math.min(b, 5)) - at(a), h: 0.001,
        line: { color: i < 2 ? C.accent1 : C.accent4, width: 5 }, objectName: id("range") });
      text(s, [{ text: lab, options: { breakLine: false } }, { text: "   " + rid, options: { color: C.accent6 } }],
        { x: 0.6, y, w: 3.8, h: 0.34, fontSize: 12, color: C.text1, valign: "middle" });
    });

    box(s, { x: 9.0, y: 1.45, w: 3.75, h: 5.3, fill: { color: C.background2 } });
    text(s, "RO already defines these by start and end points", { x: 9.25, y: 1.65, w: 3.3, h: 0.75, fontSize: 16, bold: true });
    text(s, "That is the endpoint form the reasoner uses, so they map across directly.", { x: 9.25, y: 2.45, w: 3.3, h: 0.8, fontSize: 14 });
    text(s, "Some additions and corrections", { x: 9.25, y: 3.4, w: 3.3, h: 0.4, fontSize: 16, bold: true, color: C.accent3 });
    text(s, [
      { text: "a missing converse: starts after", options: { bullet: true, breakLine: true } },
      { text: "missing inverses on several existence relations", options: { bullet: true, breakLine: true } },
      { text: "one inequality the wrong way round", options: { bullet: true, breakLine: true } },
      { text: "open or closed interval ends, made consistent", options: { bullet: true } }],
      { x: 9.25, y: 3.85, w: 3.3, h: 2.8, fontSize: 14, paraSpaceAfter: 6 });
    s.addNotes("We are not inventing a timing vocabulary from scratch. OBO already has one, with Allen readings: preceded_by and immediately_preceded_by between stages and processes, and the existence relations that tie a structure's start or end to a stage. RO defines these in terms of start and end points, which is exactly the form the reasoner uses. A few additions and corrections are needed, listed on the right; the details are in the RO report.");
  }

  // ================================================================ 8b New C:C relations
  {
    const s = slide("CONTENT", "Relations in time", "New relations needed: timing between structures");
    const lv = [
      ["exists_after", "dfOMP", "X starts after Y starts", 0.6, 1.45, 7.0, 4.15, C.background2, C.text1],
      ["exists_directly_after", "dfOM", "… and no later than Y ends: no gap", 0.95, 2.55, 6.3, 2.9, C.accent5, C.text1],
      ["exists_immediately_after", "M", "X starts exactly as Y ends", 1.3, 3.65, 5.6, 1.6, C.accent1, C.background1],
    ];
    lv.forEach(([nm, al, gloss, x, y, w, h, fill, fg]) => {
      box(s, { x, y, w, h, fill: { color: fill } });
      text(s, nm, { x: x + 0.25, y: y + 0.15, w: w - 1.6, h: 0.4, fontSize: 17, bold: true, color: fg, fontFace: "Cambria" });
      text(s, al, { x: x + w - 1.35, y: y + 0.15, w: 1.1, h: 0.4, fontSize: 17, bold: true, color: fg === C.text1 ? C.accent1 : C.background1, align: "right", fontFace: "Cambria" });
      text(s, gloss, { x: x + 0.25, y: y + 0.55, w: w - 0.5, h: 0.35, fontSize: 14, color: fg });
    });
    bar(s, 1.55, 4.55, 2.2, "Y", { h: 0.3, fill: C.accent2, color: C.text1, fontSize: 12 });
    bar(s, 3.75, 4.85, 2.4, "X", { h: 0.3, fill: C.background1, color: C.text1, fontSize: 12 });

    text(s, "Developmental relations take a level", { x: 8.0, y: 1.45, w: 4.75, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const maps = [["develops_from", "exists_after"], ["transformation_of", "exists_after"],
      ["directly_develops_from", "exists_directly_after"], ["immediate_transformation_of", "exists_immediately_after"]];
    maps.forEach(([a, b], i) => {
      const y = 2.0 + i * 0.72;
      text(s, a, { x: 8.0, y, w: 4.75, h: 0.32, fontSize: 14, bold: true });
      text(s, "⊑  " + b, { x: 8.3, y: y + 0.32, w: 4.45, h: 0.32, fontSize: 13, color: C.accent1, fontFace: "Cambria" });
    });
    box(s, { x: 8.0, y: 5.0, w: 4.75, h: 1.75, fill: { color: C.background2 } });
    text(s, [{ text: "Why new? ", options: { bold: true } },
      { text: "RO has no timing relation between two structures. Making develops_from a kind of preceded_by is unsatisfiable: structures are continuants, preceded_by relates occurrents." }],
      { x: 8.2, y: 5.12, w: 4.35, h: 1.55, fontSize: 14 });
    text(s, "With them, OWL chains work too:  exists_after ∘ existence_starts_during ⊑ existence_starts_during_or_after.  Minted locally for now; to be proposed to RO.",
      { x: 0.6, y: 6.85, w: 12.1, h: 0.45, fontSize: 13, italic: true, color: C.accent6 });
    s.addNotes("To reason about timing from develops_from we need timing relations between two structures, and RO has none. The obvious shortcut, making develops_from a subproperty of preceded_by, is unsatisfiable, because structures are continuants and preceded_by relates occurrents. So three new continuant-to-continuant relations, nested: exists_after, X starts after Y starts; exists_directly_after, with no gap; and exists_immediately_after, X starts exactly as Y ends. Each developmental relation takes the appropriate level as a superproperty. With them, simple OWL property chains also carry timing from developmental relations onto stages. They are minted locally for now and would be proposed to RO.");
  }

  // ================================================================ 9 Inference from developmental relations
  {
    const s = slide("CONTENT", "Relations in time", "Timing inferred from developmental relations");
    text(s, "A bound nobody curated", { x: 0.6, y: 1.45, w: 6.6, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 0.6, 1.95, 6.6, ["CS10", "CS11", "CS12", "CS13", "CS14", "CS15"]);
    bar(s, at(2, 0.45), 2.6, at(6) - at(2, 0.45), "Y  starts during CS12  (curated)", { fill: C.accent2, color: C.text1 });
    bar(s, at(0, 0.1), 3.35, at(6) - at(0, 0.1), "X  no curated bounds", { fill: C.background2, color: C.accent6, dashed: true });
    text(s, "X develops_from Y   ⇒   s(Y) < s(X)", { x: 0.6, y: 4.0, w: 6.6, h: 0.4, fontSize: 16, bold: true, align: "center", fontFace: "Cambria" });
    arrow(s, at(2, 0.45), 4.5, at(2, 0.45), 4.85, { color: C.accent1, width: 2 });
    bar(s, at(2, 0.45), 4.95, at(6) - at(2, 0.45), "X  starts during or after CS12  (derived)", { bold: true });
    text(s, "On current data: 746 new bound statements on 344 structures.", { x: 0.6, y: 5.6, w: 6.6, h: 0.75, fontSize: 15 });

    box(s, { x: 7.65, y: 1.45, w: 5.1, h: 5.25 });
    text(s, "\"Directly develops from\" covers two shapes", { x: 7.9, y: 1.65, w: 4.6, h: 0.75, fontSize: 18, bold: true });
    text(s, "Budding: the precursor persists", { x: 7.9, y: 2.5, w: 4.6, h: 0.35, fontSize: 15, bold: true, color: C.accent1 });
    bar(s, 7.9, 2.95, 4.5, "neural tube", { fill: C.accent6 });
    bar(s, 9.6, 3.4, 2.8, "neural crest", { fill: C.accent2, color: C.text1 });
    text(s, "Transformation: the precursor becomes the product", { x: 7.9, y: 4.05, w: 4.6, h: 0.35, fontSize: 15, bold: true, color: C.accent1 });
    bar(s, 7.9, 4.5, 2.3, "otic placode", { fill: C.accent6 });
    bar(s, 10.2, 4.95, 2.2, "otic pit", { fill: C.accent2, color: C.text1 });
    text(s, "No separate budding relation is needed: it is direct development that is not a transformation. RO's current definition of directly_develops_from rules budding out, a change we would propose.",
      { x: 7.9, y: 5.55, w: 4.6, h: 1.1, fontSize: 13, color: C.accent6 });
    s.addNotes("Developmental relations carry timing. If Y starts during CS12 and X develops from Y, X cannot start before CS12, so X gains a bound nobody curated. Across the current data this yields 746 new bound statements, most of them one-sided. On the right: direct development comes in two shapes, budding where the precursor persists, as neural crest delaminating from the neural tube, and transformation where the precursor becomes the product. One relation covers both; budding is direct development minus transformation. RO's present wording of directly_develops_from forbids the budding case, which is one of the changes we would put to RO.");
  }

  // ================================================================ 10 part_of readings
  {
    const s = slide("CONTENT", "Relations in time", "What does part_of mean in time?");
    const cards = [
      ["Part exists only while the whole does", "containment", [[0.3, 4.1, "whole", C.accent6], [1.0, 2.7, "part", C.accent1]], "Every part_of edge constrains both ends of the part.", "10 conflicts", C.accent3],
      ["Part of the whole whenever both exist, and they do coexist", "overlap", [[0.3, 2.9, "whole", C.accent6], [1.9, 2.5, "part", C.accent1]], "Only overlap: each starts before the other ends.", "2 conflicts", C.accent2],
      ["Part of the whole whenever both exist", "nothing", [[0.3, 1.6, "whole", C.accent6], [2.4, 1.9, "part", C.accent1]], "True even of things that never coexist. No timing content.", "no constraint", C.accent4],
    ];
    const cw = 3.9, gap = 0.2;
    cards.forEach(([h, tag, bars, cap, res, rc], i) => {
      const x = 0.6 + i * (cw + gap);
      box(s, { x, y: 1.45, w: cw, h: 4.55 });
      text(s, h, { x: x + 0.25, y: 1.65, w: cw - 0.5, h: 0.95, fontSize: 17, bold: true });
      bars.forEach(([bx, bw, lab, col], j) => bar(s, x + 0.25 + bx * 0.78, 2.85 + j * 0.5, bw * 0.78, lab, { fill: col }));
      text(s, cap, { x: x + 0.25, y: 4.0, w: cw - 0.5, h: 1.0, fontSize: 15 });
      chip(s, res, x + 0.25, 5.25, 1.7, rc);
    });
    text(s, "The reading decides most of what the network can find. The 2 conflicts that survive the weak reading do not involve part_of at all.",
      { x: 0.6, y: 6.2, w: 12.1, h: 0.6, fontSize: 16, bold: true, color: C.accent6 });
    s.addNotes("part_of is the hardest relation to read in time. The strong reading, the 2005 OBO relations reading, says a part exists only while some whole does, so the part's lifetime lies inside the whole's. A more cautious reading says x is part of y at all times both exist. On its own that says nothing about timing, since it is true of things that never coexist; adding that they do coexist at some point gives overlap. On the current data, containment finds 10 conflicts; overlap finds 2, and those 2 don't involve part_of. Class-level quantification makes the cautious reading very hard to state in OWL. On individuals it is a single fact about two lifetimes.");
  }

  // ================================================================ 11 Test containment
  {
    const s = slide("CONTENT", "Relations in time", "Assume overlap, test containment edge by edge");
    text(s, "A part that outlives its whole", { x: 0.6, y: 1.45, w: 6.4, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 0.6, 1.95, 6.4, ["CS9", "CS10", "CS11", "CS12", "CS13"]);
    bar(s, at(0, 0.3), 2.6, at(2, 0.55) - at(0, 0.3), "otic placode  (whole)", { fill: C.accent6 });
    bar(s, at(2, 0.3), 3.1, at(3, 0.7) - at(2, 0.3), "otic pit  (part)", { fill: C.accent1 });
    arrow(s, at(2, 0.55), 3.75, at(3, 0.7), 3.75, { color: C.accent3, width: 2, both: true });
    text(s, "part outlives whole", { x: at(2, 0.55) - 0.2, y: 3.85, w: 2.4, h: 0.35, fontSize: 14, bold: true, color: C.accent3 });
    text(s, "The pit is the placode after it invaginates: a later phase of the same tissue, recorded as a part. With individuals we can say that directly: one tissue, passing through named phases.",
      { x: 0.6, y: 4.45, w: 6.4, h: 1.4, fontSize: 15 });

    const tiers = [["Errors", "Constrain with overlap: violations hold under any reasonable reading.", C.accent3],
      ["Warnings", "Check containment per edge: \"part outlives whole\", \"part predates whole\".", C.accent2],
      ["Conditional bounds", "Bounds that need containment are kept, labelled as such.", C.accent4]];
    tiers.forEach(([h, b, col], i) => {
      const y = 1.45 + i * 1.32;
      box(s, { x: 7.45, y, w: 5.3, h: 1.15, fill: { color: C.background2 } });
      chip(s, h, 7.65, y + 0.38, 2.1, col);
      text(s, b, { x: 9.95, y: y + 0.12, w: 2.65, h: 0.95, fontSize: 14, valign: "middle" });
    });
    box(s, { x: 7.45, y: 5.45, w: 5.3, h: 1.25, fill: { color: C.background1 }, line: { color: C.accent5, width: 1 } });
    text(s, [{ text: "5 part_of edges flagged. ", options: { bold: true } },
      { text: "3 look like phases (otic pit, neural groove, lung saccule); 2 are knock-on effects of other errors." }],
      { x: 7.7, y: 5.6, w: 4.85, h: 1.0, fontSize: 15, valign: "middle" });
    s.addNotes("Proposal: use the cautious reading, overlap, as the constraint, so errors are errors under any reading. Then test containment edge by edge and report failures as warnings. Bounds that rely on containment are kept but labelled. On the current data five part_of edges fail containment. Three look like phases of one tissue recorded as parts, such as the otic pit and otic placode; two are side effects of errors elsewhere. This is where individuals help most: we can represent one tissue passing through named phases, which classes cannot express.");
  }

  // ================================================================ 12 Curation
  pres.addSection({ title: "Curation" });
  {
    const s = slide("CONTENT", "Curation", "Curating start and end times, with evidence");
    const steps = [
      ["Claim", "neural tube marginal layer starts during CS12", "structure · predicate · stage · point or interval onset"],
      ["Evidence", "\"in most embryos a marginal layer begins to develop\"", "verbatim from O'Rahilly & Müller (1987), stage 12"],
      ["Verify", "checked as the record is written", "rejects paraphrase, wrong stage, mislabelled IDs, hidden hedges"],
      ["Publish", "taxon-scoped axiom in OWL", "only sourced rows are offered to Uberon"],
    ];
    const w = 2.85, gap = 0.27;
    steps.forEach(([h, ex, sub], i) => {
      const x = 0.6 + i * (w + gap);
      box(s, { x, y: 1.5, w, h: 2.9, fill: { color: i === 1 ? C.accent1 : C.background2 } });
      const fg = i === 1 ? C.background1 : C.text1;
      text(s, `${i + 1}  ${h}`, { x: x + 0.2, y: 1.68, w: w - 0.4, h: 0.45, fontSize: 20, bold: true, color: i === 1 ? C.background1 : C.accent1, fontFace: "Cambria" });
      text(s, ex, { x: x + 0.2, y: 2.25, w: w - 0.4, h: 1.0, fontSize: 15, bold: true, color: fg, italic: i === 1 });
      text(s, sub, { x: x + 0.2, y: 3.3, w: w - 0.4, h: 0.95, fontSize: 13, color: i === 1 ? C.background2 : C.accent6 });
      if (i < 3) arrow(s, x + w + 0.03, 2.95, x + w + gap - 0.03, 2.95, { color: C.accent1, width: 2 });
    });
    const stats = [["174", "live rows, 113 structures"], ["60", "with a quoted passage"], ["33", "ready to go to Uberon"]];
    stats.forEach(([num, lab], i) => {
      const x = 0.6 + i * 2.6;
      text(s, num, { x, y: 4.75, w: 2.4, h: 0.85, fontSize: 44, bold: true, color: C.accent1, fontFace: "Cambria" });
      text(s, lab, { x, y: 5.6, w: 2.4, h: 0.7, fontSize: 14, color: C.accent6 });
    });
    box(s, { x: 8.6, y: 4.7, w: 4.15, h: 2.0, fill: { color: C.background2 } });
    text(s, "End bounds are harder", { x: 8.85, y: 4.85, w: 3.7, h: 0.4, fontSize: 16, bold: true });
    text(s, "A start is usually observed: absent, then present. An end is often a naming decision: when an arch stops being an arch.",
      { x: 8.85, y: 5.3, w: 3.7, h: 1.3, fontSize: 14 });
    s.addNotes("Each row of the table is a claim: a structure, a predicate, a stage, and whether the onset is a definable point or progressive. Evidence is a verbatim passage from the staging reference, O'Rahilly and Müller 1987. A write-time check refuses any quote that isn't verbatim at the cited stage, any identifier whose label doesn't match, and any hedged passage recorded as unhedged. Only sourced rows are packaged for Uberon. Ends are harder than starts because many are naming decisions, not observations.");
  }

  // ================================================================ 13 Agentic loop
  {
    const s = slide("CONTENT", "Curation", "Towards an agentic curation loop");
    const cx = 4.0, cy = 4.1, rx = 2.5, ry = 2.0, bw = 2.1, bh = 0.95;
    const nodes = [["Propose", "agents draft bounds from literature"], ["Source", "find verbatim evidence in corpora"],
      ["Verify", "hooks check quote, stage and IDs"], ["Reason", "timing network checks consistency"], ["Triage", "conflicts become ranked tasks"]];
    const pos = nodes.map((_, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / 5; return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)]; });
    for (let i = 0; i < 5; i++) {
      const [x1, y1] = pos[i], [x2, y2] = pos[(i + 1) % 5];
      // start and end where the line leaves each box, plus a small gap
      const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
      const edge = Math.min((bw / 2) / Math.max(Math.abs(ux), 1e-6), (bh / 2) / Math.max(Math.abs(uy), 1e-6)) + 0.08;
      arrow(s, x1 + ux * edge, y1 + uy * edge, x2 - ux * edge, y2 - uy * edge, { color: C.accent4, width: 2 });
    }
    nodes.forEach(([h, b], i) => {
      const [x, y] = pos[i];
      const hl = i === 3 || i === 4;
      s.addShape(S.ROUNDED_RECTANGLE, { x: x - bw / 2, y: y - bh / 2, w: bw, h: bh, rectRadius: 0.1,
        fill: { color: hl ? C.accent1 : C.background2 }, line: { color: C.accent1, width: 1.25 }, objectName: id("loopnode") });
      text(s, h, { x: x - bw / 2 + 0.12, y: y - bh / 2 + 0.06, w: bw - 0.24, h: 0.34, fontSize: 15, bold: true, color: hl ? C.background1 : C.accent1 });
      text(s, b, { x: x - bw / 2 + 0.12, y: y - bh / 2 + 0.38, w: bw - 0.24, h: 0.44, fontSize: 12, color: hl ? C.background1 : C.text1 });
    });
    await badge(s, fa.FaUserCheck, cx - 0.4, cy - 0.55, 0.8, C.accent2, HEX.ink);
    text(s, "curator", { x: cx - 0.8, y: cy + 0.3, w: 1.6, h: 0.35, fontSize: 14, bold: true, align: "center" });

    box(s, { x: 7.7, y: 1.45, w: 5.05, h: 5.25 });
    text(s, "What the reasoner adds", { x: 7.95, y: 1.65, w: 4.6, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    text(s, "It tells agents and curators where to look. Each conflict names the two bounds and the Uberon path between them: which claim to source next, or which relation to question.",
      { x: 7.95, y: 2.1, w: 4.6, h: 1.6, fontSize: 15 });
    text(s, "Already in place", { x: 7.95, y: 3.85, w: 4.6, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    text(s, [{ text: "A stage-by-stage corpus of the staging reference, with a quote finder", options: { bullet: true, breakLine: true } },
      { text: "Write-time checks that reject unverifiable evidence", options: { bullet: true, breakLine: true } },
      { text: "The timing network, with conflict reports per axiom", options: { bullet: true } }],
      { x: 7.95, y: 4.3, w: 4.6, h: 2.2, fontSize: 15, paraSpaceAfter: 6 });
    s.addNotes("The pieces exist for a larger agentic loop. Agents propose bounds; a sourcing skill finds verbatim evidence; write-time hooks reject anything that can't be verified; the timing network checks the result against everything else; and conflicts come back as ranked tasks for agents and curators. The reasoner's contribution is direction: it says which claim, or which Uberon relation, deserves attention next.");
  }

  // ================================================================ 14 POC pipeline
  pres.addSection({ title: "Current experiments" });
  {
    const s = slide("CONTENT", "Current experiments", "The proof of concept");
    const col = (x, w, head, items, fill, fg) => {
      text(s, head, { x, y: 1.45, w, h: 0.4, fontSize: 16, bold: true, color: C.accent1 });
      items.forEach((it, i) => s.addText(it, { shape: S.ROUNDED_RECTANGLE, rectRadius: 0.08, x, y: 1.95 + i * 0.9, w, h: 0.75,
        fill: { color: fill }, line: { color: fill, width: 0 }, fontSize: 14, color: fg, align: "center", valign: "middle",
        margin: [0, 6, 0, 6], isTextBox: true, objectName: id("pipe") }));
    };
    col(0.6, 2.7, "Inputs", ["Curated table\n174 rows", "Uberon\n30k relations", "HsapDv\nstage order"], C.background2, C.text1);
    col(3.75, 2.4, "Export", ["SPARQL over the build artefacts", "facts, each tagged with its source axiom"], C.background2, C.text1);
    col(6.6, 2.9, "Reason (Soufflé)", ["semantics.dl\none rule per relation", "network.dl\nclosure, conflicts, bounds", "report.dl\nread-only views"], C.accent1, C.background1);
    col(9.95, 2.8, "Outputs", ["Conflicts, explained", "Bounds, new vs curated", "Queries"], C.accent2, C.text1);
    arrow(s, 3.35, 2.95, 3.7, 2.95, { color: C.accent1, width: 2 });
    arrow(s, 6.2, 2.95, 6.55, 2.95, { color: C.accent1, width: 2 });
    arrow(s, 9.55, 2.95, 9.9, 2.95, { color: C.accent1, width: 2 });

    const stats = [["778", "structures in the network"], ["1.1 M", "entailed orderings"], ["~15 s", "per reasoning pass"], ["193", "tests: hand-checked cases and random networks against a brute-force solver"]];
    stats.forEach(([num, lab], i) => {
      const x = 0.6 + i * 3.08;
      box(s, { x, y: 4.85, w: 2.88, h: 1.85, fill: { color: C.background2 } });
      text(s, num, { x: x + 0.2, y: 4.95, w: 2.5, h: 0.8, fontSize: 36, bold: true, color: C.accent1, fontFace: "Cambria" });
      text(s, lab, { x: x + 0.2, y: 5.75, w: 2.5, h: 0.9, fontSize: 13, color: C.accent6 });
    });
    s.addNotes("The proof of concept takes the curated table, Uberon's relations and HsapDv's stage order; exports them as facts with SPARQL, each fact tagged with the axiom it came from; and reasons in Soufflé. The reasoning is three short files: semantics, one rule per relation; the network, which is transitive closure plus conflict and bound extraction; and read-only report views. 778 structures, about 1.1 million entailed orderings, around 15 seconds a pass. 13 hand-checked cases and 180 random networks are checked against an independent brute-force solver.");
  }

  // ================================================================ 15 Queries
  {
    const s = slide("CONTENT", "Current experiments", "What you can ask the network");
    const cards = [
      [fa.FaClock, "Could two structures coexist?", [["heart tube · atrial septum primum", "never"], ["intermediate mesoderm · mesonephros", "certainly"], ["optic vesicle · optic cup", "unknown"]]],
      [fa.FaProjectDiagram, "What develops from intermediate mesoderm, and when?", [["metanephros", "CS14"], ["gonadal ridge", "CS15"], ["Müllerian duct", "CS16"]]],
      [fa.FaLayerGroup, "What is present during CS12?", [["certainly", "132"], ["possibly", "291"], ["e.g. arches, lung bud, forelimb bud", ""]]],
      [fa.FaHistory, "What must exist before metanephros starts?", [["ureteric bud", ""], ["metanephric mesenchyme", ""], ["mesonephros, and more", ""]]],
    ];
    for (let i = 0; i < 4; i++) {
      const [I, q, ans] = cards[i];
      const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 2.55;
      box(s, { x, y, w: 5.95, h: 2.35 });
      await badge(s, I, x + 0.25, y + 0.22, 0.55, C.accent1, HEX.white);
      text(s, q, { x: x + 0.95, y: y + 0.2, w: 4.8, h: 0.65, fontSize: 16, bold: true, valign: "middle" });
      ans.forEach(([a, v], j) => {
        text(s, a, { x: x + 0.95, y: y + 0.98 + j * 0.42, w: 3.6, h: 0.38, fontSize: 14 });
        if (v) text(s, v, { x: x + 4.55, y: y + 0.98 + j * 0.42, w: 1.2, h: 0.38, fontSize: 14, bold: true, color: v === "never" ? C.accent3 : C.accent1, align: "right" });
      });
    }
    text(s, "\"Certainly\" means entailed by the curated bounds plus Uberon. \"Unknown\": the optic vesicle ends and the optic cup starts in the same stage, so their order is open.",
      { x: 0.6, y: 6.6, w: 12.1, h: 0.5, fontSize: 13, italic: true, color: C.accent6 });
    s.addNotes("Four example queries, each a few lines of Datalog. Coexistence: never, certainly, or unknown, and unknown is honest. The optic vesicle ends and the optic cup starts in the same stage, so their order can't be settled from stage-level data. Derivatives walks develops_from backwards, which OWL can't. Presence during a stage separates certain from possible. And what must already exist when a structure starts.");
  }

  // ================================================================ 16 Conflicts
  {
    const s = slide("CONTENT", "Current experiments", "How a timing conflict is found");
    text(s, "Neural tube marginal layer vs mantle layer", { x: 0.6, y: 1.45, w: 7.4, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
    const at = ruler(s, 0.6, 1.95, 7.4, ["CS11", "CS12", "CS13", "CS14"]);
    bar(s, at(1, 0.35), 2.6, at(4) - at(1, 0.35), "marginal layer · CS12 · sourced", { fill: C.accent2, color: C.text1 });
    bar(s, at(2, 0.35), 3.1, at(4) - at(2, 0.35), "mantle layer · CS13 · sourced", { fill: C.accent6 });
    text(s, "Uberon:  marginal layer develops_from mantle layer", { x: 0.6, y: 3.75, w: 7.4, h: 0.4, fontSize: 15, bold: true, color: C.accent3 });
    box(s, { x: 0.6, y: 4.3, w: 7.4, h: 1.75, fill: { color: C.background2 } });
    text(s, [
      { text: "start(CS13)  ≤  s(mantle)", options: { breakLine: true } },
      { text: "                <  s(marginal)       develops_from", options: { breakLine: true } },
      { text: "                <  end(CS12)  =  start(CS13)", options: { breakLine: true } },
      { text: "⇒  a point strictly before itself", options: { bold: true, color: C.accent3 } }],
      { x: 0.85, y: 4.42, w: 7.0, h: 1.55, fontSize: 15, fontFace: "Cambria" });
    text(s, "Uberon's axiom note says the layer \"forms from axons\": what it is made of, not what it develops from.",
      { x: 0.6, y: 6.2, w: 7.4, h: 0.55, fontSize: 13, italic: true, color: C.accent6 });

    const steps = [["Find", "a chain of statements that puts some point strictly before itself"],
      ["Explain", "as two curated bounds plus the Uberon path joining them, with who asserted each"],
      ["Withhold and rerun", "set those axioms aside, so other bounds come from a consistent remainder"]];
    steps.forEach(([h, b], i) => {
      const y = 1.45 + i * 1.75;
      box(s, { x: 8.4, y, w: 4.35, h: 1.55 });
      s.addShape(S.OVAL, { x: 8.6, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: id("num") });
      text(s, String(i + 1), { x: 8.6, y: y + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle" });
      text(s, h, { x: 9.3, y: y + 0.22, w: 3.3, h: 0.4, fontSize: 16, bold: true });
      text(s, b, { x: 9.3, y: y + 0.62, w: 3.3, h: 0.85, fontSize: 14 });
    });
    s.addNotes("A worked conflict. O'Rahilly records a marginal layer at stage 12 and a mantle zone at stage 13; both bounds are sourced. Uberon says the marginal layer develops from the mantle layer. Chained together, the start of stage 13 ends up strictly before itself. The system reports this as the two bounds plus the one Uberon axiom joining them, then withholds the axioms involved and reruns, so the remaining bounds come from a consistent set.");
  }

  // ================================================================ 17 Findings
  {
    const s = slide("CONTENT", "Current experiments", "What the first run found");
    const stats = [["1", "inconsistency in HsapDv itself"], ["10", "timing conflicts, over 40 structures"], ["7", "point at Uberon's relations, not our stage data"]];
    stats.forEach(([num, lab], i) => {
      const x = 0.6 + i * 4.1;
      text(s, num, { x, y: 1.4, w: 1.15, h: 1.1, fontSize: 60, bold: true, color: i === 2 ? C.accent3 : C.accent1, fontFace: "Cambria", align: "right" });
      text(s, lab, { x: x + 1.35, y: 1.65, w: 2.55, h: 0.8, fontSize: 15, valign: "middle" });
    });
    const kinds = [
      [fa.FaUndoAlt, "An edge runs backwards", "neural plate regions made to develop from neural tube regions; lung saccule as part of the alveolus"],
      [fa.FaGlobeEurope, "True in other taxa", "amnion from amniotic folds, as in chick; the human amnion forms by cavitation"],
      [fa.FaClone, "part_of for a later phase", "otic pit recorded as part of the otic placode"],
      [fa.FaTable, "Our own data", "a point bound on a generic class, inherited by a subclass that starts later"],
    ];
    for (let i = 0; i < 4; i++) {
      const [I, h, b] = kinds[i];
      const x = 0.6 + i * 3.08;
      box(s, { x, y: 2.85, w: 2.88, h: 3.15 });
      await badge(s, I, x + 0.22, 3.05, 0.6, i === 3 ? C.accent4 : C.accent3, HEX.white);
      text(s, h, { x: x + 0.22, y: 3.8, w: 2.45, h: 0.7, fontSize: 16, bold: true });
      text(s, b, { x: x + 0.22, y: 4.3, w: 2.45, h: 1.6, fontSize: 14 });
    }
    text(s, "All four conflicts predicted in advance were found. Under the weakest part_of reading, 2 of the 10 remain.",
      { x: 0.6, y: 6.25, w: 12.1, h: 0.5, fontSize: 16, bold: true, color: C.accent6 });
    s.addNotes("The first run on real data. One inconsistency in HsapDv itself. Ten distinct timing conflicts over 40 structures, seven of which point at Uberon's relations rather than our stage data. They fall into recognisable kinds: an edge that runs backwards, a relation that holds in chick or mouse but not human, part_of used for a later phase of the same tissue, and one problem in our own table. The four conflicts predicted before the Datalog was written were all found. A written report for Uberon editors exists, with axioms, evidence and suggested fixes.");
  }

  // ================================================================ 17a Uberon issues in detail
  {
    const s = slide("CONTENT", "Current experiments", "Conflicts in detail: six Uberon issues");
    const cards = [
      [fa.FaUndoAlt, "Marginal layer from mantle layer", "NT marginal layer develops_from NT mantle layer  (note: \"forms from axons\")",
        "marginal starts CS12, mantle CS13; both sourced", "remove, or derive from the neuroepithelium", "likely error", C.accent3],
      [fa.FaUndoAlt, "Neural plate from neural tube", "neural plate regions develop_from presumptive regions, which develop_from neural tube regions  (XAO, ZFA)",
        "neural tube starts CS10 (sourced); neural plate CS8", "reverse the direction", "likely error", C.accent3],
      [fa.FaGlobeEurope, "Amnion and chorion from amniotic folds", "amnion, chorion develops_from amniotic fold develops_from somatopleure  (Kardong)",
        "amnion CS5, before lateral plate mesoderm (CS8)", "scope by taxon; the human amnion cavitates", "likely in human", C.accent3],
      [fa.FaUndoAlt, "Lung saccule as part of alveolus", "lung saccule part_of alveolus of lung  (source: GO)",
        "saccules from week 24, alveoli from week 36", "alveolus develops_from lung saccule", "likely error", C.accent3],
      [fa.FaClone, "Otic pit as part of otic placode", "otic pit part_of otic placode",
        "the pit ends in CS12, after the placode (CS11)", "develops_from, not part_of", "probable error", C.accent2],
      [fa.FaQuestion, "Chorionic villi after the allantois", "villus develops_from chorionic plate (MP-def); placenta develops_from allantois (Kardong)",
        "primary villi CS6 (sourced), allantois CS7", "decide which link gives way", "needs review", C.accent4],
    ];
    const cw = 3.95, ch = 2.6, gx = 0.125, gy = 0.15;
    for (let i = 0; i < cards.length; i++) {
      const [I, h, ax, col, fix, verdict, vc] = cards[i];
      const x = 0.6 + (i % 3) * (cw + gx), y = 1.45 + Math.floor(i / 3) * (ch + gy);
      box(s, { x, y, w: cw, h: ch });
      await badge(s, I, x + 0.2, y + 0.18, 0.45, vc, i === 4 ? HEX.ink : HEX.white);
      text(s, h, { x: x + 0.78, y: y + 0.15, w: cw - 0.95, h: 0.5, fontSize: 15, bold: true, valign: "middle" });
      text(s, ax, { x: x + 0.2, y: y + 0.75, w: cw - 0.4, h: 0.62, fontSize: 12, fontFace: "Cambria", color: C.accent6 });
      text(s, [{ text: "Collides with: ", options: { bold: true } }, { text: col }], { x: x + 0.2, y: y + 1.38, w: cw - 0.4, h: 0.5, fontSize: 13 });
      text(s, [{ text: "Suggested: ", options: { bold: true } }, { text: fix }], { x: x + 0.2, y: y + 1.88, w: cw - 1.9, h: 0.65, fontSize: 13 });
      chip(s, verdict, x + cw - 1.65, y + ch - 0.55, 1.45, vc);
    }
    s.addNotes("The six groups of Uberon axioms in more detail. Each card gives the axiom under suspicion, with its provenance where Uberon records one, what it collides with, and a suggested fix. The strongest case is the first: both bounds are quoted from O'Rahilly, so the develops_from edge between them must be wrong. Two of the axioms came in from frog and zebrafish anatomy, two from a comparative anatomy textbook and one from a mouse phenotype definition. That fits a pattern: relations imported from other taxa, applied to human. A full written report with derivations is in docs/uberon-timing-conflicts.md.");
  }

  // ================================================================ 17b How solid is each conflict
  {
    const s = slide("CONTENT", "Current experiments", "How solid is each conflict?");
    const H = (t, al) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 }, align: al || "left" } });
    const ev = { both: ["both sourced", C.accent1], one: ["one sourced", C.accent6], none: ["unsourced", C.accent4] };
    const R = (k, pair, axiom, e, needs, culprit) => [
      { text: String(k), options: { align: "center", color: C.accent4 } },
      { text: pair },
      { text: axiom, options: { fontFace: "Cambria", color: C.accent6 } },
      { text: ev[e][0], options: { color: ev[e][1], bold: e === "both" } },
      { text: needs ? "yes" : "no", options: { align: "center", bold: !needs, color: needs ? C.accent6 : C.accent1 } },
      { text: culprit, options: { bold: true, color: culprit.startsWith("our") ? C.accent4 : C.accent3 } },
    ];
    const rows = [
      [H("#", "center"), H("Bounds in conflict"), H("Axiom in question"), H("Evidence"), H("Needs containment", "center"), H("Likely culprit")],
      R(1, "NT mantle CS13 · NT marginal CS12", "marginal develops_from mantle", "both", false, "Uberon"),
      R(2, "posterior NT CS10 · neural plate CS8", "chain via presumptive hindbrain (XAO)", "none", false, "Uberon"),
      R(3, "neural tube CS10 · neural plate CS8", "the same chain, via posterior NT part_of NT", "one", true, "Uberon"),
      R(4, "lateral plate mesoderm CS8 · amnion CS5", "amnion via amniotic fold", "none", true, "Uberon, taxon"),
      R(5, "lateral plate mesoderm CS8 · villus CS6", "chorion via amniotic fold", "one", true, "Uberon, taxon"),
      R(6, "allantois CS7 · chorionic villus CS6", "villus develops_from chorionic plate", "one", true, "Uberon, review"),
      R(7, "alveolus wk36 · lung saccule wk24", "saccule part_of alveolus", "none", true, "Uberon"),
      R(8, "otic pit ends CS12 · placode ends CS11", "pit part_of placode", "one", true, "Uberon"),
      R(9, "groove ends CS11 · plate ends CS10", "neural groove part_of neural plate", "one", true, "our plate end?"),
      R(10, "rhombic lip CS16 · NT marginal CS12", "generic bound inherited by cerebellum layer", "both", true, "our table"),
    ];
    s.addTable(rows, { x: 0.6, y: 1.4, w: 12.1, colW: [0.45, 3.7, 3.65, 1.4, 1.3, 1.6], rowH: 0.42, fontSize: 13, color: C.text1,
      border: { type: "solid", pt: 0.75, color: HEX.rule }, valign: "middle", margin: [0.03, 0.08, 0.03, 0.08], objectName: id("table") });
    text(s, [{ text: "Strongest: ", options: { bold: true, color: C.accent1 } },
      { text: "1 and 2 hold even under the weakest part_of reading. 1 rests on two quoted bounds. Most others need containment, or rest on unsourced bounds that sourcing would settle." }],
      { x: 0.6, y: 6.4, w: 11.5, h: 0.55, fontSize: 14 });
    s.addNotes("All ten conflicts, ranked by how much they rest on. Two hold even under the weakest reading of part_of, and one of those, the marginal and mantle layers, rests on two quoted bounds, which makes it the strongest single finding. Most of the rest depend on reading part_of as containment, or rest on unsourced bounds, so they are candidates rather than verdicts. Sourcing those bounds is exactly the agentic curation task from earlier. Two of the ten are our own: a plate end bound that is probably too early, and a point bound on a generic class.");
  }

  // ================================================================ 18 Next
  pres.addSection({ title: "Next" });
  {
    const s = slide("CLOSING_DARK", "Next", "Open questions and next steps");
    const items = [
      [fa.FaBalanceScale, "Settle the part_of reading", "overlap as the constraint, containment as warnings"],
      [fa.FaRulerHorizontal, "Fix interval endpoints", "\"ends during\" should be half-open"],
      [fa.FaVial, "Leave-one-out evaluation", "hide a curated bound, re-derive it, score it"],
      [fa.FaExpandArrowsAlt, "Scale to EHDAA2", "2,125 bounded develops_from edges, human, Carnegie-staged"],
      [fa.FaRobot, "Wire into agentic curation", "conflicts as ranked tasks for sourcing"],
      [fa.FaShareSquare, "Take findings upstream", "Uberon issues; HsapDv fix; continuant-to-continuant timing relations for RO"],
    ];
    for (let i = 0; i < items.length; i++) {
      const [I, h, b] = items[i];
      const x = 0.6 + (i % 2) * 6.2, y = 1.9 + Math.floor(i / 2) * 1.7;
      await badge(s, I, x, y, 0.7, C.accent1, HEX.white);
      text(s, h, { x: x + 0.95, y: y - 0.02, w: 5.0, h: 0.4, fontSize: 18, bold: true, color: C.background1 });
      text(s, b, { x: x + 0.95, y: y + 0.42, w: 5.0, h: 0.75, fontSize: 15, color: C.accent5 });
    }
    s.addNotes("Next steps. Decide the part_of reading. Fix the endpoint convention for ends. Measure the network properly by hiding curated bounds and re-deriving them. Scale to EHDAA2, which is human and Carnegie-staged, so the semantics carry over unchanged. Connect the reasoner to agentic curation. And take the findings upstream: Uberon issues, the HsapDv fix, and a proposal for continuant-to-continuant timing relations in RO.");
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
