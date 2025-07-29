def get_tab_value(data):
    parameters = {
        "nscf_kpoints_distance": data["kPointsDistance"],
        "use_pdos_degauss": data["usePdosDegauss"],
        "pdos_degauss": data["pdosDegauss"],
        "energy_grid_step": data["energyGridStep"],
    }
    return parameters
