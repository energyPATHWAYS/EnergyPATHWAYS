#!/usr/bin/env bash

# Generates validation-metadata.csv with the following columns:
#
# table,column,foreign_table,foreign_column,on_del,nullable
# BlendNodeBlendMeasuresData,gau_id,GeographiesData,id,NO ACTION,NO
# BlendNodeBlendMeasuresData,parent_id,BlendNodeBlendMeasures,id,CASCADE,NO
# BlendNodeBlendMeasures,blend_node_id,SupplyNodes,id,CASCADE,YES
# BlendNodeInputsData,blend_node_id,SupplyNodes,id,CASCADE,NO
# BlendNodeInputsData,supply_node_id,SupplyNodes,id,NO ACTION,NO
# CO2PriceMeasuresData,gau_id,GeographiesData,id,NO ACTION,NO
# ...

DB=190905_US

psql -d $DB -c "\
\\copy (SELECT x.table_name as table, x.column_name as column, \
       y.table_name AS foreign_table, \
       y.column_name AS foreign_column,
       c.delete_rule AS on_del, \
       z.is_nullable as nullable \
       FROM information_schema.referential_constraints c \
       JOIN information_schema.key_column_usage x \
       ON x.constraint_name = c.constraint_name \
       JOIN information_schema.key_column_usage y \
       ON y.ordinal_position = x.position_in_unique_constraint \
       AND y.constraint_name = c.unique_constraint_name \
       JOIN information_schema.columns z \
       ON z.table_schema = 'public' \
       AND z.table_name = x.table_name \
       AND z.column_name = x.column_name \
       WHERE z.is_nullable = 'NO' OR c.delete_rule = 'CASCADE' \
       ORDER BY c.constraint_name, x.ordinal_position) \
TO 'validation-metadata.csv' with csv header"
