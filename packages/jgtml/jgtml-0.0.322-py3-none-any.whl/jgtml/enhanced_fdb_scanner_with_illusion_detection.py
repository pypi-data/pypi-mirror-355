#!/usr/bin/env python3
"""
Enhanced FDB Scanner with Alligator Illusion Detection - Phase 3 Integration

Integrates the Alligator Illusion Detection system with the existing FDB scanning workflow
to provide comprehensive signal quality assessment and false-positive detection.

Building on successful FDB scanning activation and Phase 2 real data testing.
"""

import sys
import os
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add jgtml to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import signal ordering and direction detection
from .SignalOrderingHelper import is_mouth_open, is_bar_out_of_mouth, create_fdb_entry_order
from .SOHelper import get_last_two_bars
from jgtutils.jgtconstants import FDB, HIGH, LOW, LIPS, TEETH, JAW

class AlligatorIllusionDetector:
    """Detect alligator illusions across multiple timeframes"""
    
    def __init__(self, data_path="/src/jgtml/cache/fdb_scanners"):
        self.data_path = Path(data_path)
    
    def load_csv_data(self, instrument, timeframe):
        """Load CDS CSV data for alligator analysis"""
        filename = f"{instrument}_{timeframe}_cds_cache.csv"
        filepath = self.data_path / filename
        
        if not filepath.exists():
            return None
        
        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            return df
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def analyze_alligator_pattern(self, data, timeframe):
        """Analyze alligator mouth status and detect potential illusions"""
        if data is None or len(data) < 2:
            return None
        
        # Get latest bar data
        latest_bar = data.iloc[-1]
        
        try:
            # Extract alligator values
            jaw = self.safe_float(latest_bar.get('jaw', 0))
            teeth = self.safe_float(latest_bar.get('teeth', 0))
            lips = self.safe_float(latest_bar.get('lips', 0))
            
            high = self.safe_float(latest_bar.get('High', 0))
            low = self.safe_float(latest_bar.get('Low', 0))
            close = self.safe_float(latest_bar.get('Close', 0))
            
            # Determine alligator mouth status
            mouth_open_bull = lips > teeth > jaw
            mouth_open_bear = lips < teeth < jaw
            mouth_sleeping = abs(lips - jaw) < (abs(high - low) * 0.1)  # Threshold for sleeping
            
            # Calculate mouth separation (distance between lips and jaw)
            mouth_separation = abs(lips - jaw)
            
            # Determine trend direction
            trend = self.determine_trend(jaw, teeth, lips)
            
            # Check if price is outside mouth
            price_above_mouth = low > max(jaw, teeth, lips)
            price_below_mouth = high < min(jaw, teeth, lips)
            price_in_mouth = not (price_above_mouth or price_below_mouth)
            
            return {
                'timeframe': timeframe,
                'jaw': jaw,
                'teeth': teeth,
                'lips': lips,
                'high': high,
                'low': low,
                'close': close,
                'mouth_open_bull': mouth_open_bull,
                'mouth_open_bear': mouth_open_bear,
                'mouth_sleeping': mouth_sleeping,
                'mouth_separation': mouth_separation,
                'trend': trend,
                'price_above_mouth': price_above_mouth,
                'price_below_mouth': price_below_mouth,
                'price_in_mouth': price_in_mouth
            }
            
        except Exception as e:
            print(f"Error analyzing alligator pattern for {timeframe}: {e}")
            return None
    
    def safe_float(self, value):
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def determine_trend(self, jaw, teeth, lips):
        """Determine trend based on alligator line arrangement"""
        if lips > teeth > jaw:
            return "bullish"
        elif lips < teeth < jaw:
            return "bearish"
        else:
            return "sideways"
    
    def calculate_mouth_separation(self, jaw, lips):
        """Calculate the separation between jaw and lips"""
        return abs(lips - jaw)
    
    def detect_illusions(self, multi_tf_readings):
        """Detect illusions by comparing different timeframe alignments"""
        illusions = []
        
        # Sort timeframes by hierarchy (higher to lower)
        tf_hierarchy = ['MN1', 'W1', 'D1', 'H4', 'H1', 'm15', 'm5', 'm1']
        available_tfs = [tf for tf in tf_hierarchy if tf in multi_tf_readings]
        
        for i, tf in enumerate(available_tfs[:-1]):  # Don't check the lowest timeframe
            current_reading = multi_tf_readings[tf]
            
            # Check against lower timeframes
            for lower_tf in available_tfs[i+1:]:
                lower_reading = multi_tf_readings[lower_tf]
                
                if current_reading and lower_reading:
                    # Illusion 1: Higher TF mouth open, lower TF contradicts
                    if (current_reading['mouth_open_bull'] and lower_reading['mouth_open_bear']):
                        illusions.append({
                            'type': 'Contradiction Illusion',
                            'higher_tf': tf,
                            'lower_tf': lower_tf,
                            'alligator_type': 'Bull/Bear Contradiction',
                            'description': f'{tf} shows bullish mouth, {lower_tf} shows bearish mouth'
                        })
                    
                    elif (current_reading['mouth_open_bear'] and lower_reading['mouth_open_bull']):
                        illusions.append({
                            'type': 'Contradiction Illusion',
                            'higher_tf': tf,
                            'lower_tf': lower_tf,
                            'alligator_type': 'Bear/Bull Contradiction',
                            'description': f'{tf} shows bearish mouth, {lower_tf} shows bullish mouth'
                        })
                    
                    # Illusion 2: Price action contradicts alligator signal
                    if (current_reading['mouth_open_bull'] and lower_reading['price_below_mouth']):
                        illusions.append({
                            'type': 'Price Action Illusion',
                            'higher_tf': tf,
                            'lower_tf': lower_tf,
                            'alligator_type': 'Bull Signal, Bear Price',
                            'description': f'{tf} bullish mouth, but {lower_tf} price below mouth'
                        })
                    
                    elif (current_reading['mouth_open_bear'] and lower_reading['price_above_mouth']):
                        illusions.append({
                            'type': 'Price Action Illusion',
                            'higher_tf': tf,
                            'lower_tf': lower_tf,
                            'alligator_type': 'Bear Signal, Bull Price',
                            'description': f'{tf} bearish mouth, but {lower_tf} price above mouth'
                        })
        
        return illusions
    
    def scan_multi_timeframe(self, instrument, timeframes=None):
        """Scan multiple timeframes for alligator illusions"""
        if timeframes is None:
            timeframes = ['D1', 'H4', 'H1', 'm15']
        
        readings = {}
        
        # Collect readings from all timeframes
        for tf in timeframes:
            data = self.load_csv_data(instrument, tf)
            if data is not None:
                reading = self.analyze_alligator_pattern(data, tf)
                if reading:
                    readings[tf] = reading
        
        # Detect illusions
        illusions = self.detect_illusions(readings)
        
        return {
            'status': 'success',
            'instrument': instrument,
            'timeframes_analyzed': list(readings.keys()),
            'readings': readings,
            'illusions': illusions,
            'illusion_count': len(illusions),
            'recommendation': 'PROCEED' if not illusions else 'CAUTION'
        }

class EnhancedFDBScanner:
    """Enhanced FDB Scanner with integrated Alligator Illusion Detection and Direction Analysis"""
    
    def __init__(self, data_path="/src/jgtml/cache/fdb_scanners"):
        self.illusion_detector = AlligatorIllusionDetector(data_path)
        self.data_path = Path(data_path)
    
    def load_fdb_signals(self, instrument, timeframe):
        """Load FDB signals from CDS cache data"""
        filename = f"{instrument}_{timeframe}_cds_cache.csv"
        filepath = self.data_path / filename
        
        if not filepath.exists():
            return None
        
        try:
            data = []
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            print(f"Error loading FDB data: {e}")
            return None
    
    def analyze_fdb_signals_with_direction(self, data, timeframe, instrument):
        """Analyze FDB signals and determine trade direction"""
        if not data or len(data) == 0:
            return None
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        df.index = pd.to_datetime(df['Date'])
        
        # Get last two bars for signal analysis
        signal_bar, current_bar = get_last_two_bars(df)
        
        fdb_signals = []
        direction_bias = "NONE"
        
        # Check FDB signal from signal bar
        fdb_value = int(float(signal_bar.get(FDB, 0)))
        
        if fdb_value == 1:  # Buy signal
            direction_bias = "BUY"
            
            # Validate signal using SignalOrderingHelper
            entry_order, msg = create_fdb_entry_order(
                instrument, 
                signal_bar, 
                current_bar,
                lots=1,
                t=timeframe,
                quiet=True,
                verbose_level=0
            )
            
            if entry_order:
                fdb_signals.append({
                    'type': 'buy',
                    'timestamp': signal_bar.get('Date', ''),
                    'entry_rate': entry_order.get('entry_rate', 0),
                    'stop_rate': entry_order.get('stop_rate', 0),
                    'validated': True
                })
        
        elif fdb_value == -1:  # Sell signal
            direction_bias = "SELL"
            
            # Validate signal using SignalOrderingHelper
            entry_order, msg = create_fdb_entry_order(
                instrument,
                signal_bar,
                current_bar,
                lots=1,
                t=timeframe,
                quiet=True,
                verbose_level=0
            )
            
            if entry_order:
                fdb_signals.append({
                    'type': 'sell',
                    'timestamp': signal_bar.get('Date', ''),
                    'entry_rate': entry_order.get('entry_rate', 0),
                    'stop_rate': entry_order.get('stop_rate', 0),
                    'validated': True
                })
        
        return {
            'timeframe': timeframe,
            'total_signals': len(fdb_signals),
            'signals': fdb_signals,
            'latest_signal': fdb_signals[-1] if fdb_signals else None,
            'direction_bias': direction_bias,
            'fdb_value': fdb_value
        }
    
    def enhanced_scan(self, instrument, timeframes=None, include_illusion_detection=True):
        """Perform enhanced FDB scan with optional illusion detection"""
        if timeframes is None:
            timeframes = ['D1', 'H1']
        
        print(f"\n🚀 ENHANCED FDB SCANNER - Phase 3 Integration")
        print(f"Instrument: {instrument}")
        print(f"Timeframes: {timeframes}")
        print("=" * 60)
        
        # Step 1: Standard FDB Signal Analysis
        print(f"\n📊 STEP 1: FDB SIGNAL ANALYSIS")
        print("-" * 30)
        
        fdb_results = {}
        for tf in timeframes:
            data = self.load_fdb_signals(instrument, tf)
            if data:
                fdb_analysis = self.analyze_fdb_signals_with_direction(data, tf, instrument)
                if fdb_analysis:
                    fdb_results[tf] = fdb_analysis
                    
                    print(f"{tf}: {fdb_analysis['total_signals']} FDB signals detected")
                    if fdb_analysis['latest_signal']:
                        latest = fdb_analysis['latest_signal']
                        print(f"  Latest: {latest['type'].upper()} signal at {latest['timestamp']}")
        
        # Step 2: Alligator Illusion Detection (if enabled)
        illusion_results = None
        if include_illusion_detection:
            print(f"\n🐊 STEP 2: ALLIGATOR ILLUSION DETECTION")
            print("-" * 30)
            
            illusion_results = self.illusion_detector.scan_multi_timeframe(instrument, timeframes)

            if illusion_results.get('status') == 'success':
                print(f"Analyzed {len(illusion_results['timeframes_analyzed'])} timeframes")
                
                if illusion_results['illusions']:
                    print(f"⚠️  {illusion_results['illusion_count']} ILLUSION(S) DETECTED:")
                    for i, illusion in enumerate(illusion_results['illusions'], 1):
                        print(f"  {i}. {illusion['type']} ({illusion['alligator_type']})")
                        print(f"     {illusion['description']}")
                else:
                    print("✅ NO ILLUSIONS DETECTED - Clear signal environment")
            else:
                print(f"❌ Illusion detection error: {illusion_results.get('message', 'Unknown error')}")
        
        # Step 3: Integrated Analysis & Recommendation
        print(f"\n🎯 STEP 3: INTEGRATED ANALYSIS")
        print("-" * 30)
        
        total_fdb_signals = sum(result['total_signals'] for result in fdb_results.values())
        illusion_count = illusion_results.get('illusion_count', 0) if illusion_results else 0
        
        # Calculate signal quality score
        signal_quality_score = self.calculate_signal_quality_score(
            total_fdb_signals, illusion_count, fdb_results, illusion_results
        )
        
        # Generate final recommendation
        final_recommendation = self.generate_final_recommendation(
            signal_quality_score, total_fdb_signals, illusion_count, fdb_results
        )
        
        print(f"FDB Signals Found: {total_fdb_signals}")
        print(f"Illusions Detected: {illusion_count}")
        print(f"Signal Quality Score: {signal_quality_score:.2f}/10")
        print(f"Final Recommendation: {final_recommendation}")
        
        # Step 4: Generate Comprehensive Report
        report = self.generate_comprehensive_report(
            instrument, timeframes, fdb_results, illusion_results, 
            signal_quality_score, final_recommendation
        )
        
        print(f"\n📋 COMPREHENSIVE ANALYSIS COMPLETE")
        print("=" * 60)
        
        return {
            'instrument': instrument,
            'timeframes': timeframes,
            'fdb_results': fdb_results,
            'illusion_results': illusion_results,
            'signal_quality_score': signal_quality_score,
            'final_recommendation': final_recommendation,
            'report': report,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_signal_quality_score(self, fdb_signals, illusions, fdb_results, illusion_results):
        """Calculate overall signal quality score (0-10)"""
        score = 5.0  # Base score
        
        # Add points for FDB signals
        if fdb_signals > 0:
            score += min(fdb_signals * 1.5, 3.0)  # Max 3 points for signals
        
        # Subtract points for illusions
        if illusions > 0:
            score -= min(illusions * 1.0, 4.0)  # Max -4 points for illusions
        
        # Bonus for multi-timeframe alignment
        if illusion_results and illusion_results.get('status') == 'success':
            if illusion_results.get('illusion_count', 0) == 0:
                score += 1.0  # Bonus for clean alignment
        
        return max(0.0, min(10.0, score))
    
    def generate_final_recommendation(self, quality_score, fdb_signals, illusions, fdb_results):
        """Generate final trading recommendation with direction"""
        # Determine dominant direction from FDB results
        buy_signals = 0
        sell_signals = 0
        
        for tf_result in fdb_results.values():
            direction = tf_result.get('direction_bias', 'NONE')
            if direction == 'BUY':
                buy_signals += 1
            elif direction == 'SELL':
                sell_signals += 1
        
        # Determine direction and strength
        if buy_signals > sell_signals:
            direction = "BUY"
        elif sell_signals > buy_signals:
            direction = "SELL"
        else:
            direction = "CONFLICTED"
        
        # Determine signal strength based on quality and illusions
        if quality_score >= 9.0 and fdb_signals >= 4 and illusions == 0:
            if direction in ["BUY", "SELL"]:
                return f"STRONG {direction}"
            else:
                return "MONITOR"  # Conflicted signals
        elif quality_score >= 8.0 and fdb_signals >= 3:
            if direction in ["BUY", "SELL"]:
                return f"MODERATE {direction}"
            else:
                return "MONITOR"
        elif quality_score >= 7.0 and fdb_signals >= 2:
            if direction in ["BUY", "SELL"]:
                return f"WEAK {direction}"
            else:
                return "MONITOR"
        elif quality_score >= 4.0:
            return "MONITOR"
        else:
            return "NO SIGNAL"
    
    def generate_comprehensive_report(self, instrument, timeframes, fdb_results, 
                                    illusion_results, quality_score, recommendation):
        """Generate comprehensive analysis report"""
        report = f"""
🚀 ENHANCED FDB SCANNER REPORT - Phase 3 Integration
Instrument: {instrument}
Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timeframes: {', '.join(timeframes)}

{'='*60}

📊 FDB SIGNAL ANALYSIS:
"""
        
        for tf, result in fdb_results.items():
            report += f"""
{tf} Timeframe:
  - Total Signals: {result['total_signals']}
  - Latest Signal: {result['latest_signal']['type'].upper() if result['latest_signal'] else 'None'}
"""
        
        if illusion_results:
            report += f"""
🐊 ALLIGATOR ILLUSION ANALYSIS:
  - Timeframes Analyzed: {len(illusion_results.get('timeframes_analyzed', []))}
  - Illusions Detected: {illusion_results.get('illusion_count', 0)}
  - Status: {illusion_results.get('recommendation', 'Unknown')}
"""
            
            if illusion_results.get('illusions'):
                report += "\n  Detected Illusions:\n"
                for i, illusion in enumerate(illusion_results['illusions'], 1):
                    report += f"    {i}. {illusion['type']} - {illusion['description']}\n"
        
        report += f"""
🎯 INTEGRATED ASSESSMENT:
  - Signal Quality Score: {quality_score:.2f}/10
  - Final Recommendation: {recommendation}
  - Analysis Confidence: {'High' if quality_score >= 7 else 'Medium' if quality_score >= 4 else 'Low'}

{'='*60}
"""
        
        return report

def main():
    """CLI interface for Enhanced FDB Scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced FDB Scanner with Alligator Illusion Detection')
    parser.add_argument('-i', '--instrument', required=True, 
                       help='Instrument to analyze (e.g., EUR-USD, SPX500)')
    parser.add_argument('-t', '--timeframes', nargs='+', default=['D1', 'H1'],
                       help='Timeframes to analyze')
    parser.add_argument('--no-illusion-detection', action='store_true',
                       help='Disable alligator illusion detection')
    parser.add_argument('--data-path', default='/src/jgtml/cache/fdb_scanners',
                       help='Path to CDS cache data')
    
    args = parser.parse_args()
    
    # Initialize enhanced scanner
    scanner = EnhancedFDBScanner(args.data_path)
    
    # Perform enhanced scan
    result = scanner.enhanced_scan(
        args.instrument, 
        args.timeframes, 
        include_illusion_detection=not args.no_illusion_detection
    )
    
    # Output comprehensive report
    print(result['report'])
    
    # Summary
    print(f"\n🎯 SCAN SUMMARY:")
    print(f"Quality Score: {result['signal_quality_score']:.2f}/10")
    print(f"Recommendation: {result['final_recommendation']}")

if __name__ == "__main__":
    main() 