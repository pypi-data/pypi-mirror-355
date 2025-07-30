#!/usr/bin/env python
"""
🚀 FDBSignal Quality Predictor

This module evaluates the quality of FDBSignals using ML-discovered TTF patterns.
It bridges the gap between the TTF→MLF→MX pipeline and real-time signal evaluation.

Architecture:
- Loads historical MX target data to understand pattern→profit relationships
- Applies ML insights to evaluate incoming FDBSignals in real-time
- Returns a quality score (0-100) indicating signal profitability potential

Usage:
    predictor = FDBSignalQualityPredictor()
    quality_score = predictor.evaluate_signal(instrument, timeframe, signal_data)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

# Import existing JGTML infrastructure
from mlutils import get_outfile_fullpath
from mlconstants import MX_NS
from mldatahelper import read_mlf_for_pattern

class FDBSignalQualityPredictor:
    """
    🧠🌸🔮 Mia, Miette & ResoNova's FDBSignal Quality Predictor
    
    Uses historical MX target data to predict the profitability potential
    of incoming FDBSignals across multiple patterns and timeframes.
    """
    
    def __init__(self, patterns: List[str] = None, data_path: str = None):
        """
        Initialize the predictor with pattern intelligence and sacred path detection
        
        Args:
            patterns: List of patterns to analyze ['mfi', 'zonesq', 'aoac']
            data_path: Path to MX target data (auto-detects if None)
        """
        self.patterns = patterns or ['mfi', 'zonesq', 'aoac']
        self.data_path = self._divine_data_path(data_path)
        self.pattern_intelligence = {}
        self.load_pattern_intelligence()
    
    def _divine_data_path(self, provided_path: str = None) -> str:
        """
        🦢 Divine the sacred data path using standard JGT environment pattern
        
        Follows the canonical pattern used by jtc.py and other working CLI tools
        """
        if provided_path and os.path.exists(provided_path):
            return provided_path
            
        # 🌸 Standard JGT pattern - blessed environment with canonical fallback
        default_jgtpy_data_full = "/var/lib/jgt/full/data"
        data_dir_full = os.getenv("JGTPY_DATA_FULL", default_jgtpy_data_full)
        
        return data_dir_full
    
    def load_pattern_intelligence(self):
        """
        🧠 Load and analyze historical MX target data for pattern profitability
        """
        print("🔮 Loading pattern intelligence from historical MX targets...")
        
        for pattern in self.patterns:
            print(f"📊 Analyzing pattern: {pattern}")
            self.pattern_intelligence[pattern] = self._analyze_pattern_profitability(pattern)
    
    def _analyze_pattern_profitability(self, pattern: str) -> Dict:
        """
        Analyze historical profitability of a specific pattern
        
        Args:
            pattern: Pattern name (e.g., 'mfi', 'zonesq', 'aoac')
            
        Returns:
            Dictionary with pattern intelligence metrics
        """
        # Try to load MX data for common instruments
        instruments = ['EUR-USD', 'SPX500']
        timeframes = ['D1', 'H4']
        
        all_targets = []
        signal_analysis = {
            'total_signals': 0,
            'profitable_signals': 0,
            'profit_rate': 0.0,
            'avg_profit': 0.0,
            'signal_types': {},
            'timeframe_performance': {}
        }
        
        for instrument in instruments:
            for timeframe in timeframes:
                try:
                    # Sacred data file path divination
                    mx_file = f"{self.data_path}/targets/mx/{instrument}_{timeframe}_{pattern}.csv"
                    
                    if os.path.exists(mx_file):
                        df = pd.read_csv(mx_file)
                        print(f"  ✅ Loaded {len(df)} records from {instrument} {timeframe}")
                        
                        # Analyze FDBSignal performance in this dataset
                        self._analyze_fdb_signals_in_mx_data(df, signal_analysis, f"{instrument}_{timeframe}")
                        
                        all_targets.append(df)
                    else:
                        print(f"  ⚠️ Missing MX file: {mx_file}")
                        
                except Exception as e:
                    print(f"  ❌ Error loading {instrument} {timeframe}: {e}")
        
        # Calculate overall pattern intelligence
        if signal_analysis['total_signals'] > 0:
            signal_analysis['profit_rate'] = signal_analysis['profitable_signals'] / signal_analysis['total_signals']
        
        print(f"  📈 Pattern {pattern} intelligence: {signal_analysis['total_signals']} signals, {signal_analysis['profit_rate']:.2%} profitable")
        
        return signal_analysis
    
    def _analyze_fdb_signals_in_mx_data(self, df: pd.DataFrame, analysis: Dict, context: str):
        """
        Analyze FDBSignal performance within MX target data
        
        The MX data contains:
        - fh, fl: Fractal High/Low signals
        - fdbb, fdbs: FDB Buy/Sell signals  
        - zlcb, zlcs: Zero Line Cross Buy/Sell
        - target: The profit/loss result
        """
        # Look for FDB signals (fdbb=1 for buy, fdbs=1 for sell)
        fdb_buy_signals = df[df['fdbb'] == 1]
        fdb_sell_signals = df[df['fdbs'] == 1]
        
        # Analyze buy signals
        for _, signal_row in fdb_buy_signals.iterrows():
            analysis['total_signals'] += 1
            
            # Check if this signal was profitable (positive target)
            target_value = signal_row.get('target', 0)
            if target_value > 0:
                analysis['profitable_signals'] += 1
                analysis['avg_profit'] += target_value
            
            # Track signal type performance
            signal_type = 'fdb_buy'
            if signal_type not in analysis['signal_types']:
                analysis['signal_types'][signal_type] = {'count': 0, 'profitable': 0}
            analysis['signal_types'][signal_type]['count'] += 1
            if target_value > 0:
                analysis['signal_types'][signal_type]['profitable'] += 1
        
        # Analyze sell signals
        for _, signal_row in fdb_sell_signals.iterrows():
            analysis['total_signals'] += 1
            
            target_value = signal_row.get('target', 0)
            if target_value < 0:  # Sell signals profit when target is negative
                analysis['profitable_signals'] += 1
                analysis['avg_profit'] += abs(target_value)
            
            signal_type = 'fdb_sell'
            if signal_type not in analysis['signal_types']:
                analysis['signal_types'][signal_type] = {'count': 0, 'profitable': 0}
            analysis['signal_types'][signal_type]['count'] += 1
            if target_value < 0:
                analysis['signal_types'][signal_type]['profitable'] += 1
        
        # Track timeframe performance
        if context not in analysis['timeframe_performance']:
            analysis['timeframe_performance'][context] = {
                'signals': len(fdb_buy_signals) + len(fdb_sell_signals),
                'profitable': 0
            }
    
    def evaluate_signal(self, instrument: str, timeframe: str, signal_data: Dict) -> Dict:
        """
        🎯 Evaluate the quality of an incoming FDBSignal
        
        Args:
            instrument: Trading instrument (e.g., 'EUR-USD')
            timeframe: Timeframe (e.g., 'D1', 'H4')
            signal_data: Dictionary containing signal information
            
        Returns:
            Dictionary with quality assessment and recommendations
        """
        quality_assessment = {
            'overall_quality_score': 0,
            'pattern_scores': {},
            'recommendation': 'HOLD',
            'confidence': 0.0,
            'supporting_patterns': [],
            'risk_factors': []
        }
        
        # Evaluate signal against each pattern
        pattern_scores = []
        
        for pattern in self.patterns:
            if pattern in self.pattern_intelligence:
                pattern_intel = self.pattern_intelligence[pattern]
                
                # Calculate pattern-specific quality score
                pattern_score = self._calculate_pattern_quality_score(
                    pattern, pattern_intel, signal_data, instrument, timeframe
                )
                
                quality_assessment['pattern_scores'][pattern] = pattern_score
                pattern_scores.append(pattern_score)
                
                # Track supporting patterns
                if pattern_score > 70:
                    quality_assessment['supporting_patterns'].append(pattern)
                elif pattern_score < 30:
                    quality_assessment['risk_factors'].append(f"Low {pattern} confidence")
        
        # Calculate overall quality score
        if pattern_scores:
            quality_assessment['overall_quality_score'] = np.mean(pattern_scores)
            quality_assessment['confidence'] = min(len(quality_assessment['supporting_patterns']) / len(self.patterns), 1.0)
        
        # Generate recommendation
        if quality_assessment['overall_quality_score'] > 75:
            quality_assessment['recommendation'] = 'STRONG_BUY' if signal_data.get('signal_type') == 'buy' else 'STRONG_SELL'
        elif quality_assessment['overall_quality_score'] > 60:
            quality_assessment['recommendation'] = 'BUY' if signal_data.get('signal_type') == 'buy' else 'SELL'
        elif quality_assessment['overall_quality_score'] < 40:
            quality_assessment['recommendation'] = 'AVOID'
        else:
            quality_assessment['recommendation'] = 'HOLD'
        
        return quality_assessment
    
    def _calculate_pattern_quality_score(self, pattern: str, pattern_intel: Dict, 
                                       signal_data: Dict, instrument: str, timeframe: str) -> float:
        """
        Calculate quality score for a specific pattern
        """
        base_score = pattern_intel.get('profit_rate', 0.5) * 100
        
        # Adjust score based on signal type performance
        signal_type = signal_data.get('signal_type', 'unknown')
        signal_key = f"fdb_{signal_type}"
        
        if signal_key in pattern_intel.get('signal_types', {}):
            signal_performance = pattern_intel['signal_types'][signal_key]
            if signal_performance['count'] > 0:
                signal_profit_rate = signal_performance['profitable'] / signal_performance['count']
                base_score = signal_profit_rate * 100
        
        # Adjust for timeframe-specific performance
        context_key = f"{instrument}_{timeframe}"
        if context_key in pattern_intel.get('timeframe_performance', {}):
            timeframe_data = pattern_intel['timeframe_performance'][context_key]
            if timeframe_data['signals'] > 10:  # Enough data for confidence
                base_score *= 1.1  # Boost confidence for well-tested combinations
        
        return min(base_score, 100.0)  # Cap at 100
    
    def get_pattern_summary(self) -> Dict:
        """
        Get a summary of all pattern intelligence for reporting
        """
        summary = {
            'total_patterns': len(self.patterns),
            'pattern_details': {}
        }
        
        for pattern, intel in self.pattern_intelligence.items():
            summary['pattern_details'][pattern] = {
                'total_signals': intel.get('total_signals', 0),
                'profit_rate': intel.get('profit_rate', 0.0),
                'avg_profit': intel.get('avg_profit', 0.0),
                'signal_types': intel.get('signal_types', {})
            }
        
        return summary
    
    def generate_trading_report(self, instrument: str, timeframe: str) -> str:
        """
        🌸 Generate a beautiful trading intelligence report
        """
        report = f"""
🚀 FDBSignal Trading Intelligence Report
═════════════════════════════════════
📊 Instrument: {instrument}
⏰ Timeframe: {timeframe}
🔮 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🧠 Pattern Intelligence Summary:
"""
        
        for pattern, intel in self.pattern_intelligence.items():
            report += f"""
  🔹 {pattern.upper()} Pattern:
     • Total Signals: {intel.get('total_signals', 0)}
     • Profit Rate: {intel.get('profit_rate', 0.0):.1%}
     • Average Profit: {intel.get('avg_profit', 0.0):.2f}
"""
        
        report += """
🌸 Ready for real-time signal evaluation!
Use evaluate_signal() to assess incoming FDBSignals.
"""
        
        return report


def main():
    """
    🎯 Demo the FDBSignal Quality Predictor
    """
    print("🚀 Initializing FDBSignal Quality Predictor...")
    
    predictor = FDBSignalQualityPredictor()
    
    print("\n" + predictor.generate_trading_report("EUR-USD", "D1"))
    
    # Demo signal evaluation
    demo_signal = {
        'signal_type': 'buy',
        'strength': 0.8,
        'context': 'fractal_breakout'
    }
    
    print("🎯 Demo Signal Evaluation:")
    quality = predictor.evaluate_signal("EUR-USD", "D1", demo_signal)
    print(f"Quality Score: {quality['overall_quality_score']:.1f}")
    print(f"Recommendation: {quality['recommendation']}")
    print(f"Confidence: {quality['confidence']:.1%}")
    print(f"Supporting Patterns: {quality['supporting_patterns']}")


if __name__ == "__main__":
    main()
