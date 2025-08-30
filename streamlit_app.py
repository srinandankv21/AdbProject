import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import warnings
import os
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

def get_file_path(filename):
    """Get the correct file path for Streamlit deployment"""
    try:
        # Try to find the file in the current directory
        if os.path.exists(filename):
            return filename
        # Try to find in a 'data' subdirectory
        data_path = os.path.join('data', filename)
        if os.path.exists(data_path):
            return data_path
        # For Streamlit sharing, files might be in root
        return filename
    except:
        return filename

@st.cache_data
def load_data_from_csv():
    """Load data from CSV files matching your fact constellation schema"""
    
    try:
        # Load dimension tables
        dim_student = pd.read_csv(get_file_path('DimStudent.csv'), parse_dates=['RegistrationDate'], dayfirst=True)
        dim_date = pd.read_csv(get_file_path('DimDate.csv'), parse_dates=['FullDate'], dayfirst=True)
        dim_assessment = pd.read_csv(get_file_path('DimAssessment.csv'))
        dim_category = pd.read_csv(get_file_path('DimCategory.csv'))
        dim_course = pd.read_csv(get_file_path('DimCourse.csv'), parse_dates=['CreatedDate'], dayfirst=True)
        dim_instructor = pd.read_csv(get_file_path('DimInstructor.csv'))
        
        # Load fact tables
        fact_enrollment = pd.read_csv(get_file_path('FactEnrollment.csv'))
        fact_performance = pd.read_csv(get_file_path('FactAssessmentPerformance.csv'))
        
        # Debug: Show loaded data info
        st.sidebar.success(f"✅ Loaded {len(dim_student)} students, {len(dim_course)} courses")
        
        # Merge enrollment data with dimensions
        enrollment_df = fact_enrollment.merge(
            dim_student[['StudentKey', 'StudentName', 'MembershipType']], 
            on='StudentKey'
        ).merge(
            dim_course[['CourseKey', 'CourseTitle', 'Level']], 
            on='CourseKey'
        ).merge(
            dim_instructor[['InstructorKey', 'InstructorName']], 
            on='InstructorKey'
        ).merge(
            dim_category[['CategoryKey', 'CategoryName']], 
            on='CategoryKey'
        ).merge(
            dim_date[['DateKey', 'FullDate']].rename(columns={'FullDate': 'EnrollmentDate'}),
            left_on='EnrollmentDateKey', right_on='DateKey'
        ).merge(
            dim_date[['DateKey', 'FullDate']].rename(columns={'FullDate': 'CompletionDate'}),
            left_on='CompletionDateKey', right_on='DateKey', how='left'
        )
        
        # Merge performance data with dimensions
        performance_df = fact_performance.merge(
            dim_student[['StudentKey', 'StudentName']], 
            on='StudentKey'
        ).merge(
            dim_course[['CourseKey', 'CourseTitle']], 
            on='CourseKey'
        ).merge(
            dim_assessment[['AssessmentKey', 'AssessmentTitle', 'AssessmentType', 'DifficultyLevel', 'MaxScore']], 
            on='AssessmentKey'
        ).merge(
            dim_date[['DateKey', 'FullDate']].rename(columns={'FullDate': 'SubmissionDate'}),
            left_on='SubmissionDateKey', right_on='DateKey'
        )
        
        # Calculate additional fields
        performance_df['ScorePercentage'] = (performance_df['ScoreEarned'] / performance_df['MaxPossibleScore']) * 100
        
        # Select relevant columns for the dashboard
        enrollment_df = enrollment_df[[
            'EnrollmentKey', 'StudentName', 'CourseTitle', 'CategoryName', 'InstructorName',
            'MembershipType', 'EnrollmentDate', 'CompletionDate', 'CoursePrice', 
            'ProgressPercentage', 'DaysToComplete', 'CompletionStatus', 'PaymentStatus', 'Level'
        ]].rename(columns={'Level': 'CourseLevel'})
        
        performance_df = performance_df[[
            'PerformanceKey', 'StudentName', 'CourseTitle', 'AssessmentTitle', 
            'AssessmentType', 'DifficultyLevel', 'ScoreEarned', 'MaxPossibleScore',
            'ScorePercentage', 'TimeSpentMinutes', 'AttemptsCount', 'SubmissionDate', 'IsCompleted'
        ]].rename(columns={'MaxPossibleScore': 'MaxScore'})
        
        return enrollment_df, performance_df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Using sample data instead. Please ensure CSV files are in the same directory.")
        return load_sample_data()

@st.cache_data
def load_sample_data():
    """Fallback sample data if CSV loading fails"""
    np.random.seed(42)
    
    enrollment_data = {
        'EnrollmentKey': list(range(1, 21)),
        'StudentName': [f'Student_{i}' for i in range(1, 21)],
        'CourseTitle': (['Python Basics', 'Data Analysis', 'Web Design', 'Business Strategy', 'Digital Marketing'] * 4),
        'CategoryName': (['Programming', 'Data Science', 'Design', 'Business', 'Marketing'] * 4),
        'InstructorName': (['Dr. Smith', 'Prof. Johnson', 'Ms. Lee', 'Mr. Brown', 'Dr. Wilson'] * 4),
        'MembershipType': (['Premium', 'Free'] * 10),
        'EnrollmentDate': pd.date_range('2024-01-01', periods=20, freq='W'),
        'CoursePrice': ([99.99, 149.99, 79.99, 199.99, 89.99] * 4),
        'ProgressPercentage': np.random.uniform(20, 100, 20).tolist(),
        'CompletionStatus': np.random.choice(['Completed', 'In Progress', 'Dropped'], 20).tolist(),
        'CourseLevel': (['Beginner', 'Intermediate', 'Advanced'] * 6 + ['Beginner', 'Intermediate']),
        'DaysToComplete': np.random.randint(15, 90, 20).tolist()
    }
    
    performance_data = {
        'PerformanceKey': range(1, 31),
        'StudentName': [f'Student_{np.random.randint(1, 21)}' for _ in range(30)],
        'CourseTitle': np.random.choice(['Python Basics', 'Data Analysis', 'Web Design', 'Business Strategy', 'Digital Marketing'], 30),
        'AssessmentTitle': ['Quiz 1', 'Assignment 1', 'Project', 'Final Exam'] * 7 + ['Quiz 1', 'Assignment 1'],
        'AssessmentType': ['Quiz', 'Assignment', 'Project', 'Exam'] * 7 + ['Quiz', 'Assignment'],
        'DifficultyLevel': np.random.choice(['Easy', 'Medium', 'Hard'], 30),
        'ScoreEarned': np.random.uniform(60, 100, 30),
        'MaxScore': [100] * 30,
        'TimeSpentMinutes': np.random.randint(15, 180, 30),
        'AttemptsCount': np.random.randint(1, 4, 30),
        'SubmissionDate': pd.date_range('2024-01-15', periods=30, freq='5D')
    }
    
    enrollment_df = pd.DataFrame(enrollment_data)
    performance_df = pd.DataFrame(performance_data)
    performance_df['ScorePercentage'] = (performance_df['ScoreEarned'] / performance_df['MaxScore']) * 100
    
    return enrollment_df, performance_df

def create_sidebar_filters(enrollment_df, performance_df):
    """Create sidebar filters for dashboard interactivity"""
    
    st.sidebar.header("📊 Dashboard Filters")
    
    # Extract date from EnrollmentDateKey (20250829 format)
    if len(enrollment_df) > 0 and 'EnrollmentDate' in enrollment_df.columns:
        # Convert to proper datetime
        enrollment_dates = pd.to_datetime(enrollment_df['EnrollmentDate'])
        min_date = enrollment_dates.min()
        max_date = enrollment_dates.max()
        
        st.sidebar.info(f"📅 Data range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    else:
        # Fallback: your data is from August 29, 2024
        min_date = pd.to_datetime('2024-08-29')
        max_date = pd.to_datetime('2024-08-29')
        st.sidebar.info("📅 Your data is from: August 29, 2024")

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Handle single date selection
    if len(date_range) == 1:
        date_range = (date_range[0], date_range[0])
    elif len(date_range) == 0:
        date_range = (min_date, max_date)
    
    # Rest of the filters...
    categories = st.sidebar.multiselect(
        "Select Categories",
        options=enrollment_df['CategoryName'].unique(),
        default=enrollment_df['CategoryName'].unique()
    )
    
    membership_types = st.sidebar.multiselect(
        "Select Membership Types",
        options=enrollment_df['MembershipType'].unique(),
        default=enrollment_df['MembershipType'].unique()
    )
    
    course_levels = st.sidebar.multiselect(
        "Select Course Levels",
        options=enrollment_df['CourseLevel'].unique(),
        default=enrollment_df['CourseLevel'].unique()
    )
    
    completion_statuses = st.sidebar.multiselect(
        "Select Completion Status",
        options=enrollment_df['CompletionStatus'].unique(),
        default=enrollment_df['CompletionStatus'].unique()
    )
    
    return date_range, categories, membership_types, course_levels, completion_statuses
def filter_data(df, date_col, date_range, categories, membership_types=None, course_levels=None, completion_statuses=None):
    """Apply filters to dataframe"""
    
    # Date filter
    filtered_df = df[
        (df[date_col] >= pd.Timestamp(date_range[0])) & 
        (df[date_col] <= pd.Timestamp(date_range[1]))
    ]
    
    # Category filter
    if 'CategoryName' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CategoryName'].isin(categories)]
    
    # Membership filter
    if membership_types and 'MembershipType' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['MembershipType'].isin(membership_types)]
    
    # Course level filter
    if course_levels and 'CourseLevel' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CourseLevel'].isin(course_levels)]
    
    # Completion status filter
    if completion_statuses and 'CompletionStatus' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CompletionStatus'].isin(completion_statuses)]
    
    return filtered_df

def enrollment_dashboard(enrollment_df):
    """Enrollment Dashboard - Strategic Business Intelligence"""
    
    if len(enrollment_df) == 0:
        st.warning("No enrollment data available for the selected filters.")
        return
    
    st.markdown("<h2 style='color: #1f77b4;'>📈 Enrollment Dashboard - Strategic Business Intelligence</h2>", unsafe_allow_html=True)
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_enrollments = len(enrollment_df)
        st.metric("Total Enrollments", f"{total_enrollments:,}")
    
    with col2:
        total_revenue = enrollment_df['CoursePrice'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        avg_progress = enrollment_df['ProgressPercentage'].mean()
        st.metric("Avg Progress", f"{avg_progress:.1f}%")
    
    with col4:
        completion_rate = (enrollment_df['CompletionStatus'] == 'Completed').sum() / len(enrollment_df) * 100
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # Visualizations Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Enrollment by Category")
        category_counts = enrollment_df['CategoryName'].value_counts()
        fig_pie = px.pie(
            values=category_counts.values, 
            names=category_counts.index,
            title="Course Enrollments by Category"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("💰 Revenue by Membership Type")
        revenue_by_membership = enrollment_df.groupby('MembershipType')['CoursePrice'].sum().reset_index()
        fig_bar = px.bar(
            revenue_by_membership, 
            x='MembershipType', 
            y='CoursePrice',
            title="Revenue Distribution by Membership",
            color='MembershipType'
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Visualizations Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Enrollment Trends Over Time")
        enrollment_df['EnrollmentMonth'] = enrollment_df['EnrollmentDate'].dt.to_period('M')
        monthly_enrollments = enrollment_df.groupby('EnrollmentMonth').size().reset_index(name='count')
        monthly_enrollments['EnrollmentMonth'] = monthly_enrollments['EnrollmentMonth'].astype(str)
        
        fig_line = px.line(
            monthly_enrollments, 
            x='EnrollmentMonth', 
            y='count',
            title="Monthly Enrollment Trends",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Course Performance Matrix")
        course_metrics = enrollment_df.groupby('CourseTitle').agg({
            'CoursePrice': 'mean',
            'ProgressPercentage': 'mean',
            'EnrollmentKey': 'count'
        }).reset_index()
        course_metrics.rename(columns={'EnrollmentKey': 'enrollments'}, inplace=True)
        
        fig_scatter = px.scatter(
            course_metrics,
            x='CoursePrice',
            y='ProgressPercentage',
            size='enrollments',
            hover_data=['CourseTitle'],
            title="Course Price vs Progress (Size = Enrollments)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Completion Analysis
    st.subheader("✅ Completion Status Analysis")
    completion_data = enrollment_df['CompletionStatus'].value_counts().reset_index()
    completion_data.columns = ['Status', 'Count']
    
    fig_completion = px.bar(
        completion_data,
        x='Status',
        y='Count',
        color='Status',
        title="Distribution of Enrollment Status"
    )
    st.plotly_chart(fig_completion, use_container_width=True)

def performance_dashboard(performance_df):
    """Performance Dashboard - Educational Quality Assurance"""
    
    if len(performance_df) == 0:
        st.warning("No performance data available for the selected filters.")
        return
    
    st.markdown("<h2 style='color: #ff7f0e;'>🎓 Performance Dashboard - Educational Quality Assurance</h2>", unsafe_allow_html=True)
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = performance_df['ScorePercentage'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col2:
        total_submissions = len(performance_df)
        st.metric("Total Submissions", f"{total_submissions:,}")
    
    with col3:
        avg_time = performance_df['TimeSpentMinutes'].mean()
        st.metric("Avg Time Spent", f"{avg_time:.0f} mins")
    
    with col4:
        success_rate = (performance_df['ScorePercentage'] >= 70).sum() / len(performance_df) * 100
        st.metric("Success Rate (≥70%)", f"{success_rate:.1f}%")
    
    # Visualizations Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Performance by Assessment Type")
        perf_by_type = performance_df.groupby('AssessmentType')['ScorePercentage'].mean().reset_index()
        fig_bar = px.bar(
            perf_by_type,
            x='AssessmentType',
            y='ScorePercentage',
            title="Average Performance by Assessment Type",
            color='AssessmentType'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Time vs Performance Analysis")
        fig_scatter = px.scatter(
            performance_df,
            x='TimeSpentMinutes',
            y='ScorePercentage',
            color='DifficultyLevel',
            title="Time Spent vs Score Achieved"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Visualizations Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Score Distribution")
        fig_hist = px.histogram(
            performance_df,
            x='ScorePercentage',
            nbins=20,
            title="Score Distribution Across All Assessments"
        )
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("🔄 Attempts vs Difficulty")
        attempts_difficulty = performance_df.groupby('DifficultyLevel')['AttemptsCount'].mean().reset_index()
        fig_bar = px.bar(
            attempts_difficulty,
            x='DifficultyLevel',
            y='AttemptsCount',
            title="Average Attempts by Difficulty Level",
            color='DifficultyLevel'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Difficulty Analysis
    st.subheader("🎯 Performance by Difficulty Level")
    difficulty_performance = performance_df.groupby('DifficultyLevel').agg({
        'ScorePercentage': 'mean',
        'TimeSpentMinutes': 'mean',
        'PerformanceKey': 'count'
        }).reset_index()
    difficulty_performance.rename(columns={'PerformanceKey': 'count'}, inplace=True)
    
    fig_difficulty = px.bar(
        difficulty_performance,
        x='DifficultyLevel',
        y='ScorePercentage',
        color='DifficultyLevel',
        title="Average Score by Difficulty Level"
    )
    st.plotly_chart(fig_difficulty, use_container_width=True)

def integrated_analysis(enrollment_df, performance_df):
    """Integrated Analysis - Cross-Fact Insights"""
    
    if len(enrollment_df) == 0 or len(performance_df) == 0:
        st.warning("Not enough data for integrated analysis with current filters.")
        return
    
    st.markdown("<h2 style='color: #2ca02c;'>🔗 Integrated Analysis - Cross-Fact Insights</h2>", unsafe_allow_html=True)
    
    # Merge data for integrated analysis
    integrated_df = pd.merge(
        enrollment_df[['StudentName', 'CourseTitle', 'MembershipType', 'ProgressPercentage', 'CompletionStatus']],
        performance_df[['StudentName', 'CourseTitle', 'ScorePercentage', 'AssessmentType']],
        on=['StudentName', 'CourseTitle'],
        how='inner'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Enrollment vs Performance Correlation")
        correlation_data = integrated_df.groupby('MembershipType').agg({
            'ProgressPercentage': 'mean',
            'ScorePercentage': 'mean'
        }).reset_index()
        
        fig_correlation = go.Figure()
        fig_correlation.add_trace(go.Scatter(
            x=correlation_data['ProgressPercentage'],
            y=correlation_data['ScorePercentage'],
            mode='markers+text',
            text=correlation_data['MembershipType'],
            textposition='top center',
            marker=dict(size=15, color=['blue', 'orange', 'green', 'red'])
        ))
        fig_correlation.update_layout(
            title="Course Progress vs Assessment Performance",
            xaxis_title="Average Progress %",
            yaxis_title="Average Score %"
        )
        st.plotly_chart(fig_correlation, use_container_width=True)
    
    with col2:
        st.subheader("📊 Success Rate by Membership")
        success_by_membership = integrated_df.groupby('MembershipType').apply(
            lambda x: (x['ScorePercentage'] >= 70).sum() / len(x) * 100
        ).reset_index(name='success_rate')
        
        fig_success = px.bar(
            success_by_membership,
            x='MembershipType',
            y='success_rate',
            title="Success Rate by Membership Type",
            color='MembershipType'
        )
        st.plotly_chart(fig_success, use_container_width=True)
    
    # Completion vs Performance Analysis
    st.subheader("📈 Completion Status vs Performance")
    completion_performance = integrated_df.groupby('CompletionStatus')['ScorePercentage'].mean().reset_index()
    
    fig_completion_perf = px.bar(
        completion_performance,
        x='CompletionStatus',
        y='ScorePercentage',
        color='CompletionStatus',
        title="Average Score by Completion Status"
    )
    st.plotly_chart(fig_completion_perf, use_container_width=True)

# Main Application
def main():
    # Load data
    if not st.session_state.data_loaded:
        enrollment_df, performance_df = load_data_from_csv()
        st.session_state.enrollment_df = enrollment_df
        st.session_state.performance_df = performance_df
        st.session_state.data_loaded = True
    
    enrollment_df = st.session_state.enrollment_df
    performance_df = st.session_state.performance_df
    
    # Main title
    st.markdown("<h1 class='main-header'>🎓 EduSkillUp Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("**Fact Constellation Analytics | Business Intelligence & Educational Quality Assurance**")
    
    # Sidebar filters
    date_range, categories, membership_types, course_levels, completion_statuses = create_sidebar_filters(enrollment_df, performance_df)
    
    # Apply filters
    filtered_enrollment = filter_data(
        enrollment_df, 'EnrollmentDate', date_range, categories, 
        membership_types, course_levels, completion_statuses
    )
    filtered_performance = filter_data(performance_df, 'SubmissionDate', date_range, categories)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📈 Enrollment Dashboard", "🎓 Performance Dashboard", "🔗 Integrated Analysis"])
    
    with tab1:
        enrollment_dashboard(filtered_enrollment)
    
    with tab2:
        performance_dashboard(filtered_performance)
    
    with tab3:
        integrated_analysis(filtered_enrollment, filtered_performance)
    
    # Data summary
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Data Summary")
    st.sidebar.info(f"""
    - 📚 Enrollments: {len(enrollment_df):,}
    - 🎯 Assessments: {len(performance_df):,}
    - 👥 Students: {enrollment_df['StudentName'].nunique():,}
    - 🏫 Courses: {enrollment_df['CourseTitle'].nunique():,}
    - 📈 Categories: {enrollment_df['CategoryName'].nunique():,}
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("**EduSkillUp Fact Constellation Dashboard** | TMV6014 Advanced Databases Project")

if __name__ == "__main__":
    main()
