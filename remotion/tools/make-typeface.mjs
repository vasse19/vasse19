// Converts an OTF/TTF font into three's JSON typeface format (same algorithm as three's TTFLoader,
// which imports opentype.js from a CDN and so cannot run offline). Keeps Latin glyphs only.
import fs from "node:fs";
import opentype from "opentype.js";

const [src, out] = process.argv.slice(2);
const font = opentype.loadSync(src);
const round = Math.round;
const scale = 100000 / ((font.unitsPerEm || 2048) * 72);
const glyphs = {};
const keep = (cp) => cp >= 0x20 && cp <= 0x24f;
for (const [unicode, index] of Object.entries(font.encoding.cmap.glyphIndexMap)) {
  if (!keep(Number(unicode))) continue;
  const glyph = font.glyphs.get(index);
  const token = { ha: round(glyph.advanceWidth * scale), x_min: round(glyph.xMin * scale), x_max: round(glyph.xMax * scale), o: "" };
  for (const c of glyph.path.commands) {
    token.o += (c.type.toLowerCase() === "c" ? "b" : c.type.toLowerCase()) + " ";
    if (c.x !== undefined) token.o += round(c.x * scale) + " " + round(c.y * scale) + " ";
    if (c.x1 !== undefined) token.o += round(c.x1 * scale) + " " + round(c.y1 * scale) + " ";
    if (c.x2 !== undefined) token.o += round(c.x2 * scale) + " " + round(c.y2 * scale) + " ";
  }
  glyphs[String.fromCodePoint(Number(unicode))] = token;
}
const json = {
  glyphs,
  familyName: font.getEnglishName("fullName"),
  ascender: round(font.ascender * scale),
  descender: round(font.descender * scale),
  underlinePosition: font.tables.post.underlinePosition,
  underlineThickness: font.tables.post.underlineThickness,
  boundingBox: { xMin: font.tables.head.xMin, xMax: font.tables.head.xMax, yMin: font.tables.head.yMin, yMax: font.tables.head.yMax },
  resolution: 1000,
  original_font_information: font.tables.name,
};
fs.writeFileSync(out, JSON.stringify(json));
console.log("wrote", out, Object.keys(glyphs).length, "glyphs");
