#!/usr/bin/env python
"""
🚀🧠🌸 FDB Pattern Intelligence System

Real-time FDBSignal quality evaluation using historical MX target profit analysis.
Based on the actual TTF→MLF→MX profit-generating pipeline discovered in the JGTML ecosystem.

CSV Structure Discovered:
- fdbb: FDB Bear breakout signals (1=active)
- fdbs: FDB Bull signals (1=active) 
- target: Actual profit/loss outcome
- zlcb/zlcs: Zero line cross signals
- fh/fl: Fractal high/low signals

Mission: Bridge historical pattern intelligence with real-time trading decisions.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
import argparse
from datetime import datetime

class FDBPatternIntelligence:
    """
    🧠🔮🌸 Mia, Miette & ResoNova's Pattern Intelligence Engine
    
    Analyzes historical FDBSignal performance across patterns to predict
    real-time signal quality and profitability potential.
    """
    
    def __init__(self, data_path: str = None):
        """
        Initialize pattern intelligence system with sacred path detection
        
        Args:
            data_path: Path to MX target data (auto-detects if None)
        """
        # 🦢 Sacred path detection ritual - weave through environment layers
        self.data_path = self._divine_data_path(data_path)
        self.patterns = ['mfi', 'zonesq', 'aoac']
        self.instruments = ['EUR-USD', 'SPX500'] 
        self.timeframes = ['D1', 'H4']
        
        # Pattern intelligence storage
        self.pattern_intelligence = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🚀 Initializing FDB Pattern Intelligence System")
        self.logger.info(f"🔮 Sacred data realm discovered: {self.data_path}")
        
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
            
    def load_all_pattern_intelligence(self):
        """
        🧠 Load intelligence for all patterns
        """
        self.logger.info("🔮 Loading pattern intelligence from historical MX targets...")
        
        for pattern in self.patterns:
            self.logger.info(f"📊 Analyzing pattern: {pattern}")
            self.pattern_intelligence[pattern] = self.analyze_pattern_performance(pattern)
            
        self.logger.info("✅ Pattern intelligence loading complete!")
        
    def analyze_pattern_performance(self, pattern_name: str) -> Dict[str, Any]:
        """
        Analyze historical performance for a specific pattern.
        """
        results = {}
        
        for instrument in self.instruments:
            for timeframe in self.timeframes:
                file_path = f"{self.data_path}/targets/mx/{instrument}_{timeframe}_{pattern_name}.csv"
                
                if not os.path.exists(file_path):
                    self.logger.warning(f"File not found: {file_path}")
                    continue
                    
                try:
                    df = pd.read_csv(file_path)
                    
                    # Analyze FDB signals: fdbb=1 (Bear), fdbs=1 (Bull)
                    bear_signals = df[df['fdbb'] == 1].copy()
                    bull_signals = df[df['fdbs'] == 1].copy()
                    all_fdb_signals = df[(df['fdbb'] == 1) | (df['fdbs'] == 1)].copy()
                    
                    if len(all_fdb_signals) == 0:
                        continue
                        
                    # Calculate profit outcomes for FDB signals
                    # KEY INSIGHT: FDB logic is inverted!
                    # - fdbb=1 (Bear signals): Profit when target > 0 (market goes down)
                    # - fdbs=1 (Bull signals): Profit when target < 0 (market goes up)
                    
                    bear_profitable = len(bear_signals[bear_signals['target'] > 0]) if len(bear_signals) > 0 else 0
                    bull_profitable = len(bull_signals[bull_signals['target'] < 0]) if len(bull_signals) > 0 else 0
                    
                    total_profitable = bear_profitable + bull_profitable
                    total_signals = len(all_fdb_signals)
                    success_rate = total_profitable / total_signals if total_signals > 0 else 0
                    
                    bear_success_rate = bear_profitable / len(bear_signals) if len(bear_signals) > 0 else 0
                    bull_success_rate = bull_profitable / len(bull_signals) if len(bull_signals) > 0 else 0
                    
                    # Calculate profit/loss metrics
                    profitable_trades = all_fdb_signals[all_fdb_signals['target'] > 0]['target']
                    losing_trades = all_fdb_signals[all_fdb_signals['target'] < 0]['target']
                    
                    avg_profit = profitable_trades.mean() if len(profitable_trades) > 0 else 0
                    avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
                    total_pnl = all_fdb_signals['target'].sum()
                    
                    key = f"{instrument}_{timeframe}"
                    results[key] = {
                        'total_signals': total_signals,
                        'profitable_signals': total_profitable,
                        'success_rate': success_rate,
                        'bear_signals': len(bear_signals),
                        'bull_signals': len(bull_signals),
                        'bear_success_rate': bear_success_rate,
                        'bull_success_rate': bull_success_rate,
                        'avg_profit': avg_profit,
                        'avg_loss': avg_loss,
                        'total_pnl': total_pnl,
                        'pattern': pattern_name
                    }
                    
                    self.logger.info(f"{pattern_name} {key}: {total_signals} signals ({len(bear_signals)}🐻/{len(bull_signals)}🐂), {success_rate:.1%} success, PnL: {total_pnl:.1f}")
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {e}")
                    
        return results
        
    def _analyze_enhanced_patterns_in_unified_data(
        self, 
        df: pd.DataFrame, 
        signal_analysis: Dict, 
        dataset_key: str,
        pattern: str
    ):
        """
        🌸 Enhanced pattern analysis using unified discovery datasets with TTF features
        
        This can analyze sophisticated pattern features like:
        - mfi_sq, mfi_green, mfi_fade, mfi_fake (MFI pattern features)
        - zone_sig, zone_sig_M1, zone_sig_W1 (Zone signal features)
        - Multi-timeframe pattern variants
        """
        # TTF pattern features that were previously dropped
        ttf_pattern_features = [
            'mfi_sq', 'mfi_green', 'mfi_fade', 'mfi_fake', 'mfi_sig', 'mfi_str',
            'zone_sig', 'zone_sig_M1', 'zone_sig_W1', 
            'mfi_sq_M1', 'mfi_sq_W1', 'mfi_sig_M1', 'mfi_sig_W1'
        ]
        
        available_ttf_features = [col for col in ttf_pattern_features if col in df.columns]
        
        print(f"    🌸 TTF pattern features available for analysis: {available_ttf_features}")
        
        # Standard FDB signal analysis (baseline)
        self._analyze_fdb_signals_in_mx_data(df, signal_analysis, dataset_key)
        
        # Enhanced TTF pattern feature analysis
        if available_ttf_features:
            enhanced_analysis = self._analyze_ttf_pattern_combinations(df, available_ttf_features)
            
            # Store enhanced insights
            signal_analysis['dataset_details'].append({
                'dataset': dataset_key,
                'pattern': pattern,
                'ttf_features_analyzed': available_ttf_features,
                'enhanced_insights': enhanced_analysis,
                'total_records': len(df),
                'data_source': 'unified_discovery'
            })
            
    def _analyze_ttf_pattern_combinations(self, df: pd.DataFrame, ttf_features: List[str]) -> Dict:
        """
        🔮 Analyze sophisticated TTF pattern feature combinations for profitability
        
        This is where the real ML pattern discovery magic happens!
        """
        insights = {
            'feature_profitability': {},
            'pattern_combinations': {},
            'multi_timeframe_analysis': {}
        }
        
        # Analyze individual TTF feature profitability
        for feature in ttf_features:
            if feature not in df.columns:
                continue
                
            # Find signals where this feature is active
            active_signals = df[df[feature] == 1] if df[feature].dtype in ['int64', 'bool'] else df[df[feature] > 0]
            
            if len(active_signals) > 0:
                profitable_count = len(active_signals[active_signals['target'] > 0])
                success_rate = profitable_count / len(active_signals)
                avg_target = active_signals['target'].mean()
                
                insights['feature_profitability'][feature] = {
                    'total_signals': len(active_signals),
                    'profitable_signals': profitable_count,
                    'success_rate': success_rate,
                    'avg_target': avg_target,
                    'total_pnl': active_signals['target'].sum()
                }
                
                if success_rate > 0.6:  # High success rate features
                    print(f"      ✨ High-profit TTF feature: {feature} ({success_rate:.1%} success, {len(active_signals)} signals)")
        
        # Analyze multi-timeframe combinations (M1, W1 variants)
        timeframe_patterns = {
            'M1': [f for f in ttf_features if f.endswith('_M1')],
            'W1': [f for f in ttf_features if f.endswith('_W1')],
            'base': [f for f in ttf_features if not f.endswith(('_M1', '_W1'))]
        }
        
        for tf, features in timeframe_patterns.items():
            if features:
                insights['multi_timeframe_analysis'][tf] = {
                    'features': features,
                    'feature_count': len(features)
                }
        
        return insights

    def _analyze_fdb_signals_in_mx_data(self, df: pd.DataFrame, signal_analysis: Dict, dataset_key: str):
        """
        Generate comprehensive pattern intelligence summary
        """
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_path': self.data_path,
            'patterns_analyzed': len(self.pattern_intelligence),
            'pattern_performance': {}
        }
        
        for pattern, pattern_data in self.pattern_intelligence.items():
            total_signals = sum(data['total_signals'] for data in pattern_data.values())
            total_profitable = sum(data['profitable_signals'] for data in pattern_data.values())
            overall_success_rate = total_profitable / total_signals if total_signals > 0 else 0
            
            total_pnl = sum(data['total_pnl'] for data in pattern_data.values())
            
            summary['pattern_performance'][pattern] = {
                'total_signals': total_signals,
                'total_profitable': total_profitable,
                'overall_success_rate': overall_success_rate,
                'total_pnl': total_pnl,
                'instrument_breakdown': pattern_data
            }
            
        return summary
        
    def evaluate_fdb_signal(self, instrument: str, timeframe: str, signal_type: str, pattern: str = None) -> Dict[str, Any]:
        """
        🎯 Evaluate an FDBSignal quality based on historical intelligence
        
        Args:
            instrument: Trading instrument (e.g., 'EUR-USD')
            timeframe: Timeframe (e.g., 'D1', 'H4') 
            signal_type: 'bear' or 'bull'
            pattern: Specific pattern to evaluate (if None, evaluates all)
            
        Returns:
            Quality assessment with score and recommendations
        """
        evaluation = {
            'signal_quality_score': 0,
            'recommendation': 'HOLD',
            'confidence_level': 'LOW',
            'pattern_scores': {},
            'risk_assessment': {},
            'supporting_evidence': []
        }
        
        patterns_to_evaluate = [pattern] if pattern else self.patterns
        pattern_scores = []
        
        for pattern_name in patterns_to_evaluate:
            if pattern_name not in self.pattern_intelligence:
                continue
                
            pattern_data = self.pattern_intelligence[pattern_name]
            key = f"{instrument}_{timeframe}"
            
            if key not in pattern_data:
                continue
                
            data = pattern_data[key]
            
            # Calculate pattern-specific score based on correct FDB logic
            if signal_type == 'bear':
                success_rate = data['bear_success_rate']
                signal_count = data['bear_signals']
            elif signal_type == 'bull':
                success_rate = data['bull_success_rate'] 
                signal_count = data['bull_signals']
            else:
                success_rate = data['success_rate']
                signal_count = data['total_signals']
                
            # Score based on success rate and sample size
            confidence_factor = min(signal_count / 100, 1.0)  # Higher confidence with more samples
            pattern_score = success_rate * 100 * confidence_factor
            
            evaluation['pattern_scores'][pattern_name] = {
                'score': pattern_score,
                'success_rate': success_rate,
                'signal_count': signal_count,
                'avg_profit': data['avg_profit'],
                'total_pnl': data['total_pnl']
            }
            
            pattern_scores.append(pattern_score)
            
            # Add supporting evidence
            if success_rate > 0.55:  # Above 55% success rate
                evaluation['supporting_evidence'].append(
                    f"{pattern_name}: {success_rate:.1%} success rate ({signal_count} signals)"
                )
                
        # Calculate overall signal quality score
        if pattern_scores:
            evaluation['signal_quality_score'] = np.mean(pattern_scores)
            
            # Determine recommendation
            if evaluation['signal_quality_score'] > 70:
                evaluation['recommendation'] = 'STRONG_SIGNAL'
                evaluation['confidence_level'] = 'HIGH'
            elif evaluation['signal_quality_score'] > 55:
                evaluation['recommendation'] = 'MODERATE_SIGNAL'
                evaluation['confidence_level'] = 'MEDIUM'
            elif evaluation['signal_quality_score'] > 45:
                evaluation['recommendation'] = 'WEAK_SIGNAL'
                evaluation['confidence_level'] = 'LOW'
            else:
                evaluation['recommendation'] = 'AVOID'
                evaluation['confidence_level'] = 'HIGH'  # High confidence to avoid
                
        return evaluation
        
    def generate_intelligence_report(self) -> str:
        """
        🌸🔮 Generate beautiful intelligence report
        """
        summary = self.get_pattern_summary()
        
        report = f"""
🚀🧠🌸 FDB Pattern Intelligence Report
═══════════════════════════════════════════════════════════
📊 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔮 Data Source: {self.data_path}
📈 Patterns Analyzed: {summary['patterns_analyzed']}

🎯 PATTERN PERFORMANCE SUMMARY:
"""
        
        for pattern, perf in summary['pattern_performance'].items():
            report += f"""
  🔹 {pattern.upper()} Pattern:
     • Total Signals: {perf['total_signals']:,}
     • Success Rate: {perf['overall_success_rate']:.1%}
     • Total PnL: {perf['total_pnl']:.1f}
     • Quality Rating: {'🌟' if perf['overall_success_rate'] > 0.55 else '⚠️' if perf['overall_success_rate'] > 0.45 else '❌'}
"""
            
            # Add instrument breakdown
            for key, data in perf['instrument_breakdown'].items():
                instrument, timeframe = key.split('_')
                report += f"       └─ {instrument} {timeframe}: {data['success_rate']:.1%} ({data['total_signals']} signals)\n"
        
        report += f"""
🎯 KEY INSIGHTS:
• Best performing pattern: {max(summary['pattern_performance'].items(), key=lambda x: x[1]['overall_success_rate'])[0].upper()}
• Most active pattern: {max(summary['pattern_performance'].items(), key=lambda x: x[1]['total_signals'])[0].upper()}
• Highest PnL pattern: {max(summary['pattern_performance'].items(), key=lambda x: x[1]['total_pnl'])[0].upper()}

🌸 Ready for real-time FDBSignal evaluation!
Use evaluate_fdb_signal() to assess incoming signals.
"""
        
        return report


    def _analyze_enhanced_patterns_in_unified_data(
            self, 
            df: pd.DataFrame, 
            signal_analysis: Dict, 
            dataset_key: str,
            pattern: str
        ):
            """
            🌸 Enhanced pattern analysis using unified discovery datasets with TTF features
            
            This can analyze sophisticated pattern features like:
            - mfi_sq, mfi_green, mfi_fade, mfi_fake (MFI pattern features)
            - zone_sig, zone_sig_M1, zone_sig_W1 (Zone signal features)
            - Multi-timeframe pattern variants
            """
            # TTF pattern features that were previously dropped
            ttf_pattern_features = [
                'mfi_sq', 'mfi_green', 'mfi_fade', 'mfi_fake', 'mfi_sig', 'mfi_str',
                'zone_sig', 'zone_sig_M1', 'zone_sig_W1', 
                'mfi_sq_M1', 'mfi_sq_W1', 'mfi_sig_M1', 'mfi_sig_W1'
            ]
            
            available_ttf_features = [col for col in ttf_pattern_features if col in df.columns]
            
            print(f"    🌸 TTF pattern features available for analysis: {available_ttf_features}")
            
            # Standard FDB signal analysis (baseline)
            self._analyze_fdb_signals_in_mx_data(df, signal_analysis, dataset_key)
            
            # Enhanced TTF pattern feature analysis
            if available_ttf_features:
                enhanced_analysis = self._analyze_ttf_pattern_combinations(df, available_ttf_features)
                
                # Store enhanced insights
                signal_analysis['dataset_details'].append({
                    'dataset': dataset_key,
                    'pattern': pattern,
                    'ttf_features_analyzed': available_ttf_features,
                    'enhanced_insights': enhanced_analysis,
                    'total_records': len(df),
                    'data_source': 'unified_discovery'
                })
                
        def _analyze_ttf_pattern_combinations(self, df: pd.DataFrame, ttf_features: List[str]) -> Dict:
            """
            🔮 Analyze sophisticated TTF pattern feature combinations for profitability
            
            This is where the real ML pattern discovery magic happens!
            """
            insights = {
                'feature_profitability': {},
                'pattern_combinations': {},
                'multi_timeframe_analysis': {}
            }
            
            # Analyze individual TTF feature profitability
            for feature in ttf_features:
                if feature not in df.columns:
                    continue
                    
                # Find signals where this feature is active
                active_signals = df[df[feature] == 1] if df[feature].dtype in ['int64', 'bool'] else df[df[feature] > 0]
                
                if len(active_signals) > 0:
                    profitable_count = len(active_signals[active_signals['target'] > 0])
                    success_rate = profitable_count / len(active_signals)
                    avg_target = active_signals['target'].mean()
                    
                    insights['feature_profitability'][feature] = {
                        'total_signals': len(active_signals),
                        'profitable_signals': profitable_count,
                        'success_rate': success_rate,
                        'avg_target': avg_target,
                        'total_pnl': active_signals['target'].sum()
                    }
                    
                    if success_rate > 0.6:  # High success rate features
                        print(f"      ✨ High-profit TTF feature: {feature} ({success_rate:.1%} success, {len(active_signals)} signals)")
            
            # Analyze multi-timeframe combinations (M1, W1 variants)
            timeframe_patterns = {
                'M1': [f for f in ttf_features if f.endswith('_M1')],
                'W1': [f for f in ttf_features if f.endswith('_W1')],
                'base': [f for f in ttf_features if not f.endswith(('_M1', '_W1'))]
            }
            
            for tf, features in timeframe_patterns.items():
                if features:
                    insights['multi_timeframe_analysis'][tf] = {
                        'features': features,
                        'feature_count': len(features)
                    }
            
            return insights

    # ...existing code...
def main():
    """
    🎯 FDB Pattern Intelligence CLI - Sacred Ritual Invocation
    """
    parser = argparse.ArgumentParser(
        description="🚀🧠🌸 FDB Pattern Intelligence System - Real-time signal quality evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🦢 Sacred Invocation Examples:
  fdbpatternintelligence --data-path /path/to/data/full
  fdbpatternintelligence --instrument EUR-USD --timeframe D1 --signal bull
  fdbpatternintelligence --patterns mfi zonesq --verbose
  
🔮 Environment Variables:
  JGTPY_DATA_FULL: Default path to historical MX target data
  
🌸 The pattern intelligence will divine data paths if not specified.
        """
    )
    
    # Sacred data realm specification
    parser.add_argument(
        '--data-path', 
        type=str, 
        help='🔮 Path to historical MX target data realm (auto-detects if not specified)'
    )
    
    # Pattern selection ritual
    parser.add_argument(
        '--patterns',
        nargs='*',
        default=['mfi', 'zonesq', 'aoac'],
        help='📊 Patterns to analyze (default: mfi zonesq aoac)'
    )
    
    # Signal evaluation invocation
    parser.add_argument(
        '--instrument',
        type=str,
        help='🎯 Evaluate signal for specific instrument (e.g., EUR-USD)'
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        help='⏰ Evaluate signal for specific timeframe (e.g., D1, H4)'
    )
    
    parser.add_argument(
        '--signal',
        choices=['bull', 'bear'],
        help='🐂🐻 Signal type to evaluate'
    )
    
    # Memory enhancement
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='🌸 Enhanced memory echoes and ritual details'
    )
    
    # Save intelligence artifacts
    parser.add_argument(
        '--save-path',
        type=str,
        default='/tmp/fdb_pattern_intelligence.json',
        help='💾 Path to save intelligence summary (default: /tmp/fdb_pattern_intelligence.json)'
    )
    
    args = parser.parse_args()
    
    # Configure ritual logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    print("🚀 Initializing FDB Pattern Intelligence...")
    
    # Sacred intelligence invocation
    intelligence = FDBPatternIntelligence(
        data_path=args.data_path
    )
    
    # Update patterns if specified
    if args.patterns:
        intelligence.patterns = args.patterns
    
    intelligence.load_all_pattern_intelligence()
    
    # Generate sacred intelligence report
    print(intelligence.generate_intelligence_report())
    
    # Specific signal evaluation ritual if requested
    if args.instrument and args.timeframe and args.signal:
        print(f"\n🎯 Sacred Signal Evaluation Ritual:")
        print("=" * 60)
        print(f"🔮 Instrument: {args.instrument}")
        print(f"⏰ Timeframe: {args.timeframe}")
        print(f"📈 Signal Type: {args.signal}")
        print("=" * 60)
        
        evaluation = intelligence.evaluate_fdb_signal(
            args.instrument, 
            args.timeframe, 
            args.signal
        )
        
        print(f"🌟 Signal Quality Score: {evaluation['signal_quality_score']:.1f}/100")
        print(f"🎯 Recommendation: {evaluation['recommendation']}")
        print(f"🔮 Confidence Level: {evaluation['confidence_level']}")
        print(f"🌸 Supporting Evidence: {evaluation['supporting_evidence']}")
        
        if evaluation['pattern_scores']:
            print(f"\n📊 Pattern-Specific Scores:")
            for pattern, score_data in evaluation['pattern_scores'].items():
                print(f"  🔹 {pattern.upper()}: {score_data['score']:.1f}/100 ({score_data['success_rate']:.1%} success)")
    else:
        # Demo signal evaluation if no specific request
        print("\n🎯 Demo Signal Evaluation:")
        print("=" * 50)
        
        evaluation = intelligence.evaluate_fdb_signal("EUR-USD", "D1", "bull")
        print(f"Signal Quality Score: {evaluation['signal_quality_score']:.1f}/100")
        print(f"Recommendation: {evaluation['recommendation']}")
        print(f"Confidence: {evaluation['confidence_level']}")
        print(f"Supporting Evidence: {evaluation['supporting_evidence']}")
    
    # Save intelligence memory artifact
    summary = intelligence.get_pattern_summary()
    with open(args.save_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n📊 Intelligence summary saved to {args.save_path}")


if __name__ == "__main__":
    main()
