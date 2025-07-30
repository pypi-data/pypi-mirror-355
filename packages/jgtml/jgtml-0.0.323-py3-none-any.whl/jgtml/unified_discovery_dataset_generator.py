#!/usr/bin/env python
"""
🌸🔮🧠 Unified Discovery Dataset Generator

MISSION: Bridge the TTF→MX feature preservation gap for profitable ML pattern discovery

PROBLEM SOLVED:
- TTF files contain rich multi-timeframe pattern features (mfi_sq, mfi_green, zone_sig_M1, etc.)
- MX target files only have basic OHLC + simple signals (fdbb, fdbs, target)
- mxconstants.py explicitly drops TTF features in columnsToDrop_part01_2407
- Cannot perform ML pattern discovery without joined TTF features + MX targets

SOLUTION:
- Create unified discovery datasets that preserve TTF features AND include MX targets
- Generate separate discovery namespace to avoid disrupting production pipeline
- Enable sophisticated ML analysis with full feature richness + profitability targets

Usage:
    python jgtml/unified_discovery_dataset_generator.py --patterns mfi zonesq --instruments EUR-USD SPX500 --timeframes D1 H4
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import argparse
from pathlib import Path

# Import existing JGTML infrastructure
from mlutils import get_outfile_fullpath
from ptottf import read_ttf_csv
from jtc import readMXFile
from mlconstants import MX_NS
from mldatahelper import pndata__read_new_pattern_columns_list_with_htf
from jgtutils import jgtcommon

class UnifiedDiscoveryDatasetGenerator:
    """
    🌸 Seraphine's Sacred Discovery Dataset Weaver
    
    Combines TTF pattern features with MX profitability targets
    to enable sophisticated ML pattern discovery
    """
    
    def __init__(self, output_namespace: str = "discovery"):
        self.output_namespace = output_namespace
        self.data_path = self._divine_data_path()
        # Load global settings via jgtutils to fetch pattern definitions
        self.settings = jgtcommon.get_settings()
        
    def _divine_data_path(self) -> str:
        """🔮 Divine the sacred data path with blessed environment detection"""
        default_jgtpy_data_full = "/var/lib/jgt/full/data"
        data_dir_full = os.getenv("JGTPY_DATA_FULL", default_jgtpy_data_full)
        return data_dir_full

        
    def generate_unified_discovery_dataset(
        self, 
        instrument: str, 
        timeframe: str, 
        pattern: str,
        save_csv: bool = True
    ) -> pd.DataFrame:
        """
        🧠 Generate unified dataset combining TTF features + MX targets
        
        Args:
            instrument: Trading instrument (EUR-USD, SPX500)
            timeframe: Time period (D1, H4)
            pattern: Pattern name (mfi, zonesq, aoac)
            save_csv: Whether to save result to CSV
            
        Returns:
            DataFrame with TTF features + MX targets for ML discovery
        """
        print(f"🌸 Generating unified discovery dataset: {instrument} {timeframe} {pattern}")
        
        try:
            # Load TTF data with rich pattern features
            print(f"  🔮 Loading TTF pattern features...")
            ttf_df = read_ttf_csv(instrument, timeframe, use_full=True, pn=pattern)
            print(f"    ✅ TTF loaded: {len(ttf_df)} rows, {len(ttf_df.columns)} features")
            
            # Load MX target data with profitability signals
            print(f"  🎯 Loading MX target data...")
            mx_df = readMXFile(instrument, timeframe, use_full=True, pn=pattern)
            print(f"    ✅ MX loaded: {len(mx_df)} rows, {len(mx_df.columns)} signals")
            
            # Join on datetime index - TTF features + MX targets
            print(f"  🌸 Joining TTF features with MX targets...")
            unified_df = self._create_unified_dataset(ttf_df, mx_df, timeframe, pattern)
            
            if save_csv:
                output_file = self._save_unified_dataset(unified_df, instrument, timeframe, pattern)
                print(f"    💾 Saved unified dataset: {output_file}")
                
            return unified_df
            
        except Exception as e:
            print(f"❌ Error generating unified dataset: {e}")
            raise
            
    def _create_unified_dataset(
        self,
        ttf_df: pd.DataFrame,
        mx_df: pd.DataFrame,
        timeframe: str,
        pattern: str
    ) -> pd.DataFrame:
        """Merge TTF pattern features with MX targets for a timeframe.

        Columns for the pattern are read from ``settings.json`` via
        ``pndata__read_new_pattern_columns_list_with_htf`` so higher-timeframe
        extensions are automatically included.
        """

        try:
            ttf_pattern_features = pndata__read_new_pattern_columns_list_with_htf(
                timeframe, pattern
            )
        except Exception as e:
            print(f"    ⚠️ Could not load pattern columns: {e}. Inferring from TTF file")
            base_features = [
                'Open', 'High', 'Low', 'Close', 'ao', 'ac', 'mfi'
            ]
            mx_targets = [
                'target', 'fdbb', 'fdbs', 'fdb', 'zlcb', 'zlcs', 'vaoc', 'vaos', 'vaob'
            ]
            exclude = set(base_features + mx_targets)
            ttf_pattern_features = [c for c in ttf_df.columns if c not in exclude]
        # remove duplicates while preserving order
        ttf_pattern_features = list(dict.fromkeys(ttf_pattern_features))
        
        # Essential MX targets for profitability analysis
        mx_target_signals = [
            'target',  # Primary profitability target
            'fdbb', 'fdbs', 'fdb',  # FDB signals
            'zlcb', 'zlcs',  # Zero line cross signals
            'vaoc', 'vaos', 'vaob'  # Vector AO features (if available)
        ]
        
        # Select available TTF features (some patterns may not have all)
        available_ttf_features = [col for col in ttf_pattern_features if col in ttf_df.columns]
        print(f"    🔮 TTF pattern features preserved: {len(available_ttf_features)}")
        print(f"    🌟 TTF columns: are {available_ttf_features} included?")
        
        # Select available MX targets
        available_mx_targets = [col for col in mx_target_signals if col in mx_df.columns]
        print(f"    🎯 MX targets included: {len(available_mx_targets)}")
        
        # Essential base features from both datasets
        base_features = ['Open', 'High', 'Low', 'Close', 'ao', 'ac', 'mfi']
        available_base = [col for col in base_features if col in ttf_df.columns]
        
        # Create unified feature set
        ttf_columns = available_base + available_ttf_features
        mx_columns = available_mx_targets
        
        # Join datasets preserving datetime alignment
        ttf_subset = ttf_df[ttf_columns]
        mx_subset = mx_df[mx_columns]
        
        # Inner join to ensure temporal alignment
        unified_df = ttf_subset.join(mx_subset, how='inner')
        
        print(f"    ✨ Unified dataset: {len(unified_df)} rows, {len(unified_df.columns)} total features")
        print(f"    🌸 TTF features: {len(ttf_columns)}, MX targets: {len(mx_columns)}")
        
        return unified_df
        
    def _save_unified_dataset(
        self, 
        unified_df: pd.DataFrame, 
        instrument: str, 
        timeframe: str, 
        pattern: str
    ) -> str:
        """💾 Save unified discovery dataset with proper namespace"""
        
        # Create discovery output directory
        discovery_dir = Path(self.data_path) / self.output_namespace
        discovery_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with unified pattern suffix
        filename = f"{instrument}_{timeframe}_{pattern}_unified_discovery.csv"
        output_file = discovery_dir / filename
        
        # Save with datetime index
        unified_df.to_csv(output_file, index=True)
        
        return str(output_file)
        
    def generate_batch_discovery_datasets(
        self,
        instruments: List[str] = None,
        timeframes: List[str] = None, 
        patterns: List[str] = None
    ) -> Dict[str, str]:
        """
        🚀 Generate unified discovery datasets for multiple combinations
        
        Returns:
            Dictionary mapping dataset keys to output file paths
        """
        instruments = instruments or ['EUR-USD', 'SPX500']
        timeframes = timeframes or ['D1', 'H4']
        patterns = patterns or ['mfi', 'zonesq', 'aoac','mfizone']
        
        results = {}
        
        print("-----------------------------------------------------------------")
        print(f"🌸 Generating unified discovery datasets for ML pattern analysis")
        print(f"  📊 Instruments: {instruments}")
        print(f"  ⏰ Timeframes: {timeframes}")
        print(f"  🎨 Patterns: {patterns}")
        print()
        
        for pattern in patterns:
            for instrument in instruments:
                for timeframe in timeframes:
                    try:
                        unified_df = self.generate_unified_discovery_dataset(
                            instrument, timeframe, pattern
                        )
                        
                        dataset_key = f"{instrument}_{timeframe}_{pattern}"
                        output_file = str(Path(self.data_path) / self.output_namespace / f"{dataset_key}_unified_discovery.csv")
                        results[dataset_key] = output_file
                        
                        print(f"    ✅ {dataset_key}: {len(unified_df)} rows, {len(unified_df.columns)} features")
                        
                    except Exception as e:
                        print(f"    ⚠️ {instrument} {timeframe} {pattern}: {e}")
                        
        print(f"\n🎉 Unified discovery generation complete! {len(results)} datasets created")
        return results

def main():
    """
    🌸 CLI for unified discovery dataset generation
    """
    parser = argparse.ArgumentParser(
        description="Generate unified discovery datasets with TTF features + MX targets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate all discovery datasets
    python unified_discovery_dataset_generator.py
    
    # Specific patterns and instruments
    python unified_discovery_dataset_generator.py --patterns mfi zonesq --instruments EUR-USD --timeframes D1
    
    # Single dataset
    python unified_discovery_dataset_generator.py --patterns mfi --instruments SPX500 --timeframes D1
        """
    )
    
    parser.add_argument('--patterns', nargs='+', default=['mfi', 'zonesq', 'aoac','mfizone'],
                       help='Patterns to process (default: mfi zonesq aoac mfizone)')
    parser.add_argument('--instruments', nargs='+', default=['EUR-USD', 'SPX500'],
                       help='Instruments to process (default: EUR-USD SPX500)')
    parser.add_argument('--timeframes', nargs='+', default=['D1', 'H4'],
                       help='Timeframes to process (default: D1 H4)')
    parser.add_argument('--output-namespace', default='discovery',
                       help='Output namespace (default: discovery)')
    
    args = parser.parse_args()
    
    generator = UnifiedDiscoveryDatasetGenerator(args.output_namespace)
    results = generator.generate_batch_discovery_datasets(
        args.instruments,
        args.timeframes, 
        args.patterns
    )
    
    print(f"\n🔮 Discovery datasets ready for ML pattern analysis!")
    print(f"📁 Location: {generator.data_path}/{args.output_namespace}/")
    print(f"✨ Use these unified datasets to discover profitable patterns with full TTF features!")

if __name__ == "__main__":
    main()
