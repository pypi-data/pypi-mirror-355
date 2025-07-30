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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add jgtml to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class AlligatorIllusionDetector:
    """Integrated Alligator Illusion Detection for FDB Scanner"""
    
    def __init__(self, data_path="/src/jgtml/cache/fdb_scanners"):
        self.data_path = Path(data_path)
    
    def load_csv_data(self, instrument, timeframe):
        """Load CDS cache data using basic CSV reader"""
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
            print(f"Error loading {instrument} {timeframe}: {e}")
            return None
    
    def analyze_alligator_pattern(self, data, timeframe):
        """Analyze alligator pattern from latest data"""
        if not data or len(data) == 0:
            return None
        
        latest = data[-1]
        
        # Extract alligator values
        jaw = self.safe_float(latest.get('jaw', 0))
        teeth = self.safe_float(latest.get('teeth', 0))
        lips = self.safe_float(latest.get('lips', 0))
        
        # Also extract big and tide alligator values
        bjaw = self.safe_float(latest.get('bjaw', 0))
        bteeth = self.safe_float(latest.get('bteeth', 0))
        blips = self.safe_float(latest.get('blips', 0))
        
        tjaw = self.safe_float(latest.get('tjaw', 0))
        tteeth = self.safe_float(latest.get('tteeth', 0))
        tlips = self.safe_float(latest.get('tlips', 0))
        
        # Determine trends for all alligator types
        regular_trend = self.determine_trend(jaw, teeth, lips)
        big_trend = self.determine_trend(bjaw, bteeth, blips)
        tide_trend = self.determine_trend(tjaw, tteeth, tlips)
        
        # Calculate mouth separations
        regular_mouth_sep = self.calculate_mouth_separation(jaw, lips)
        big_mouth_sep = self.calculate_mouth_separation(bjaw, blips)
        tide_mouth_sep = self.calculate_mouth_separation(tjaw, tlips)
        
        return {
            'timeframe': timeframe,
            'regular': {
                'jaw': jaw, 'teeth': teeth, 'lips': lips,
                'trend': regular_trend,
                'mouth_separation': regular_mouth_sep
            },
            'big': {
                'jaw': bjaw, 'teeth': bteeth, 'lips': blips,
                'trend': big_trend,
                'mouth_separation': big_mouth_sep
            },
            'tide': {
                'jaw': tjaw, 'teeth': tteeth, 'lips': tlips,
                'trend': tide_trend,
                'mouth_separation': tide_mouth_sep
            },
            'timestamp': latest.get('Date', '')
        }
    
    def safe_float(self, value):
        """Safely convert value to float"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def determine_trend(self, jaw, teeth, lips):
        """Determine trend direction from alligator lines"""
        if lips > teeth > jaw:
            return "bullish"
        elif lips < teeth < jaw:
            return "bearish"
        else:
            return "sideways"
    
    def calculate_mouth_separation(self, jaw, lips):
        """Calculate mouth separation percentage"""
        if jaw != 0:
            return abs(lips - jaw) / abs(jaw) * 100
        return 0.0
    
    def detect_illusions(self, multi_tf_readings):
        """Detect illusion patterns across multiple timeframes"""
        illusions = []
        
        if len(multi_tf_readings) < 2:
            return illusions
        
        timeframes = list(multi_tf_readings.keys())
        
        # Check for timeframe contradictions across all alligator types
        for alligator_type in ['regular', 'big', 'tide']:
            for i in range(len(timeframes)):
                for j in range(i+1, len(timeframes)):
                    tf1, tf2 = timeframes[i], timeframes[j]
                    
                    if tf1 not in multi_tf_readings or tf2 not in multi_tf_readings:
                        continue
                    
                    r1 = multi_tf_readings[tf1].get(alligator_type, {})
                    r2 = multi_tf_readings[tf2].get(alligator_type, {})
                    
                    if not r1 or not r2:
                        continue
                    
                    # Check for trend contradiction
                    if (r1.get('trend') == 'bullish' and r2.get('trend') == 'bearish') or \
                       (r1.get('trend') == 'bearish' and r2.get('trend') == 'bullish'):
                        
                        illusions.append({
                            'type': 'TIMEFRAME_CONTRADICTION',
                            'alligator_type': alligator_type,
                            'primary_tf': tf1,
                            'conflicting_tf': tf2,
                            'description': f"{alligator_type.upper()} alligator: {tf1} shows {r1.get('trend')} while {tf2} shows {r2.get('trend')}",
                            'confidence': 0.8,
                            'recommendation': 'Wait for timeframe alignment'
                        })
        
        # Check for weak signals
        for tf, reading in multi_tf_readings.items():
            for alligator_type in ['regular', 'big', 'tide']:
                alligator_data = reading.get(alligator_type, {})
                if not alligator_data:
                    continue
                
                trend = alligator_data.get('trend', 'sideways')
                mouth_sep = alligator_data.get('mouth_separation', 0)
                
                if trend != 'sideways' and mouth_sep < 0.05:
                    illusions.append({
                        'type': 'WEAK_SIGNAL',
                        'alligator_type': alligator_type,
                        'primary_tf': tf,
                        'conflicting_tf': None,
                        'description': f"Weak {alligator_type} alligator signal on {tf} - mouth separation only {mouth_sep:.3f}%",
                        'confidence': 0.6,
                        'recommendation': 'Wait for stronger confirmation'
                    })
        
        return illusions
    
    def scan_multi_timeframe(self, instrument, timeframes=None):
        """Scan instrument across multiple timeframes for illusions"""
        if timeframes is None:
            timeframes = ['D1', 'H1']
        
        readings = {}
        
        for tf in timeframes:
            data = self.load_csv_data(instrument, tf)
            if data:
                analysis = self.analyze_alligator_pattern(data, tf)
                if analysis:
                    readings[tf] = analysis
        
        if not readings:
            return {
                'status': 'error',
                'message': 'No data available for analysis'
            }
        
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
    """Enhanced FDB Scanner with integrated Alligator Illusion Detection"""
    
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
    
    def analyze_fdb_signals(self, data, timeframe):
        """Analyze FDB signals from the data"""
        if not data or len(data) == 0:
            return None
        
        # Get recent signals (last 10 bars)
        recent_data = data[-10:] if len(data) >= 10 else data
        
        fdb_signals = []
        
        for i, row in enumerate(recent_data):
            fdbb = int(float(row.get('fdbb', 0)))  # FDB Bear
            fdbs = int(float(row.get('fdbs', 0)))  # FDB Bull
            fdb = int(float(row.get('fdb', 0)))    # General FDB
            
            if fdbb == 1 or fdbs == 1 or fdb == 1:
                signal_type = 'bear' if fdbb == 1 else 'bull' if fdbs == 1 else 'general'
                
                fdb_signals.append({
                    'index': len(data) - len(recent_data) + i,
                    'timestamp': row.get('Date', ''),
                    'type': signal_type,
                    'fdbb': fdbb,
                    'fdbs': fdbs,
                    'fdb': fdb,
                    'close': float(row.get('Close', 0)),
                    'high': float(row.get('High', 0)),
                    'low': float(row.get('Low', 0))
                })
        
        return {
            'timeframe': timeframe,
            'total_signals': len(fdb_signals),
            'signals': fdb_signals,
            'latest_signal': fdb_signals[-1] if fdb_signals else None
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
                fdb_analysis = self.analyze_fdb_signals(data, tf)
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
            signal_quality_score, total_fdb_signals, illusion_count
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
    
    def generate_final_recommendation(self, quality_score, fdb_signals, illusions):
        """Generate final trading recommendation"""
        # Simple directional recommendation based on quality and signal count
        if quality_score >= 9.0 and fdb_signals >= 4 and illusions == 0:
            # For high quality signals, we need additional context to determine direction
            # For now, return a high-confidence signal that requires direction analysis
            return "STRONG SIGNAL" # Requires further direction analysis
        elif quality_score >= 8.0 and fdb_signals >= 3:
            return "MODERATE SIGNAL"
        elif quality_score >= 7.0 and fdb_signals >= 2:
            return "WEAK SIGNAL"
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