import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Industry benchmark data (based on aggregated anonymous data)
INDUSTRY_BENCHMARKS = {
    "match_rate": {
        "top_10_percent": 0.98,
        "average": 0.85,
        "bottom_25_percent": 0.70,
        "target": 0.92
    },
    "fraud_risk": {
        "top_10_percent": 15,
        "average": 35,
        "bottom_25_percent": 60,
        "target": 25
    },
    "audit_time_hours": {
        "small_firm": {"average": 25, "top_performers": 15},
        "medium_firm": {"average": 45, "top_performers": 30},
        "large_firm": {"average": 80, "top_performers": 55}
    },
    "anomaly_rate": {
        "average": 0.08,  # 8% of transactions flagged
        "top_performers": 0.03,
        "target": 0.05
    }
}

def get_firm_size(total_audits):
    """Determine firm size based on audit volume"""
    if total_audits < 20:
        return "small_firm"
    elif total_audits < 100:
        return "medium_firm"
    else:
        return "large_firm"

def calculate_percentile(value, metric):
    """Calculate percentile rank based on industry distribution"""
    if metric == "match_rate":
        if value >= INDUSTRY_BENCHMARKS["match_rate"]["top_10_percent"]:
            return 90
        elif value >= INDUSTRY_BENCHMARKS["match_rate"]["average"]:
            return 60
        elif value >= INDUSTRY_BENCHMARKS["match_rate"]["bottom_25_percent"]:
            return 25
        else:
            return 10
    elif metric == "fraud_risk":
        if value <= INDUSTRY_BENCHMARKS["fraud_risk"]["top_10_percent"]:
            return 90
        elif value <= INDUSTRY_BENCHMARKS["fraud_risk"]["average"]:
            return 60
        elif value <= INDUSTRY_BENCHMARKS["fraud_risk"]["bottom_25_percent"]:
            return 25
        else:
            return 10
    return 50

def get_performance_rating(value, metric, higher_is_better=True):
    """Get performance rating (Excellent, Good, Average, Needs Improvement)"""
    if metric == "match_rate":
        if value >= INDUSTRY_BENCHMARKS["match_rate"]["top_10_percent"]:
            return "Excellent 🏆", "top_10_percent"
        elif value >= INDUSTRY_BENCHMARKS["match_rate"]["average"]:
            return "Good ✓", "average"
        elif value >= INDUSTRY_BENCHMARKS["match_rate"]["bottom_25_percent"]:
            return "Average", "bottom_25_percent"
        else:
            return "Needs Improvement ⚠️", "below"
    elif metric == "fraud_risk":
        if value <= INDUSTRY_BENCHMARKS["fraud_risk"]["top_10_percent"]:
            return "Excellent 🏆", "top_10_percent"
        elif value <= INDUSTRY_BENCHMARKS["fraud_risk"]["average"]:
            return "Good ✓", "average"
        elif value <= INDUSTRY_BENCHMARKS["fraud_risk"]["bottom_25_percent"]:
            return "Average", "bottom_25_percent"
        else:
            return "Needs Improvement ⚠️", "below"
    return "Average", "average"

def generate_benchmark_recommendations(match_rate, fraud_risk, total_audits):
    """Generate recommendations based on benchmark comparison"""
    recommendations = []
    
    # Match rate recommendations
    if match_rate < INDUSTRY_BENCHMARKS["match_rate"]["average"]:
        recommendations.append({
            "area": "Match Rate",
            "current": f"{match_rate:.1%}",
            "benchmark": f"{INDUSTRY_BENCHMARKS['match_rate']['average']:.1%}",
            "gap": f"{(INDUSTRY_BENCHMARKS['match_rate']['average'] - match_rate):.1%}",
            "recommendation": "Improve reconciliation by standardizing transaction descriptions and implementing automated mapping rules."
        })
    elif match_rate < INDUSTRY_BENCHMARKS["match_rate"]["top_10_percent"]:
        recommendations.append({
            "area": "Match Rate",
            "current": f"{match_rate:.1%}",
            "benchmark": f"{INDUSTRY_BENCHMARKS['match_rate']['top_10_percent']:.1%}",
            "gap": f"{(INDUSTRY_BENCHMARKS['match_rate']['top_10_percent'] - match_rate):.1%}",
            "recommendation": "Review unmatched transactions weekly to maintain top-tier performance."
        })
    
    # Fraud risk recommendations
    if fraud_risk > INDUSTRY_BENCHMARKS["fraud_risk"]["average"]:
        recommendations.append({
            "area": "Fraud Risk",
            "current": f"{fraud_risk:.0f}%",
            "benchmark": f"{INDUSTRY_BENCHMARKS['fraud_risk']['average']:.0f}%",
            "gap": f"{(fraud_risk - INDUSTRY_BENCHMARKS['fraud_risk']['average']):.0f}%",
            "recommendation": "Increase testing of high-risk transactions and implement additional controls for round-dollar amounts."
        })
    
    # Volume-based recommendations
    if total_audits < 20:
        recommendations.append({
            "area": "Audit Volume",
            "current": str(total_audits),
            "benchmark": "20+",
            "gap": f"{20 - total_audits}",
            "recommendation": "Increase audit frequency to establish meaningful performance trends."
        })
    
    return recommendations

def display_benchmark_dashboard(firm_id, stats, audits):
    """Display benchmarking dashboard"""
    
    st.markdown("### 📊 Audit Benchmarking")
    st.markdown("Compare your audit performance against industry standards.")
    
    if not audits or len(audits) < 5:
        st.info("Run at least 5 audits to see meaningful benchmark comparisons.")
        return
    
    # Calculate key metrics
    avg_match_rate = stats['avg_match_rate']
    avg_fraud_risk = stats['avg_fraud_risk']
    total_audits = stats['total_audits']
    
    # Get firm size
    firm_size = get_firm_size(total_audits)
    
    st.markdown("---")
    
    # Match Rate Benchmark
    st.subheader("📈 Match Rate Benchmark")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gauge chart for match rate
        rating, percentile = get_performance_rating(avg_match_rate, "match_rate")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = avg_match_rate * 100,
            title = {'text': "Match Rate"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 70], 'color': "#ff6b6b"},
                    {'range': [70, 85], 'color': "#ffa500"},
                    {'range': [85, 98], 'color': "#ffa500"},
                    {'range': [98, 100], 'color': "#4ecdc4"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': INDUSTRY_BENCHMARKS["match_rate"]["average"] * 100
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"**Performance Rating:** {rating}")
        st.markdown(f"**Your Score:** {avg_match_rate:.1%}")
        st.markdown(f"**Industry Average:** {INDUSTRY_BENCHMARKS['match_rate']['average']:.1%}")
        st.markdown(f"**Top 10%:** {INDUSTRY_BENCHMARKS['match_rate']['top_10_percent']:.1%}")
        
        gap = avg_match_rate - INDUSTRY_BENCHMARKS["match_rate"]["average"]
        if gap > 0:
            st.success(f"✅ {gap:.1%} above industry average")
        else:
            st.warning(f"⚠️ {abs(gap):.1%} below industry average")
    
    st.markdown("---")
    
    # Fraud Risk Benchmark
    st.subheader("🚨 Fraud Risk Benchmark")
    
    col1, col2 = st.columns(2)
    
    with col1:
        rating, percentile = get_performance_rating(avg_fraud_risk, "fraud_risk")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = avg_fraud_risk,
            title = {'text': "Fraud Risk Score"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#ffa500"},
                'steps': [
                    {'range': [0, 15], 'color': "#4ecdc4"},
                    {'range': [15, 35], 'color': "#ffa500"},
                    {'range': [35, 100], 'color': "#ff6b6b"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': INDUSTRY_BENCHMARKS["fraud_risk"]["average"]
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"**Performance Rating:** {rating}")
        st.markdown(f"**Your Score:** {avg_fraud_risk:.0f}%")
        st.markdown(f"**Industry Average:** {INDUSTRY_BENCHMARKS['fraud_risk']['average']:.0f}%")
        st.markdown(f"**Top 10%:** {INDUSTRY_BENCHMARKS['fraud_risk']['top_10_percent']:.0f}%")
        
        if avg_fraud_risk < INDUSTRY_BENCHMARKS["fraud_risk"]["average"]:
            st.success(f"✅ {INDUSTRY_BENCHMARKS['fraud_risk']['average'] - avg_fraud_risk:.0f}% lower risk than average")
        else:
            st.warning(f"⚠️ {avg_fraud_risk - INDUSTRY_BENCHMARKS['fraud_risk']['average']:.0f}% higher risk than average")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("💡 Improvement Recommendations")
    
    recommendations = generate_benchmark_recommendations(avg_match_rate, avg_fraud_risk, total_audits)
    
    if recommendations:
        for rec in recommendations:
            with st.container():
                st.markdown(f"**{rec['area']}**")
                col1, col2, col3 = st.columns(3)
                col1.metric("Your Score", rec['current'])
                col2.metric("Industry Benchmark", rec['benchmark'])
                col3.metric("Gap", rec['gap'])
                st.info(f"📝 {rec['recommendation']}")
                st.markdown("---")
    else:
        st.success("🎉 Your performance is above industry benchmarks! Keep up the great work.")
    
    # Export option
    if st.button("📥 Download Benchmark Report"):
        report_data = {
            "Metric": ["Match Rate", "Fraud Risk", "Total Audits"],
            "Your Score": [f"{avg_match_rate:.1%}", f"{avg_fraud_risk:.0f}%", total_audits],
            "Industry Average": [f"{INDUSTRY_BENCHMARKS['match_rate']['average']:.1%}", 
                                f"{INDUSTRY_BENCHMARKS['fraud_risk']['average']:.0f}%", "N/A"],
            "Top 10%": [f"{INDUSTRY_BENCHMARKS['match_rate']['top_10_percent']:.1%}", 
                       f"{INDUSTRY_BENCHMARKS['fraud_risk']['top_10_percent']:.0f}%", "N/A"]
        }
        df = pd.DataFrame(report_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"benchmark_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )