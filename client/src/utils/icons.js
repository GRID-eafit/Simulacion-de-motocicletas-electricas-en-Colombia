import L from "leaflet";
export function makeColoredIcon(hex, num, type = "normal") {
  const color = hex.replace("#", "%23");
  const borderColor = type === "start" ? "%23ffffff" : (type === "end" ? "%23000000" : color);
  const svg = `
  <svg width="28" height="42" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
    <path d="M12.5 0C5.6 0 0 5.6 0 12.5c0 9.2 12.5 28.5 12.5 28.5S25 21.7 25 12.5C25 5.6 19.4 0 12.5 0z"
      fill="${color}" stroke="${borderColor}" stroke-width="2"/>
    <circle cx="12.5" cy="12.5" r="5" fill="%23ffffff"/>
    <text x="12.5" y="15" text-anchor="middle" font-size="10" font-family="Arial" fill="%23000" font-weight="bold">${num}</text>
  </svg>`;
  const url = `data:image/svg+xml;utf8,${svg.trim()}`;
  return L.icon({ iconUrl: url, iconSize: [28, 42], iconAnchor: [14, 42], popupAnchor: [0, -40],
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png", shadowSize: [41, 41], shadowAnchor: [12, 41] });
}