from marshmallow import Schema, fields, pprint


class ScenarioRunStatusSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.Str(requried=True)
    description = fields.Str(required=True)


class ScenarioSchema(Schema):
    id = fields.Integer()
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    demand_package_group_ids = fields.List(fields.Integer, required=True)
    supply_package_group_ids = fields.List(fields.Integer, required=True)
    # this is ignored when writing but provided on reading since it may be useful for the web interface to group
    # built-in scenarios separately from user-created scenarios
    is_built_in = fields.Boolean()
    # Only expected to be read, not written
    status = fields.Nested(ScenarioRunStatusSchema)


# Note that this works for both DemandCaseData and SupplyCaseData since we only expose the fields they have in common
class CaseDataSchema(Schema):
    id = fields.Integer(required=True)
    description = fields.Str(requried=True)


class DemandSubsectorSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.Str(requried=True)
    sector_id = fields.Integer()
    sector_name = fields.Str()
    demand_case_data = fields.Nested(CaseDataSchema, many=True)


class SupplyNodeSchema(Schema):
    id = fields.Integer(required=True)
    name = fields.Str(requried=True)
    supply_type_id = fields.Integer()
    supply_type_name = fields.Str()
    supply_case_data = fields.Nested(CaseDataSchema, many=True)


class OutputDataSchema(Schema):
    subsector = fields.Integer()
    series = fields.Str()
    year = fields.Integer()
    value = fields.Float()


class OutputSchema(Schema):
    output_type_id = fields.Integer()
    output_type_name = fields.Str()
    unit = fields.Str()
    data = fields.Nested(OutputDataSchema, many=True)


class ScenarioWithOutputSchema(ScenarioSchema):
    outputs = fields.Nested(OutputSchema, many=True)


class ScenarioWithBasicOutputSchema(ScenarioSchema):
    outputs = fields.Nested(OutputSchema, attribute='basic_outputs', many=True)
