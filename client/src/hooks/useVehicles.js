import { useEffect, useState } from "react";
export default function useVehicles() {
  const [vehicles, setVehicles] = useState(() => [{ id: "moto-1", waypoints: [] }]);
  const [activeVehicle, setActiveVehicle] = useState(0);
  const [lastPoint, setLastPoint] = useState();

  useEffect(() => {
    const wp = vehicles[activeVehicle]?.waypoints || [];
    if (wp.length > 0) {
      const [lng, lat] = wp[wp.length - 1].coordinates;
      setLastPoint({ lat, lng });
    } else setLastPoint(undefined);
  }, [vehicles, activeVehicle]);

  const addVehicle = () => { setVehicles(v => [...v, { id: `moto-${v.length + 1}`, waypoints: [] }]); setActiveVehicle(vehicles.length); };
  const removeVehicle = () => {
    if (vehicles.length <= 1) return;
    const idx = activeVehicle;
    setVehicles(prev => prev.filter((_, i) => i !== idx).map((v, i2) => ({ ...v, id: `moto-${i2 + 1}` })));
    setActiveVehicle(0);
  };
  const handleAddWaypoint = (lnglat) => {
    setVehicles(prev => { const copy = prev.slice(); const cur = copy[activeVehicle];
      copy[activeVehicle] = { ...cur, waypoints: [...cur.waypoints, { coordinates: lnglat }] }; return copy; });
    setLastPoint({ lat: lnglat[1], lng: lnglat[0] });
  };
  const undoWaypoint = () => { setVehicles(prev => { const c = prev.slice(); const cur = c[activeVehicle]; c[activeVehicle] = { ...cur, waypoints: cur.waypoints.slice(0, -1) }; return c; }); };
  const clearAll = () => { setVehicles(vs => vs.map(v => ({ ...v, waypoints: [] }))); setLastPoint(undefined); };
  const removeWaypointAt = (idx) => { setVehicles(prev => { const copy = prev.slice(); const cur = copy[activeVehicle];
      copy[activeVehicle] = { ...cur, waypoints: cur.waypoints.filter((_, i) => i !== idx) }; return copy; }); };
  const clearWaypointsActive = () => { setVehicles(prev => { const copy = prev.slice(); copy[activeVehicle] = { ...copy[activeVehicle], waypoints: [] }; return copy; }); };

  return { vehicles, setVehicles, activeVehicle, setActiveVehicle, lastPoint, setLastPoint,
    addVehicle, removeVehicle, handleAddWaypoint, undoWaypoint, clearAll, removeWaypointAt, clearWaypointsActive };
}