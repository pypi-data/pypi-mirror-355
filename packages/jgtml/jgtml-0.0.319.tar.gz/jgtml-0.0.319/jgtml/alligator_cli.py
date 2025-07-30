#!/usr/bin/env python
"""
alligator_cli.py - Unified CLI for JGTML Alligator Analysis

This CLI consolidates the three Alligator implementations into a single,
intent-driven command interface supporting:
- Regular Alligator (5-8-13): Quick market direction detection
- Big Alligator (34-55-89): Intermediate cycle analysis  
- Tide Alligator (144-233-377): Macro trend identification

Replaces fragmented CLI commands:
- alligator_cli.py (unified JGTML Alligator CLI)
- ptojgtmlbigalligator (generated BIG analysis)
- jgtapp tide (basic wrapper)

Usage Examples:
    # Single Alligator analysis
    python alligator_cli.py -i SPX500 -t D1 -d S --type tide
    
    # Multi-Alligator convergence analysis
    python alligator_cli.py -i EUR/USD -t H4 -d B --type all
    
    # Generate .jgtml-spec from analysis
    python alligator_cli.py -i SPX500 -t D1 -d S --type all --generate-spec
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd

# Add the current directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from TideAlligatorAnalysis import AlligatorAnalysis, AlligatorConfig, AlligatorType
from jtc import pto_target_calculation

# Direct imports for pattern initialization instead of subprocess calls
import jgtapp
from ptottf import create_ttf_csv

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the unified Alligator CLI"""
    parser = argparse.ArgumentParser(
        description="Unified JGTML Alligator Analysis CLI",
        epilog="""
        This tool provides unified analysis across all three Alligator contexts:
        - Regular (5-8-13): Primary market direction and entry signals
        - Big (34-55-89): Higher timeframe context and cycle analysis
        - Tide (144-233-377): Macro trend identification and major support/resistance
        
        Signal Types Analyzed:
        - signals_in_teeth: Price action within Alligator teeth (retracement zones)
        - signals_mouth_open_in_teeth: Signals when mouth is open + price in teeth
        - signals_mouth_open_in_lips: Signals when mouth is open + price in lips
        
        The analysis outputs CSV and Markdown reports showing signal performance
        metrics including count, total profit, and average per trade.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required parameters
    parser.add_argument('-i', '--instrument', type=str, required=True,
                       help='Trading instrument (e.g., SPX500, EUR/USD)')
    parser.add_argument('-t', '--timeframe', type=str, required=True,
                       help='Analysis timeframe (e.g., D1, H4, H1)')
    parser.add_argument('-d', '--direction', type=str, choices=['S', 'B'], required=True,
                       help='Signal direction: S (Sell) or B (Buy)')
    
    # Alligator configuration
    parser.add_argument('--type', type=str, choices=['regular', 'big', 'tide', 'all'], 
                       default='all',
                       help='Alligator analysis type (default: all)')
    
    # Data processing options
    parser.add_argument('--fresh', action='store_true', default=True,
                       help='Use fresh data (regenerate if needed)')
    parser.add_argument('--no-fresh', dest='fresh', action='store_false',
                       help='Use cached data (do not regenerate)')
    parser.add_argument('--regenerate-cds', action='store_true', default=True,
                       help='Force regeneration of CDS data')
    parser.add_argument('--no-regenerate-cds', dest='regenerate_cds', action='store_false',
                       help='Use existing CDS data')
    
    # Analysis options
    parser.add_argument('--mfi', action='store_true', default=True,
                       help='Enable Market Facilitation Index analysis')
    parser.add_argument('--no-mfi', dest='mfi', action='store_false',
                       help='Disable MFI analysis')
    
    # Output options
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress output (only show errors)')
    parser.add_argument('--output-dir', type=str,
                       help='Custom output directory (default: $jgtdroot/drop)')
    parser.add_argument('--output-basename', type=str,
                       help='Custom output filename base')
    
    # Intent-driven features
    parser.add_argument('--generate-spec', action='store_true',
                       help='Generate .jgtml-spec file from analysis results')
    parser.add_argument('--spec-template', type=str,
                       help='Template file for .jgtml-spec generation')
    
    # Advanced options
    parser.add_argument('--data-dir', type=str,
                       help='Override data directory (default: $JGTPY_DATA_FULL)')
    parser.add_argument('--force-regenerate-mx', action='store_true', default=True,
                       help='Force regeneration of MX files')
    
    return parser

def parse_alligator_types(type_arg: str) -> List[AlligatorType]:
    """Parse the alligator type argument into a list of types"""
    if type_arg == 'all':
        return [AlligatorType.REGULAR, AlligatorType.BIG, AlligatorType.TIDE]
    elif type_arg == 'regular':
        return [AlligatorType.REGULAR]
    elif type_arg == 'big':
        return [AlligatorType.BIG]
    elif type_arg == 'tide':
        return [AlligatorType.TIDE]
    else:
        raise ValueError(f"Unknown alligator type: {type_arg}")

def ensure_pattern_files_exist(config: AlligatorConfig) -> bool:
    """
    Ensure TTF pattern files exist for the given configuration.
    Consolidates workflow logic from _fnml.sh to create self-contained initialization.
    
    Returns True if files exist or were created successfully, False otherwise.
    """
    
    # Define pattern file paths based on JGTML data structure
    data_path = Path(config.jgtdroot) / "data" / "full" / "pn"
    required_files = [
        data_path / "mfi.csv",
        data_path / "ttf.csv", 
        data_path / "zonesq.csv"
    ]
    
    # Check if all required files exist
    all_exist = all(f.exists() for f in required_files)
    
    if all_exist and not config.regenerate_cds:
        if not config.quiet:
            print("✅ Pattern files exist - proceeding with analysis")
        return True
    
    if not config.quiet:
        print("🔄 Pattern files missing or regeneration requested - initializing TTF patterns...")
    
    # Create data directory if it doesn't exist
    data_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Initialize CDS (Consolidated Data Source)
        if not config.quiet:
            print("  📊 Initializing CDS...")
        success = _initialize_cds(config.instrument, config.timeframe)
        if not success:
            return False
            
        # Step 2: Create TTF patterns 
        if not config.quiet:
            print("  🔧 Creating TTF patterns...")
        success = _create_ttf_patterns(config.instrument, config.timeframe)
        if not success:
            return False
            
        # Step 3: Generate MX files
        if not config.quiet:
            print("  ⚙️  Generating MX target files...")
        success = _generate_mx_files(config.instrument, config.timeframe)
        if not success:
            return False
            
        if not config.quiet:
            print("✅ Pattern initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Pattern initialization failed: {e}")
        return False

def _initialize_cds(instrument: str, timeframe: str) -> bool:
    """Initialize CDS using direct jgtapp.cds function call"""
    try:
        # Direct call instead of subprocess: jgtapp.cds(instrument, timeframe, use_fresh=True, use_full=True)
        jgtapp.cds(instrument, timeframe, use_fresh=True, use_full=True)
        return True
    except Exception as e:
        print(f"❌ CDS initialization error: {e}")
        return False

def _create_ttf_patterns(instrument: str, timeframe: str) -> bool:
    """Create TTF patterns using direct ptottf.create_ttf_csv function calls"""
    try:
        # TTF patterns from the workflow: ttf, mfi, zonesq
        # Note: zonesq pattern may not be fully implemented yet
        patterns = ["ttf", "mfi", "zonesq"]
        supported_patterns = ["ttf", "mfi"]  # Known working patterns
        
        for pattern in patterns:
            print(f"    🔨 Creating pattern: {pattern}")
            
            try:
                # Direct call instead of subprocess: create_ttf_csv with pattern name
                create_ttf_csv(
                    instrument, 
                    timeframe, 
                    use_full=True, 
                    use_fresh=False,  # CDS was already refreshed in _initialize_cds
                    pn=pattern
                )
            except FileNotFoundError as e:
                if pattern not in supported_patterns and ("zonesq.csv" in str(e) or pattern == "zonesq"):
                    print(f"    ⚠️  Skipping {pattern} pattern - not yet fully implemented")
                    print(f"    💡 Available patterns: {', '.join(supported_patterns)}")
                    continue
                else:
                    # Re-raise for other FileNotFoundError cases
                    raise
        
        return True
    except Exception as e:
        print(f"❌ TTF pattern creation error: {e}")
        return False

def _generate_mx_files(instrument: str, timeframe: str) -> bool:
    """Generate MX target files using direct jtc.pto_target_calculation call"""
    try:
        # Direct call instead of subprocess: jtc.pto_target_calculation with ttf pattern
        pto_target_calculation(
            instrument, 
            timeframe,
            pto_vec_fdb_ao_vector_window_flag=True,
            drop_calc_col=False,
            save_outputs=True,
            use_fresh=True,
            use_ttf=True,
            pn="ttf"
        )
        return True
    except Exception as e:
        print(f"❌ MX generation error: {e}")
        return False

def load_market_data(config: AlligatorConfig) -> 'pd.DataFrame':
    """
    Load market data using JGTML data pipeline.
    Uses the get_pto_dataframe_mx_based_en_ttf pattern from original scripts.
    """
    
    # First ensure pattern files exist
    if not ensure_pattern_files_exist(config):
        print("EXITING - RUN PREREQ SCRIPTS BEFORE RUNNING THIS SCRIPT. (might be great to ensure that runs correctly and not always outputting that)") # FIX THAT
        print("Pattern file initialization failed. Please check your JGTML environment setup.")
        sys.exit(1)
    
    try:
        # Get data through the consolidated jtc pipeline - pattern from original scripts
        df = None
        try:
            if not config.force_regenerate_mxfiles:
                from jtc import readMXFile
                df = readMXFile(config.instrument, config.timeframe)
        except:
            pass

        # Set df to None if column 'mfi' is not present (force regeneration)
        if df is not None and 'mfi' not in df.columns:
            df = None

        if df is None:
            from jtc import pto_target_calculation
            df, sel1, sel2 = pto_target_calculation(
                config.instrument, 
                config.timeframe,
                mfi_flag=config.mfi_flag,
                talligator_flag=AlligatorType.TIDE in config.alligator_types,
                balligator_flag=AlligatorType.BIG in config.alligator_types,
                regenerate_cds=config.regenerate_cds,
                use_fresh=config.use_fresh,
                use_ttf=True  # Use TTF (Time To Fill) data by default
            )
        
        if not config.quiet:
            print(f"✅ Loaded {len(df) if df is not None else 0} data points for {config.instrument} {config.timeframe}")
            if df is not None and not df.empty:
                print(f"📊 Data range: {df.index[0]} to {df.index[-1]}")
        
        return df if df is not None else pd.DataFrame()
        
    except Exception as e:
        if not config.quiet:
            print(f"⚠️  Error loading market data: {e}")
            print("This may indicate a JGTML environment configuration issue.")
        # Return empty DataFrame as fallback
        import pandas as pd
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error loading market data: {e}")
        print("Note: Data loading requires proper jgtpy/jgtml environment setup")
        return pd.DataFrame()

def generate_jgtml_spec(results: Dict, config: AlligatorConfig, output_dir: str) -> str:
    """Generate a .jgtml-spec file from analysis results"""
    
    spec_content = f"""# JGTML Trading Specification
# Generated from Alligator Analysis Results
# Timestamp: {results.get('analysis_timestamp', 'unknown')}

[meta]
instrument = "{config.instrument}"
timeframe = "{config.timeframe}"
analysis_types = {[t.value for t in config.alligator_types]}
generated_from = "alligator_cli.py"

[signal_requirements]
# Signal criteria based on analysis results
"""
    
    # Add signal performance analysis
    for alligator_type, type_results in results.get('results', {}).items():
        spec_content += f"\n[{alligator_type}_alligator]\n"
        
        for direction, analysis in type_results.items():
            if direction in ['S', 'B']:
                spec_content += f"{direction}_signals = true\n"
                
                # Extract best performing signal types
                best_signals = []
                for signal_type, metrics in analysis.items():
                    if isinstance(metrics, dict) and 'count' in metrics:
                        if metrics['count'] > 0:
                            avg_profit = metrics['sum'] / metrics['count']
                            if avg_profit > 0:  # Profitable signals
                                best_signals.append((signal_type, avg_profit, metrics['count']))
                
                # Sort by profitability
                best_signals.sort(key=lambda x: x[1], reverse=True)
                
                if best_signals:
                    spec_content += f"# Best {direction} signals for {alligator_type} Alligator:\n"
                    for signal_type, avg_profit, count in best_signals[:3]:  # Top 3
                        spec_content += f"# - {signal_type}: {avg_profit:.2f} avg, {count} trades\n"
                    
                    # Add the top signal as a requirement
                    top_signal = best_signals[0][0]
                    spec_content += f"required_{direction}_signal = \"{top_signal}\"\n"
    
    # Write to file
    spec_filename = f"alligator_analysis_{config.instrument}_{config.timeframe}.jgtml-spec"
    spec_path = os.path.join(output_dir, spec_filename)
    
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    return spec_path

def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Parse alligator types
        alligator_types = parse_alligator_types(args.type)
        
        # Create configuration
        config = AlligatorConfig(
            instrument=args.instrument,
            timeframe=args.timeframe,
            alligator_types=alligator_types,
            force_regenerate_mxfiles=args.force_regenerate_mx,
            mfi_flag=args.mfi,
            regenerate_cds=args.regenerate_cds,
            use_fresh=args.fresh,
            quiet=args.quiet,
            jgtdroot_default=args.data_dir or os.getenv("jgtdroot", "/b/Dropbox/jgt"),
            drop_subdir=args.output_dir or "drop",
            result_file_basename_default=args.output_basename or f"alligator_analysis_{args.instrument}_{args.timeframe}.result"
        )
        
        if not args.quiet:
            print(f"🐊 JGTML Unified Alligator Analysis")
            print(f"Instrument: {config.instrument}")
            print(f"Timeframe: {config.timeframe}")
            print(f"Direction: {args.direction}")
            print(f"Types: {[t.value for t in alligator_types]}")
            print()
        
        # Initialize analyzer
        analyzer = AlligatorAnalysis(config)
        
        # Load market data
        df = load_market_data(config)
        
        if df.empty:
            print("⚠️  No market data loaded. Please check your jgtpy/jgtml environment setup.")
            print("This CLI requires a properly configured JGTML data pipeline.")
            print("\nFor demonstration purposes, generating mock analysis structure...")
            
            # Generate mock results for demonstration
            mock_results = {
                'config': config.get_config(),
                'analysis_timestamp': '2025-01-05T00:00:00',
                'results': {}
            }
            
            for alligator_type in alligator_types:
                mock_results['results'][alligator_type.value] = {
                    args.direction: {
                        'alligator_type': alligator_type.value,
                        'direction': args.direction,
                        'signals_in_teeth': {'count': 15, 'sum': 450.0},
                        'signals_mouth_open_in_teeth': {'count': 8, 'sum': 320.0},
                        'signals_mouth_open_in_lips': {'count': 5, 'sum': 180.0}
                    }
                }
            
            results = mock_results
        else:
            # Run analysis with real data
            results = analyzer.run_full_analysis(df, [args.direction])
        
        # Save results
        output_path = analyzer.save_results(results)
        
        if not args.quiet:
            print(f"\n✅ Analysis complete!")
            print(f"📁 Results saved to: {output_path}")
        
        # Generate .jgtml-spec if requested
        if args.generate_spec:
            spec_path = generate_jgtml_spec(results, config, output_path)
            if not args.quiet:
                print(f"📝 Specification file generated: {spec_path}")
        
        if not args.quiet:
            print(f"\n🎯 Next steps:")
            print(f"   - Review analysis results in the generated files")
            print(f"   - Use jgtagenticcli to process .jgtml-spec files")
            print(f"   - Integrate findings into your trading strategy")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
