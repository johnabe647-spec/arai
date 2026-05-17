import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def save_feedback(firm_id, client_name, client_email, audit_id, rating, nps_score, comments):
    """Save client feedback to database"""
    supabase = get_supabase()
    
    # Simple sentiment analysis
    sentiment = "neutral"
    if comments:
        positive_words = ["good", "great", "excellent", "amazing", "helpful", "clear", "accurate", "fast", "professional"]
        negative_words = ["bad", "poor", "slow", "confusing", "error", "wrong", "inaccurate", "unhelpful"]
        
        comments_lower = comments.lower()
        pos_count = sum(1 for word in positive_words if word in comments_lower)
        neg_count = sum(1 for word in negative_words if word in comments_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
    
    try:
        result = supabase.table("client_feedback").insert({
            "firm_id": firm_id,
            "client_name": client_name,
            "client_email": client_email,
            "audit_id": audit_id,
            "rating": rating,
            "nps_score": nps_score,
            "comments": comments,
            "sentiment": sentiment
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def get_feedback(firm_id, limit=100):
    """Get all feedback for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("client_feedback").select("*").eq("firm_id", firm_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        return []

def get_feedback_stats(firm_id):
    """Get feedback statistics"""
    feedback = get_feedback(firm_id, limit=1000)
    
    if not feedback:
        return {
            "total": 0,
            "avg_rating": 0,
            "avg_nps": 0,
            "promoters": 0,
            "passives": 0,
            "detractors": 0,
            "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0}
        }
    
    ratings = [f.get('rating', 0) for f in feedback if f.get('rating')]
    nps_scores = [f.get('nps_score', 0) for f in feedback if f.get('nps_score') is not None]
    
    # Calculate NPS categories
    promoters = sum(1 for n in nps_scores if n >= 9)
    passives = sum(1 for n in nps_scores if 7 <= n <= 8)
    detractors = sum(1 for n in nps_scores if n <= 6)
    nps = round(((promoters - detractors) / len(nps_scores)) * 100) if nps_scores else 0
    
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for f in feedback:
        sentiment = f.get('sentiment', 'neutral')
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    return {
        "total": len(feedback),
        "avg_rating": sum(ratings) / len(ratings) if ratings else 0,
        "avg_nps": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "nps_score": nps,
        "sentiment_counts": sentiment_counts
    }

def display_feedback_form():
    """Display feedback form for clients"""
    
    st.markdown("### 📝 Client Feedback")
    st.markdown("We value your opinion! Please take a moment to share your experience.")
    
    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Your Name")
        with col2:
            client_email = st.text_input("Your Email")
        
        st.markdown("---")
        st.markdown("#### How would you rate your experience?")
        
        rating = st.select_slider(
            "Overall Rating",
            options=[1, 2, 3, 4, 5],
            value=5
        )
        
        st.markdown("#### How likely are you to recommend us to others?")
        
        nps_score = st.select_slider(
            "0 (Not likely) to 10 (Very likely)",
            options=list(range(11)),
            value=10
        )
        
        st.markdown("#### Any additional comments?")
        comments = st.text_area("Your feedback helps us improve", height=100)
        
        submitted = st.form_submit_button("Submit Feedback", type="primary")
        
        if submitted:
            if client_name and client_email:
                # For demo, use a placeholder audit_id
                success, result = save_feedback(1, client_name, client_email, None, rating, nps_score, comments)
                if success:
                    st.success("Thank you for your feedback!")
                    st.balloons()
                else:
                    st.error(f"Error: {result}")
            else:
                st.warning("Please enter your name and email")

def display_feedback_dashboard(firm_id):
    """Display feedback analytics dashboard"""
    
    st.markdown("### 📊 Client Feedback Dashboard")
    
    stats = get_feedback_stats(firm_id)
    feedback = get_feedback(firm_id)
    
    if not feedback:
        st.info("No feedback received yet. Share the feedback link with clients.")
        return
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Responses", stats['total'])
    col2.metric("Avg Rating", f"{stats['avg_rating']:.1f} ⭐")
    col3.metric("NPS Score", stats['nps_score'])
    col4.metric("Avg NPS", f"{stats['avg_nps']:.1f}")
    
    st.markdown("---")
    
    # NPS Gauge
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Net Promoter Score")
        
        nps_color = "#28a745" if stats['nps_score'] >= 50 else "#ffc107" if stats['nps_score'] >= 0 else "#dc3545"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 3rem; font-weight: bold; color: {nps_color};">{stats['nps_score']}</div>
            <div style="font-size: 0.9rem;">NPS Score</div>
            <hr>
            <div style="display: flex; justify-content: space-around;">
                <div><strong>Promoters</strong><br>{stats['promoters']}</div>
                <div><strong>Passives</strong><br>{stats['passives']}</div>
                <div><strong>Detractors</strong><br>{stats['detractors']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Rating Distribution")
        
        rating_counts = {}
        for f in feedback:
            r = f.get('rating')
            if r:
                rating_counts[r] = rating_counts.get(r, 0) + 1
        
        if rating_counts:
            rating_df = pd.DataFrame(list(rating_counts.items()), columns=['Rating', 'Count'])
            fig = px.bar(rating_df, x='Rating', y='Count', color='Rating',
                         color_continuous_scale='Blues')
            fig.update_layout(showlegend=False, height=250)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Sentiment Analysis
    st.markdown("#### Sentiment Analysis")
    
    sentiment_df = pd.DataFrame(list(stats['sentiment_counts'].items()), columns=['Sentiment', 'Count'])
    colors = {'positive': '#28a745', 'neutral': '#ffc107', 'negative': '#dc3545'}
    fig = px.pie(sentiment_df, values='Count', names='Sentiment', color='Sentiment',
                 color_discrete_map=colors)
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent Feedback
    st.markdown("#### Recent Feedback")
    
    for f in feedback[:10]:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{f.get('client_name', 'Anonymous')}**")
                stars = "⭐" * f.get('rating', 0)
                st.caption(f"Rating: {stars} | NPS: {f.get('nps_score', 'N/A')}/10")
                if f.get('comments'):
                    st.write(f"💬 {f['comments'][:200]}")
            with col2:
                st.caption(f"{f['created_at'][:10]}")
                sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(f.get('sentiment'), "😐")
                st.caption(f"Sentiment: {sentiment_emoji}")
            st.markdown("---")
    
    # Export button
    if st.button("📥 Export Feedback (CSV)"):
        df = pd.DataFrame(feedback)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"client_feedback_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )