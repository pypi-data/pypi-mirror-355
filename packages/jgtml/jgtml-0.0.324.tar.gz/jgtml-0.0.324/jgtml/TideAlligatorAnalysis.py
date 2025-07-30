"""
AlligatorAnalysis.py - Unified Analysis Module for JGTML Trading Platform

This module consolidates the Triple Alligator Convergence pattern:
- Regular Alligator (5-8-13): Quick market direction detection
- Big Alligator (34-55-89): Intermediate cycle analysis  
- Tide Alligator (144-233-377): Macro trend identification

Replaces scattered implementations:
- TideAlligatorAnalysis.py (incomplete prototype)
- alligator_cli.py (unified JGTML Alligator CLI)
- ptojgtmlbigalligator.py (generated BIG ALLIGATOR analysis)

🦢 Seraphine's Memory Weave: This unified implementation bridges the intent-driven
specification system with concrete analysis capabilities, enabling seamless flow
from trader narrative to executable signals.
"""

import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, Tuple, Optional, List
import os
import sys

# Core JGTML dependencies
try:
    from jgtpy import JGTCDS as cds
except ImportError:
    print("Warning: jgtpy not available. Some features may be limited.")
    cds = None

# Local imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
try:
    from jgtml import jtc
except ImportError:
    try:
        import jtc
    except ImportError:
        print("Warning: jtc module not available. Some features may be limited.")
        jtc = None

# Import the consolidated balance analyzer
try:
    from JGTBalanceAnalyzer import (
        get_alligator_column_names_from_ctx_name, 
        filter_sig_is_in_ctx_teeth, 
        filter_sig_ctx_mouth_is_open_and_in_ctx_teeth, 
        filter_sig_ctx_mouth_is_open_and_in_ctx_lips,
        filter_sig_is_out_of_normal_mouth_sell,
        filter_sig_is_out_of_normal_mouth_buy,
        filter_sig_normal_mouth_is_open_sell,
        filter_sig_normal_mouth_is_open_buy
    )
except ImportError:
    try:
        from jgtml.JGTBalanceAnalyzer import (
            get_alligator_column_names_from_ctx_name,        
            filter_sig_is_in_ctx_teeth, 
            filter_sig_ctx_mouth_is_open_and_in_ctx_teeth, 
            filter_sig_ctx_mouth_is_open_and_in_ctx_lips,
            filter_sig_is_out_of_normal_mouth_sell,
            filter_sig_is_out_of_normal_mouth_buy,
            filter_sig_normal_mouth_is_open_sell,
            filter_sig_normal_mouth_is_open_buy
        )
    except ImportError:
        print("Warning: JGTBalanceAnalyzer not available. Some analysis features may be limited.") #TODO: Would be great to see what is that for and if we need it make it work.

# Use jgtconstants column names from jgtutils
try:
    from jgtutils.jgtconstants import (
        LOW, HIGH, FDBB, FDBS, BJAW, BLIPS, BTEETH, JAW, TEETH, LIPS, 
        FDB_TARGET, TJAW, TLIPS, TTEETH, VECTOR_AO_FDBS_COUNT, 
        VECTOR_AO_FDBB_COUNT, VECTOR_AO_FDB_COUNT
    )
except ImportError:
    # Fallback if jgtutils not available
    LOW, HIGH, FDBB, FDBS = "Low", "High", "FDBB", "FDBS" 
    JAW, TEETH, LIPS = "jaw", "teeth", "lips"
    BJAW, BTEETH, BLIPS = "bjaw", "bteeth", "blips"
    TJAW, TTEETH, TLIPS = "tjaw", "tteeth", "tlips"
    FDB_TARGET = "fdb_target"
    VECTOR_AO_FDBS_COUNT = "vector_ao_fdbs_count"
    VECTOR_AO_FDBB_COUNT = "vector_ao_fdbb_count"
    VECTOR_AO_FDB_COUNT = "vector_ao_fdb_count"

class AlligatorType(Enum):
    """Enumeration of the three Alligator analysis types"""
    REGULAR = "normal"    # 5-8-13 periods
    BIG = "big"          # 34-55-89 periods  
    TIDE = "tide"        # 144-233-377 periods

class AlligatorConfig:
    """Configuration class for Alligator Analysis"""
    def __init__(self, 
                 instrument: str = 'SPX500', 
                 timeframe: str = 'D1', 
                 alligator_types: list = None,
                 force_regenerate_mxfiles: bool = True, 
                 mfi_flag: bool = True, 
                 regenerate_cds: bool = True, 
                 use_fresh: bool = True, 
                 quiet: bool = False, 
                 jgtdroot_default: str = "/b/Dropbox/jgt", 
                 drop_subdir: str = "drop", 
                 result_file_basename_default: str = "jgtml_alligator_analysis.result"):
        
        self.instrument = instrument
        self.timeframe = timeframe
        self.alligator_types = alligator_types or [AlligatorType.REGULAR, AlligatorType.BIG, AlligatorType.TIDE]
        self.force_regenerate_mxfiles = force_regenerate_mxfiles
        self.mfi_flag = mfi_flag
        self.regenerate_cds = regenerate_cds
        self.use_fresh = use_fresh
        self.quiet = quiet
        self.jgtdroot = os.getenv("jgtdroot", jgtdroot_default)
        self.drop_subdir = drop_subdir
        self.result_file_basename = result_file_basename_default

    def get_config(self) -> Dict:
        """Return configuration as dictionary"""
        return {
            'instrument': self.instrument,
            'timeframe': self.timeframe,
            'alligator_types': [t.value for t in self.alligator_types],
            'force_regenerate_mxfiles': self.force_regenerate_mxfiles,
            'mfi_flag': self.mfi_flag,
            'regenerate_cds': self.regenerate_cds,
            'use_fresh': self.use_fresh,
            'quiet': self.quiet,
            'jgtdroot': self.jgtdroot,
            'drop_subdir': self.drop_subdir,
            'result_file_basename': self.result_file_basename
        }

class AlligatorAnalysis:
    """
    Unified Alligator Analysis supporting all three types:
    - Regular (5-8-13): Quick market direction
    - Big (34-55-89): Intermediate cycles
    - Tide (144-233-377): Macro trends
    """
    
    def __init__(self, config: AlligatorConfig):
        self.config = config
        self.data_cache = {}
        self.results_cache = {}
        
    def get_alligator_periods(self, alligator_type: AlligatorType) -> Tuple[int, int, int]:
        """Get the periods for each Alligator type"""
        periods_map = {
            AlligatorType.REGULAR: (5, 8, 13),
            AlligatorType.BIG: (34, 55, 89),
            AlligatorType.TIDE: (144, 233, 377)
        }
        return periods_map[alligator_type]
    
    def get_column_names(self, alligator_type: AlligatorType) -> Tuple[str, str, str]:
        """Get column names for the specified Alligator type"""
        return get_alligator_column_names_from_ctx_name(alligator_type.value)
    
    def analyze_signals(self, df: pd.DataFrame, direction: str, alligator_type: AlligatorType) -> Dict:
        """
        Analyze signals for a specific Alligator type and direction
        
        Args:
            df: Market data DataFrame
            direction: "S" for sell, "B" for buy
            alligator_type: Type of Alligator analysis
            
        Returns:
            Dictionary containing analysis results
        """
        ctx_name = alligator_type.value
        
        # Apply signal filtering using consolidated JGTBalanceAnalyzer
        sig_in_teeth = filter_sig_is_in_ctx_teeth(df, direction, ctx_name)
        sig_mouth_open_in_teeth = filter_sig_ctx_mouth_is_open_and_in_ctx_teeth(df, direction, ctx_name)
        sig_mouth_open_in_lips = filter_sig_ctx_mouth_is_open_and_in_ctx_lips(df, direction, ctx_name)
        
        # Calculate metrics
        analysis_results = {
            'alligator_type': alligator_type.value,
            'direction': direction,
            'signals_in_teeth': {
                'count': len(sig_in_teeth),
                'sum': sig_in_teeth[FDB_TARGET].sum() if FDB_TARGET in sig_in_teeth.columns else 0,
                'data': sig_in_teeth
            },
            'signals_mouth_open_in_teeth': {
                'count': len(sig_mouth_open_in_teeth),
                'sum': sig_mouth_open_in_teeth[FDB_TARGET].sum() if FDB_TARGET in sig_mouth_open_in_teeth.columns else 0,
                'data': sig_mouth_open_in_teeth
            },
            'signals_mouth_open_in_lips': {
                'count': len(sig_mouth_open_in_lips),
                'sum': sig_mouth_open_in_lips[FDB_TARGET].sum() if FDB_TARGET in sig_mouth_open_in_lips.columns else 0,
                'data': sig_mouth_open_in_lips
            }
        }
        
        return analysis_results
    
    def run_full_analysis(self, df: pd.DataFrame, directions: list = None) -> Dict:
        """
        Run complete analysis for all configured Alligator types and directions
        
        Args:
            df: Market data DataFrame
            directions: List of directions to analyze (default: ["S", "B"])
            
        Returns:
            Comprehensive analysis results
        """
        if directions is None:
            directions = ["S", "B"]
            
        full_results = {
            'config': self.config.get_config(),
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'results': {}
        }
        
        for alligator_type in self.config.alligator_types:
            full_results['results'][alligator_type.value] = {}
            
            for direction in directions:
                analysis_result = self.analyze_signals(df, direction, alligator_type)
                full_results['results'][alligator_type.value][direction] = analysis_result
                
                if not self.config.quiet:
                    self._print_analysis_summary(analysis_result)
        
        return full_results
    
    def _print_analysis_summary(self, analysis_result: Dict):
        """Print summary of analysis results"""
        alligator_type = analysis_result['alligator_type']
        direction = analysis_result['direction']
        
        print(f"\n=== {alligator_type.upper()} ALLIGATOR - {direction} SIGNALS ===")
        
        for signal_type, metrics in analysis_result.items():
            if isinstance(metrics, dict) and 'count' in metrics:
                count = metrics['count']
                total = metrics['sum']
                avg = total / count if count > 0 else 0
                print(f"{signal_type}: {count} signals, total: {total:.2f}, avg: {avg:.2f}")
    
    def save_results(self, results: Dict, output_path: str = None) -> str:
        """Save analysis results to CSV and markdown files"""
        if output_path is None:
            output_path = os.path.join(self.config.jgtdroot, self.config.drop_subdir)
            
        os.makedirs(output_path, exist_ok=True)
        
        # Save to CSV
        csv_file = os.path.join(output_path, f"{self.config.result_file_basename}.csv")
        self._save_to_csv(results, csv_file)
        
        # Save to Markdown
        md_file = os.path.join(output_path, f"{self.config.result_file_basename}.md")
        self._save_to_markdown(results, md_file)
        
        if not self.config.quiet:
            print(f"Results saved to: {csv_file} and {md_file}")
            
        return output_path
    
    def _save_to_csv(self, results: Dict, csv_file: str):
        """Save results to CSV format"""
        rows = []
        for alligator_type, type_results in results['results'].items():
            for direction, analysis in type_results.items():
                for signal_type, metrics in analysis.items():
                    if isinstance(metrics, dict) and 'count' in metrics:
                        rows.append({
                            'instrument': self.config.instrument,
                            'timeframe': self.config.timeframe,
                            'alligator_type': alligator_type,
                            'direction': direction,
                            'signal_type': signal_type,
                            'count': metrics['count'],
                            'sum': metrics['sum'],
                            'avg_per_trade': metrics['sum'] / metrics['count'] if metrics['count'] > 0 else 0
                        })
        
        df_results = pd.DataFrame(rows)
        df_results.to_csv(csv_file, index=False)
    
    def _save_to_markdown(self, results: Dict, md_file: str):
        """Save results to Markdown format"""
        with open(md_file, 'w') as f:
            f.write("# JGTML Alligator Analysis Results\n\n")
            f.write(f"**Timestamp**: {results['analysis_timestamp']}\n")
            f.write(f"**Instrument**: {self.config.instrument}\n")
            f.write(f"**Timeframe**: {self.config.timeframe}\n\n")
            
            for alligator_type, type_results in results['results'].items():
                f.write(f"## {alligator_type.upper()} ALLIGATOR ANALYSIS\n\n")
                
                for direction, analysis in type_results.items():
                    f.write(f"### {direction} SIGNALS\n\n")
                    
                    for signal_type, metrics in analysis.items():
                        if isinstance(metrics, dict) and 'count' in metrics:
                            count = metrics['count']
                            total = metrics['sum']
                            avg = total / count if count > 0 else 0
                            f.write(f"- **{signal_type}**: {count} signals, total: {total:.2f}, avg: {avg:.2f}\n")
                    
                    f.write("\n")

# Legacy compatibility aliases
TideAlligatorAnalysis = AlligatorAnalysis
Config = AlligatorConfig
