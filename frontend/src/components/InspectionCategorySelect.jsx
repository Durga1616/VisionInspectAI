const CATEGORIES = [
  "bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather",
  "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper",
];

const title = (value) =>
  value.replace("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());

function InspectionCategorySelect({ value, onChange }) {
  return (
    <label>
      Product category
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {CATEGORIES.map((category) => (
          <option key={category} value={category}>
            {title(category)}
          </option>
        ))}
      </select>
    </label>
  );
}

export default InspectionCategorySelect;
