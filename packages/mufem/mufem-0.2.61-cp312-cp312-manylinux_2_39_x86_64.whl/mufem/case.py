import mufem
from mufem.thermal import (
    SolidTemperatureMaterial,
    SolidTemperatureModel,
    TemperatureCondition,
)


sim = mufem.Simulation.New("Test case", f"geometry.nm2")

# Setup Problem
steady_runner = mufem.SteadyRunner(total_iterations=3)
sim.set_runner(steady_runner)

thermal_domain = mufem.Marker(mufem.Where.Volume, [1])

thermal_model = SolidTemperatureModel(thermal_domain)
sim.get_model_manager().add_model(thermal_model)

gold_material = SolidTemperatureMaterial.Constant(
    "Gold",
    thermal_domain,
    thermal_conductivity=237.0,
    heat_capacity=129.0,
    density=19320,
)

thermal_model.add_materials([gold_material])

# Boundaries
cond_T300 = mufem.Marker(mufem.Where.Boundary, [5])
cond_T400 = mufem.Marker(mufem.Where.Boundary, [6])

bc_T300 = TemperatureCondition.Constant("Temperature = 300K", cond_T300, 300)
bc_T400 = TemperatureCondition.Constant("Temperature = 400K", cond_T400, 400)

thermal_model.add_conditions([bc_T300, bc_T400])

sim.run()
