from fastapi.routing import APIRoute

from backend.api import cost, energy, maintenance, occupancy


def _query_fields(router):
    fields = {}
    for route in router.routes:
        if isinstance(route, APIRoute):
            fields.update({field.name: field for field in route.dependant.query_params})
    return fields


def _constraint(field, name):
    return next(item for item in field.field_info.metadata if type(item).__name__ == name)


def test_expensive_windows_and_lists_have_bounds():
    energy_fields = _query_fields(energy.router)
    occupancy_fields = _query_fields(occupancy.router)
    cost_fields = _query_fields(cost.router)
    maintenance_fields = _query_fields(maintenance.router)

    assert _constraint(energy_fields["days"], "Ge").ge == 1
    assert _constraint(energy_fields["days"], "Le").le == 31
    assert _constraint(energy_fields["limit"], "Le").le == 1000
    assert _constraint(occupancy_fields["days"], "Le").le == 31
    assert _constraint(occupancy_fields["limit"], "Le").le <= 1000
    assert _constraint(cost_fields["months"], "Le").le == 24
    assert _constraint(cost_fields["limit"], "Le").le <= 1000
    assert _constraint(maintenance_fields["limit"], "Le").le == 500


def test_maintenance_seed_requires_one_facility():
    fields = _query_fields(maintenance.router)

    assert fields["facility_id"].required
    assert _constraint(fields["facility_id"], "MaxLen").max_length == 64


def test_seed_endpoints_require_explicit_facility_selection():
    for router in (energy.router, occupancy.router, cost.router):
        fields = _query_fields(router)
        assert fields["facility_id"].required