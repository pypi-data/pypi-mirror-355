from typing import List
from itertools import product

from confinety.parameters import *
from confinety.sections import *


class Configurations:

    """
    This module manages simulation configurations.

    The `Configurations` module is responsible for collecting all the configurations 
    set by the user for the simulation and generating the running configurations 
    based on them. It serves as a base class, providing the foundational structure 
    and functionality for managing configurations.

    Users can extend this class to add custom behavior or additional configuration 
    types as needed for their specific simulations.
    """

    # This is the section group object that will be used to group the sections.    
    SECTION_GROUP_OBJ = SectionGroup

    def __init__(self, sections: List[Section]=[], param_sweepers=[]):
        """
        Initializes the Configurations object.
    
        Parameters:
        - `sections` (list): The default set of configurations for the simulation.
        - `param_sweepers` (list): A list of parameter sweepers to test multiple 
          values for specific parameters.
        """
        self.sections: List[Section] = sections
        self.param_sweepers: List[ParameterSweeperBase] = param_sweepers
        

    def add_config(self, section):
        """
        Adds a new configuration to the simulation.
    
        The `add_config` method allows the user to add additional configurations 
        to the simulation. These configurations can be used to extend or modify 
        the default setup, enabling more flexible and customizable simulation scenarios.
        """
        if section is None:
            raise ValueError("section cannot be None")
        
        if type(section) is list:
            self.sections.extend(section)
        else:
            self.sections.append(section)

    def add_param_sweeper(self, sweepers = []):
        """
        Adds a parameter sweeper to the simulation.
    
        The `add_param_sweeper` method allows the user to include a parameter sweeper, 
        which defines multiple values for a specific parameter to be tested in the simulation. 
        This enables systematic exploration of the parameter's impact on the simulation results.
        """
        if type(sweepers) is list:
            self.param_sweepers.extend(sweepers)
        else:
            self.param_sweepers.append(sweepers)

    def override_section(self, section: Section):
        """
        Overrides a section in the configuration.
    
        The `override_section` method is used to test exactly one configuration 
        from a specific group. It replaces or modifies the section in the configuration, 
        ensuring that only the desired configuration from the group is applied 
        during the simulation.
        """
        group = section.group
        section_to_replace = None
        for s in self.sections:
            if s.group == group:
                section_to_replace = s
                break
        if section_to_replace is not None:
            self.sections.remove(section_to_replace)
            
        self.sections.append(section)


    def _get_curr_run_section_id(self):
        """
        Retrieves the current run section ID.
    
        The `_get_curr_run_section_id` method generates and returns a unique identifier 
        for the current run section. This ID is used to distinguish and track specific 
        sections within the simulation configuration.
        """
        return len(self.run_sections)
    
    def _turn_param_sweeper_to_sections(self):
        """
        Converts parameter sweepers into configuration sections.
    
        The `_turn_param_sweeper_to_sections` method processes the list of parameter 
        sweepers and generates corresponding configuration sections for each combination 
        of parameter values. This enables the simulation to test multiple parameter 
        variations systematically.
        """
        if len(self.param_sweepers) == 0:
            return []


        param_sweepers_sections = []
        param_lists = [sweeper.to_list() for sweeper in self.param_sweepers]
        sweep_product = list(product(*param_lists))
        for idx, sweep in enumerate(sweep_product):
            section = ParamSweepSection(
                name=f"sweep_{idx}",
                children=list(sweep),
            )
            param_sweepers_sections.append(section)

        return param_sweepers_sections

    def _calculate_base_sections(self, param_sweepers_sections):
        """
        Calculates the base sections for the simulation.

        The `_calculate_base_sections` method determines the default set of sections 
        that form the foundation of the simulation configuration. These sections 
        include the main configurations and any additional overrides or modifications 
        applied by the user.
        """
        all_sections = self.sections + param_sweepers_sections
        for section in all_sections:
            section.prepare_deatils()

        return all_sections

    def _get_section_groups(self, sections):
        """
        Retrieves the section groups from the configuration.
    
        The `_get_section_groups` method collects and returns all the section groups 
        defined in the configuration. Section groups are used to organize related 
        configurations, ensuring that only one configuration from each group is 
        applied during a simulation run.
        """
        group_free = []
        groups = {}
        section: Section
        for section in sections:
            if section.group == self.SECTION_GROUP_OBJ.GROUP_FREE:
                group_free.append(section)
            else:
                if section.group not in groups:
                    groups[section.group] = []
                groups[section.group].append(section)
        
        return group_free, groups.values()
    
    def _flat_and_add_group_free(self, group_free, groups):
        """
        Flattens the configuration and adds group-free sections.
    
        The `_flat_and_add_group_free` method processes the configuration by flattening 
        nested structures and ensuring that group-free sections are included. Group-free 
        sections are those that are not part of any specific section group and are 
        always applied to the simulation.
        """
        flatten_sections = list(product(*groups))
        sections_with_groupfree = [list(sections)+group_free for sections in flatten_sections]
        return sections_with_groupfree
    
    def _claculate_run_sections(self, all_sections):
        """
        Calculates the run sections for the simulation.
    
        The `_claculate_run_sections` method generates the final set of sections 
        to be used in each simulation run. It combines the base sections, group-specific 
        configurations, and parameter sweepers to create a complete configuration 
        for each run.
        """
        group_free, groups = self._get_section_groups(all_sections) 
        sections_with_groupfree = self._flat_and_add_group_free(group_free, groups)

        run_sections = []
        for sections_collection in sections_with_groupfree:
            run_sec = RunningSection(
                name=f"run_{len(run_sections)}", 
                extentions=sections_collection,
            )
            run_sections.append(run_sec)

        return run_sections

    def _get_sections_as_string(self, sections):
        """
        Converts all sections into a string representation.
    
        The `_get_sections_as_string` method generates a string representation of 
        all the sections in the configuration. This is typically used to export 
        the configuration into a format suitable for writing to an INI file or 
        displaying for debugging purposes.
        """
        sections_txt = ""
        for section in sections:
            sections_txt += section.export()  
        
        return sections_txt

    
    def export(self):
        """
        Exports the configuration to a file.
    
        The `export` method writes the current configuration, including all sections 
        and their details, to an output file. This is typically used to generate 
        the INI file required for running the simulation.
        """
        param_sweepers_sections = self._turn_param_sweeper_to_sections()
        all_sections = self._calculate_base_sections(param_sweepers_sections)
        run_sections = self._claculate_run_sections(all_sections)
        
        confs_txt = ""
        confs_txt += self._get_sections_as_string(all_sections)
        confs_txt += self._get_sections_as_string(run_sections)
        return confs_txt


