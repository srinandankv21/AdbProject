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
    """Load data from CSV files with better error handling"""
    
    try:
        # First, let's check what files are actually available
        import os
        available_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        st.sidebar.info(f"Available CSV files: {available_files}")
        
        # Try to load each file with multiple path options
        csv_files = {
            'DimStudent.csv': None,
            'DimDate.csv': None, 
            'DimAssessment.csv': None,
            'DimCategory.csv': None,
            'DimCourse.csv': None,
            'DimInstructor.csv': None,
            'FactEnrollment.csv': None,
            'FactAssessmentPerformance.csv': None
        }
        
        # Try to load each file
        for file_name in csv_files.keys():
            try:
                if file_name in available_files:
                    if file_name in ['DimStudent.csv', 'DimDate.csv', 'DimCourse.csv']:
                        csv_files[file_name] = pd.read_csv(file_name, parse_dates=True, dayfirst=True, infer_datetime_format=True)
                    else:
                        csv_files[file_name] = pd.read_csv(file_name)
                    st.sidebar.success(f"✅ Loaded {file_name}")
                else:
                    st.sidebar.warning(f"❌ {file_name} not found")
            except Exception as e:
                st.sidebar.error(f"Error loading {file_name}: {str(e)}")
        
        # Check if we have the essential files
        if csv_files['DimStudent.csv'] is None or csv_files['FactEnrollment.csv'] is None:
            st.error("Essential files missing. Using sample data.")
            return load_sample_data()
        
        # Let's see what columns we actually have
        st.sidebar.write("DimStudent columns:", list(csv_files['DimStudent.csv'].columns))
        st.sidebar.write("FactEnrollment columns:", list(csv_files['FactEnrollment.csv'].columns))
        
        # For now, let's just work with basic data without complex joins
        enrollment_df = csv_files['FactEnrollment.csv'].copy()
        performance_df = csv_files['FactAssessmentPerformance.csv'].copy()
        
        # Add basic student info if available
        if csv_files['DimStudent.csv'] is not None:
            student_map = csv_files['DimStudent.csv'][['StudentKey', 'StudentName', 'MembershipType']]
            enrollment_df = enrollment_df.merge(student_map, on='StudentKey', how='left')
        
        if csv_files['DimCourse.csv'] is not None:
            course_map = csv_files['DimCourse.csv'][['CourseKey', 'CourseTitle', 'Level']]
            enrollment_df = enrollment_df.merge(course_map, on='CourseKey', how='left')
            performance_df = performance_df.merge(course_map, on='CourseKey', how='left')
        
        # Simple date handling - convert DateKey to datetime
        try:
            enrollment_df['EnrollmentDate'] = pd.to_datetime(enrollment_df['EnrollmentDateKey'].astype(str), format='%Y%m%d')
            enrollment_df['CompletionDate'] = pd.to_datetime(enrollment_df['CompletionDateKey'].astype(str), format='%Y%m%d', errors='coerce')
            performance_df['SubmissionDate'] = pd.to_datetime(performance_df['SubmissionDateKey'].astype(str), format='%Y%m%d')
        except:
            st.sidebar.warning("Could not convert date keys. Using sample dates.")
            enrollment_df['EnrollmentDate'] = pd.date_range('2024-08-29', periods=len(enrollment_df))
            performance_df['SubmissionDate'] = pd.date_range('2024-08-29', periods=len(performance_df))
        
        # Calculate score percentage
        performance_df['ScorePercentage'] = (performance_df['ScoreEarned'] / performance_df['MaxPossibleScore']) * 100
        
        st.sidebar.success(f"✅ Successfully loaded {len(enrollment_df)} enrollments and {len(performance_df)} assessments")
        return enrollment_df, performance_df
        
    except Exception as e:
        st.error(f"Critical error loading data: {str(e)}")
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
    
    # Debug: Check if we have data
    if len(enrollment_df) == 0:
        st.sidebar.warning("No enrollment data loaded")
        return (pd.Timestamp('2024-08-29'), pd.Timestamp('2024-08-29')), [], [], [], []
    
    # Extract date from data
    try:
        min_date = enrollment_df['EnrollmentDate'].min()
        max_date = enrollment_df['EnrollmentDate'].max()
        st.sidebar.info(f"📅 Data range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    except:
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
    
    # Get unique values for filters (with fallbacks)
    try:
        categories = enrollment_df['CategoryName'].unique().tolist()
    except:
        categories = []
    
    try:
        membership_types = enrollment_df['MembershipType'].unique().tolist()
    except:
        membership_types = []
    
    try:
        course_levels = enrollment_df['CourseLevel'].unique().tolist()
    except:
        course_levels = []
    
    try:
        completion_statuses = enrollment_df['CompletionStatus'].unique().tolist()
    except:
        completion_statuses = []
    
    # Create filters only if we have options
    if categories:
        selected_categories = st.sidebar.multiselect(
            "Select Categories",
            options=categories,
            default=categories
        )
    else:
        selected_categories = []
        st.sidebar.warning("No categories available")
    
    if membership_types:
        selected_membership_types = st.sidebar.multiselect(
            "Select Membership Types",
            options=membership_types,
            default=membership_types
        )
    else:
        selected_membership_types = []
        st.sidebar.warning("No membership types available")
    
    if course_levels:
        selected_course_levels = st.sidebar.multiselect(
            "Select Course Levels",
            options=course_levels,
            default=course_levels
        )
    else:
        selected_course_levels = []
        st.sidebar.warning("No course levels available")
    
    if completion_statuses:
        selected_completion_statuses = st.sidebar.multiselect(
            "Select Completion Status",
            options=completion_statuses,
            default=completion_statuses
        )
    else:
        selected_completion_statuses = []
        st.sidebar.warning("No completion statuses available")
    
    return date_range, selected_categories, selected_membership_types, selected_course_levels, selected_completion_statuses
def filter_data(df, date_col, date_range, categories, membership_types=None, course_levels=None, completion_statuses=None):
    """Apply filters to dataframe"""
    
    if len(df) == 0:
        return df
    
    # Start with original dataframe
    filtered_df = df.copy()
    
    # Date filter
    try:
        filtered_df = filtered_df[
            (filtered_df[date_col] >= pd.Timestamp(date_range[0])) & 
            (filtered_df[date_col] <= pd.Timestamp(date_range[1]))
        ]
    except:
        pass  # Skip date filtering if it fails
    
    # Category filter
    if categories and 'CategoryName' in filtered_df.columns:
        try:
            filtered_df = filtered_df[filtered_df['CategoryName'].isin(categories)]
        except:
            pass
    
    # Membership filter
    if membership_types and 'MembershipType' in filtered_df.columns:
        try:
            filtered_df = filtered_df[filtered_df['MembershipType'].isin(membership_types)]
        except:
            pass
    
    # Course level filter
    if course_levels and 'CourseLevel' in filtered_df.columns:
        try:
            filtered_df = filtered_df[filtered_df['CourseLevel'].isin(course_levels)]
        except:
            pass
    
    # Completion status filter
    if completion_statuses and 'CompletionStatus' in filtered_df.columns:
        try:
            filtered_df = filtered_df[filtered_df['CompletionStatus'].isin(completion_statuses)]
        except:
            pass
    
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
    # Load data
    if not st.session_state.data_loaded:
        try:
            enrollment_df, performance_df = load_data_from_csv()
        except:
            st.warning("Using sample data due to loading issues")
            enrollment_df, performance_df = create_sample_data_from_schema()
        
        st.session_state.enrollment_df = enrollment_df
        st.session_state.performance_df = performance_df
        st.session_state.data_loaded = True
    
    enrollment_df = st.session_state.enrollment_df
    performance_df = st.session_state.performance_df
    
    # Debug info
    st.sidebar.subheader("🔍 Data Info")
    st.sidebar.write(f"Enrollments: {len(enrollment_df)}")
    st.sidebar.write(f"Assessments: {len(performance_df)}")
    if len(enrollment_df) > 0:
        st.sidebar.write("Columns:", list(enrollment_df.columns))
                          
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
