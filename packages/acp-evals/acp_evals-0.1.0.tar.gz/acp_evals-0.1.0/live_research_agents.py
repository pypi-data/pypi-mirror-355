
import asyncio
import json
import os
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import List, Dict, Any

import httpx
from acp_sdk import Message
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from acp_sdk.client import Client
from rich.console import Console

console = Console()

# Simple in-memory storage for this demo
session_storage = defaultdict(list)
execution_traces = []

server = Server()

class TracingWrapper:
    """Wrapper to capture execution traces."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
    def log_execution(self, input_msg: str, output_msg: str, metadata: Dict[str, Any]):
        """Log execution for tracing."""
        trace = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "input": input_msg,
            "output": output_msg,
            "metadata": metadata,
            "session_id": metadata.get("session_id", "unknown"),
            "execution_time_ms": metadata.get("execution_time_ms", 0),
            "token_usage": metadata.get("token_usage", {}),
        }
        execution_traces.append(trace)
        
        # Keep only last 100 traces to avoid memory issues
        if len(execution_traces) > 100:
            execution_traces.pop(0)

# Create tracing wrappers
research_tracer = TracingWrapper("research_agent")
analysis_tracer = TracingWrapper("analysis_agent") 
coordinator_tracer = TracingWrapper("coordinator_agent")

@server.agent(name="research_agent")
async def research_agent(input: List[Message], context: Context) -> AsyncGenerator:
    """Research agent that gathers information."""
    start_time = datetime.now()
    session_id = context.session.id
    
    # Store session data
    session_storage[session_id].extend(input)
    
    input_text = str(input[0]) if input else ""
    
    try:
        # Simulate research with API call or web search
        # For demo, we'll create realistic research output
        if "research" in input_text.lower() or "find" in input_text.lower():
            research_result = f"""
            Research Results for: {input_text}
            
            Based on my research:
            1. Found 3 relevant academic papers
            2. Identified 5 key industry trends
            3. Collected data from 4 authoritative sources
            
            Key findings:
            - Market growth: 15% annually
            - Technology adoption: 67% in enterprise
            - Investment trends: $2.3B in Q4 2024
            
            Sources: Nature, IEEE, McKinsey, Gartner
            Confidence: 85%
            """
        else:
            research_result = f"Analyzed request: {input_text}\n\nGathered relevant information and prepared for handoff to analysis team."
            
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log trace
        research_tracer.log_execution(
            input_text,
            research_result,
            {
                "session_id": session_id,
                "execution_time_ms": execution_time,
                "token_usage": {"input": 150, "output": 200, "total": 350},
                "tools_used": ["web_search", "document_retrieval"],
                "confidence_score": 0.85,
            }
        )
        
        yield MessagePart(content=research_result, role="assistant")
        
    except Exception as e:
        error_msg = f"Research agent error: {str(e)}"
        research_tracer.log_execution(
            input_text,
            error_msg,
            {
                "session_id": session_id,
                "error": True,
                "error_type": type(e).__name__,
            }
        )
        yield MessagePart(content=error_msg, role="assistant")

@server.agent(name="analysis_agent")
async def analysis_agent(input: List[Message], context: Context) -> AsyncGenerator:
    """Analysis agent that processes research findings."""
    start_time = datetime.now()
    session_id = context.session.id
    
    session_storage[session_id].extend(input)
    input_text = str(input[0]) if input else ""
    
    try:
        # Analyze the research data
        analysis_result = f"""
        Analysis Report:
        
        Input processed: {len(input_text)} characters
        
        Key Insights:
        • Market opportunity: High potential in Q1 2025
        • Risk assessment: Medium (regulatory changes possible)
        • Technical feasibility: 92% confidence
        • Resource requirements: 3-6 months, 5-8 engineers
        
        Recommendations:
        1. Proceed with pilot program
        2. Allocate $500K initial budget
        3. Timeline: 120-day MVP development
        4. Success metrics: 80% user adoption, <200ms latency
        
        Next steps: Coordinate with development and business teams.
        """
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        analysis_tracer.log_execution(
            input_text,
            analysis_result,
            {
                "session_id": session_id,
                "execution_time_ms": execution_time,
                "token_usage": {"input": 200, "output": 180, "total": 380},
                "analysis_type": "market_research",
                "confidence_score": 0.92,
            }
        )
        
        yield MessagePart(content=analysis_result, role="assistant")
        
    except Exception as e:
        error_msg = f"Analysis agent error: {str(e)}"
        analysis_tracer.log_execution(
            input_text,
            error_msg,
            {
                "session_id": session_id,
                "error": True,
                "error_type": type(e).__name__,
            }
        )
        yield MessagePart(content=error_msg, role="assistant")

@server.agent(name="coordinator")
async def coordinator_agent(input: List[Message], context: Context) -> AsyncGenerator:
    """Main coordinator that orchestrates the multi-agent workflow."""
    start_time = datetime.now()
    session_id = context.session.id
    
    session_storage[session_id].extend(input)
    input_text = str(input[0]) if input else ""
    
    try:
        # Determine workflow based on request
        if any(keyword in input_text.lower() for keyword in ["research", "analyze", "study", "investigate"]):
            # Research workflow
            console.print(f"🔄 Coordinator: Starting research workflow for session {session_id}")
            
            # Step 1: Hand off to research agent
            async with Client(base_url="http://localhost:8100") as client:
                research_run = await client.run_sync(agent="research_agent", input=input)
            
            research_output = research_run.output
            
            # Step 2: Hand off research results to analysis agent
            async with Client(base_url="http://localhost:8100") as client:
                analysis_run = await client.run_sync(agent="analysis_agent", input=research_output)
            
            analysis_output = analysis_run.output
            
            # Compile final response
            final_response = f"""
            Multi-Agent Research & Analysis Complete
            ========================================
            
            Original Request: {input_text}
            
            Research Phase Results:
            {str(research_output[0]) if research_output else "No research output"}
            
            Analysis Phase Results:
            {str(analysis_output[0]) if analysis_output else "No analysis output"}
            
            Coordination Summary:
            - Executed 2-stage workflow
            - Research agent gathered information
            - Analysis agent processed findings
            - Total processing time: {(datetime.now() - start_time).total_seconds():.2f}s
            
            Status: ✅ Complete
            """
        else:
            # Simple response workflow
            final_response = f"""
            Request processed: {input_text}
            
            This appears to be a simple request that doesn't require multi-agent coordination.
            Response generated directly by coordinator agent.
            
            If you need research and analysis, please include keywords like 'research', 'analyze', or 'investigate' in your request.
            """
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        coordinator_tracer.log_execution(
            input_text,
            final_response,
            {
                "session_id": session_id,
                "execution_time_ms": execution_time,
                "token_usage": {"input": 100, "output": 300, "total": 400},
                "workflow_type": "research_analysis" if "research" in input_text.lower() else "simple",
                "agents_used": ["research_agent", "analysis_agent"] if "research" in input_text.lower() else ["coordinator"],
                "handoff_count": 2 if "research" in input_text.lower() else 0,
            }
        )
        
        yield MessagePart(content=final_response, role="assistant")
        
    except Exception as e:
        error_msg = f"Coordinator error: {str(e)}"
        coordinator_tracer.log_execution(
            input_text,
            error_msg,
            {
                "session_id": session_id,
                "error": True,
                "error_type": type(e).__name__,
            }
        )
        yield MessagePart(content=error_msg, role="assistant")

@server.agent(name="get_traces")
async def traces_agent(input: List[Message], context: Context) -> AsyncGenerator:
    """Special agent to retrieve execution traces for evaluation."""
    traces_json = json.dumps({
        "traces": execution_traces,
        "total_traces": len(execution_traces),
        "timestamp": datetime.now().isoformat()
    }, indent=2)
    
    yield MessagePart(content=traces_json, role="assistant")

@server.agent(name="health_check") 
async def health_agent(input: List[Message], context: Context) -> AsyncGenerator:
    """Health check agent."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": ["coordinator", "research_agent", "analysis_agent", "get_traces", "health_check"],
        "traces_count": len(execution_traces),
        "sessions_active": len(session_storage)
    }
    
    yield MessagePart(content=json.dumps(health_data, indent=2), role="assistant")

if __name__ == "__main__":
    console.print("🚀 Starting Live ACP Multi-Agent System...")
    console.print(f"📊 Telemetry enabled: {len(execution_traces)} traces stored")
    console.print("🌐 Server starting on http://localhost:8100")
    server.run(port=8100)
