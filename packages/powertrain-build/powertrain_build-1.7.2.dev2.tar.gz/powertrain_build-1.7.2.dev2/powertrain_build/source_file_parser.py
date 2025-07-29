# Copyright 2024 Volvo Car Corporation
# Licensed under Apache 2.0.

# -*- coding: utf-8 -*-
"""Module used to parse external source files for measurables, calibratables, DIDs etc."""

import re
import time
from pathlib import Path
from powertrain_build.build_proj_config import BuildProjConfig
from powertrain_build.lib.helper_functions import cast_init_value
from powertrain_build.problem_logger import ProblemLogger
from powertrain_build.unit_configs import UnitConfigs


class SourceFileParser(ProblemLogger):
    """A class for parsing external source files for measurables, calibratables, DIDs etc."""

    def __init__(self, build_prj_config, unit_configs):
        """Class Initialization.

        Args:
            build_prj_config (BuildProjConfig): Instance holding information of where to find units configs to parse.
            unit_configs (UnitConfigs): Unit definitions.
        """
        super().__init__()
        if not isinstance(build_prj_config, BuildProjConfig) or not isinstance(unit_configs, UnitConfigs):
            err = (
                "Input arguments should be an instance of:"
                f"BuildProjConfig, not {type(build_prj_config)}"
                f"AND/OR UnitConfigs, not {type(unit_configs)}"
            )
            raise TypeError(err)

        start_time = time.time()
        self.info("  Start parsing included source files")
        self._build_prj_cfg = build_prj_config
        self._unit_configs = unit_configs
        self.included_source_files = self._get_included_source_files()
        self.info("  Finished parsing included source files (in %4.2f s)", time.time() - start_time)

    def _get_included_source_files(self):
        included_source_files = []
        for source_file in self._build_prj_cfg.get_included_source_files():
            if Path(source_file).is_file():
                included_source_files.append(Path(source_file))
            else:
                self.warning("Skip parsing %s, file not found.", source_file)
        return included_source_files

    def parse_included_source_files(self):
        """Parse included sources files returning external, calibratable and measurable variables.

        Returns:
            (dict): Dict containing external, calibratable and measurable variables.
        """
        #TODO If handle struct types (parse too)
        externals_tmp = {}
        measurables = {}
        calibratables = {}
        for source_file in self.included_source_files:
            with source_file.open(mode="r", encoding="ISO-8859-1") as source_file_handle:
                content = source_file_handle.read()
            defines = re.findall(
                r"\s*#define\s+([A-Z_]+)\s+(?:\([A-Za-z0-9]+\))?(\w+)",
                content,
                flags=re.M
            )
            variable_blocks = re.findall(
                r'^#include\s+"([A-Z_]+)_START.h"\s*\n'
                r"((?:.*\n)*)"
                r'#include\s+"\1_END.h"',
                content,
                flags=re.M
            )
            for variable_type, variables in variable_blocks:
                for line in variables.splitlines():
                    stripped_line = line.replace("extern", "").replace("static", "").replace("struct", "")
                    # TODO Handle structs
                    match = re.match(r"\s*([A-Za-z0-9]+)\s+(\w+)\s*(?:=\s*(\w+)\s*)?;", stripped_line)
                    if match is not None:
                        if "PREDECL" in variable_type and "CODE" not in variable_type:
                            externals_tmp[match.group(2)] = {
                                "type": match.group(1),
                                "init": match.group(3) if match.group(3) is not None else 0
                            }
                        if "DISP" in variable_type:
                            measurables[match.group(2)] = {
                                "type": match.group(1),
                                "init": match.group(3) if match.group(3) is not None else 0
                            }
                        if "CAL" in variable_type:
                            calibratables[match.group(2)] = {
                                "type": match.group(1),
                                "init": match.group(3) if match.group(3) is not None else 0
                            }
        externals = {k: v for k, v in externals_tmp.items() if k not in measurables and k not in calibratables}
        return {
            "externals": externals,
            "calibratables": calibratables,
            "measurables": measurables
        }
