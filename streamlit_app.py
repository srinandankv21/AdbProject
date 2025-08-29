import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="EduSkillUp Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for data
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

@st.cache_data
def load_sample_data():
    """Load sample data that matches your fact constellation schema"""
    
    # Sample enrollment data
    enrollment_data = {
        'enrollment_key': range(1, 21),
        'student_name': [f'Student_{i}' for i in range(1, 21)],
        'course_title': ['Python Basics', 'Data Analysis', 'Web Design', 'Business Strategy', 'Digital Marketing'] * 4,
        'category_name': ['Programming', 'Data Science', 'Design', 'Business', 'Marketing'] * 4,
        'instructor_name': ['Dr. Smith', 'Prof. Johnson', 'Ms. Lee', 'Mr. Brown', 'Dr. Wilson'] * 4,
        'membership_type': ['Premium', 'Free'] * 10,
        'enrollment_date': pd.date_range('2024-01-01', periods=20, freq='W'),
        'course_price': [99.99, 149.99, 79.99, 199.99, 89.99] * 4,
        'progress_percentage': np.random.uniform(20, 100, 20),
        'completion_status': np.random.choice(['Completed', 'In Progress', 'Enrolled'], 20),
        'course_level': ['Beginner', 'Intermediate', 'Advanced'] * 7 + ['Beginner'],
        'days_to_complete': np.random.randint(15, 90, 20)
    }
    
    # Sample performance data
    performance_data = {
        'performance_key': range(1, 31),
        'student_name': [f'Student_{np.random.randint(1, 21)}' for _ in range(30)],
        'course_title': np.random.choice(['Python Basics', 'Data Analysis', 'Web Design', 'Business Strategy', 'Digital Marketing'], 30),
        'assessment_title': ['Quiz 1', 'Assignment 1', 'Project', 'Final Exam'] * 8 - ['Quiz 1', 'Assignment 1'],
        'assessment_type': ['Quiz', 'Assignment', 'Project', 'Exam'] * 8 - ['Quiz', 'Assignment'],
        'difficulty_level': np.random.choice(['Easy', 'Medium', 'Hard'], 30),
        'score_earned': np.random.uniform(60, 100, 30),
        'max_score': [100] * 30,
        'time_spent_minutes': np.random.randint(15, 180, 30),
        'attempts_count': np.random.randint(1, 4, 30),
        'submission_date': pd.date_range('2024-01-15', periods=30, freq='5D')
    }
    
    enrollment_df = pd.DataFrame(enrollment_data)
    performance_df = pd.DataFrame(performance_data)
    performance_df['score_percentage'] = (performance_df['score_earned'] / performance_df['max_score']) * 100
    
    return enrollment_df, performance_df

def create_sidebar_filters(enrollment_df, performance_df):
    """Create sidebar filters for dashboard interactivity"""
    
    st.sidebar.header("📊 Dashboard Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(enrollment_df['enrollment_date'].min(), enrollment_df['enrollment_date'].max()),
        min_value=enrollment_df['enrollment_date'].min(),
        max_value=enrollment_df['enrollment_date'].max()
    )
    
    # Category filter
    categories = st.sidebar.multiselect(
        "Select Categories",
        options=enrollment_df['category_name'].unique(),
        default=enrollment_df['category_name'].unique()
    )
    
    # Membership filter
    membership_types = st.sidebar.multiselect(
        "Select Membership Types",
        options=enrollment_df['membership_type'].unique(),
        default=enrollment_df['membership_type'].unique()
    )
    
    # Course level filter
    course_levels = st.sidebar.multiselect(
        "Select Course Levels",
        options=enrollment_df['course_level'].unique(),
        default=enrollment_df['course_level'].unique()
    )
    
    return date_range, categories, membership_types, course_levels

def filter_data(df, date_col, date_range, categories, membership_types=None, course_levels=None):
    """Apply filters to dataframe"""
    
    # Date filter
    filtered_df = df[
        (df[date_col] >= pd.Timestamp(date_range[0])) & 
        (df[date_col] <= pd.Timestamp(date_range[1]))
    ]
    
    # Category filter
    if 'category_name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category_name'].isin(categories)]
    
    # Membership filter
    if membership_types and 'membership_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['membership_type'].isin(membership_types)]
    
    # Course level filter
    if course_levels and 'course_level' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['course_level'].isin(course_levels)]
    
    return filtered_df

def enrollment_dashboard(enrollment_df):
    """Enrollment Dashboard - Strategic Business Intelligence"""
    
    st.markdown("<h2 style='color: #1f77b4;'>📈 Enrollment Dashboard - Strategic Business Intelligence</h2>", unsafe_allow_html=True)
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_enrollments = len(enrollment_df)
        st.metric("Total Enrollments", f"{total_enrollments:,}")
    
    with col2:
        total_revenue = enrollment_df['course_price'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        avg_progress = enrollment_df['progress_percentage'].mean()
        st.metric("Avg Progress", f"{avg_progress:.1f}%")
    
    with col4:
        completion_rate = (enrollment_df['completion_status'] == 'Completed').sum() / len(enrollment_df) * 100
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # Visualizations Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Enrollment by Category")
        category_counts = enrollment_df['category_name'].value_counts()
        fig_pie = px.pie(
            values=category_counts.values, 
            names=category_counts.index,
            title="Course Enrollments by Category"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("💰 Revenue by Membership Type")
        revenue_by_membership = enrollment_df.groupby('membership_type')['course_price'].sum().reset_index()
        fig_bar = px.bar(
            revenue_by_membership, 
            x='membership_type', 
            y='course_price',
            title="Revenue Distribution by Membership",
            color='membership_type'
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Visualizations Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Enrollment Trends Over Time")
        enrollment_df['enrollment_month'] = enrollment_df['enrollment_date'].dt.to_period('M')
        monthly_enrollments = enrollment_df.groupby('enrollment_month').size().reset_index(name='count')
        monthly_enrollments['enrollment_month'] = monthly_enrollments['enrollment_month'].astype(str)
        
        fig_line = px.line(
            monthly_enrollments, 
            x='enrollment_month', 
            y='count',
            title="Monthly Enrollment Trends",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Course Performance Matrix")
        course_metrics = enrollment_df.groupby('course_title').agg({
            'course_price': 'first',
            'progress_percentage': 'mean',
            'enrollment_key': 'count'
        }).reset_index()
        course_metrics.rename(columns={'enrollment_key': 'enrollments'}, inplace=True)
        
        fig_scatter = px.scatter(
            course_metrics,
            x='course_price',
            y='progress_percentage',
            size='enrollments',
            hover_data=['course_title'],
            title="Course Price vs Progress (Size = Enrollments)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # OLAP Analysis Section
    st.subheader("🔍 OLAP Analysis - Enrollment Patterns")
    
    # ROLLUP equivalent analysis
    rollup_data = enrollment_df.groupby(['category_name', 'course_level']).agg({
        'enrollment_key': 'count',
        'course_price': 'sum',
        'progress_percentage': 'mean'
    }).reset_index()
    
    fig_rollup = px.sunburst(
        rollup_data,
        path=['category_name', 'course_level'],
        values='enrollment_key',
        title="Hierarchical Enrollment Analysis (Category → Level)"
    )
    st.plotly_chart(fig_rollup, use_container_width=True)

def performance_dashboard(performance_df):
    """Performance Dashboard - Educational Quality Assurance"""
    
    st.markdown("<h2 style='color: #ff7f0e;'>🎓 Performance Dashboard - Educational Quality Assurance</h2>", unsafe_allow_html=True)
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = performance_df['score_percentage'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col2:
        total_submissions = len(performance_df)
        st.metric("Total Submissions", f"{total_submissions:,}")
    
    with col3:
        avg_time = performance_df['time_spent_minutes'].mean()
        st.metric("Avg Time Spent", f"{avg_time:.0f} mins")
    
    with col4:
        success_rate = (performance_df['score_percentage'] >= 70).sum() / len(performance_df) * 100
        st.metric("Success Rate (≥70%)", f"{success_rate:.1f}%")
    
    # Visualizations Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Performance by Assessment Type")
        perf_by_type = performance_df.groupby('assessment_type')['score_percentage'].mean().reset_index()
        fig_bar = px.bar(
            perf_by_type,
            x='assessment_type',
            y='score_percentage',
            title="Average Performance by Assessment Type",
            color='assessment_type'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Time vs Performance Analysis")
        fig_scatter = px.scatter(
            performance_df,
            x='time_spent_minutes',
            y='score_percentage',
            color='difficulty_level',
            title="Time Spent vs Score Achieved"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Visualizations Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Score Distribution")
        fig_hist = px.histogram(
            performance_df,
            x='score_percentage',
            bins=20,
            title="Score Distribution Across All Assessments"
        )
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("🔄 Attempts vs Difficulty")
        attempts_difficulty = performance_df.groupby('difficulty_level')['attempts_count'].mean().reset_index()
        fig_bar = px.bar(
            attempts_difficulty,
            x='difficulty_level',
            y='attempts_count',
            title="Average Attempts by Difficulty Level",
            color='difficulty_level'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # OLAP Analysis Section
    st.subheader("🔍 OLAP Analysis - Performance Patterns")
    
    # CUBE equivalent analysis
    cube_data = performance_df.groupby(['assessment_type', 'difficulty_level']).agg({
        'score_percentage': 'mean',
        'time_spent_minutes': 'mean',
        'performance_key': 'count'
    }).reset_index()
    
    fig_heatmap = px.density_heatmap(
        performance_df,
        x='assessment_type',
        y='difficulty_level',
        z='score_percentage',
        title="Performance Heatmap (Assessment Type × Difficulty)"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

def integrated_analysis(enrollment_df, performance_df):
    """Integrated Analysis - Cross-Fact Insights"""
    
    st.markdown("<h2 style='color: #2ca02c;'>🔗 Integrated Analysis - Cross-Fact Insights</h2>", unsafe_allow_html=True)
    
    # Merge data for integrated analysis
    integrated_df = pd.merge(
        enrollment_df[['student_name', 'course_title', 'membership_type', 'progress_percentage', 'completion_status']],
        performance_df[['student_name', 'course_title', 'score_percentage', 'assessment_type']],
        on=['student_name', 'course_title'],
        how='inner'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Enrollment vs Performance Correlation")
        correlation_data = integrated_df.groupby('membership_type').agg({
            'progress_percentage': 'mean',
            'score_percentage': 'mean'
        }).reset_index()
        
        fig_correlation = go.Figure()
        fig_correlation.add_trace(go.Scatter(
            x=correlation_data['progress_percentage'],
            y=correlation_data['score_percentage'],
            mode='markers+text',
            text=correlation_data['membership_type'],
            textposition='top center',
            marker=dict(size=15, color=['blue', 'orange'])
        ))
        fig_correlation.update_layout(
            title="Course Progress vs Assessment Performance",
            xaxis_title="Average Progress %",
            yaxis_title="Average Score %"
        )
        st.plotly_chart(fig_correlation, use_container_width=True)
    
    with col2:
        st.subheader("📊 Success Rate by Membership")
        success_by_membership = integrated_df.groupby('membership_type').apply(
            lambda x: (x['score_percentage'] >= 70).sum() / len(x) * 100
        ).reset_index(name='success_rate')
        
        fig_success = px.bar(
            success_by_membership,
            x='membership_type',
            y='success_rate',
            title="Success Rate by Membership Type",
            color='membership_type'
        )
        st.plotly_chart(fig_success, use_container_width=True)

# Main Application
def main():
    # Load data
    if not st.session_state.data_loaded:
        enrollment_df, performance_df = load_sample_data()
        st.session_state.enrollment_df = enrollment_df
        st.session_state.performance_df = performance_df
        st.session_state.data_loaded = True
    
    enrollment_df = st.session_state.enrollment_df
    performance_df = st.session_state.performance_df
    
    # Main title
    st.markdown("<h1 class='main-header'>🎓 EduSkillUp Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("**Fact Constellation Analytics | Business Intelligence & Educational Quality Assurance**")
    
    # Sidebar filters
    date_range, categories, membership_types, course_levels = create_sidebar_filters(enrollment_df, performance_df)
    
    # Apply filters
    filtered_enrollment = filter_data(enrollment_df, 'enrollment_date', date_range, categories, membership_types, course_levels)
    filtered_performance = filter_data(performance_df, 'submission_date', date_range, categories)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📈 Enrollment Dashboard", "🎓 Performance Dashboard", "🔗 Integrated Analysis"])
    
    with tab1:
        enrollment_dashboard(filtered_enrollment)
    
    with tab2:
        performance_dashboard(filtered_performance)
    
    with tab3:
        integrated_analysis(filtered_enrollment, filtered_performance)
    
    # Footer
    st.markdown("---")
    st.markdown("**EduSkillUp Fact Constellation Dashboard** | TMV6014 Advanced Databases Project")

if __name__ == "__main__":
    main()
