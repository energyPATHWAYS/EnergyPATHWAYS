update "DemandFuelSwitchingMeasures" as orig set name = (
select concat(dfsm.name, ' - ', ds.name, ' - ', fe1.name, ' to ', fe2.name)
from "DemandFuelSwitchingMeasures" as dfsm,
     "DemandSubsectors" as ds,
     "FinalEnergy" as fe1,
     "FinalEnergy" as fe2
where dfsm.id = orig.id and
      dfsm.subsector_id = ds.id and
      dfsm.final_energy_from_id = fe1.id and
      dfsm.final_energy_to_id = fe2.id)
where orig.id not in (2, 3);
