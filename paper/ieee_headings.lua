-- IEEE-style heading numbers: "I.", "II." for sections; "A.", "B." for subsections.
-- Headings with the class "unnumbered" (pandoc {-}) are left as written.
local roman = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"}
local section, subsection = 0, 0

function Header(el)
  if el.classes:includes("unnumbered") then
    return el
  end
  if el.level == 1 then
    section, subsection = section + 1, 0
    table.insert(el.content, 1, pandoc.Str(roman[section] .. ".\u{00A0}"))
  elseif el.level == 2 then
    subsection = subsection + 1
    table.insert(el.content, 1, pandoc.Str(string.char(64 + subsection) .. ".\u{00A0}"))
  end
  return el
end
