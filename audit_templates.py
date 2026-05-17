import streamlit as st
from supabase import create_client
from datetime import datetime
import json

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_public_templates(industry=None):
    """Get all public templates, optionally filtered by industry"""
    supabase = get_supabase()
    
    try:
        query = supabase.table("audit_templates").select("*").eq("is_public", True)
        if industry and industry != "All":
            query = query.eq("industry", industry)
        result = query.order("usage_count", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting templates: {e}")
        return []

def get_firm_templates(firm_id):
    """Get templates created by the firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("audit_templates").select("*").eq("firm_id", firm_id).order("created_at", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting firm templates: {e}")
        return []

def create_template(firm_id, name, description, industry, template_data, is_public=False):
    """Create a new audit template"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("audit_templates").insert({
            "firm_id": firm_id,
            "name": name,
            "description": description,
            "industry": industry,
            "template_data": template_data,
            "is_public": is_public
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def update_template_usage(template_id):
    """Increment usage count for a template"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("audit_templates").select("usage_count").eq("id", template_id).execute()
        if result.data:
            current = result.data[0].get("usage_count", 0)
            supabase.table("audit_templates").update({"usage_count": current + 1}).eq("id", template_id).execute()
    except Exception as e:
        print(f"Error updating usage: {e}")

def apply_template_to_audit(template, bank_file=None, ledger_file=None):
    """Apply template settings to an audit"""
    template_data = template.get("template_data", {})
    
    recommendations = {
        "focus_areas": template_data.get("focus_areas", []),
        "sample_size": template_data.get("sample_size", 0.1),
        "risk_factors": template_data.get("risk_factors", [])
    }
    
    return recommendations

def display_template_library(firm_id):
    """Display template library in Analytics page"""
    
    st.markdown("### 📚 Audit Template Library")
    st.markdown("Use pre-built audit templates or create your own.")
    
    # Create 3 tabs (fixed: was trying to unpack 2 values into 3 tabs)
    tab1, tab2, tab3 = st.tabs(["Public Templates", "My Templates", "Create Template"])
    
    # Public Templates Tab
    with tab1:
        st.markdown("#### Available Templates")
        
        # Industry filter
        industries = ["All", "Retail", "Manufacturing", "Technology", "Non-Profit", "Construction", "Healthcare"]
        selected_industry = st.selectbox("Filter by Industry", industries, key="template_industry_filter")
        
        templates = get_public_templates(selected_industry if selected_industry != "All" else None)
        
        if templates:
            for template in templates:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(template.get('description', 'No description'))
                        st.caption(f"Industry: {template.get('industry', 'General')}")
                    
                    with col2:
                        st.caption(f"Used {template.get('usage_count', 0)} times")
                        focus_areas = template.get('template_data', {}).get('focus_areas', [])
                        if focus_areas:
                            st.caption(f"Focus: {', '.join(focus_areas[:2])}")
                    
                    with col3:
                        if st.button("Use Template", key=f"use_{template['id']}"):
                            update_template_usage(template['id'])
                            st.session_state.selected_template = template
                            st.success(f"Template '{template['name']}' loaded!")
                            
                            recommendations = apply_template_to_audit(template)
                            st.session_state.template_recommendations = recommendations
                            
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No templates found for this industry.")
    
    # My Templates Tab
    with tab2:
        st.markdown("#### Your Custom Templates")
        
        templates = get_firm_templates(firm_id)
        
        if templates:
            for template in templates:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(template.get('description', 'No description'))
                        st.caption(f"Industry: {template.get('industry', 'General')}")
                        if template.get('is_public'):
                            st.caption("🌍 Public")
                    
                    with col2:
                        st.caption(f"Created: {template['created_at'][:10] if template.get('created_at') else 'Unknown'}")
                    
                    with col3:
                        if st.button("Use", key=f"use_firm_{template['id']}"):
                            update_template_usage(template['id'])
                            st.session_state.selected_template = template
                            st.success(f"Template '{template['name']}' loaded!")
                            st.rerun()
                        
                        if st.button("Delete", key=f"delete_{template['id']}"):
                            supabase = get_supabase()
                            supabase.table("audit_templates").delete().eq("id", template['id']).execute()
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("You haven't created any templates yet.")
    
    # Create Template Tab
    with tab3:
        st.markdown("#### Create Custom Template")
        
        with st.form("create_template_form"):
            template_name = st.text_input("Template Name", placeholder="e.g., My Retail Audit Template")
            template_description = st.text_area("Description", placeholder="What is this template for?")
            template_industry = st.selectbox("Industry", ["Retail", "Manufacturing", "Technology", "Non-Profit", "Construction", "Healthcare", "Other"])
            
            st.markdown("##### Template Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                focus_areas = st.multiselect(
                    "Focus Areas",
                    ["inventory_valuation", "revenue_recognition", "cash_handling", "accounts_payable", 
                     "accounts_receivable", "fixed_assets", "cost_of_goods_sold", "supplier_contracts",
                     "grant_compliance", "equity_transactions", "r_and_d_costs"]
                )
            
            with col2:
                sample_size = st.slider("Sample Size", min_value=0.05, max_value=0.5, value=0.15, step=0.05, format="%.0f%%")
                risk_factors = st.multiselect(
                    "Risk Factors",
                    ["high_cash", "complex_inventory", "rapid_growth", "supplier_concentration", 
                     "long_term_contracts", "cost_overruns", "regulatory_compliance", "donor_restrictions"]
                )
            
            is_public = st.checkbox("Make this template public (share with other users)")
            
            submitted = st.form_submit_button("Create Template")
            
            if submitted and template_name:
                template_data = {
                    "focus_areas": focus_areas,
                    "sample_size": sample_size,
                    "risk_factors": risk_factors
                }
                
                success, result = create_template(
                    firm_id,
                    template_name,
                    template_description,
                    template_industry,
                    template_data,
                    is_public
                )
                
                if success:
                    st.success(f"Template '{template_name}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {result}")
    
    # Show active template recommendations
    if st.session_state.get("template_recommendations"):
        st.markdown("---")
        st.markdown("### 📋 Active Template Recommendations")
        
        recs = st.session_state.template_recommendations
        
        st.markdown("**Focus Areas:**")
        for area in recs.get("focus_areas", []):
            st.markdown(f"- {area.replace('_', ' ').title()}")
        
        st.markdown(f"**Suggested Sample Size:** {recs.get('sample_size', 0.15):.0%}")
        
        st.markdown("**Risk Factors to Watch:**")
        for factor in recs.get("risk_factors", []):
            st.markdown(f"- {factor.replace('_', ' ').title()}")
        
        if st.button("Clear Recommendations"):
            del st.session_state.template_recommendations
            st.rerun()