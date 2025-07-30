"""
Streamlit GUI for the evi package.
"""
import os
import streamlit as st
import json
from typing import Dict, Any

# Optional import for visualization
try:
    import graphviz
except ImportError:
    graphviz = None

from .core import EviGenerator


def create_visualization(config: Dict[str, Any], framework: str):
    """
    Create a visualization of the agent system based on the framework and configuration.
    
    Args:
        config: The agent configuration
        framework: The framework used
        
    Returns:
        A graphviz.Digraph object or None if visualization could not be created
    """
    if graphviz is None:
        st.warning("Graphviz package not installed. Install it with 'pip install graphviz' for visualizations.")
        return None
        
    try:
        # Create a new directed graph
        dot = graphviz.Digraph()
        dot.attr(rankdir='TB', size='8,5', dpi='300')
        
        # Customize visualization based on the framework
        if framework == "crewai":
            # Add agent nodes
            for agent in config.get("agents", []):
                name = agent.get("name", "Unknown")
                role = agent.get("role", "")
                dot.node(name, f"{name}\n({role})", shape="box")
                
            # Add task nodes and edges
            for task in config.get("tasks", []):
                task_name = task.get("name", "Unknown")
                agent_name = task.get("agent", "")
                dot.node(task_name, task_name, shape="ellipse")
                
                if agent_name:
                    dot.edge(agent_name, task_name)
            
        elif framework == "langgraph":
            # Add node vertices
            for node in config.get("nodes", []):
                name = node.get("name", "Unknown")
                dot.node(name, name, shape="box")
                
            # Add edges between nodes
            for edge in config.get("edges", []):
                source = edge.get("source", "")
                target = edge.get("target", "")
                if source and target:
                    dot.edge(source, target)
            
        elif framework == "react":
            # Add agent nodes
            for agent in config.get("agents", []):
                name = agent.get("name", "Unknown")
                dot.node(name, name, shape="box")
                
            # Add tool nodes
            for tool in config.get("tools", []):
                name = tool.get("name", "Unknown")
                dot.node(name, name, shape="ellipse")
                
            # Add edges from each agent to all tools
            for agent in config.get("agents", []):
                agent_name = agent.get("name", "Unknown")
                for tool in agent.get("tools", []):
                    dot.edge(agent_name, tool)
        
        return dot
        
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="evi - Agent Generator",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 evi - Multi-Agent Framework Generator")
    st.markdown(
        """
        Generate AI agent systems using natural language instructions.
        Simply describe what you want your agent to do, and get ready-to-use code!
        """
    )
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        framework = st.selectbox(
            "Agent Framework",
            options=["crewai", "langgraph", "react"],
            format_func=lambda x: {
                "crewai": "CrewAI",
                "langgraph": "LangGraph",
                "react": "ReAct"
            }.get(x, x.title())
        )
        
        provider = st.selectbox(
            "LLM Provider",
            options=["openai", "gemini"],
            format_func=lambda x: {
                "openai": "OpenAI",
                "gemini": "Google Gemini"
            }.get(x, x.title())
        )
        
        # API key input
        st.header("🔑 API Keys")
        
        if provider == "openai":
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=st.session_state.get("openai_api_key", ""),
                help="Enter your OpenAI API key"
            )
            if api_key:
                st.session_state.openai_api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key
        
        elif provider == "gemini":
            api_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=st.session_state.get("gemini_api_key", ""),
                help="Enter your Google Gemini API key"
            )
            if api_key:
                st.session_state.gemini_api_key = api_key
                os.environ["GEMINI_API_KEY"] = api_key
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Describe Your Agent System")
        
        # Example prompts for reference
        with st.expander("Example prompts"):
            st.markdown("""
            **Example 1:** Create a research assistant that can search academic papers and summarize findings on climate change.
            
            **Example 2:** Build a collaborative agent system where one agent extracts information from news articles, another fact-checks it, and a third writes a summary report.
            
            **Example 3:** Create an agent that can analyze financial data, identify trends, and generate investment recommendations.
            """)
        
        # Text area for user prompt
        user_prompt = st.text_area(
            "Describe what you want your agent system to do",
            height=150,
            placeholder="Example: Create a research assistant that can search academic papers and summarize findings on a given topic...",
            key="user_prompt"
        )
        
        # Advanced options
        with st.expander("Advanced options"):
            model_id = st.text_input(
                "Custom model ID",
                placeholder="e.g., gpt-4 for OpenAI or gemini-1.0-pro for Gemini",
                help="Leave blank to use the default model for the selected provider"
            )
            
            output_format = st.radio(
                "Output format",
                options=["code", "json"],
                format_func=lambda x: "Python Code" if x == "code" else "JSON Configuration",
                horizontal=True
            )
        
        # Generate button
        generate_button = st.button("🚀 Generate Agent System")
    
    # Initialize the state if it doesn't exist
    if "generated_code" not in st.session_state:
        st.session_state.generated_code = None
        
    if "config" not in st.session_state:
        st.session_state.config = None
        
    if "framework" not in st.session_state:
        st.session_state.framework = framework
    
    # Process generation request
    if generate_button and user_prompt:
        with st.spinner("Generating your agent system..."):
            try:
                # Initialize the generator with the specified framework and provider
                generator = EviGenerator(provider=provider, framework=framework)
                
                # Set custom model if provided
                if model_id:
                    generator.provider.set_model_id(model_id)
                
                # Generate the output
                result = generator.generate(prompt=user_prompt, output_format=output_format)
                
                # Store the output in session state
                st.session_state.generated_code = result
                
                # If output was code, try to parse config from generator
                if output_format == "code":
                    try:
                        st.session_state.config = generator.framework.get_default_config()
                    except:
                        # If we can't get the config, it's okay - visualization will be skipped
                        st.session_state.config = None
                else:
                    # For JSON output, parse the JSON
                    try:
                        st.session_state.config = json.loads(result)
                    except:
                        st.session_state.config = None
                
                st.session_state.framework = framework
                
            except Exception as e:
                st.error(f"Error generating agent system: {str(e)}")
    
    # Display the generated output and visualization
    with col2:
        st.header("📊 Visualization")
        if st.session_state.config is not None:
            # Create and display visualization
            dot = create_visualization(st.session_state.config, st.session_state.framework)
            if dot is not None:
                st.graphviz_chart(dot)
            else:
                st.info("Could not create visualization with the current configuration.")
        else:
            st.info("Generate an agent system to see its visualization here.")
    
    # Display generated code/JSON
    if st.session_state.generated_code is not None:
        st.header("🖥️ Generated Output")
        
        # Add a download button
        extension = "py" if output_format == "code" else "json"
        
        st.download_button(
            label="📥 Download",
            data=st.session_state.generated_code,
            file_name=f"agent_system.{extension}",
            mime="text/plain"
        )
        
        # Display the code/JSON with syntax highlighting
        language = "python" if output_format == "code" else "json"
        st.code(st.session_state.generated_code, language=language)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center">
            Made with ❤️ using <b>evi</b> | 
            Created by: Your Name | 
            <a href="https://github.com/username/evi">GitHub Repository</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
