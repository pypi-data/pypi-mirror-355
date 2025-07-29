from pathlib import Path
import bisect
import math
from copy import deepcopy
from collections.abc import Mapping
import pandas as pd
import itertools
from functools import lru_cache
from tqdm import tqdm
from simera import Ratesheet, Config
from simera.utils import DataInputError, deep_sizeof

import cProfile, pstats

# class OrderToShipment:
#     pass

sc = Config()

class Shipment:
    """
    Consolidate all orderline level data to shipment data
    """
    # future: itertools.count is unique per python process. When moving to multiprocessing for cost,
    #  make sure it's not shipment are created before split.
    _id_counter = itertools.count(1)

    # Class variables - defaults and choices
    # Note: config values are taken from sc.config (not from ratesheet) as ratesheet could have older version
    _config_choices_volume = sc.config.units_of_measure.get('choices').get('volume')
    _config_choices_weight = sc.config.units_of_measure.get('choices').get('weight')
    _config_choices_volume_and_weight = sc.config.units_of_measure.get('choices').get('volume_and_weight')
    _config_units_of_measure_conversions_volume = sc.config.units_of_measure['conversions']['volume']
    _config_units_of_measure_conversions_weight = sc.config.units_of_measure['conversions']['weight']

    def __init__(self, input_data):
        # Process input data into dict with meta, lane and cost keys. Probably will be extended with SubClasses
        self.id = next(Shipment._id_counter)
        self.input_data = input_data
        self.units = self._get_unit_attributes()
        self.lane = self._get_lane_attributes()
        self.meta = self._get_meta_attributes()

    def __repr__(self):
        return f"Shipment"

    def _get_lane_attributes(self):
        lane_items_builtin = [
            'src_site', 'src_region', 'src_ctry', 'src_zip', 'src_zone',
            'dest_site', 'dest_region', 'dest_ctry', 'dest_zip', 'dest_zone',
        ]
        lane_items = dict.fromkeys(lane_items_builtin)
        if (lane_input := self.input_data.get('lane')) is not None:
            lane_items.update(lane_input)

        if lane_items.get('dest_ctry') is None and lane_items.get('dest_zone') is None:
            raise DataInputError(f"Shipment data missing (to determine dest_zone): 'lane.dest_ctry'.",
                                 solution="Provide lane.dest_ctry or lane.dest_zone")
        if lane_items.get('dest_zip') is None and lane_items.get('dest_zone') is None:
            raise DataInputError(f"Shipment data missing (to determine dest_zone): 'lane.dest_zip'.",
                                 solution="Provide lane.dest_zip or lane.dest_zone")
        return lane_items

    def _get_unit_attributes(self):
        cost_units_builtin = []
        cost_units = dict.fromkeys(cost_units_builtin)
        # Update units from input_data
        if (cost_input := self.input_data.get('unit')) is not None:
            cost_units.update(cost_input)

        # Convert weight and volume units to 'default_in_calculation' units (m3 and kg). It's for chargeable_ratios
        converted_cost_units = {}
        for cost_unit in cost_units.keys():
            if cost_unit in self._config_choices_volume:
                ratio_to_m3 = self._config_units_of_measure_conversions_volume[cost_unit]['m3']
                converted_cost_units.update({'m3': cost_units[cost_unit] / ratio_to_m3})
                continue
            if cost_unit in self._config_choices_weight:
                ratio_to_kg = self._config_units_of_measure_conversions_weight[cost_unit]['kg']
                converted_cost_units.update({'kg': cost_units[cost_unit] / ratio_to_kg})
        cost_units.update(converted_cost_units)
        return cost_units

    def _get_meta_attributes(self):
        meta_items_builtin = []
        meta_items = dict.fromkeys(meta_items_builtin)
        if (meta_input := self.input_data.get('meta')) is not None:
            meta_items.update(meta_input)
        return meta_items

    # class CostUnit:
    #     def __init__(self, requirements):
    #         self.requirements = requirements
    #
    # class PalFul(CostUnit):
    #     pass


class Cost:
    # Class variables - defaults and choices
    # Note: config values are taken from sc.config (not from ratesheet) as ratesheet could have older version
    _config_ratesheet_cost_types = sc.config.ratesheet.get('cost_types')
    _total_name = 'total'  # Name for totals

    def __init__(self, shipment, ratesheet):
        self.sh = shipment
        self.rs = ratesheet

        # Finding zone and transit time
        self.zone = self._get_dest_zone()
        self.transit_time = self._get_transit_time()

        # Shipment data unique to ratesheet
        self.sh_units = self.sh.units.copy()

        # Cost calculation process
        self.cost_types = self._process_cost_types()
        self.cost_groups, self.cost_total = self._process_cost_groups()
        self.cost_breakdown = self._get_cost_breakdown()

        # Shipment summary
        self.cost_summary = self._get_shipment_summary()

    def __repr__(self):
        return 'ShipmentCost'

    def _get_dest_zone(self):
        # dest_zone can be already provided with shipment.lane. If not, found it based on dest_ctry and dest_zip
        if (zone := self.sh.lane.get('dest_zone')) is None:
            ctry_attributes = self.rs.lane.find_dest_zone.get(self.sh.lane.get('dest_ctry'))
            integer_key = ctry_attributes['key_function'](self.sh.lane.get('dest_zip'))
            position_in_list = bisect.bisect_right(ctry_attributes['dest_zip_from'], integer_key) - 1
            # Just to confirm it was found properly
            if position_in_list >= 0 and integer_key <= ctry_attributes['dest_zip_to'][position_in_list]:
                return ctry_attributes['dest_zone'][position_in_list]
        else:
            return zone

    def _get_transit_time(self):
        # Transit time can be missing in ratesheet.
        ctry_attributes = self.rs.lane.find_transit_time.get(self.sh.lane.get('dest_ctry'))
        if ctry_attributes is None:
            return None
        else:
            integer_key = ctry_attributes['key_function'](self.sh.lane.get('dest_zip'))
            position_in_list = bisect.bisect_right(ctry_attributes['dest_zip_from'], integer_key) - 1
            # Just to confirm it was found properly
            if position_in_list >= 0 and integer_key <= ctry_attributes['dest_zip_to'][position_in_list]:
                return ctry_attributes['transit_time'][position_in_list]

    @staticmethod
    def calculate_packages(shipment_units, package_size_max):
        """
        Calculate the number of packages needed based on shipment units and package size limits.
        Args:
            shipment_units (dict): Dictionary containing shipment quantities by unit type
            package_size_max (dict): Dictionary containing maximum allowed quantities per package by unit type
        Returns:
            dict: Dictionary with 'package' key containing the number of packages needed
        """
        # If package_size_max is empty, return 1 package
        if not package_size_max:
            return {'package': 1}

        max_packages = 1  # Start with 1 package minimum

        # Check each unit in package_size_max
        for unit, max_per_package in package_size_max.items():
            # Only calculate if the unit exists in shipment_units
            if unit in shipment_units:
                shipment_quantity = shipment_units[unit]

                # Calculate packages needed for this unit (round up)
                packages_needed = math.ceil(shipment_quantity / max_per_package)

                # Keep the maximum packages needed across all units
                max_packages = max(max_packages, packages_needed)

        return {'package': max_packages}

    @staticmethod
    def split_shipment_units(shipment_units: dict, shipment_size_max: dict) -> dict:
        """
        Splits shipment_units into 'full' and 'rest' blocks based on one or more constraints of shipment_size_max.
        Uses 'total_shipments' in each block to indicate how many sub-shipments were created.
        """
        # No constraints → single shipment
        if not shipment_size_max:
            return {'full': {'total_shipments': 1, **shipment_units}}

        # Compute split ratios for each constrained unit
        ratios = {}
        for u, max_u in shipment_size_max.items():
            orig = shipment_units.get(u, 0)
            if max_u > 0:
                ratios[u] = orig / max_u

        # If nothing exceeds its max, return one shipment of everything
        if not ratios or all(r <= 1 for r in ratios.values()):
            return {'full': {'total_shipments': 1, **shipment_units}}

        # Pick the “driver” unit with the largest ratio
        driver = max(ratios, key=ratios.get)
        max_driver = shipment_size_max[driver]
        orig_driver = shipment_units.get(driver, 0.0)

        # How many full loads, and what’s left?
        full_count = int(orig_driver // max_driver)
        remainder  = orig_driver - full_count * max_driver

        # Build a block that carries `amount_driver` of the driver unit
        def build_block(amount_driver: float, num_shipments: int):
            block = {'total_shipments': num_shipments}
            scale = (amount_driver / orig_driver) if orig_driver else 0
            for k, v in shipment_units.items():
                if k == 'total_shipments':
                    # skip scaling the original count key
                    continue
                block[k] = v * scale
            return block
        result = {}
        if full_count > 0:
            result['full'] = build_block(max_driver, full_count)
            result['full'].update({'shipment': 1})  # To make sure all is evaluated as 1 shipment
        if remainder > 0:
            result['rest'] = build_block(remainder, 1)  # To make sure all is evaluated as 1 shipment
            result['rest'].update({'shipment': 1})
        return result

    def merge_full_and_rest(self, d1, d2, parent_keys=None):
        """
        Recursively merges d2 into d1, summing numeric leaves,
        except that if key == 'mul' and it's directly under a top-level
        group (i.e. parent_keys length == 1), we take d1['mul'] verbatim.
        """
        if parent_keys is None:
            parent_keys = []
        result = deepcopy(d1)

        for key, val in d2.items():
            if key in result:
                # special case: top‐level mul under 'full'/'rest'
                if key == 'mul' and len(parent_keys) == 1:
                    # just take the 'full' side wholesale
                    result[key] = deepcopy(result[key])
                elif isinstance(val, Mapping) and isinstance(result[key], Mapping):
                    # recurse, carrying the current key in the path
                    result[key] = self.merge_full_and_rest(
                        result[key], val, parent_keys + [key]
                    )
                else:
                    # normal numeric leaf: sum
                    result[key] = result[key] + val
            else:
                # new key entirely: copy it in
                result[key] = deepcopy(val)
        return result

    def _process_cost_types(self):
        # Processing all cost_types relevant to ratesheet

        # Naming convention
        m3_chargeable = 'm3_chg'
        kg_chargeable = 'kg_chg'

        # Step1. If ratesheet has chargeable_ratios, make sure that shipment have both weight and volume units provided.
        # Note: volume and weight shipment units (if present) are automatically converted to m3 and kg in Shipment class.
        if (chargeable_ratio_kg_per_m3:=self.rs.meta.chargeable_ratios.get('kg/m3')) is not None:
            shipment_kg = self.sh_units.get('kg')
            shipment_m3 = self.sh_units.get('m3')
            if shipment_kg is None or shipment_m3 is None:
                raise DataInputError(f"Shipment misses volume and/or weight units that are required to calculate chargeable units for ratesheet '{self.rs.input}'.\n"
                                     f"Available volume units: {[i for i in self.sh_units if i in self.sh._config_choices_volume]}\n"
                                     f"Available weight units: {[i for i in self.sh_units if i in self.sh._config_choices_weight]}",
                                     solution=f"Add missing units to shipment.")
            shipment_m3_chargeable = max(shipment_kg * (1/chargeable_ratio_kg_per_m3), shipment_m3)
            shipment_kg_chargeable = max(shipment_m3 * chargeable_ratio_kg_per_m3, shipment_kg)
            # Add chargeable values to shipment.units
            self.sh_units.update({m3_chargeable: shipment_m3_chargeable,
                                  kg_chargeable: shipment_kg_chargeable})

        # ==============================================================================================================
        # Calculate nb of packages in shipment with <package_max_size>
        # ==============================================================================================================
        # Add to shipment.units nb of packages ('package': x) based on package_max_size.func_input
        # Note: splitting of shipments is based on standard weight and volume (not chargeable).
        #  Package size max is assumed to be related to physical constraints, that may trigger cost in other areas.
        self.sh_units.update(self.calculate_packages(self.sh_units, self.rs.meta.package_size_max.get('func_input', {})))

        # ==============================================================================================================
        # Split shipment if exceeds <shipment_max_size>
        # ==============================================================================================================
        # Convert shipment.units into shipment.units_max_size
        # Note: splitting of shipments is based on standard weight and volume. It's before chargeable ratio is applied.
        #  Shipment size max is assumed to be related to physical constraints, while chargeable weight only to cost.
        setattr(self, 'sh_units_max_size', self.split_shipment_units(self.sh_units, self.rs.meta.shipment_size_max.get('func_input', {})))

        # todo: loop over units_split per cost_type. Not sure if it's enough to simply replace units with units_split
        #  Make sure somwhere below units are not updated (if are should be updated as units_split)
        #  Run cost calculation for full and rest, apply * total_shipments and summaries the cost
        #  Make sute that if no split is needed, speed betweem units and units_split is same

        # Process separately for 'full' and 'rest' units_max_size
        output_per_category = {}
        for unit_category, shipment_units in self.sh_units_max_size.items():

            # Step2: Processing of cost_types separately.
            output = {}
            for cost_type, cost_type_items in self.rs.cost.find_cost.get(self.zone).items():
                range_unit = cost_type_items.get('range_unit')
                # Check if chargeable ratios should be applied to cost_type (when chargeable_ratio exist in ratesheet and cost_type have chargeable_ratio=True)
                # if so, overwrite range_unit to chargeable m3_chg or kg_chg
                chargeable_ratio_in_ratesheet = chargeable_ratio_kg_per_m3 is not None
                chargeable_ratio_in_cost_type = self._config_ratesheet_cost_types.get(cost_type, {}).get('chargeable_ratios', False)
                use_chargeable_ratios = chargeable_ratio_in_ratesheet and chargeable_ratio_in_cost_type
                # Apply chargeable part1/2. To range unit
                if use_chargeable_ratios:
                    range_unit = {'m3': m3_chargeable, 'kg': kg_chargeable}.get(range_unit, range_unit)

                # shipment_unit_value = self.shipment.units.get(range_unit)
                shipment_unit_value = shipment_units.get(range_unit)

                # Check if shipment.units has required range_unit
                if shipment_unit_value is None:
                    raise DataInputError(f"Ratesheet range_unit '{range_unit}' not found in shipment data: {shipment_units}",
                                         solution=f"Make sure shipment has all required units. Example: '{range_unit}: 10'")

                # Determine position in range_value that will be used for shipment_unit_value
                position_in_list = max(bisect.bisect_left(cost_type_items.get('range_value_from'), shipment_unit_value) - 1, 0)
                # Check if shipment units value does not exceed ratesheet max range_value for given cost_type
                if shipment_unit_value > cost_type_items['range_value_to'][position_in_list]:
                    raise DataInputError(f"Shipment unit '{range_unit}: {shipment_unit_value}' exceeds max range_value for cost_type '{cost_type}: {max(cost_type_items.get('range_value_to'))} [{range_unit}]' ",
                                             solution=f"Make range_value bigger or reduce shipment size for unit '{range_unit}'")

                # Apply chargeable part2/2. To cost unit
                cost_unit = cost_type_items.get('cost_unit')[position_in_list]
                if use_chargeable_ratios:
                    cost_unit = {'m3': m3_chargeable, 'kg': kg_chargeable}.get(cost_unit, cost_unit)

                # Build cost_type_items
                output[cost_type] = {
                    'chargeable_ratios': use_chargeable_ratios,
                    'range_unit': range_unit,
                    'range_value_shipment': shipment_unit_value,
                    'range_value_from': cost_type_items.get('range_value_from')[position_in_list],
                    'range_value_to': cost_type_items.get('range_value_to')[position_in_list],
                    'range_position_in_list': position_in_list,
                    'cost_unit': cost_unit,
                    'cost_rate': cost_type_items.get('cost_rate')[position_in_list],
                }

                # Adding shipment unit to cost_type
                # <SpecialCase> For cost_types with function: 'mul' (surcharges/discounts), cost_unit is set to 'cost_value'
                if self.rs.cost.types.get(cost_type).get('function') == 'mul':
                    output[cost_type].update({
                        'cost_unit': 'cost_value',
                        'shipment_unit_value': 1,
                        'shipment_unit_value_origin': 'auto-script-mul'})
                else:
                    if (cost_unit := output[cost_type].get('cost_unit')) not in shipment_units:
                        raise DataInputError(f"Cost unit '{cost_unit}' does not exist in shipments units '{shipment_units}'",
                                             solution=f"Add '{cost_unit}' to shipment.units")
                    else:
                        output[cost_type].update(
                            {'shipment_unit_value': shipment_units.get(cost_unit),
                             'shipment_unit_value_origin': '(tbd) provided_with_data'}
                            # todo: Calculated from Receipt, Taken from Assumptions (inc list of assumption)
                        )
                output_per_category.update({unit_category: output})
        return output_per_category

    def _process_cost_groups(self):
        # Calculation of cost inside each cost_group. Summarizing ('sum'), applying minimum_charge ('max') and
        # final surcharge/discounts ('mul')

        output_per_category = {}
        # Separately for 'full' and 'rest'
        for category, cost_types_per_category in self.cost_types.items():
            _total_shipments = self.sh_units_max_size[category]['total_shipments']

            # Process each cost_group and their functions
            cost_groups_per_category = {}
            for cost_group, cost_group_items in self.rs.cost.get_cost.items():
                cost_groups_per_category.update({cost_group: {'total_shipments': _total_shipments}})

                # Step1 - Calculation inside function per cost_group
                for function, cost_types in cost_group_items['functions'].items():
                    # Some function will not have cost_types, skip those
                    if cost_types:
                        cost_groups_per_category[cost_group].update({function: {}})
                        cost_values = []
                        for cost_type in cost_types:
                            cost_value = round(cost_types_per_category.get(cost_type).get('cost_rate') * cost_types_per_category.get(cost_type).get('shipment_unit_value'), 6)
                            # For function with 'sum' and 'max' multiply with total_shipments, for 'mul', not
                            if function in ['sum', 'max']:
                                cost_value *= _total_shipments
                            cost_groups_per_category[cost_group][function].update({f'{cost_type}': cost_value})
                            cost_values.append(cost_value)
                        # Final aggregation based on function type:
                        if function == 'sum':
                            cost_groups_per_category[cost_group][function].update({self._total_name: sum(cost_values)})
                        if function == 'max':
                            cost_groups_per_category[cost_group][function].update({self._total_name: max(cost_values)})
                        if function == 'mul':
                            cost_groups_per_category[cost_group][function].update({self._total_name: math.prod(cost_values)})

            # Step2 - Calculate inside cost_group
            total_cost = 0
            for cost_group, cost_group_items in cost_groups_per_category.items():
                _sum = cost_group_items.get('sum', {}).get(self._total_name, 0)
                _max = cost_group_items.get('max', {}).get(self._total_name, 0)
                _mul_rate = cost_group_items.get('mul', {}).get(self._total_name, 1)
                _sum_max = max(_sum, _max)
                _mul = (_sum_max * _mul_rate) - _sum_max
                _all = _sum_max + _mul
                cost_group_items.update({self._total_name: {'sum_max': _sum_max, 'mul': _mul, self._total_name: _all}})
                total_cost += _all
            cost_groups_per_category.update({self._total_name: {self._total_name: {self._total_name: total_cost}}})
            output_per_category.update({category: cost_groups_per_category})

        # Summarize full end rest to 'total'
        full = output_per_category.get('full', {})
        rest = output_per_category.get('rest')
        if rest is None:
            output_per_category[self._total_name] = full
        else:
            output_per_category[self._total_name] = self.merge_full_and_rest(full, rest)

        total_cost = output_per_category[self._total_name][self._total_name][self._total_name][self._total_name]
        return output_per_category, total_cost

    def _get_cost_breakdown(self):
        breakdown = {}
        for cost_group, cost_group_items in self.cost_groups.get(self._total_name).items():
            for function, function_items in cost_group_items.items():
                if function != 'total_shipments':
                    for cost_type, value in function_items.items():
                        breakdown[f'{cost_group}|{function}|{cost_type}'] = round(value, 6)
        return breakdown

    def _get_shipment_summary(self):
        output = {}
        # Input
        output.update({'sh_id': self.sh.id})
        output.update(self.sh.input_data.get('lane', {}))
        # Zone & transit-time
        output.update({'zone': self.zone})
        # Units input
        output.update(self.sh_units)
        # Units calculated
        # Total shipments if split with shipment_max_size
        total_shipments = self.sh_units_max_size.get('full', {}).get('total_shipments', 0) + self.sh_units_max_size.get('rest', {}).get('total_shipments', 0)
        output.update({'total_shipments': total_shipments})
        # Service
        output.update(self.rs.shortcuts.display_on_shipment_summary)
        # output.update({'sheet_name': self.rs.shortcuts.display_on_shipment_summary.get('sheet_name')})
        # Cost total
        output.update({'cost_total': self.cost_total})
        # Cost breakdown
        output.update(self.cost_breakdown)
        return output

# future: Process of Calculation
#  Class Shipment:
#   Have recipes (class CostUnit) to calculate CostUnits based on input data.
#   CostUnits will be calculated only when requested by Ratesheet
#  Class Cost:
#   Determine what is needed based on Ratesheet
#   Get required cost unit from Shipment or from Ratesheet.meta custom_default/custom_ratios (and/or raise error/warning/log)


if __name__ == '__main__':
    # Single testing
    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'m3': 1, 'shipment': 1, 'kg': 100, 'pal_ful': 2}})
    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'kg': 20}})
    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'shipment': 1, 'm3': 100, 'kg': 10000, 'pal_ful': 100, 'box_ful': 300}})
    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'shipment': 1, 'm3': 12, 'lb': 2300, 'pal_ful': 10}})
    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'shipment': 1, 'm3': 1, 'kg': 300, 'pal_ful': 3}})
    rs = Ratesheet(Path(r'simera_inputs\transport\Simera Ratesheet Tester.xlsb'), '2')
    # cost = Cost(sh, rs)
    # df = pd.DataFrame([cost.shipment_summary])

    # sh =  Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'shipment': 1, 'm3': 1, 'kg': 120}})
    # rss = [Ratesheet(Path(r'simera_inputs\transport\Simera Ratesheet Tester.xlsb'), f't{i}') for i in range(1, 3)]
    # cost = Cost(sh, rss[0])
    # cost = Cost(sh, rss[1])
    # df = pd.DataFrame([cost.cost_summary])

    # Mass testing
    # rs_file = Path(r'simera_inputs\transport\Simera Ratesheet Tester.xlsb')
    # ratesheets = [Ratesheet(rs_file, s) for s in pd.ExcelFile(rs_file).sheet_names]

    # sh_inputs = (
    #     {'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'m3': 1, 'shipment': 1, 'kg': 100, 'pal_ful': 2}},
    #     # {'lane': {'dest_ctry': 'PL', 'dest_zip': '10000'}, 'unit': {'m3': 1, 'shipment': 1, 'kg': 150}},
    #     # {'lane': {'dest_ctry': 'PL', 'dest_zip': '20000'}, 'unit': {'m3': 1.5, 'shipment': 1, 'kg': 240}},
    #     # {'lane': {'dest_ctry': 'SK', 'dest_zip': '30000'}, 'unit': {'m3': 2.1, 'shipment': 1, 'kg': 400}},
    # )
    # shipments = [Shipment(i) for i in sh_inputs]
    # costs = []
    # for sh in shipments:
    #     for rs in ratesheets:
    #         costs.append(Cost(sh, rs))
    # df = pd.DataFrame([cost.shipment_summary for cost in costs])
    
    # todo: Make an interactive demonstration and share with people: shipments to DE zip per many different modes and carriers
    # todo: splitting packages package, large_package (this is name for surcharge: new costGroup trp_sur>large_package 65.7 (per large_package), trp_sur>lps_discount 0.4%
    # todo: make shipment_summary more readable
    # todo: how to apply parcel not allowed
    # todo: translate orders into shipment -> that should be in Shipment itself (Orders to Shipment)
    # todo: cost_type display to get table with shipment_summary
    # todo: add a check that is shipment_size_max or package_size_max is provided and have m3 and/or kg, than shipment also should have them.
    # rs = Ratesheet(Path(r'simera_inputs\transport\Simera Ratesheet Template_v0.4.7.xlsb'), 'tester')
    # shp = Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': '29234'}, 'unit': {'m3': 1.2, 'kg': 30, 'drop': 0, 'shipment': 1, 'pal_ful': 1}})
    # cost = Cost(shp, rs)
    # df = pd.DataFrame([cost.shipment_summary])

    # Testing for speed
    def calc(shps, rss):
        results = []
        shpsrss = list(itertools.product(shps, rss))
        for shp, rs in tqdm(shpsrss, desc="Calculating shipment-ratesheet costs", mininterval=1):
            results.append(Cost(shp, rs))
        # for shp in tqdm(shps, desc="Calculating shipment costs", mininterval=10):
        #     results.append(Cost(shp, rs))
        return results

    shps = [Shipment({'lane': {'dest_ctry': 'PL', 'dest_zip': f'{i:0>5}'}, 'unit': {'m3': i/1000, 'kg': 100+1*i, 'drop': 0, 'shipment': 1, 'pal_ful': 1, 'box_ful': i}}) for i in range(100000)]
    rss = [Ratesheet(Path(r'simera_inputs\transport\Simera Ratesheet Tester.xlsb'), f't{i}') for i in range(1, 4)]
    shp_cost = calc(shps, rss)
    all_cost_summaries = [shp.cost_summary for shp in shp_cost]
    df = pd.DataFrame(all_cost_summaries)

    # Super to check computing time per function
    # ------------------------------------------
    # prof = cProfile.Profile()
    # prof.enable()
    # shp_cost = calc(shps, rss)
    # prof.disable()
    # stats = pstats.Stats(prof).sort_stats('tottime')
    # stats.print_stats()

    # rs = Ratesheet(Path(r'simera_inputs\transport\Simera Ratesheet Tester.xlsb'), '3')

    # Optilo
    # df = pd.read_csv(Path(r'simera_inputs\transport\ifc_output_20250610.csv'), sep=';', low_memory=False, header=[1])
    # a = pd.DataFrame(df.isna().all(), columns=['check'])
    # show_columns = a[a.check]
    # df.drop(columns=show_columns.index, inplace=True)
    # df.info(show_counts=True)
    # df.ccw_zaokraglanie.value_counts()
